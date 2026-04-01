"""Route planner service — find stops along a driving route."""
import logging
import math
import requests
from flask import current_app
from ..extensions import db
from ..models.truck_stop import TruckStop
from ..models.rest_area import RestArea
from ..models.weigh_station import WeighStation

logger = logging.getLogger(__name__)

CORRIDOR_MILES = 25  # Search within 25 miles of route
MILES_TO_DEGREES = 1 / 69.0  # Rough conversion for bounding box


def get_route(origin, destination):
    """Get driving route from Google Directions API.
    Returns dict with: polyline points, distance, duration, bounds, steps.
    """
    api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        return None

    resp = requests.get('https://maps.googleapis.com/maps/api/directions/json', params={
        'origin': origin,
        'destination': destination,
        'key': api_key,
        'mode': 'driving',
        'avoid': 'tolls',  # Truckers often avoid tolls
    }, timeout=10)
    data = resp.json()

    if data.get('status') != 'OK' or not data.get('routes'):
        return None

    route = data['routes'][0]
    leg = route['legs'][0]

    return {
        'polyline': route['overview_polyline']['points'],
        'distance_text': leg['distance']['text'],
        'distance_meters': leg['distance']['value'],
        'duration_text': leg['duration']['text'],
        'duration_seconds': leg['duration']['value'],
        'start_address': leg['start_address'],
        'end_address': leg['end_address'],
        'start_lat': leg['start_location']['lat'],
        'start_lng': leg['start_location']['lng'],
        'end_lat': leg['end_location']['lat'],
        'end_lng': leg['end_location']['lng'],
        'bounds': route['bounds'],
        'steps': [
            {'lat': s['end_location']['lat'], 'lng': s['end_location']['lng']}
            for s in leg['steps']
        ],
    }


def decode_polyline(encoded):
    """Decode a Google encoded polyline string into lat/lng pairs."""
    points = []
    index = 0
    lat = 0
    lng = 0
    while index < len(encoded):
        for coord in range(2):
            shift = 0
            result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if (result & 1) else (result >> 1)
            if coord == 0:
                lat += delta
            else:
                lng += delta
        points.append((lat / 1e5, lng / 1e5))
    return points


def find_stops_along_route(route_data, corridor_miles=CORRIDOR_MILES):
    """Find truck stops, rest areas, and weigh stations along a route.
    Uses bounding box of route expanded by corridor width.
    Then filters by distance to nearest route point.
    """
    if not route_data:
        return {'truck_stops': [], 'rest_areas': [], 'weigh_stations': []}

    # Decode polyline to get route points
    points = decode_polyline(route_data['polyline'])
    if not points:
        return {'truck_stops': [], 'rest_areas': [], 'weigh_stations': []}

    # Sample every Nth point to reduce computation (keep ~100 points max)
    step = max(1, len(points) // 100)
    sampled = points[::step]

    # Compute bounding box
    bounds = route_data['bounds']
    margin = corridor_miles * MILES_TO_DEGREES
    min_lat = bounds['southwest']['lat'] - margin
    max_lat = bounds['northeast']['lat'] + margin
    min_lng = bounds['southwest']['lng'] - margin
    max_lng = bounds['northeast']['lng'] + margin

    # Query all three entity types within the bounding box
    truck_stops = TruckStop.query.filter(
        TruckStop.is_active == True,
        TruckStop.latitude.between(min_lat, max_lat),
        TruckStop.longitude.between(min_lng, max_lng),
    ).all()

    rest_areas = RestArea.query.filter(
        RestArea.is_active == True,
        RestArea.latitude.between(min_lat, max_lat),
        RestArea.longitude.between(min_lng, max_lng),
    ).all()

    weigh_stations = WeighStation.query.filter(
        WeighStation.is_active == True,
        WeighStation.latitude.between(min_lat, max_lat),
        WeighStation.longitude.between(min_lng, max_lng),
    ).all()

    # Filter to within corridor_miles of any route point
    def within_corridor(lat, lng):
        for plat, plng in sampled:
            dist = _haversine(lat, lng, plat, plng)
            if dist <= corridor_miles:
                return True
        return False

    filtered_stops = [s for s in truck_stops if within_corridor(s.latitude, s.longitude)]
    filtered_rest = [r for r in rest_areas if within_corridor(r.latitude, r.longitude)]
    filtered_weigh = [w for w in weigh_stations if within_corridor(w.latitude, w.longitude)]

    return {
        'truck_stops': filtered_stops,
        'rest_areas': filtered_rest,
        'weigh_stations': filtered_weigh,
    }


def _haversine(lat1, lng1, lat2, lng2):
    """Calculate distance in miles between two lat/lng points."""
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))
