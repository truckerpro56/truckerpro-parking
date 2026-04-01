"""BTS/FHWA weigh station importer — GeoJSON download."""
import logging
import requests
from ..services.geo_service import slugify

logger = logging.getLogger(__name__)

BTS_WEIGH_URL = 'https://geodata.bts.gov/datasets/893768eebc9f42089f1f2fa671c0cb51_0.geojson'

# Map state FIPS to state codes
FIPS_TO_STATE = {
    '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA', '08': 'CO', '09': 'CT', '10': 'DE',
    '11': 'DC', '12': 'FL', '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL', '18': 'IN', '19': 'IA',
    '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME', '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN',
    '28': 'MS', '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH', '34': 'NJ', '35': 'NM',
    '36': 'NY', '37': 'NC', '38': 'ND', '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI',
    '45': 'SC', '46': 'SD', '47': 'TN', '48': 'TX', '49': 'UT', '50': 'VT', '51': 'VA', '53': 'WA',
    '54': 'WV', '55': 'WI', '56': 'WY',
}


def fetch_weigh_stations():
    """Fetch all weigh stations from BTS. Returns list of GeoJSON features."""
    resp = requests.get(BTS_WEIGH_URL, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data.get('features', [])


def parse_bts_feature(feature):
    """Map a BTS GeoJSON feature to WeighStation field dict."""
    props = feature.get('properties', {})
    geom = feature.get('geometry') or {}
    coords = geom.get('coordinates', [None, None])
    lng = coords[0] if len(coords) >= 1 else None
    lat = coords[1] if len(coords) >= 2 else None

    state = (props.get('state') or '').strip()
    if not state and props.get('State_FIPS'):
        fips = str(props['State_FIPS']).zfill(2)
        state = FIPS_TO_STATE.get(fips, '')

    station_id = (props.get('station_id') or '').strip()
    func_class = (props.get('functional_class') or '').strip()

    annual_count = None
    try:
        annual_count = int(props.get('Counts_Year') or 0)
        if annual_count == 0:
            annual_count = None
    except (ValueError, TypeError):
        pass

    days_active = None
    try:
        days_active = int(props.get('Num_Days_Active') or 0)
        if days_active == 0:
            days_active = None
    except (ValueError, TypeError):
        pass

    name = f"Weigh Station {station_id}" if station_id else f"Weigh Station — {state}"
    slug = slugify(f"weigh-station {station_id} {state}".strip())

    return {
        'name': name,
        'slug': slug,
        'station_id': station_id or None,
        'state_province': state,
        'country': 'US',
        'latitude': lat,
        'longitude': lng,
        'functional_class': func_class or None,
        'annual_truck_count': annual_count,
        'days_active': days_active,
        'is_permanent': True,
        'station_type': 'weigh_station',
        'data_source': 'bts',
    }
