"""Admin API endpoints — seed, diagnostics."""
from flask import jsonify, request, current_app
from . import api_bp
from ..models.location import ParkingLocation


@api_bp.route('/admin/seed', methods=['POST'])
def admin_seed():
    """One-time seed endpoint. Requires secret key in header."""
    auth = request.headers.get('X-Admin-Key', '')
    if auth != current_app.config.get('SECRET_KEY', ''):
        return jsonify({'error': 'Unauthorized'}), 403
    from ..seed.locations import seed_locations
    seed_locations()
    count = ParkingLocation.query.count()
    return jsonify({'success': True, 'locations': count})
