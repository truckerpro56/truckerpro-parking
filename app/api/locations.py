# Parking location API endpoints — will be populated from existing parking_club_routes.py
from flask import jsonify
from . import api_bp


@api_bp.route('/locations')
def list_locations():
    """Placeholder — full implementation coming from truckerpro-web extraction."""
    return jsonify({'locations': [], 'total': 0, 'message': 'Coming soon'})


@api_bp.route('/locations/<int:location_id>')
def get_location(location_id):
    return jsonify({'error': 'Coming soon'}), 501
