"""Geocoding and distance utilities."""
import math
import re
import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km using Haversine formula."""
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return round(R * c, 1)


def geocode_address(address, city, province):
    """Geocode an address using Google Maps API. Returns (lat, lng) or (None, None)."""
    api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        return None, None
    try:
        resp = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params={
            'address': f"{address}, {city}, {province}, Canada",
            'key': api_key,
        }, timeout=10)
        data = resp.json()
        if data.get('results'):
            loc = data['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    except Exception as e:
        logger.warning("Geocoding failed: %s", str(e)[:200])
    return None, None


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def format_price(cents):
    """Format price from cents to display string."""
    if cents is None:
        return None
    return f"{cents / 100:,.2f}"
