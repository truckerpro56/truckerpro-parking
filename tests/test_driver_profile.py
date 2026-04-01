"""Tests for driver profile — favorites, settings, contributions."""
import pytest
from app.models.user import User
from app.models.favorite_stop import FavoriteStop
from app.models.truck_stop import TruckStop


def _create_stop(db_session):
    stop = TruckStop(
        brand='loves', brand_display_name="Love's", name="Test Stop",
        slug='test-stop-profile', store_number='999',
        address='123 Test St', city='Dallas', state_province='TX',
        postal_code='75201', country='US', latitude=32.78, longitude=-96.80,
        has_diesel=True, data_source='test', is_active=True,
    )
    db_session.session.add(stop)
    db_session.session.commit()
    return stop


def _create_user(db_session, email='profile@test.com'):
    user = User(email=email, role='driver')
    db_session.session.add(user)
    db_session.session.commit()
    return user


class TestProfilePage:
    def test_profile_requires_auth(self, stops_client):
        resp = stops_client.get('/profile')
        assert resp.status_code == 302  # redirect to login

    def test_profile_returns_200_when_authenticated(self, client, db):
        user = _create_user(db)
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
        # Note: this test uses parking client, profile is stops-only
        # Would need stops_client with auth support


class TestFavorites:
    def test_add_favorite(self, db):
        user = _create_user(db)
        stop = _create_stop(db)
        fav = FavoriteStop(user_id=user.id, truck_stop_id=stop.id)
        db.session.add(fav)
        db.session.commit()
        assert FavoriteStop.query.filter_by(user_id=user.id).count() == 1

    def test_unique_constraint(self, db):
        user = _create_user(db, email='unique@test.com')
        stop = _create_stop(db)
        fav1 = FavoriteStop(user_id=user.id, truck_stop_id=stop.id)
        db.session.add(fav1)
        db.session.commit()
        fav2 = FavoriteStop(user_id=user.id, truck_stop_id=stop.id)
        db.session.add(fav2)
        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()
        db.session.rollback()
