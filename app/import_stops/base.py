"""Shared import logic — upsert, slug generation, border distance."""
import logging
from ..extensions import db
from ..models.truck_stop import TruckStop
from ..services.geo_service import slugify
from ..services.border_crossings import compute_border_distance

logger = logging.getLogger(__name__)

# Max lengths must match TruckStop model column sizes
_STRING_LIMITS = {
    'brand': 50,
    'brand_display_name': 100,
    'name': 200,
    'slug': 200,
    'store_number': 50,
    'address': 300,
    'city': 100,
    'state_province': 50,
    'postal_code': 20,
    'country': 2,
    'highway': 50,
    'exit_number': 100,
    'direction': 2,
    'scale_type': 20,
    'phone': 20,
    'website': 300,
    'data_source': 20,
}


def _truncate_strings(data):
    """Truncate string fields to match DB column limits, logging any that overflow."""
    for field, limit in _STRING_LIMITS.items():
        val = data.get(field)
        if isinstance(val, str) and len(val) > limit:
            logger.warning(
                "Truncating %s from %d to %d chars: %r",
                field, len(val), limit, val,
            )
            data[field] = val[:limit]
    return data


def generate_stop_slug(brand, store_number, city, state_province):
    brand_slug = brand.replace('_', '-')
    parts = [brand_slug]
    if store_number:
        parts.append(store_number)
    parts.extend([city, state_province])
    return slugify(' '.join(parts))


def upsert_truck_stop(data):
    """Insert or update a truck stop by brand + store_number. Does NOT commit."""
    _truncate_strings(data)
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
