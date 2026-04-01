"""TruckStop model — core location data for truck stops directory."""
from datetime import datetime, timezone
from ..extensions import db


class TruckStop(db.Model):
    __tablename__ = 'truck_stops'

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False, index=True)
    brand_display_name = db.Column(db.String(100))
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    store_number = db.Column(db.String(50))
    address = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    state_province = db.Column(db.String(50), nullable=False, index=True)
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(2), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    highway = db.Column(db.String(50), index=True)
    exit_number = db.Column(db.String(100))
    direction = db.Column(db.String(2))
    total_parking_spots = db.Column(db.Integer)
    truck_spots = db.Column(db.Integer)
    car_spots = db.Column(db.Integer)
    handicap_spots = db.Column(db.Integer)
    reserved_spots = db.Column(db.Integer)
    has_diesel = db.Column(db.Boolean, default=True)
    has_gas = db.Column(db.Boolean, default=False)
    has_def = db.Column(db.Boolean, default=False)
    has_ev_charging = db.Column(db.Boolean, default=False)
    has_showers = db.Column(db.Boolean, default=False)
    shower_count = db.Column(db.Integer)
    has_scale = db.Column(db.Boolean, default=False)
    scale_type = db.Column(db.String(20))
    has_repair = db.Column(db.Boolean, default=False)
    has_tire_service = db.Column(db.Boolean, default=False)
    has_wifi = db.Column(db.Boolean, default=False)
    has_laundry = db.Column(db.Boolean, default=False)
    restaurants = db.Column(db.JSON, default=list)
    loyalty_programs = db.Column(db.JSON, default=list)
    hours_of_operation = db.Column(db.JSON, default=dict)
    phone = db.Column(db.String(20))
    website = db.Column(db.String(300))
    photos = db.Column(db.JSON, default=list)
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_verified = db.Column(db.Boolean, default=False)
    nearest_border_crossing = db.Column(db.String(100))
    border_distance_km = db.Column(db.Float)
    parking_location_id = db.Column(
        db.Integer, db.ForeignKey('parking_locations.id'), nullable=True
    )
    parking_location = db.relationship('ParkingLocation', backref='truck_stops')
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.String(500))
    data_source = db.Column(db.String(20), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    fuel_prices = db.relationship('FuelPrice', backref='truck_stop', lazy='dynamic')
    reviews = db.relationship('TruckStopReview', backref='truck_stop', lazy='dynamic')
    reports = db.relationship('TruckStopReport', backref='truck_stop', lazy='dynamic')

    __table_args__ = (
        db.Index('idx_truck_stops_coords', 'latitude', 'longitude'),
    )
