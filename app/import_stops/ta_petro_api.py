"""TA/Petro importer — pulls from AllThePlaces GeoJSON (CC-0)."""
import logging
import requests

logger = logging.getLogger(__name__)

TA_GEOJSON_URL = 'https://data.alltheplaces.xyz/runs/latest/output/travelcenters_of_america_us.geojson'


def fetch_ta_stores():
    """Fetch all TA/Petro locations from AllThePlaces. Returns list of feature dicts."""
    resp = requests.get(TA_GEOJSON_URL, timeout=60, stream=True)
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


def parse_ta_feature(feature):
    """Map an AllThePlaces GeoJSON feature to truck_stops field dict."""
    props = feature.get('properties', {})
    coords = feature.get('geometry', {}).get('coordinates', [None, None])
    lng, lat = coords[0], coords[1]

    ref = (props.get('ref') or '').strip()
    name = (props.get('name') or '').strip()
    brand = (props.get('brand') or props.get('official_name') or '').strip()

    # Determine sub-brand
    brand_lower = brand.lower() if brand else ''
    if 'petro' in brand_lower and 'ta' not in brand_lower:
        display_name = 'Petro Stopping Centers'
    elif 'express' in brand_lower:
        display_name = 'TA Express'
    else:
        display_name = 'TA Travel Center'

    if not name:
        name = f"{display_name} #{ref}" if ref else display_name

    # Check fuel flags
    has_def = _yn(props.get('fuel:adblue_at_pump')) or _yn(props.get('fuel:adblue'))
    has_diesel = _yn(props.get('fuel:diesel')) or True  # All truck stops have diesel

    return {
        'brand': 'ta_petro',
        'brand_display_name': display_name,
        'name': name,
        'store_number': ref,
        'address': (props.get('addr:street_address') or '').strip(),
        'city': (props.get('addr:city') or '').strip(),
        'state_province': (props.get('addr:state') or '').strip(),
        'postal_code': (props.get('addr:postcode') or '').strip(),
        'country': 'US',
        'latitude': lat,
        'longitude': lng,
        'phone': (props.get('phone') or '').strip() or None,
        'website': (props.get('website') or '').strip() or None,
        'has_diesel': has_diesel,
        'has_def': has_def,
        'has_showers': True,
        'data_source': 'alltheplaces',
    }


def _yn(val):
    return str(val).strip().lower() in ('yes', 'true', '1', 'y')
