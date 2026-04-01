"""RestArea model — highway rest areas and welcome centers."""
from datetime import datetime, timezone
from ..extensions import db


class RestArea(db.Model):
    __tablename__ = 'rest_areas'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    highway = db.Column(db.String(100), index=True)
    mile_post = db.Column(db.String(20))
    direction = db.Column(db.String(20))  # EB, WB, NB, SB
    city = db.Column(db.String(100), index=True)
    county = db.Column(db.String(100))
    state_province = db.Column(db.String(50), nullable=False, index=True)
    country = db.Column(db.String(2), nullable=False, default='US', index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    parking_spaces = db.Column(db.Integer)
    truck_parking = db.Column(db.Boolean, default=False)
    has_restrooms = db.Column(db.Boolean, default=True)
    has_picnic = db.Column(db.Boolean, default=False)
    has_vending = db.Column(db.Boolean, default=False)
    has_water = db.Column(db.Boolean, default=False)
    has_pet_area = db.Column(db.Boolean, default=False)
    is_welcome_center = db.Column(db.Boolean, default=False)
    is_seasonal = db.Column(db.Boolean, default=False)
    area_type = db.Column(db.String(50), default='rest_area')  # rest_area, welcome_center, turnout
    data_source = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.Index('idx_rest_areas_coords', 'latitude', 'longitude'),
    )
