"""Admin endpoints for truck stop management."""
from flask import jsonify, request, current_app
from . import stops_api_bp
from ..extensions import db
from ..middleware import site_required
from ..models.truck_stop import TruckStop
from ..import_stops.base import upsert_truck_stop, generate_stop_slug
from ..services.border_crossings import compute_border_distance


@stops_api_bp.route('/admin/truck-stops', methods=['POST'])
@site_required('stops')
def admin_create_truck_stops():
    auth = request.headers.get('X-Admin-Key', '')
    admin_key = current_app.config.get('ADMIN_SECRET_KEY') or current_app.config.get('SECRET_KEY', '')
    if not auth or auth != admin_key:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400
    stops_data = data if isinstance(data, list) else [data]
    count = 0
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
        upsert_truck_stop(item)
        count += 1
    db.session.commit()
    return jsonify({'success': True, 'count': count})
