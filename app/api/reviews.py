"""Review API endpoints — submit reviews for completed bookings."""
from flask import jsonify, request
from flask_login import login_required, current_user
import logging

from . import api_bp
from ..extensions import db
from ..models.booking import ParkingBooking
from ..models.review import ParkingReview

logger = logging.getLogger(__name__)


@api_bp.route('/reviews', methods=['POST'])
@login_required
def submit_review():
    """Submit a review for a completed booking."""
    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    rating = data.get('rating')
    review_text = data.get('review_text', '').strip()

    if not booking_id or rating is None:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    try:
        rating = int(rating)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Rating must be a number'}), 400

    if rating < 1 or rating > 5:
        return jsonify({'success': False, 'error': 'Rating must be 1-5'}), 400

    # Verify booking belongs to user and is completed
    booking = ParkingBooking.query.filter_by(
        id=booking_id, driver_id=current_user.id,
    ).first()

    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    if booking.status not in ('completed', 'checked_in'):
        return jsonify({'success': False, 'error': 'Can only review completed bookings'}), 400

    # Check if already reviewed
    existing = ParkingReview.query.filter_by(booking_id=booking_id).first()
    if existing:
        return jsonify({'success': False, 'error': 'Already reviewed'}), 400

    try:
        review = ParkingReview(
            booking_id=booking_id,
            location_id=booking.location_id,
            driver_id=current_user.id,
            rating=rating,
            review_text=review_text[:2000] if review_text else '',
            is_verified=True,
        )
        db.session.add(review)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error("Review submission failed: %s", str(e)[:200], exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to submit review'}), 500
