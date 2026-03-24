from ..extensions import db


class ParkingAvailability(db.Model):
    __tablename__ = 'parking_availability'

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('parking_locations.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    available_spots = db.Column(db.Integer, nullable=False, default=0)
    is_closed = db.Column(db.Boolean, default=False)
    special_notes = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint('location_id', 'date', name='uq_availability_location_date'),
    )
