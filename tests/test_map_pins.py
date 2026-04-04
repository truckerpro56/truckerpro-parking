"""Tests for map pins API endpoint."""
import json


class TestMapPinsAPI:
    def test_returns_200(self, stops_client):
        resp = stops_client.get('/api/v1/map-pins')
        assert resp.status_code == 200

    def test_returns_json_with_required_keys(self, stops_client):
        resp = stops_client.get('/api/v1/map-pins')
        data = resp.get_json()
        assert 'truck_stops' in data
        assert 'rest_areas' in data
        assert 'weigh_stations' in data
        assert 'counts' in data

    def test_counts_match_array_lengths(self, stops_client):
        resp = stops_client.get('/api/v1/map-pins')
        data = resp.get_json()
        assert data['counts']['truck_stops'] == len(data['truck_stops'])
        assert data['counts']['rest_areas'] == len(data['rest_areas'])
        assert data['counts']['weigh_stations'] == len(data['weigh_stations'])

    def test_truck_stop_has_required_fields(self, stops_client, db):
        from app.models.truck_stop import TruckStop
        stop = TruckStop(
            name="Test Stop", slug="test-stop", brand="loves",
            address="123 Main", city="Dallas", state_province="TX",
            country="US", latitude=32.7, longitude=-96.8,
            data_source="test", is_active=True,
        )
        db.session.add(stop)
        db.session.commit()

        resp = stops_client.get('/api/v1/map-pins')
        data = resp.get_json()
        assert len(data['truck_stops']) >= 1
        s = data['truck_stops'][0]
        for key in ('id', 'name', 'brand', 'lat', 'lng', 'city', 'state', 'url'):
            assert key in s, f"Missing key: {key}"

    def test_rest_area_has_required_fields(self, stops_client, db):
        from app.models.rest_area import RestArea
        ra = RestArea(
            name="I-80 Rest Area", slug="i-80-rest-area",
            state_province="NE", country="US",
            latitude=41.1, longitude=-96.5,
            data_source="test", is_active=True,
        )
        db.session.add(ra)
        db.session.commit()

        resp = stops_client.get('/api/v1/map-pins')
        data = resp.get_json()
        assert len(data['rest_areas']) >= 1
        r = data['rest_areas'][0]
        for key in ('id', 'name', 'lat', 'lng', 'state', 'url'):
            assert key in r, f"Missing key: {key}"

    def test_weigh_station_has_required_fields(self, stops_client, db):
        from app.models.weigh_station import WeighStation
        ws = WeighStation(
            name="I-80 Scale", slug="i-80-scale",
            state_province="NE", country="US",
            latitude=41.05, longitude=-96.8,
            data_source="test", is_active=True,
        )
        db.session.add(ws)
        db.session.commit()

        resp = stops_client.get('/api/v1/map-pins')
        data = resp.get_json()
        assert len(data['weigh_stations']) >= 1
        w = data['weigh_stations'][0]
        for key in ('id', 'name', 'lat', 'lng', 'state', 'url'):
            assert key in w, f"Missing key: {key}"

    def test_inactive_stops_excluded(self, stops_client, db):
        from app.models.truck_stop import TruckStop
        stop = TruckStop(
            name="Inactive Stop", slug="inactive-stop", brand="loves",
            address="456 Main", city="Houston", state_province="TX",
            country="US", latitude=29.7, longitude=-95.4,
            data_source="test", is_active=False,
        )
        db.session.add(stop)
        db.session.commit()

        resp = stops_client.get('/api/v1/map-pins')
        data = resp.get_json()
        names = [s['name'] for s in data['truck_stops']]
        assert 'Inactive Stop' not in names

    def test_not_accessible_on_parking_domain(self, client):
        resp = client.get('/api/v1/map-pins')
        assert resp.status_code == 404

    def test_has_cache_control_header(self, stops_client):
        resp = stops_client.get('/api/v1/map-pins')
        assert 'public' in resp.headers.get('Cache-Control', '')
