"""Tests for WebhookEvent retention cleanup (Round-4 #K)."""
from datetime import datetime, timezone, timedelta

from app.models.webhook_event import WebhookEvent


def test_purge_removes_events_older_than_retention(app, db):
    from app.tasks.webhook_cleanup import (
        _purge_now as purge_old_webhook_events,
        WEBHOOK_RETENTION_DAYS,
    )
    far_past = datetime.now(timezone.utc) - timedelta(days=WEBHOOK_RETENTION_DAYS + 30)
    recent = datetime.now(timezone.utc) - timedelta(days=10)

    old = WebhookEvent(provider='stripe', event_id='evt_old',
                       event_type='payment_intent.succeeded')
    fresh = WebhookEvent(provider='stripe', event_id='evt_fresh',
                         event_type='payment_intent.succeeded')
    db.session.add_all([old, fresh])
    db.session.flush()
    # Backdate the old row past the retention window
    old.received_at = far_past
    fresh.received_at = recent
    db.session.commit()

    deleted = purge_old_webhook_events()
    assert deleted == 1
    remaining = [e.event_id for e in WebhookEvent.query.all()]
    assert 'evt_fresh' in remaining
    assert 'evt_old' not in remaining


def test_purge_is_idempotent(app, db):
    """Running the task twice in a row should not delete extra rows."""
    from app.tasks.webhook_cleanup import _purge_now as purge_old_webhook_events
    fresh = WebhookEvent(provider='stripe', event_id='evt_keep',
                         event_type='payment_intent.succeeded')
    db.session.add(fresh)
    db.session.commit()

    first = purge_old_webhook_events()
    second = purge_old_webhook_events()
    assert first == 0 and second == 0
    assert WebhookEvent.query.count() == 1


def test_purge_handles_empty_table(app, db):
    """No rows at all → return 0, don't crash."""
    from app.tasks.webhook_cleanup import _purge_now as purge_old_webhook_events
    assert purge_old_webhook_events() == 0
