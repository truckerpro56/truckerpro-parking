"""Template helpers for stops.truckerpro.net pages."""
from ..services.geo_service import format_price, slugify
from ..constants import (
    US_STATES, US_STATE_CODE_TO_SLUG, PROVINCE_MAP, PROVINCE_CODE_TO_SLUG,
    ALL_REGIONS, ALL_REGION_CODE_TO_SLUG, BRAND_MAP, BRAND_SLUG_TO_KEY,
)


def state_code_to_slug(code):
    return ALL_REGION_CODE_TO_SLUG.get(code, slugify(code))

def state_slug_to_code(slug):
    region = ALL_REGIONS.get(slug)
    return region['code'] if region else None

def state_slug_to_name(slug):
    region = ALL_REGIONS.get(slug)
    return region['name'] if region else slug.replace('-', ' ').title()

def country_for_state(code):
    if code in US_STATE_CODE_TO_SLUG:
        return 'US'
    if code in PROVINCE_CODE_TO_SLUG:
        return 'CA'
    return None

def brand_key_to_slug(brand_key):
    info = BRAND_MAP.get(brand_key)
    return info['slug'] if info else slugify(brand_key)

def brand_slug_to_key(slug):
    return BRAND_SLUG_TO_KEY.get(slug)

def brand_slug_to_name(slug):
    key = BRAND_SLUG_TO_KEY.get(slug)
    if key:
        return BRAND_MAP[key]['name']
    return slug.replace('-', ' ').title()

def highway_to_slug(highway):
    return slugify(highway)

def stop_to_card(stop):
    return {
        'id': stop.id, 'name': stop.name, 'slug': stop.slug,
        'brand': stop.brand, 'brand_display_name': stop.brand_display_name,
        'city': stop.city, 'state_province': stop.state_province,
        'country': stop.country, 'highway': stop.highway,
        'exit_number': stop.exit_number,
        'total_parking_spots': stop.total_parking_spots,
        'has_diesel': stop.has_diesel, 'has_showers': stop.has_showers,
        'has_scale': stop.has_scale, 'has_repair': stop.has_repair,
        'has_wifi': stop.has_wifi, 'latitude': stop.latitude,
        'longitude': stop.longitude,
        'state_slug': state_code_to_slug(stop.state_province),
        'city_slug': slugify(stop.city),
        'brand_slug': brand_key_to_slug(stop.brand),
        'country_slug': 'us' if stop.country == 'US' else 'canada',
    }
