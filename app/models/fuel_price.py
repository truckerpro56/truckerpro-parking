"""FuelPrice model — timestamped fuel price data."""
from datetime import datetime, timezone
from ..extensions import db


class FuelPrice(db.Model):
    __tablename__ = 'fuel_prices'

    id = db.Column(db.Integer, primary_key=True)
    truck_stop_id = db.Column(
        db.Integer, db.ForeignKey('truck_stops.id'), nullable=False, index=True
    )
    fuel_type = db.Column(db.String(20), nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    source = db.Column(db.String(20), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
