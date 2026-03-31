"""Tests for truck stops API endpoints."""
from app.models.truck_stop import TruckStop


def _seed_stop(db, **overrides):
    defaults = dict(
        brand='loves', name="Love's #1", slug='loves-1-dallas-tx',
        store_number='1', address='123 Hwy', city='Dallas',
        state_province='TX', country='US', latitude=32.7767,
        longitude=-96.7970, highway='I-35', data_source='manual',
        is_active=True,
    )
    defaults.update(overrides)
    stop = TruckStop(**defaults)
    db.session.add(stop)
    db.session.commit()
    return stop


def test_list_truck_stops_empty(stops_client):
    resp = stops_client.get('/api/v1/truck-stops')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 0


def test_list_truck_stops_with_data(stops_client, db):
    _seed_stop(db)
    resp = stops_client.get('/api/v1/truck-stops')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['stops'][0]['brand'] == 'loves'


def test_filter_by_state(stops_client, db):
    _seed_stop(db, slug='s1', store_number='1', state_province='TX')
    _seed_stop(db, slug='s2', store_number='2', state_province='ON', country='CA')
    resp = stops_client.get('/api/v1/truck-stops?state=TX')
    data = resp.get_json()
    assert data['total'] == 1


def test_filter_by_brand(stops_client, db):
    _seed_stop(db, slug='s1', store_number='1', brand='loves')
    _seed_stop(db, slug='s2', store_number='2', brand='pilot_flying_j')
    resp = stops_client.get('/api/v1/truck-stops?brand=loves')
    data = resp.get_json()
    assert data['total'] == 1


def test_filter_by_highway(stops_client, db):
    _seed_stop(db, slug='s1', store_number='1', highway='I-35')
    _seed_stop(db, slug='s2', store_number='2', highway='I-10')
    resp = stops_client.get('/api/v1/truck-stops?highway=I-35')
    data = resp.get_json()
    assert data['total'] == 1


def test_get_truck_stop_detail(stops_client, db):
    stop = _seed_stop(db)
    resp = stops_client.get(f'/api/v1/truck-stops/{stop.id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['slug'] == 'loves-1-dallas-tx'
    assert 'banners' in data


def test_get_truck_stop_not_found(stops_client):
    resp = stops_client.get('/api/v1/truck-stops/99999')
    assert resp.status_code == 404


def test_geo_search(stops_client, db):
    _seed_stop(db, slug='near', store_number='1', latitude=32.78, longitude=-96.80)
    _seed_stop(db, slug='far', store_number='2', latitude=40.71, longitude=-74.01)
    resp = stops_client.get('/api/v1/truck-stops?lat=32.77&lng=-96.79&radius=50')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['stops'][0]['slug'] == 'near'


def test_pagination(stops_client, db):
    for i in range(25):
        _seed_stop(db, slug=f's-{i}', store_number=str(i))
    resp = stops_client.get('/api/v1/truck-stops?page=1&per_page=10')
    data = resp.get_json()
    assert data['total'] == 25
    assert len(data['stops']) == 10
    assert data['page'] == 1
    assert data['pages'] == 3
