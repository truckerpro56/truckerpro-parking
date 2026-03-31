"""TruckStopReview model — driver reviews with moderation."""
from datetime import datetime, timezone
from ..extensions import db


class TruckStopReview(db.Model):
    __tablename__ = 'truck_stop_reviews'

    id = db.Column(db.Integer, primary_key=True)
    truck_stop_id = db.Column(
        db.Integer, db.ForeignKey('truck_stops.id'), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)
    photos = db.Column(db.JSON, default=list)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_ts_review_rating'),
        db.UniqueConstraint('truck_stop_id', 'user_id', name='uq_ts_review_user_stop'),
    )
