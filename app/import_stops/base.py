"""Shared import logic — upsert, slug generation, border distance."""
from ..extensions import db
from ..models.truck_stop import TruckStop
from ..services.geo_service import slugify
from ..services.border_crossings import compute_border_distance


def generate_stop_slug(brand, store_number, city, state_province):
    brand_slug = brand.replace('_', '-')
    parts = [brand_slug]
    if store_number:
        parts.append(store_number)
    parts.extend([city, state_province])
    return slugify(' '.join(parts))


def upsert_truck_stop(data):
    """Insert or update a truck stop by brand + store_number. Does NOT commit."""
    existing = None
    if data.get('store_number'):
        existing = TruckStop.query.filter_by(
            brand=data['brand'], store_number=data['store_number']
        ).first()
    if existing:
        for key, val in data.items():
            if key != 'id' and val is not None:
                setattr(existing, key, val)
        compute_border_distance(existing)
        return existing
    stop = TruckStop(**data)
    compute_border_distance(stop)
    db.session.add(stop)
    return stop
