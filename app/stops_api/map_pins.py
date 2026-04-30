"""Map pins API — returns all active locations for map rendering."""
import json
import logging
import secrets
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
LOCK_KEY = 'map_pins:rebuild_lock'
LOCK_TTL = 30  # seconds — long enough to rebuild, short enough to recover from crashes
LOCK_WAIT_POLL_S = 0.1
LOCK_WAIT_MAX_S = 5  # cap waiters; beyond this, fall through and rebuild


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


def _read_cache(r):
    if not r:
        return None
    try:
        return r.get(CACHE_KEY)
    except Exception:
        return None


def _make_resp(body):
    resp = make_response(body)
    resp.headers['Content-Type'] = 'application/json'
    resp.headers['Cache-Control'] = 'public, max-age=300'
    return resp


_RELEASE_LOCK_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


@stops_api_bp.route('/map-pins', methods=['GET'])
@site_required('stops')
def map_pins():
    """Return all active locations as minimal JSON for map rendering.

    Redis-cached for 1 hour with single-flight rebuild: when the cache is
    cold, only one worker rebuilds; concurrent waiters poll the cache key
    instead of re-running 3 full table scans in parallel.
    """
    r = _get_redis()
    cached = _read_cache(r)
    if cached:
        return _make_resp(cached)

    # Cache miss. Try to acquire the rebuild lock with a per-request token
    # so we only release the lock if we actually still hold it. Without the
    # token check, a worker that didn't acquire the lock could delete the
    # holder's lock from its own `finally`, breaking single-flight.
    lock_token = None
    if r is not None:
        import time
        try:
            candidate = secrets.token_hex(8)
            if r.set(LOCK_KEY, candidate, nx=True, ex=LOCK_TTL):
                lock_token = candidate
        except Exception:
            # Redis hiccup — fall through to a direct rebuild without a lock.
            # Don't pretend we hold one; that just causes parallel rebuilds.
            logger.warning('map_pins lock acquisition failed; rebuilding without single-flight')
        if lock_token is None and r is not None:
            # Another worker holds the lock. Poll the cache for a short window
            # and use whatever they produced; if they take too long, give up
            # waiting and rebuild ourselves (without holding the lock).
            waited = 0.0
            while waited < LOCK_WAIT_MAX_S:
                time.sleep(LOCK_WAIT_POLL_S)
                waited += LOCK_WAIT_POLL_S
                cached = _read_cache(r)
                if cached:
                    return _make_resp(cached)
            logger.warning('map_pins single-flight wait exceeded %ss; rebuilding', LOCK_WAIT_MAX_S)

    try:
        data_json = json.dumps(_build_pins_json())
        if r:
            try:
                r.setex(CACHE_KEY, CACHE_TTL, data_json)
            except Exception:
                logger.warning('Failed to write map pins to Redis cache')
        return _make_resp(data_json)
    finally:
        # Only release if we hold the lock AND it's still our token. Lua
        # script makes the get-then-del atomic so we don't race with TTL
        # expiry and another worker re-acquiring it.
        if r is not None and lock_token is not None:
            try:
                r.eval(_RELEASE_LOCK_LUA, 1, LOCK_KEY, lock_token)
            except Exception:
                pass
