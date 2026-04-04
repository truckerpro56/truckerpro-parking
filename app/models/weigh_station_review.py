"""WeighStationReview — driver reviews for weigh/inspection stations."""
from datetime import datetime, timezone
from ..extensions import db


class WeighStationReview(db.Model):
    __tablename__ = 'weigh_station_reviews'

    id = db.Column(db.Integer, primary_key=True)
    weigh_station_id = db.Column(
        db.Integer, db.ForeignKey('weigh_stations.id'), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship('User', backref='weigh_station_reviews', lazy='select')

    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_ws_review_rating'),
        db.UniqueConstraint('weigh_station_id', 'user_id', name='uq_ws_review_user_station'),
    )
