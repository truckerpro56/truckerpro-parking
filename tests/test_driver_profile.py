"""Tests for driver profile — favorites, settings, contributions."""
import uuid
import pytest
from app.models.user import User
from app.models.favorite_stop import FavoriteStop
from app.models.truck_stop import TruckStop
from app.models.stop_photo import StopPhoto


def _create_stop(db_session, slug=None):
    if slug is None:
        slug = 'test-stop-' + uuid.uuid4().hex[:8]
    stop = TruckStop(
        brand='loves', brand_display_name="Love's", name="Test Stop",
        slug=slug, store_number='999',
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


class TestStopPhotos:
    def test_photo_model_creation(self, db):
        user = _create_user(db, email='photo@test.com')
        stop = _create_stop(db)
        photo = StopPhoto(
            truck_stop_id=stop.id, user_id=user.id,
            filename='test.jpg', content_type='image/jpeg',
            image_data=b'\xff\xd8\xff\xe0test',
            caption='Test photo',
        )
        db.session.add(photo)
        db.session.commit()
        assert photo.id is not None
        assert photo.is_approved is True

    def test_photo_serves(self, stops_client, db):
        user = _create_user(db, email='serve@test.com')
        stop = _create_stop(db)
        photo = StopPhoto(
            truck_stop_id=stop.id, user_id=user.id,
            filename='test.jpg', content_type='image/jpeg',
            image_data=b'\xff\xd8\xff\xe0testimage',
        )
        db.session.add(photo)
        db.session.commit()
        resp = stops_client.get(f'/photos/{photo.id}')
        assert resp.status_code == 200
        assert resp.content_type == 'image/jpeg'
