"""Stripe webhook handler."""
from flask import request, jsonify
import logging
from . import api_bp
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

    # Handle events as needed
    if event_type == 'payment_intent.succeeded':
        pass  # Already handled synchronously during booking
    elif event_type == 'payment_intent.payment_failed':
        pass  # Could update booking status

    return jsonify({'received': True}), 200
