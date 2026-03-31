"""Love's Travel Stops API importer — pulls from public loves.com API."""
import logging
import requests

logger = logging.getLogger(__name__)

LOVES_API_URL = 'https://www.loves.com/api/fetch_stores'


def fetch_loves_stores():
    """Fetch all Loves stores from public API. Returns list of raw store dicts."""
    resp = requests.get(LOVES_API_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get('stores', [])


def parse_loves_api_store(store):
    """Map a Loves API store dict to truck_stops field dict."""
    number = str(store.get('number', '')).strip()
    city = (store.get('city') or '').strip()
    state = (store.get('state') or '').strip()

    return {
        'brand': 'loves',
        'brand_display_name': "Love's Travel Stops",
        'name': f"Love's Travel Stop #{number}",
        'store_number': number,
        'address': (store.get('address1') or '').strip(),
        'city': city,
        'state_province': state,
        'postal_code': (store.get('zip') or '').strip(),
        'country': 'US',
        'latitude': store.get('latitude'),
        'longitude': store.get('longitude'),
        'highway': (store.get('highway') or '').strip() or None,
        'exit_number': (store.get('exitNumber') or '').strip() or None,
        'phone': (store.get('phoneNumber') or '').strip() or None,
        'has_diesel': True,
        'data_source': 'api',
    }
