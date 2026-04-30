"""Cleanup task for the WebhookEvent idempotency table.

Stripe redelivery windows are bounded (a few days at most). Keeping events
forever just bloats the table; we retain 90 days for forensics and prune
the rest nightly.
"""
import logging
from datetime import datetime, timezone, timedelta

from . import celery_app, get_flask_app

logger = logging.getLogger(__name__)

WEBHOOK_RETENTION_DAYS = 90


def _purge_now():
    """Inner purge logic — runs inside an existing app context.

    Split out so tests can call it directly against the test fixture's
    shared in-memory DB instead of having the Celery task spin up its own
    Flask app (which would create a separate SQLite session and miss rows).
    """
    from ..extensions import db
    from ..models.webhook_event import WebhookEvent
    cutoff = datetime.now(timezone.utc) - timedelta(days=WEBHOOK_RETENTION_DAYS)
    deleted = WebhookEvent.query.filter(
        WebhookEvent.received_at < cutoff
    ).delete(synchronize_session=False)
    db.session.commit()
    logger.info(
        "Purged %d WebhookEvent rows older than %d days",
        deleted, WEBHOOK_RETENTION_DAYS,
    )
    return deleted


@celery_app.task(name='app.tasks.purge_old_webhook_events')
def purge_old_webhook_events():
    """Delete WebhookEvent rows older than WEBHOOK_RETENTION_DAYS.

    Run daily via Celery Beat. Idempotent — re-running drops nothing extra.
    """
    app = get_flask_app()
    with app.app_context():
        return _purge_now()
