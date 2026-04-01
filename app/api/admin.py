"""Admin API endpoints — seed, diagnostics."""
import hmac
from flask import jsonify, request, current_app
from . import api_bp
from ..models.location import ParkingLocation


@api_bp.route('/admin/seed', methods=['POST'])
def admin_seed():
    """One-time seed endpoint. Requires secret key in header."""
    auth = request.headers.get('X-Admin-Key', '')
    admin_key = current_app.config.get('ADMIN_SECRET_KEY', '')
    if not admin_key or not auth or not hmac.compare_digest(auth, admin_key):
        return jsonify({'error': 'Unauthorized'}), 403
    from ..seed.locations import seed_locations
    seed_locations()
    count = ParkingLocation.query.count()
    return jsonify({'success': True, 'locations': count})
