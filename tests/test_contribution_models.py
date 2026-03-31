"""Tests for FuelPrice, TruckStopReview, TruckStopReport models."""
import pytest
from datetime import datetime, timezone, timedelta
from app.models.truck_stop import TruckStop
from app.models.fuel_price import FuelPrice
from app.models.truck_stop_review import TruckStopReview
from app.models.truck_stop_report import TruckStopReport
from app.models.user import User
import bcrypt


def _make_stop(db):
    stop = TruckStop(
        brand='loves', name='Test Stop', slug='test-stop-contrib',
        address='123 St', city='Dallas', state_province='TX',
        country='US', latitude=32.0, longitude=-96.0, data_source='manual',
    )
    db.session.add(stop)
    db.session.commit()
    return stop


def _make_user(db, email='driver@test.com'):
    pw = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode('utf-8')
    user = User(email=email, password_hash=pw, name='Test Driver', role='driver')
    db.session.add(user)
    db.session.commit()
    return user


def test_create_fuel_price(db):
    stop = _make_stop(db)
    fp = FuelPrice(
        truck_stop_id=stop.id, fuel_type='diesel',
        price_cents=345, currency='USD', source='driver',
    )
    db.session.add(fp)
    db.session.commit()
    assert fp.id is not None
    assert fp.is_verified is False


def test_fuel_price_with_reporter(db):
    stop = _make_stop(db)
    user = _make_user(db)
    fp = FuelPrice(
        truck_stop_id=stop.id, fuel_type='diesel',
        price_cents=350, currency='USD',
        source='driver', reported_by=user.id,
    )
    db.session.add(fp)
    db.session.commit()
    assert fp.reported_by == user.id


def test_create_review(db):
    stop = _make_stop(db)
    user = _make_user(db)
    review = TruckStopReview(
        truck_stop_id=stop.id, user_id=user.id,
        rating=4, review_text='Clean showers, good food.',
    )
    db.session.add(review)
    db.session.commit()
    assert review.id is not None
    assert review.is_approved is False


def test_review_rating_constraint(db):
    from sqlalchemy.exc import IntegrityError
    stop = _make_stop(db)
    user = _make_user(db)
    review = TruckStopReview(
        truck_stop_id=stop.id, user_id=user.id,
        rating=6, review_text='Invalid rating',
    )
    db.session.add(review)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_review_unique_per_user_per_stop(db):
    from sqlalchemy.exc import IntegrityError
    stop = _make_stop(db)
    user = _make_user(db)
    r1 = TruckStopReview(
        truck_stop_id=stop.id, user_id=user.id,
        rating=4, review_text='First review',
    )
    db.session.add(r1)
    db.session.commit()
    r2 = TruckStopReview(
        truck_stop_id=stop.id, user_id=user.id,
        rating=5, review_text='Second review',
    )
    db.session.add(r2)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_create_report(db):
    stop = _make_stop(db)
    user = _make_user(db)
    report = TruckStopReport(
        truck_stop_id=stop.id, user_id=user.id,
        report_type='parking_availability',
        data={'available_spots': 12},
        expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
    )
    db.session.add(report)
    db.session.commit()
    assert report.id is not None
    assert report.is_verified is False
    assert report.data['available_spots'] == 12
