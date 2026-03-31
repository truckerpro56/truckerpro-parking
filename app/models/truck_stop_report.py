"""TruckStopReport model — driver-contributed updates."""
from datetime import datetime, timezone
from ..extensions import db


class TruckStopReport(db.Model):
    __tablename__ = 'truck_stop_reports'

    id = db.Column(db.Integer, primary_key=True)
    truck_stop_id = db.Column(
        db.Integer, db.ForeignKey('truck_stops.id'), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_type = db.Column(db.String(30), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
