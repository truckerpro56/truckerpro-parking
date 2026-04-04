"""WeighStation model — highway weigh stations and inspection stations."""
from datetime import datetime, timezone
from ..extensions import db


class WeighStation(db.Model):
    __tablename__ = 'weigh_stations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    station_id = db.Column(db.String(50), index=True)
    highway = db.Column(db.String(100), index=True)
    direction = db.Column(db.String(20))
    city = db.Column(db.String(100))
    county = db.Column(db.String(100))
    state_province = db.Column(db.String(50), nullable=False, index=True)
    country = db.Column(db.String(2), nullable=False, default='US', index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    functional_class = db.Column(db.String(10))
    annual_truck_count = db.Column(db.Integer)
    days_active = db.Column(db.Integer)
    is_permanent = db.Column(db.Boolean, default=True)
    has_bypass = db.Column(db.Boolean, default=False)  # PrePass/DriveWyze
    station_type = db.Column(db.String(50), default='weigh_station')  # weigh_station, inspection_station, portable
    data_source = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    reviews = db.relationship('WeighStationReview', backref='weigh_station', lazy='dynamic',
                               cascade='all, delete-orphan')
    statuses = db.relationship('WeighStationStatus', backref='weigh_station', lazy='dynamic',
                                cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_weigh_stations_coords', 'latitude', 'longitude'),
    )
