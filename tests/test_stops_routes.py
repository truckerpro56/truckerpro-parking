"""Tests for stops.truckerpro.net public page routes."""
from app.models.truck_stop import TruckStop


def _seed_stop(db, **overrides):
    defaults = dict(
        brand='loves', name="Love's #1", slug='loves-1-dallas-tx',
        store_number='1', address='123 Hwy', city='Dallas',
        state_province='TX', country='US', latitude=32.7767,
        longitude=-96.7970, highway='I-35', data_source='manual',
        is_active=True, has_diesel=True, total_parking_spots=100,
    )
    defaults.update(overrides)
    stop = TruckStop(**defaults)
    db.session.add(stop)
    db.session.commit()
    return stop


class TestHomepage:
    def test_stops_homepage(self, stops_client):
        resp = stops_client.get('/')
        assert resp.status_code == 200

    def test_stops_homepage_content(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/')
        assert b'Truck Stop' in resp.data or b'truck stop' in resp.data


class TestCountryPages:
    def test_us_page(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/us')
        assert resp.status_code == 200

    def test_canada_page(self, stops_client, db):
        _seed_stop(db, slug='ca-stop', state_province='ON', country='CA')
        resp = stops_client.get('/canada')
        assert resp.status_code == 200


class TestStatePage:
    def test_state_page(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/us/texas')
        assert resp.status_code == 200

    def test_state_page_404(self, stops_client):
        resp = stops_client.get('/us/nonexistent-state')
        assert resp.status_code == 404


class TestCityPage:
    def test_city_page(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/us/texas/dallas')
        assert resp.status_code == 200


class TestStopDetail:
    def test_stop_detail(self, stops_client, db):
        stop = _seed_stop(db)
        resp = stops_client.get(f'/us/texas/dallas/{stop.slug}')
        assert resp.status_code == 200

    def test_stop_detail_404(self, stops_client):
        resp = stops_client.get('/us/texas/dallas/nonexistent-slug')
        assert resp.status_code == 404


class TestBrandPages:
    def test_brands_index(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/brands')
        assert resp.status_code == 200

    def test_brand_detail(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/brands/loves')
        assert resp.status_code == 200

    def test_brand_state(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/brands/loves/texas')
        assert resp.status_code == 200


class TestHighwayPages:
    def test_highways_index(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/highways')
        assert resp.status_code == 200

    def test_highway_detail(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/highways/i-35')
        assert resp.status_code == 200


class TestHealthOnStopsDomain:
    def test_health(self, stops_client):
        resp = stops_client.get('/health')
        assert resp.status_code == 200
