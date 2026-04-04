"""WeighStationStatus — driver-reported live status updates (7-day TTL)."""
from datetime import datetime, timezone
from ..extensions import db


class WeighStationStatus(db.Model):
    __tablename__ = 'weigh_station_statuses'

    id = db.Column(db.Integer, primary_key=True)
    weigh_station_id = db.Column(
        db.Integer, db.ForeignKey('weigh_stations.id'), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(30), nullable=False)  # open, closed, slow, fast, inspection_only, portable_active
    wait_minutes = db.Column(db.Integer)  # estimated wait time
    note = db.Column(db.String(500))
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship('User', backref='weigh_station_statuses', lazy='select')

    VALID_STATUSES = ('open', 'closed', 'slow', 'fast', 'inspection_only', 'portable_active')
    STATUS_LABELS = {
        'open': 'Open',
        'closed': 'Closed',
        'slow': 'Slow — Long Wait',
        'fast': 'Fast — No Wait',
        'inspection_only': 'Inspection Only',
        'portable_active': 'Portable Scales Active',
    }
    STATUS_ICONS = {
        'open': 'fa-circle-check',
        'closed': 'fa-circle-xmark',
        'slow': 'fa-clock',
        'fast': 'fa-bolt',
        'inspection_only': 'fa-clipboard-check',
        'portable_active': 'fa-truck-ramp-box',
    }
    STATUS_COLORS = {
        'open': '#10b981',
        'closed': '#ef4444',
        'slow': '#f59e0b',
        'fast': '#3b82f6',
        'inspection_only': '#8b5cf6',
        'portable_active': '#f97316',
    }
