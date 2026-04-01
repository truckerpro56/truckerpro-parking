"""Google Places API integration for truck stop photos."""
import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)

# Cache photos in memory to avoid repeated API calls
_photo_cache = {}


def get_place_photos(name, latitude, longitude, max_photos=6):
    """Get Google Places photos for a truck stop by name and coordinates.

    Returns list of photo URLs (proxied through Google Places Photo API).
    Results are cached in memory.
    """
    cache_key = f"{latitude},{longitude}"
    if cache_key in _photo_cache:
        return _photo_cache[cache_key]

    api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        return []

    try:
        # Find the place using Nearby Search
        search_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        resp = requests.get(search_url, params={
            'location': f'{latitude},{longitude}',
            'radius': 100,
            'keyword': name,
            'key': api_key,
        }, timeout=5)
        data = resp.json()

        if data.get('status') != 'OK' or not data.get('results'):
            _photo_cache[cache_key] = []
            return []

        place = data['results'][0]
        photos = place.get('photos', [])[:max_photos]

        # Build photo URLs
        photo_urls = []
        for photo in photos:
            ref = photo.get('photo_reference')
            if ref:
                url = (
                    f"https://maps.googleapis.com/maps/api/place/photo"
                    f"?maxwidth=800&photo_reference={ref}&key={api_key}"
                )
                photo_urls.append(url)

        _photo_cache[cache_key] = photo_urls
        return photo_urls

    except Exception as e:
        logger.warning("Google Places API error for %s: %s", name, str(e)[:200])
        _photo_cache[cache_key] = []
        return []
