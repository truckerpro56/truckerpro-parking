"""FavoriteStop model — driver's saved truck stops."""
from datetime import datetime, timezone
from ..extensions import db


class FavoriteStop(db.Model):
    __tablename__ = 'favorite_stops'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    truck_stop_id = db.Column(db.Integer, db.ForeignKey('truck_stops.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    truck_stop = db.relationship('TruckStop', backref='favorites')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'truck_stop_id', name='uq_favorite_user_stop'),
    )
