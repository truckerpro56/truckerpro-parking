"""Tests for route planner."""
import pytest


class TestRoutePlannerPage:
    def test_page_returns_200(self, stops_client):
        resp = stops_client.get('/route-planner')
        assert resp.status_code == 200

    def test_page_contains_map(self, stops_client):
        resp = stops_client.get('/route-planner')
        assert b'route-map' in resp.data

    def test_page_contains_form(self, stops_client):
        resp = stops_client.get('/route-planner')
        assert b'route-origin' in resp.data
        assert b'route-destination' in resp.data

    def test_page_contains_plan_button(self, stops_client):
        resp = stops_client.get('/route-planner')
        assert b'plan-route' in resp.data

    def test_page_not_accessible_on_parking_domain(self, client):
        """Route planner is stops-only; parking domain gets 404."""
        resp = client.get('/route-planner')
        assert resp.status_code == 404

    def test_page_contains_filter_panel(self, stops_client):
        resp = stops_client.get('/route-planner')
        assert b'route-filters' in resp.data
        assert b'data-filter="loves"' in resp.data
        assert b'data-filter="pilot_flying_j"' in resp.data
        assert b'data-filter="ta_petro"' in resp.data
        assert b'data-filter="rest_area"' in resp.data
        assert b'data-filter="weigh_station"' in resp.data

    def test_page_loads_places_library(self, stops_client):
        resp = stops_client.get('/route-planner')
        assert b'libraries=geometry,places' in resp.data

    def test_page_loads_markerclusterer(self, stops_client):
        resp = stops_client.get('/route-planner')
        assert b'markerclusterer' in resp.data

    def test_page_fetches_map_pins(self, stops_client):
        resp = stops_client.get('/route-planner')
        assert b'/api/v1/map-pins' in resp.data


class TestPlanRouteAPI:
    def test_missing_params_returns_400(self, stops_client):
        resp = stops_client.post('/api/v1/plan-route',
                                 data='{}',
                                 content_type='application/json')
        assert resp.status_code == 400

    def test_missing_origin_returns_400(self, stops_client):
        resp = stops_client.post('/api/v1/plan-route',
                                 json={'destination': 'Dallas, TX'},
                                 content_type='application/json')
        assert resp.status_code == 400

    def test_missing_destination_returns_400(self, stops_client):
        resp = stops_client.post('/api/v1/plan-route',
                                 json={'origin': 'Houston, TX'},
                                 content_type='application/json')
        assert resp.status_code == 400

    def test_error_json_structure(self, stops_client):
        resp = stops_client.post('/api/v1/plan-route',
                                 data='{}',
                                 content_type='application/json')
        data = resp.get_json()
        assert 'error' in data

    def test_empty_strings_return_400(self, stops_client):
        resp = stops_client.post('/api/v1/plan-route',
                                 json={'origin': '  ', 'destination': ''},
                                 content_type='application/json')
        assert resp.status_code == 400

    def test_api_not_accessible_on_parking_domain(self, client):
        """API is stops-only; parking domain gets 404."""
        resp = client.post('/api/v1/plan-route',
                           json={'origin': 'Houston, TX', 'destination': 'Dallas, TX'},
                           content_type='application/json')
        assert resp.status_code == 404


class TestPolylineDecoder:
    def test_decode_simple(self):
        from app.services.route_planner import decode_polyline
        # Known encoded polyline for a simple 3-point path
        encoded = '_p~iF~ps|U_ulLnnqC_mqNvxq`@'
        points = decode_polyline(encoded)
        assert len(points) == 3
        assert abs(points[0][0] - 38.5) < 0.1
        assert abs(points[0][1] - (-120.2)) < 0.1

    def test_decode_empty_string(self):
        from app.services.route_planner import decode_polyline
        points = decode_polyline('')
        assert points == []

    def test_decode_returns_tuples(self):
        from app.services.route_planner import decode_polyline
        encoded = '_p~iF~ps|U_ulLnnqC_mqNvxq`@'
        points = decode_polyline(encoded)
        for pt in points:
            assert len(pt) == 2
            assert isinstance(pt[0], float)
            assert isinstance(pt[1], float)


class TestHaversine:
    def test_known_distance(self):
        from app.services.route_planner import _haversine
        # NYC to LA is approximately 2451 miles
        dist = _haversine(40.7128, -74.0060, 34.0522, -118.2437)
        assert 2400 < dist < 2500

    def test_same_point_is_zero(self):
        from app.services.route_planner import _haversine
        dist = _haversine(45.0, -75.0, 45.0, -75.0)
        assert dist == pytest.approx(0.0, abs=0.001)

    def test_short_distance(self):
        from app.services.route_planner import _haversine
        # Toronto to Hamilton — about 40 miles
        dist = _haversine(43.6532, -79.3832, 43.2557, -79.8711)
        assert 35 < dist < 50


class TestFindStopsAlongRoute:
    def test_returns_empty_for_none_route(self):
        from app.services.route_planner import find_stops_along_route
        result = find_stops_along_route(None)
        assert result == {'truck_stops': [], 'rest_areas': [], 'weigh_stations': []}

    def test_returns_three_keys(self, app):
        from app.services.route_planner import find_stops_along_route
        with app.app_context():
            # Minimal route_data with an empty polyline (no polyline points)
            route_data = {
                'polyline': '',
                'bounds': {
                    'southwest': {'lat': 30.0, 'lng': -100.0},
                    'northeast': {'lat': 35.0, 'lng': -95.0},
                },
            }
            result = find_stops_along_route(route_data)
            assert 'truck_stops' in result
            assert 'rest_areas' in result
            assert 'weigh_stations' in result
