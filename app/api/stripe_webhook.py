"""Stripe webhook handler."""
from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
import logging
from . import api_bp
from ..extensions import db
from ..models.booking import ParkingBooking
from ..models.webhook_event import WebhookEvent
from ..services.payment_service import verify_webhook_signature

logger = logging.getLogger(__name__)


# Statuses that indicate the booking is in a terminal state and must not be
# silently re-confirmed by a delayed/replayed payment_intent.succeeded event.
_TERMINAL_STATUSES = ('cancelled', 'refunded', 'completed', 'no_show')


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

    event_id = event.get('id')
    event_type = event.get('type', '')
    if not event_id:
        logger.warning("Stripe webhook missing event id")
        return jsonify({'error': 'missing event id'}), 400

    # Idempotency: insert (provider, event_id) up-front; duplicate = silent ack.
    record = WebhookEvent(provider='stripe', event_id=event_id, event_type=event_type)
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        logger.info("Stripe webhook duplicate event ignored: %s", event_id)
        return jsonify({'received': True, 'duplicate': True}), 200

    logger.info("Stripe webhook received: %s (%s)", event_type, event_id)

    if event_type == 'payment_intent.succeeded':
        _handle_payment_succeeded(event)
    elif event_type == 'payment_intent.payment_failed':
        _handle_payment_failed(event)

    return jsonify({'received': True}), 200


def _handle_payment_succeeded(event):
    """Update booking payment status to paid (only if not in a terminal state)."""
    pi = event.get('data', {}).get('object', {})
    pi_id = pi.get('id')
    if not pi_id:
        return
    booking = ParkingBooking.query.filter_by(stripe_payment_intent_id=pi_id).first()
    if not booking:
        return
    if booking.status in _TERMINAL_STATUSES:
        logger.info(
            "Stripe webhook payment_intent.succeeded for terminal booking %s "
            "(status=%s) — ignoring",
            booking.booking_ref, booking.status,
        )
        return
    if booking.payment_status == 'paid' and booking.status == 'confirmed':
        return  # already in desired state
    was_pending = booking.status == 'pending_payment'
    booking.payment_status = 'paid'
    if was_pending:
        booking.status = 'confirmed'
    db.session.commit()
    logger.info("Booking %s payment confirmed via webhook", booking.booking_ref)
    if was_pending:
        from ..tasks.notifications import enqueue_booking_notifications
        enqueue_booking_notifications(booking)


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
