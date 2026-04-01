from datetime import datetime, timezone
from flask_login import UserMixin
from ..extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(255), nullable=True, default='')
    phone = db.Column(db.String(20))
    # OTP auth (stops.truckerpro.net — no passwords)
    otp_code = db.Column(db.String(128))         # SHA256 hash of OTP
    otp_expires_at = db.Column(db.DateTime(timezone=True))
    otp_attempts = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default='driver')  # driver, owner, admin
    stripe_customer_id = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    display_name = db.Column(db.String(100))
    home_state = db.Column(db.String(50))   # driver's home state/province
    truck_type = db.Column(db.String(50))   # e.g., "18-wheeler", "bobtail"
    contribution_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    locations = db.relationship('ParkingLocation', backref='owner', lazy='dynamic',
                                cascade='all, delete-orphan')
    bookings = db.relationship('ParkingBooking', backref='driver', lazy='dynamic',
                               cascade='all, delete-orphan')
    reviews = db.relationship('ParkingReview', backref='driver', lazy='dynamic',
                              cascade='all, delete-orphan')
