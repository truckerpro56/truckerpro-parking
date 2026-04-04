"""Map pins API — returns all active locations for map rendering."""
import json
import logging
import redis
from flask import jsonify, make_response, current_app

from . import stops_api_bp
from ..middleware import site_required
from ..extensions import db
from ..models.truck_stop import TruckStop
from ..models.rest_area import RestArea
from ..models.weigh_station import WeighStation
from ..stops.helpers import state_code_to_slug
from ..services.geo_service import slugify

logger = logging.getLogger(__name__)

CACHE_KEY = 'map_pins:all'
CACHE_TTL = 3600  # 1 hour


def _get_redis():
    """Get Redis connection, return None if unavailable."""
    try:
        url = current_app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        r = redis.from_url(url, socket_timeout=2)
        r.ping()
        return r
    except Exception:
        return None


def _build_pins_json():
    """Query all active locations and build the pins response dict."""
    truck_stops = []
    for s in TruckStop.query.filter(TruckStop.is_active == True).all():
        truck_stops.append({
            'id': s.id, 'name': s.name, 'brand': s.brand,
            'lat': s.latitude, 'lng': s.longitude,
            'city': s.city, 'state': s.state_province,
            'url': '/{}/{}/{}/{}'.format(
                'us' if s.country == 'US' else 'canada',
                state_code_to_slug(s.state_province),
                slugify(s.city),
                s.slug,
            ),
        })

    rest_areas = []
    for r in RestArea.query.filter(RestArea.is_active == True).all():
        rest_areas.append({
            'id': r.id, 'name': r.name,
            'lat': r.latitude, 'lng': r.longitude,
            'state': r.state_province,
            'url': '/rest-areas/{}/{}'.format(
                state_code_to_slug(r.state_province),
                r.slug,
            ),
        })

    weigh_stations = []
    for w in WeighStation.query.filter(WeighStation.is_active == True).all():
        weigh_stations.append({
            'id': w.id, 'name': w.name,
            'lat': w.latitude, 'lng': w.longitude,
            'state': w.state_province,
            'url': '/weigh-stations/{}/{}'.format(
                state_code_to_slug(w.state_province),
                w.slug,
            ),
        })

    return {
        'truck_stops': truck_stops,
        'rest_areas': rest_areas,
        'weigh_stations': weigh_stations,
        'counts': {
            'truck_stops': len(truck_stops),
            'rest_areas': len(rest_areas),
            'weigh_stations': len(weigh_stations),
        },
    }


@stops_api_bp.route('/map-pins', methods=['GET'])
@site_required('stops')
def map_pins():
    """Return all active locations as minimal JSON for map rendering.
    Redis-cached for 1 hour. Browser-cached for 5 minutes.
    """
    # Try Redis cache first
    r = _get_redis()
    if r:
        try:
            cached = r.get(CACHE_KEY)
            if cached:
                resp = make_response(cached)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Cache-Control'] = 'public, max-age=300'
                return resp
        except Exception:
            pass

    # Cache miss or Redis unavailable — query DB
    data = _build_pins_json()
    data_json = json.dumps(data)

    # Store in Redis
    if r:
        try:
            r.setex(CACHE_KEY, CACHE_TTL, data_json)
        except Exception:
            logger.warning('Failed to write map pins to Redis cache')

    resp = make_response(data_json)
    resp.headers['Content-Type'] = 'application/json'
    resp.headers['Cache-Control'] = 'public, max-age=300'
    return resp
