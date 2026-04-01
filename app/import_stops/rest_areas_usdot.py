"""USDOT rest area importer — pulls from ArcGIS Feature Service."""
import logging
import requests
from ..services.geo_service import slugify

logger = logging.getLogger(__name__)

USDOT_REST_AREA_URL = (
    'https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/'
    'Truck_Stop_Parking/FeatureServer/0/query'
)


def fetch_rest_areas():
    """Fetch all rest areas from USDOT ArcGIS. Returns list of feature dicts."""
    all_features = []
    offset = 0
    page_size = 2000
    while True:
        resp = requests.get(USDOT_REST_AREA_URL, params={
            'where': '1=1',
            'outFields': '*',
            'f': 'json',
            'resultRecordCount': page_size,
            'resultOffset': offset,
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        features = data.get('features', [])
        if not features:
            break
        all_features.extend(features)
        if len(features) < page_size:
            break
        offset += page_size
    return all_features


def parse_usdot_feature(feature):
    """Map a USDOT ArcGIS feature to RestArea field dict."""
    attrs = feature.get('attributes', {})
    geom = feature.get('geometry', {})

    name = (attrs.get('nhs_rest_s') or 'Rest Area').strip()
    highway = (attrs.get('highway_ro') or '').strip()
    state = (attrs.get('state') or '').strip()
    city = (attrs.get('municipali') or '').strip()
    county = (attrs.get('county_only') or '').strip()
    mile_post = str(attrs.get('mile_post') or '').strip()
    parking = attrs.get('number_of_')
    lat = geom.get('y') or attrs.get('latitude')
    lng = geom.get('x') or attrs.get('longitude')

    # Detect direction from highway name (e.g., "I-10 EB")
    direction = None
    for d in ('EB', 'WB', 'NB', 'SB'):
        if f' {d}' in highway.upper():
            direction = d
            break

    # Detect type
    name_lower = name.lower()
    is_welcome = 'welcome' in name_lower or 'visitor' in name_lower
    area_type = 'welcome_center' if is_welcome else 'rest_area'

    slug = slugify(f"{name} {highway} {state}".strip())

    try:
        parking_int = int(parking) if parking else None
    except (ValueError, TypeError):
        parking_int = None

    return {
        'name': name,
        'slug': slug,
        'highway': highway or None,
        'mile_post': mile_post or None,
        'direction': direction,
        'city': city or None,
        'county': county or None,
        'state_province': state,
        'country': 'US',
        'latitude': lat,
        'longitude': lng,
        'parking_spaces': parking_int,
        'truck_parking': True,  # These are specifically truck parking locations
        'has_restrooms': True,
        'is_welcome_center': is_welcome,
        'area_type': area_type,
        'data_source': 'usdot',
    }
