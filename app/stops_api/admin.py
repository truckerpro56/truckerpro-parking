"""Admin endpoints for truck stop management."""
import hmac
import logging
from flask import jsonify, request, current_app
from sqlalchemy.exc import IntegrityError
from . import stops_api_bp
from ..extensions import db
from ..middleware import site_required
from ..models.truck_stop import TruckStop
from ..import_stops.base import upsert_truck_stop, generate_stop_slug
from ..services.border_crossings import compute_border_distance
from ..stops.helpers import stop_canonical_url

logger = logging.getLogger(__name__)


@stops_api_bp.route('/admin/truck-stops', methods=['POST'])
@site_required('stops')
def admin_create_truck_stops():
    auth = request.headers.get('X-Admin-Key', '')
    admin_key = current_app.config.get('ADMIN_SECRET_KEY') or current_app.config.get('SECRET_KEY', '')
    if not admin_key or not auth or not hmac.compare_digest(auth, admin_key):
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400
    stops_data = data if isinstance(data, list) else [data]
    count = 0
    skipped = 0
    touched_slugs = []
    for item in stops_data:
        if 'slug' not in item:
            item['slug'] = generate_stop_slug(
                item.get('brand', 'independent'),
                item.get('store_number', ''),
                item.get('city', ''),
                item.get('state_province', ''),
            )
        if 'data_source' not in item:
            item['data_source'] = 'manual'
        try:
            upsert_truck_stop(item)
            db.session.flush()
            touched_slugs.append(item['slug'])
            count += 1
        except IntegrityError:
            db.session.rollback()
            skipped += 1
            logger.warning('Skipped duplicate: %s', item.get('slug', ''))
    db.session.commit()

    if touched_slugs:
        stops = TruckStop.query.filter(TruckStop.slug.in_(touched_slugs),
                                       TruckStop.is_active == True).all()
        urls = [stop_canonical_url(s) for s in stops]
        from ..tasks.indexnow_task import enqueue_indexnow
        enqueue_indexnow('stops.truckerpro.net', urls)

    return jsonify({'success': True, 'count': count, 'skipped': skipped})
