"""Tests for the Stripe webhook handler."""
from unittest.mock import patch
import pytest

from app.models.booking import ParkingBooking
from app.models.location import ParkingLocation
from app.models.webhook_event import WebhookEvent


def _make_booking(db, *, payment_status='pending', status='pending_payment',
                  pi_id='pi_test_123'):
    loc = ParkingLocation(
        name='Test Lot', slug='test-lot',
        address='123 Test Rd', city='Toronto', province='ON',
        country='CA', latitude=43.65, longitude=-79.38,
        location_type='truck_stop', is_active=True, is_bookable=True,
        owner_id=None,
    )
    db.session.add(loc)
    db.session.flush()
    from datetime import datetime, timezone, timedelta
    start = datetime.now(timezone.utc) + timedelta(days=1)
    booking = ParkingBooking(
        booking_ref='TPP-2026-TEST0001',
        location_id=loc.id,
        driver_id=None,
        booking_type='daily',
        start_datetime=start,
        end_datetime=start + timedelta(days=1),
        subtotal=2500, tax_amount=325, total_amount=2825,
        commission_amount=250,
        stripe_payment_intent_id=pi_id,
        payment_status=payment_status,
        status=status,
    )
    db.session.add(booking)
    db.session.commit()
    return booking


def _event(event_id='evt_1', event_type='payment_intent.succeeded',
           pi_id='pi_test_123'):
    return {
        'id': event_id,
        'type': event_type,
        'data': {'object': {'id': pi_id}},
    }


def _post_event(client, event):
    """Bypass signature verification by patching the verifier."""
    with patch('app.api.stripe_webhook.verify_webhook_signature', return_value=event):
        return client.post(
            '/api/v1/stripe/webhook',
            data=b'{}',
            headers={'Stripe-Signature': 'fake'},
        )


class TestStripeWebhookIdempotency:

    def test_succeeded_confirms_pending_booking(self, client, db):
        booking = _make_booking(db)
        resp = _post_event(client, _event())
        assert resp.status_code == 200
        db.session.refresh(booking)
        assert booking.payment_status == 'paid'
        assert booking.status == 'confirmed'

    def test_duplicate_event_id_is_ignored(self, client, db):
        _make_booking(db)
        evt = _event(event_id='evt_dup_123')
        first = _post_event(client, evt)
        second = _post_event(client, evt)
        assert first.status_code == 200
        assert second.status_code == 200
        assert second.get_json().get('duplicate') is True
        # Only one record persisted
        count = WebhookEvent.query.filter_by(event_id='evt_dup_123').count()
        assert count == 1

    def test_succeeded_does_not_resurrect_refunded_booking(self, client, db):
        booking = _make_booking(
            db, payment_status='refunded', status='refunded', pi_id='pi_ref',
        )
        resp = _post_event(client, _event(event_id='evt_late', pi_id='pi_ref'))
        assert resp.status_code == 200
        db.session.refresh(booking)
        # Must NOT flip back to paid/confirmed
        assert booking.status == 'refunded'
        assert booking.payment_status == 'refunded'

    def test_succeeded_does_not_resurrect_cancelled_booking(self, client, db):
        booking = _make_booking(
            db, payment_status='failed', status='cancelled', pi_id='pi_cnx',
        )
        resp = _post_event(client, _event(event_id='evt_cnx', pi_id='pi_cnx'))
        assert resp.status_code == 200
        db.session.refresh(booking)
        assert booking.status == 'cancelled'

    def test_event_missing_id_rejected(self, client, db):
        evt = {'type': 'payment_intent.succeeded',
               'data': {'object': {'id': 'pi_x'}}}
        resp = _post_event(client, evt)
        assert resp.status_code == 400

    def test_failed_event_marks_pending_cancelled(self, client, db):
        booking = _make_booking(db, pi_id='pi_fail')
        evt = _event(event_id='evt_fail', event_type='payment_intent.payment_failed',
                     pi_id='pi_fail')
        resp = _post_event(client, evt)
        assert resp.status_code == 200
        db.session.refresh(booking)
        assert booking.status == 'cancelled'
        assert booking.payment_status == 'failed'

    def test_succeeded_dispatches_notification_on_pending_to_confirmed(self, client, db):
        booking = _make_booking(db, pi_id='pi_notify')
        with patch(
            'app.tasks.notifications.enqueue_booking_notifications'
        ) as mock_enqueue:
            evt = _event(event_id='evt_notify', pi_id='pi_notify')
            resp = _post_event(client, evt)
        assert resp.status_code == 200
        assert mock_enqueue.called

    def test_succeeded_does_not_redispatch_if_already_confirmed(self, client, db):
        booking = _make_booking(
            db, payment_status='paid', status='confirmed', pi_id='pi_already',
        )
        with patch(
            'app.tasks.notifications.enqueue_booking_notifications'
        ) as mock_enqueue:
            evt = _event(event_id='evt_already', pi_id='pi_already')
            resp = _post_event(client, evt)
        assert resp.status_code == 200
        assert not mock_enqueue.called
