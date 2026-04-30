"""Route planner API endpoint for stops.truckerpro.net."""
from flask import jsonify, request

from . import stops_api_bp
from ..extensions import limiter
from ..middleware import site_required
from ..services.route_planner import get_route, find_stops_along_route
from ..stops.helpers import state_code_to_slug
from ..services.geo_service import slugify


@stops_api_bp.route('/plan-route', methods=['POST'])
@site_required('stops')
@limiter.limit("10/hour")
def plan_route_api():
    """API endpoint — accepts origin/destination, returns route + stops.
    Registered on stops_api_bp which is CSRF-exempt.
    """
    data = request.get_json() or {}
    origin = data.get('origin', '').strip()
    destination = data.get('destination', '').strip()

    if not origin or not destination:
        return jsonify({'error': 'Origin and destination required'}), 400

    # Cap input length before forwarding to the Maps API. Without this, a
    # caller can pass 10k-character strings to burn paid Google quota under
    # the existing 10/hour rate limit.
    if len(origin) > 500 or len(destination) > 500:
        return jsonify({'error': 'Origin and destination must be 500 characters or fewer'}), 400

    route_data = get_route(origin, destination)
    if not route_data:
        return jsonify({'error': 'Could not find a route. Check your addresses.'}), 400

    results = find_stops_along_route(route_data)

    # Serialize stops
    truck_stops = []
    for s in results['truck_stops'][:50]:  # Cap at 50
        truck_stops.append({
            'id': s.id, 'name': s.name, 'brand': s.brand_display_name or s.brand,
            'lat': s.latitude, 'lng': s.longitude,
            'city': s.city, 'state': s.state_province,
            'highway': s.highway, 'exit': s.exit_number,
            'has_diesel': s.has_diesel, 'has_showers': s.has_showers,
            'has_scale': s.has_scale, 'parking': s.total_parking_spots,
            'url': '/{}/{}/{}/{}'.format(
                'us' if s.country == 'US' else 'canada',
                state_code_to_slug(s.state_province),
                slugify(s.city),
                s.slug,
            ),
        })

    rest_areas = []
    for r in results['rest_areas'][:30]:
        rest_areas.append({
            'id': r.id, 'name': r.name, 'lat': r.latitude, 'lng': r.longitude,
            'highway': r.highway, 'state': r.state_province,
            'parking_spaces': r.parking_spaces,
            'url': '/rest-areas/{}/{}'.format(
                state_code_to_slug(r.state_province),
                r.slug,
            ),
        })

    weigh_stations = []
    for w in results['weigh_stations'][:20]:
        weigh_stations.append({
            'id': w.id, 'name': w.name, 'lat': w.latitude, 'lng': w.longitude,
            'state': w.state_province,
            'url': '/weigh-stations/{}/{}'.format(
                state_code_to_slug(w.state_province),
                w.slug,
            ),
        })

    return jsonify({
        'route': {
            'polyline': route_data['polyline'],
            'distance': route_data['distance_text'],
            'duration': route_data['duration_text'],
            'start_address': route_data['start_address'],
            'end_address': route_data['end_address'],
            'start': {'lat': route_data['start_lat'], 'lng': route_data['start_lng']},
            'end': {'lat': route_data['end_lat'], 'lng': route_data['end_lng']},
        },
        'truck_stops': truck_stops,
        'rest_areas': rest_areas,
        'weigh_stations': weigh_stations,
        'counts': {
            'truck_stops': len(truck_stops),
            'rest_areas': len(rest_areas),
            'weigh_stations': len(weigh_stations),
        },
    })
