"""Stripe payment integration."""
import stripe
import logging
from flask import current_app

logger = logging.getLogger(__name__)


def create_payment_intent(amount_cents, currency, customer_id, payment_method_id, description, metadata):
    """Create and confirm a Stripe PaymentIntent."""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    return stripe.PaymentIntent.create(
        amount=amount_cents, currency=currency, customer=customer_id,
        payment_method=payment_method_id, off_session=True, confirm=True,
        description=description, metadata=metadata,
    )


def get_or_create_customer(email, name, stripe_customer_id=None):
    """Get existing or create new Stripe customer. Returns customer ID."""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    if stripe_customer_id:
        return stripe_customer_id
    customer = stripe.Customer.create(email=email, name=name)
    return customer.id


def refund_payment(payment_intent_id):
    """Issue a full refund for a PaymentIntent."""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    return stripe.Refund.create(payment_intent=payment_intent_id)


def verify_webhook_signature(payload, sig_header):
    """Verify Stripe webhook signature and return constructed event."""
    endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET', '')
    return stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
