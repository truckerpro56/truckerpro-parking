from datetime import datetime, timezone
from flask_login import UserMixin
from ..extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='driver')  # driver, owner, admin
    stripe_customer_id = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
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
