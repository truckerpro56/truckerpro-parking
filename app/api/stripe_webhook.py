"""Stripe webhook handler."""
from flask import request, jsonify
import logging
from . import api_bp
from ..extensions import db
from ..models.booking import ParkingBooking
from ..services.payment_service import verify_webhook_signature

logger = logging.getLogger(__name__)


@api_bp.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle incoming Stripe webhook events."""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature', '')
    try:
        event = verify_webhook_signature(payload, sig_header)
    except Exception as e:
        logger.warning("Webhook signature verification failed: %s", str(e)[:200])
        return jsonify({'error': 'Invalid signature'}), 400

    event_type = event.get('type', '')
    logger.info("Stripe webhook received: %s", event_type)

    if event_type == 'payment_intent.succeeded':
        _handle_payment_succeeded(event)
    elif event_type == 'payment_intent.payment_failed':
        _handle_payment_failed(event)

    return jsonify({'received': True}), 200


def _handle_payment_succeeded(event):
    """Update booking payment status to paid."""
    pi = event.get('data', {}).get('object', {})
    pi_id = pi.get('id')
    if not pi_id:
        return
    booking = ParkingBooking.query.filter_by(stripe_payment_intent_id=pi_id).first()
    if booking and booking.payment_status != 'paid':
        booking.payment_status = 'paid'
        # Confirm booking if it was waiting on payment (3DS, etc.)
        if booking.status == 'pending_payment':
            booking.status = 'confirmed'
        db.session.commit()
        logger.info("Booking %s payment confirmed via webhook", booking.booking_ref)


def _handle_payment_failed(event):
    """Mark booking as failed when payment fails."""
    pi = event.get('data', {}).get('object', {})
    pi_id = pi.get('id')
    if not pi_id:
        return
    booking = ParkingBooking.query.filter_by(stripe_payment_intent_id=pi_id).first()
    if booking and booking.status not in ('cancelled', 'refunded'):
        booking.payment_status = 'failed'
        booking.status = 'cancelled'
        db.session.commit()
        logger.warning("Booking %s payment failed, marked cancelled", booking.booking_ref)
