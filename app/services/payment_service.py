"""Stripe payment integration."""
import stripe
import logging
from flask import current_app

logger = logging.getLogger(__name__)


def create_payment_intent(amount_cents, currency, customer_id, payment_method_id,
                          description, metadata, idempotency_key=None):
    """Create and confirm a Stripe PaymentIntent.

    `idempotency_key` should be tied to the booking attempt (the caller's
    booking_ref is a good choice). With it set, network retries / double-
    submits won't create duplicate charges — Stripe returns the original
    PaymentIntent on a key collision.
    """
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    extra = {}
    if idempotency_key:
        extra['idempotency_key'] = idempotency_key
    return stripe.PaymentIntent.create(
        amount=amount_cents, currency=currency, customer=customer_id,
        payment_method=payment_method_id, off_session=True, confirm=True,
        description=description, metadata=metadata,
        **extra,
    )


def get_or_create_customer(email, name, stripe_customer_id=None):
    """Get existing or create new Stripe customer. Returns customer ID."""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    if stripe_customer_id:
        return stripe_customer_id
    customer = stripe.Customer.create(email=email, name=name)
    return customer.id


def refund_payment(payment_intent_id, idempotency_key=None):
    """Issue a full refund for a PaymentIntent.

    Idempotency key defaults to `refund-<payment_intent_id>` so retrying the
    refund call (e.g., after a network blip during a failed booking insert)
    does not produce a second refund — Stripe returns the original Refund.
    """
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    key = idempotency_key or f'refund-{payment_intent_id}'
    return stripe.Refund.create(payment_intent=payment_intent_id, idempotency_key=key)


def verify_webhook_signature(payload, sig_header):
    """Verify Stripe webhook signature and return constructed event."""
    endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET', '')
    if not endpoint_secret:
        raise ValueError('STRIPE_WEBHOOK_SECRET not configured')
    return stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
