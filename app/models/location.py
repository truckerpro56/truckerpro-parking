from datetime import datetime, timezone
from ..extensions import db


class ParkingLocation(db.Model):
    __tablename__ = 'parking_locations'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    province = db.Column(db.String(50), nullable=False, index=True)
    postal_code = db.Column(db.String(10))
    country = db.Column(db.String(2), default='CA')
    latitude = db.Column(db.Numeric(10, 7), nullable=False)
    longitude = db.Column(db.Numeric(10, 7), nullable=False)
    location_type = db.Column(db.String(50), nullable=False, default='truck_stop', index=True)
    total_spots = db.Column(db.Integer, default=0)
    bobtail_spots = db.Column(db.Integer, default=0)
    trailer_spots = db.Column(db.Integer, default=0)
    oversize_spots = db.Column(db.Integer, default=0)
    lcv_capable = db.Column(db.Boolean, default=False)
    hourly_rate = db.Column(db.Integer)  # cents
    daily_rate = db.Column(db.Integer)   # cents
    weekly_rate = db.Column(db.Integer)  # cents
    monthly_rate = db.Column(db.Integer) # cents
    amenities = db.Column(db.JSON, default=list)
    photos = db.Column(db.JSON, default=list)
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(255))
    access_instructions = db.Column(db.Text)
    gate_code = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_bookable = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.String(500))
    nearby_highways = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    bookings = db.relationship('ParkingBooking', backref='location', lazy='dynamic')
    reviews = db.relationship('ParkingReview', backref='location', lazy='dynamic')
    availability = db.relationship('ParkingAvailability', backref='location', lazy='dynamic')

    __table_args__ = (
        db.Index('idx_parking_locations_coords', 'latitude', 'longitude'),
    )
