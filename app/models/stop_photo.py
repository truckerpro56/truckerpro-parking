"""StopPhoto model — driver-uploaded photos of truck stops."""
from datetime import datetime, timezone
from ..extensions import db


class StopPhoto(db.Model):
    __tablename__ = 'stop_photos'

    id = db.Column(db.Integer, primary_key=True)
    truck_stop_id = db.Column(db.Integer, db.ForeignKey('truck_stops.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)
    caption = db.Column(db.String(200))
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='stop_photos')
    truck_stop = db.relationship('TruckStop', backref='driver_photos')
