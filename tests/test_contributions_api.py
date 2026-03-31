"""Tests for driver contribution API endpoints."""
import json
import bcrypt
from app.models.truck_stop import TruckStop
from app.models.fuel_price import FuelPrice
from app.models.truck_stop_review import TruckStopReview
from app.models.user import User


def _seed(db):
    stop = TruckStop(
        brand='loves', name='Test', slug='contrib-test',
        address='123 St', city='Dallas', state_province='TX',
        country='US', latitude=32.0, longitude=-96.0, data_source='manual',
    )
    pw = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode('utf-8')
    user = User(email='contrib@test.com', password_hash=pw, name='Driver', role='driver')
    db.session.add_all([stop, user])
    db.session.commit()
    return stop, user


def test_submit_fuel_price_requires_auth(stops_client, db):
    stop, _ = _seed(db)
    resp = stops_client.post(
        f'/api/v1/truck-stops/{stop.id}/fuel-prices',
        data=json.dumps({'fuel_type': 'diesel', 'price_cents': 350, 'currency': 'USD'}),
        content_type='application/json',
    )
    assert resp.status_code in (401, 302)


def test_submit_review_requires_auth(stops_client, db):
    stop, _ = _seed(db)
    resp = stops_client.post(
        f'/api/v1/truck-stops/{stop.id}/reviews',
        data=json.dumps({'rating': 4, 'review_text': 'Great stop'}),
        content_type='application/json',
    )
    assert resp.status_code in (401, 302)


def test_fuel_price_auto_verify_within_threshold(app, db):
    stop, user = _seed(db)
    fp = FuelPrice(
        truck_stop_id=stop.id, fuel_type='diesel',
        price_cents=350, currency='USD', source='import', is_verified=True,
    )
    db.session.add(fp)
    db.session.commit()
    from app.stops_api.contributions import _should_auto_verify_price
    assert _should_auto_verify_price(stop.id, 'diesel', 360) is True
    assert _should_auto_verify_price(stop.id, 'diesel', 500) is False


def test_submit_report(app, db):
    from datetime import datetime, timezone, timedelta
    from app.models.truck_stop_report import TruckStopReport
    stop, user = _seed(db)
    report = TruckStopReport(
        truck_stop_id=stop.id, user_id=user.id,
        report_type='parking_availability',
        data={'available_spots': 12},
        expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
    )
    db.session.add(report)
    db.session.commit()
    # SQLite returns naive datetimes; compare without tzinfo
    expires = report.expires_at
    if expires.tzinfo is not None:
        now = datetime.now(timezone.utc)
    else:
        now = datetime.utcnow()
    assert expires > now
