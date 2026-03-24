"""Booking API endpoints — create parking bookings with Stripe payment."""
from datetime import datetime
from flask import jsonify, request
from flask_login import login_required, current_user
import logging

from . import api_bp
from ..extensions import db
from ..models.location import ParkingLocation
from ..models.booking import ParkingBooking
from ..services.booking_service import (
    calculate_subtotal, calculate_tax, calculate_commission, generate_booking_ref,
)
from ..services.payment_service import (
    create_payment_intent, get_or_create_customer, refund_payment,
)
from ..services.geo_service import format_price

logger = logging.getLogger(__name__)


@api_bp.route('/bookings', methods=['POST'])
@login_required
def create_booking():
    """Create a parking booking with Stripe payment."""
    data = request.get_json() or {}
    location_id = data.get('location_id')
    start = data.get('start_datetime')
    end = data.get('end_datetime')
    vehicle_type = data.get('vehicle_type', 'truck_and_trailer')
    vehicle_plate = data.get('vehicle_plate', '')
    booking_type = data.get('booking_type', 'daily')
    payment_method_id = data.get('payment_method_id')

    if not all([location_id, start, end, payment_method_id]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    # Validate dates
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid date format'}), 400

    if end_dt <= start_dt:
        return jsonify({'success': False, 'error': 'End date must be after start date'}), 400

    # Get location
    loc = ParkingLocation.query.filter_by(id=location_id, is_active=True).first()
    if not loc:
        return jsonify({'success': False, 'error': 'Location not found'}), 404
    if not loc.is_bookable:
        return jsonify({'success': False, 'error': 'Location does not accept bookings'}), 400

    # Check availability — count overlapping confirmed bookings
    overlap_count = ParkingBooking.query.filter(
        ParkingBooking.location_id == location_id,
        ParkingBooking.status.in_(['confirmed', 'checked_in']),
        ParkingBooking.start_datetime < end_dt,
        ParkingBooking.end_datetime > start_dt,
    ).count()

    total_spots = loc.total_spots or 0
    if total_spots > 0 and overlap_count >= total_spots:
        return jsonify({'success': False, 'error': 'No spots available for the selected dates'}), 409

    # Determine rate
    rate_map = {
        'hourly': loc.hourly_rate,
        'daily': loc.daily_rate,
        'weekly': loc.weekly_rate,
        'monthly': loc.monthly_rate,
    }
    rate = rate_map.get(booking_type)
    if rate is None:
        return jsonify({'success': False, 'error': f'No {booking_type} rate available'}), 400

    # Calculate pricing
    subtotal = calculate_subtotal(rate, booking_type, start_dt, end_dt)
    tax_amount, tax_type = calculate_tax(subtotal, loc.province)
    total_amount = subtotal + tax_amount
    commission = calculate_commission(subtotal)
    booking_ref = generate_booking_ref()

    payment_intent = None
    try:
        # Get or create Stripe customer
        customer_id = get_or_create_customer(
            email=current_user.email,
            name=current_user.name or current_user.email,
            stripe_customer_id=current_user.stripe_customer_id,
        )

        # Save Stripe customer ID if newly created
        if not current_user.stripe_customer_id:
            current_user.stripe_customer_id = customer_id
            db.session.add(current_user)

        # Create Stripe payment
        payment_intent = create_payment_intent(
            amount_cents=total_amount,
            currency='cad',
            customer_id=customer_id,
            payment_method_id=payment_method_id,
            description=f"Truck Parking: {loc.name} - {booking_ref}",
            metadata={
                'booking_ref': booking_ref,
                'location_id': str(location_id),
                'driver_id': str(current_user.id),
            },
        )

        payment_status = 'paid' if payment_intent.status == 'succeeded' else 'pending'

        # Create booking record
        booking = ParkingBooking(
            booking_ref=booking_ref,
            location_id=location_id,
            driver_id=current_user.id,
            vehicle_type=vehicle_type,
            vehicle_plate=vehicle_plate[:20] if vehicle_plate else '',
            start_datetime=start_dt,
            end_datetime=end_dt,
            booking_type=booking_type,
            subtotal=subtotal,
            tax_amount=tax_amount,
            tax_type=tax_type,
            total_amount=total_amount,
            commission_amount=commission,
            stripe_payment_intent_id=payment_intent.id,
            payment_status=payment_status,
            status='confirmed',
        )
        db.session.add(booking)
        db.session.commit()

        return jsonify({
            'success': True,
            'booking_ref': booking_ref,
            'total_amount': total_amount,
            'total_display': format_price(total_amount),
        })

    except Exception as e:
        db.session.rollback()
        # If Stripe charge succeeded but DB insert failed, refund the charge
        try:
            if payment_intent is not None and payment_intent.status == 'succeeded':
                refund_payment(payment_intent.id)
                logger.warning("Booking DB insert failed, refunded Stripe PI %s", payment_intent.id)
        except Exception as refund_err:
            logger.error(
                "CRITICAL: Booking failed AND refund failed for PI %s: %s",
                payment_intent.id, str(refund_err)[:200],
            )
        logger.error("Booking creation failed: %s", str(e)[:300], exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Booking failed. Please try again. If charged, a refund will be issued.',
        }), 500
