"""Tests for Stripe idempotency wiring in payment_service.

Regression coverage for Round-2 #C: a network retry / double-click on a
booking submission must not create two charges, and a retried refund must
not refund twice.
"""
from unittest.mock import patch, MagicMock


def test_create_payment_intent_passes_idempotency_key(app):
    with app.app_context():
        with patch('app.services.payment_service.stripe.PaymentIntent.create') as mock_create:
            mock_create.return_value = MagicMock(id='pi_test', status='succeeded')
            from app.services.payment_service import create_payment_intent
            create_payment_intent(
                amount_cents=2500, currency='cad',
                customer_id='cus_x', payment_method_id='pm_x',
                description='', metadata={},
                idempotency_key='pi-TPP-2026-DEADBEEF',
            )
            kwargs = mock_create.call_args.kwargs
            assert kwargs.get('idempotency_key') == 'pi-TPP-2026-DEADBEEF'


def test_create_payment_intent_omits_key_when_not_provided(app):
    """Backward compat: callers that don't pass a key still work."""
    with app.app_context():
        with patch('app.services.payment_service.stripe.PaymentIntent.create') as mock_create:
            mock_create.return_value = MagicMock(id='pi_test', status='succeeded')
            from app.services.payment_service import create_payment_intent
            create_payment_intent(
                amount_cents=2500, currency='cad',
                customer_id='cus_x', payment_method_id='pm_x',
                description='', metadata={},
            )
            kwargs = mock_create.call_args.kwargs
            assert 'idempotency_key' not in kwargs


def test_refund_payment_uses_default_idempotency_key(app):
    with app.app_context():
        with patch('app.services.payment_service.stripe.Refund.create') as mock_create:
            mock_create.return_value = MagicMock(id='re_test')
            from app.services.payment_service import refund_payment
            refund_payment('pi_abc123')
            kwargs = mock_create.call_args.kwargs
            assert kwargs.get('idempotency_key') == 'refund-pi_abc123'
            assert kwargs.get('payment_intent') == 'pi_abc123'


def test_refund_payment_explicit_idempotency_key_overrides_default(app):
    with app.app_context():
        with patch('app.services.payment_service.stripe.Refund.create') as mock_create:
            mock_create.return_value = MagicMock(id='re_test')
            from app.services.payment_service import refund_payment
            refund_payment('pi_abc123', idempotency_key='custom-key')
            kwargs = mock_create.call_args.kwargs
            assert kwargs.get('idempotency_key') == 'custom-key'


def test_bookings_route_passes_idempotency_key():
    """Static check: the booking route must hand a per-booking key into Stripe."""
    import inspect
    from app.api import bookings
    src = inspect.getsource(bookings.create_booking)
    assert 'idempotency_key' in src
    assert "f'pi-{booking_ref}'" in src or 'pi-{booking_ref}' in src
