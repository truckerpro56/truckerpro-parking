# Booking API endpoints — will be populated from existing parking_club_routes.py
from flask import jsonify
from . import api_bp


@api_bp.route('/bookings', methods=['POST'])
def create_booking():
    """Placeholder — full implementation coming from truckerpro-web extraction."""
    return jsonify({'error': 'Coming soon'}), 501
