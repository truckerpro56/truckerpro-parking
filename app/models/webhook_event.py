from datetime import datetime, timezone
from ..extensions import db


class WebhookEvent(db.Model):
    """Idempotency record for processed external webhook events.

    Currently used for Stripe; `provider` lets us reuse for other providers.
    Insert succeeds only on first delivery; duplicates raise IntegrityError.
    """
    __tablename__ = 'webhook_events'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(32), nullable=False, default='stripe')
    event_id = db.Column(db.String(255), nullable=False)
    event_type = db.Column(db.String(64))
    received_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint('provider', 'event_id', name='uq_webhook_events_provider_event'),
    )
