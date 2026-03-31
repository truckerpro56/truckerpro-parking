"""Tests for stops.truckerpro.net sitemap generation."""
from app.models.truck_stop import TruckStop


def _seed(db):
    stops = [
        TruckStop(brand='loves', name="Love's #1", slug='loves-1-dallas-tx',
                  store_number='1', address='123 Hwy', city='Dallas',
                  state_province='TX', country='US', latitude=32.77,
                  longitude=-96.80, highway='I-35', data_source='manual', is_active=True),
        TruckStop(brand='pilot_flying_j', name='Pilot #2', slug='pilot-2-toronto-on',
                  store_number='2', address='401 Hwy', city='Toronto',
                  state_province='ON', country='CA', latitude=43.65,
                  longitude=-79.38, highway='401', data_source='manual', is_active=True),
    ]
    db.session.add_all(stops)
    db.session.commit()


def test_sitemap_index(stops_client, db):
    _seed(db)
    resp = stops_client.get('/sitemap.xml')
    assert resp.status_code == 200
    assert b'sitemapindex' in resp.data


def test_sitemap_stops(stops_client, db):
    _seed(db)
    resp = stops_client.get('/sitemap-stops.xml')
    assert resp.status_code == 200
    assert b'loves-1-dallas-tx' in resp.data
    assert b'pilot-2-toronto-on' in resp.data


def test_sitemap_states(stops_client, db):
    _seed(db)
    resp = stops_client.get('/sitemap-states.xml')
    assert resp.status_code == 200
    assert b'/us/texas' in resp.data or b'/canada/ontario' in resp.data
