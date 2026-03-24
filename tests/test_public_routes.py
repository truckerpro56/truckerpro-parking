"""Tests for public page routes."""
import pytest
from app.models.location import ParkingLocation
from app.models.user import User
from app.models.booking import ParkingBooking
from app.extensions import db as _db
from datetime import datetime, timezone, timedelta
import bcrypt


def _create_location(db_session, **overrides):
    """Helper to create a test parking location."""
    defaults = dict(
        name='Test Lot',
        slug='test-lot',
        address='123 Main St',
        city='Toronto',
        province='ON',
        latitude=43.6532,
        longitude=-79.3832,
        location_type='truck_stop',
        total_spots=10,
        is_active=True,
        daily_rate=2500,
    )
    defaults.update(overrides)
    loc = ParkingLocation(**defaults)
    db_session.session.add(loc)
    db_session.session.commit()
    return loc


def _create_user(db_session, **overrides):
    """Helper to create a test user."""
    pw = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode('utf-8')
    defaults = dict(
        email='driver@test.com',
        password_hash=pw,
        name='Test Driver',
        role='driver',
    )
    defaults.update(overrides)
    user = User(**defaults)
    db_session.session.add(user)
    db_session.session.commit()
    return user


class TestLandingPage:
    def test_landing_page(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_landing_page_contains_title(self, client):
        resp = client.get('/')
        assert b'Truck Parking' in resp.data


class TestHealth:
    def test_health(self, client):
        resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'

    def test_ready(self, client):
        resp = client.get('/ready')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ready'


class TestSearchPage:
    def test_search_page(self, client):
        resp = client.get('/search')
        assert resp.status_code == 200

    def test_search_with_query(self, client, db):
        _create_location(db, name='Highway Rest Stop', slug='highway-rest-stop')
        resp = client.get('/search?q=highway')
        assert resp.status_code == 200
        assert b'Highway Rest Stop' in resp.data

    def test_search_with_province_filter(self, client, db):
        _create_location(db, province='ON', slug='on-lot')
        resp = client.get('/search?province=ON')
        assert resp.status_code == 200

    def test_search_with_type_filter(self, client, db):
        _create_location(db, location_type='private_yard', slug='yard1')
        resp = client.get('/search?type=private_yard')
        assert resp.status_code == 200

    def test_search_bookable_filter(self, client, db):
        _create_location(db, is_bookable=True, slug='bookable-lot')
        resp = client.get('/search?bookable=1')
        assert resp.status_code == 200

    def test_search_lcv_filter(self, client, db):
        _create_location(db, lcv_capable=True, slug='lcv-lot')
        resp = client.get('/search?lcv=1')
        assert resp.status_code == 200


class TestProvincePage:
    def test_province_page_valid(self, client, db):
        _create_location(db, province='ON', city='Toronto', slug='toronto-lot')
        resp = client.get('/ontario')
        assert resp.status_code == 200
        assert b'Ontario' in resp.data

    def test_province_page_invalid(self, client):
        resp = client.get('/fake-province')
        assert resp.status_code == 404

    def test_province_page_empty(self, client, db):
        """Province page with no locations should still render."""
        resp = client.get('/alberta')
        assert resp.status_code == 200


class TestCityPage:
    def test_city_page_valid(self, client, db):
        _create_location(db, province='ON', city='Toronto', slug='toronto-lot-city')
        resp = client.get('/ontario/toronto')
        assert resp.status_code == 200
        assert b'Toronto' in resp.data

    def test_city_page_invalid_province(self, client):
        resp = client.get('/fake-province/toronto')
        assert resp.status_code == 404

    def test_city_page_invalid_city(self, client, db):
        resp = client.get('/ontario/nonexistent-city')
        assert resp.status_code == 404


class TestListYourSpace:
    def test_list_your_space(self, client):
        resp = client.get('/list-your-space')
        assert resp.status_code == 200


class TestLocationDetail:
    def test_location_detail_found(self, client, db):
        _create_location(db, name='Big Lot', slug='big-lot')
        resp = client.get('/location/big-lot')
        assert resp.status_code == 200
        assert b'Big Lot' in resp.data

    def test_location_detail_not_found(self, client):
        resp = client.get('/location/nonexistent-slug')
        assert resp.status_code == 404

    def test_location_detail_inactive(self, client, db):
        _create_location(db, slug='inactive-lot', is_active=False)
        resp = client.get('/location/inactive-lot')
        assert resp.status_code == 404


class TestMyBookings:
    def test_my_bookings_requires_login(self, client):
        resp = client.get('/my-bookings')
        # Should redirect to login
        assert resp.status_code == 302
        assert '/login' in resp.headers.get('Location', '')

    def test_my_bookings_authenticated(self, client, db):
        user = _create_user(db)
        # Login
        client.post('/login', data={
            'email': 'driver@test.com',
            'password': 'password123',
        })
        resp = client.get('/my-bookings')
        assert resp.status_code == 200
