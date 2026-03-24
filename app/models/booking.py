from datetime import datetime, timezone
from ..extensions import db


class ParkingBooking(db.Model):
    __tablename__ = 'parking_bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_ref = db.Column(db.String(20), unique=True, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('parking_locations.id'), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    fleet_id = db.Column(db.Integer)
    vehicle_type = db.Column(db.String(50), default='truck_and_trailer')
    vehicle_plate = db.Column(db.String(20))
    start_datetime = db.Column(db.DateTime(timezone=True), nullable=False)
    end_datetime = db.Column(db.DateTime(timezone=True), nullable=False)
    booking_type = db.Column(db.String(20), nullable=False)  # hourly, daily, weekly, monthly
    subtotal = db.Column(db.Integer, nullable=False)  # cents
    tax_amount = db.Column(db.Integer, default=0)
    tax_type = db.Column(db.String(10))
    total_amount = db.Column(db.Integer, nullable=False)  # cents
    commission_amount = db.Column(db.Integer, default=0)
    stripe_payment_intent_id = db.Column(db.String(255))
    stripe_transfer_id = db.Column(db.String(255))
    payment_status = db.Column(db.String(20), default='pending', index=True)
    status = db.Column(db.String(20), default='confirmed', index=True)
    cancellation_reason = db.Column(db.Text)
    cancelled_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    review = db.relationship('ParkingReview', backref='booking', uselist=False, lazy='select')

    __table_args__ = (
        db.Index('idx_parking_bookings_dates', 'start_datetime', 'end_datetime'),
    )
