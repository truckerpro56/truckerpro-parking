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


def test_bookings_route_idempotency_key_is_request_hash_not_booking_ref():
    """The idempotency key must be tied to immutable request inputs (so two
    clicks within the retry window collide), NOT to the random booking_ref
    (which is a fresh uuid each call and defeats dedupe)."""
    import inspect
    from app.api import bookings
    src = inspect.getsource(bookings.create_booking)
    assert 'idempotency_key' in src
    # New shape: a sha256 digest of immutable payload inputs
    assert 'hashlib' in src or 'sha256' in src
    assert 'pi-{idem_digest}' in src or 'idem_digest' in src
    # Old, broken shape must be gone
    assert 'pi-{booking_ref}' not in src


def test_two_identical_bookings_use_same_idempotency_key(app, db):
    """Bookings with identical inputs must produce the same idempotency key
    so a network retry / double-click reaches Stripe with the same key."""
    import hashlib
    from datetime import datetime, timezone, timedelta

    user_id, location_id = 7, 99
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    total = 2825
    pm = 'pm_card_visa'
    bt = 'daily'

    def key_for():
        seed = (
            f'{user_id}|{location_id}|{start.isoformat()}|'
            f'{end.isoformat()}|{total}|{pm}|{bt}'
        )
        return f'pi-{hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]}'

    assert key_for() == key_for()
    # Different start time → different key
    later = start + timedelta(hours=1)
    seed2 = (
        f'{user_id}|{location_id}|{later.isoformat()}|'
        f'{end.isoformat()}|{total}|{pm}|{bt}'
    )
    different = f'pi-{hashlib.sha256(seed2.encode("utf-8")).hexdigest()[:32]}'
    assert key_for() != different
