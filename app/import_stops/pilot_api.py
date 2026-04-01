"""Pilot Flying J importer — pulls from AllThePlaces GeoJSON (CC-0)."""
import logging
import requests

logger = logging.getLogger(__name__)

PILOT_GEOJSON_URL = 'https://data.alltheplaces.xyz/runs/latest/output/pilot_flying_j.geojson'


def fetch_pilot_stores():
    """Fetch all Pilot Flying J locations from AllThePlaces. Returns list of feature dicts."""
    resp = requests.get(PILOT_GEOJSON_URL, timeout=60, stream=True)
    resp.raise_for_status()
    import json
    features = []
    for line in resp.iter_lines(decode_unicode=True):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if obj.get('type') == 'Feature':
                features.append(obj)
        except json.JSONDecodeError:
            continue
    return features


def parse_pilot_feature(feature):
    """Map an AllThePlaces GeoJSON feature to truck_stops field dict."""
    props = feature.get('properties', {})
    coords = feature.get('geometry', {}).get('coordinates', [None, None])
    lng, lat = coords[0], coords[1]

    ref = (props.get('ref') or '').strip()
    name = (props.get('name') or '').strip()
    brand = (props.get('brand') or '').strip()

    # Determine sub-brand
    brand_lower = brand.lower() if brand else ''
    if 'flying j' in brand_lower:
        display_name = 'Flying J'
    elif 'one9' in brand_lower:
        display_name = 'ONE9 by Pilot'
    else:
        display_name = 'Pilot Flying J'

    # Use the full name or construct one
    if not name:
        name = f"{display_name} #{ref}" if ref else display_name

    return {
        'brand': 'pilot_flying_j',
        'brand_display_name': display_name,
        'name': name,
        'store_number': ref,
        'address': (props.get('addr:street_address') or '').strip(),
        'city': (props.get('addr:city') or '').strip(),
        'state_province': (props.get('addr:state') or '').strip(),
        'postal_code': (props.get('addr:postcode') or '').strip(),
        'country': _map_country(props.get('addr:country', 'US')),
        'latitude': lat,
        'longitude': lng,
        'phone': (props.get('phone') or '').strip() or None,
        'website': (props.get('website') or '').strip() or None,
        'has_diesel': True,
        'has_showers': True,  # Pilot/FJ all have showers
        'has_wifi': True,     # All have WiFi
        'data_source': 'alltheplaces',
    }


def _map_country(code):
    if not code:
        return 'US'
    code = code.upper().strip()
    if code in ('US', 'USA'):
        return 'US'
    if code in ('CA', 'CAN'):
        return 'CA'
    return code[:2]
