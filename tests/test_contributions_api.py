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
    # Within 8% (350 * 0.08 = 28). 360 - 350 = 10 → within band.
    assert _should_auto_verify_price(stop.id, 'diesel', 360) is True
    # 500 - 350 = 150 → way outside.
    assert _should_auto_verify_price(stop.id, 'diesel', 500) is False
    # 380 - 350 = 30, outside the new 8% band but inside the old 20% band —
    # this regression test catches an accidental loosening back to 20%.
    assert _should_auto_verify_price(stop.id, 'diesel', 380) is False


def test_fuel_price_auto_verify_blocks_same_user_self_confirmation(app, db):
    """A bad actor must not be able to walk the price by self-confirming."""
    stop, user = _seed(db)
    anchor = FuelPrice(
        truck_stop_id=stop.id, fuel_type='diesel',
        price_cents=350, currency='USD', source='driver', is_verified=True,
        reported_by=user.id,
    )
    db.session.add(anchor)
    db.session.commit()
    from app.stops_api.contributions import _should_auto_verify_price
    # Same user — must NOT auto-verify even within drift band
    assert _should_auto_verify_price(
        stop.id, 'diesel', 360, reporter_user_id=user.id
    ) is False
    # Different user — within drift band → may auto-verify
    other = User(email='other@test.com', name='Other', role='driver')
    db.session.add(other)
    db.session.commit()
    assert _should_auto_verify_price(
        stop.id, 'diesel', 360, reporter_user_id=other.id
    ) is True


def test_fuel_price_auto_verify_user_24h_cooldown(app, db):
    """Same user can't drive an auto-verified price more than once per 24h."""
    from datetime import datetime, timezone, timedelta
    stop, user = _seed(db)
    other = User(email='anchor@test.com', name='Anchor', role='driver')
    db.session.add(other)
    db.session.commit()
    # Anchor by another user
    db.session.add(FuelPrice(
        truck_stop_id=stop.id, fuel_type='diesel',
        price_cents=350, currency='USD', source='driver', is_verified=True,
        reported_by=other.id,
    ))
    # Recent verified submission from `user` within the cooldown
    recent = FuelPrice(
        truck_stop_id=stop.id, fuel_type='diesel',
        price_cents=355, currency='USD', source='driver', is_verified=True,
        reported_by=user.id,
    )
    db.session.add(recent)
    db.session.commit()
    # Manually backdate to 12h ago (still within 24h cooldown)
    recent.created_at = datetime.now(timezone.utc) - timedelta(hours=12)
    db.session.commit()
    from app.stops_api.contributions import _should_auto_verify_price
    assert _should_auto_verify_price(
        stop.id, 'diesel', 360, reporter_user_id=user.id
    ) is False


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


def test_review_handler_catches_integrity_error():
    """The submit_review handler must catch IntegrityError (concurrent-submission
    race past the existence check) and return 409 — not 500."""
    import inspect
    from app.stops_api import contributions
    src = inspect.getsource(contributions.submit_review)
    assert 'IntegrityError' in src, "submit_review must catch IntegrityError"
    assert '409' in src, "IntegrityError handler must return 409"


# --- Image upload magic-byte verification --------------------------------

def _real_jpeg_bytes():
    from io import BytesIO
    from PIL import Image
    img = Image.new('RGB', (8, 8), color='red')
    buf = BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def _real_png_bytes():
    from io import BytesIO
    from PIL import Image
    img = Image.new('RGBA', (8, 8), color=(0, 0, 255, 128))
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def test_verify_image_accepts_real_jpeg():
    from app.stops_api.contributions import _verify_image_bytes
    assert _verify_image_bytes(_real_jpeg_bytes(), 'image/jpeg') == 'image/jpeg'


def test_verify_image_accepts_real_png():
    from app.stops_api.contributions import _verify_image_bytes
    assert _verify_image_bytes(_real_png_bytes(), 'image/png') == 'image/png'


def test_verify_image_rejects_html_with_jpeg_content_type():
    """Forged Content-Type must be rejected — payload bytes are HTML."""
    import pytest
    from app.stops_api.contributions import _verify_image_bytes
    with pytest.raises(ValueError):
        _verify_image_bytes(b'<html><script>alert(1)</script></html>', 'image/jpeg')


def test_verify_image_rejects_svg():
    """SVG is not in the allow-list and is a stored-XSS risk."""
    import pytest
    from app.stops_api.contributions import _verify_image_bytes
    svg = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    with pytest.raises(ValueError):
        _verify_image_bytes(svg, 'image/svg+xml')


def test_verify_image_rejects_png_with_jpeg_content_type():
    """Magic bytes (PNG) must match claimed Content-Type (image/jpeg)."""
    import pytest
    from app.stops_api.contributions import _verify_image_bytes
    with pytest.raises(ValueError):
        _verify_image_bytes(_real_png_bytes(), 'image/jpeg')


def test_verify_image_rejects_truncated():
    import pytest
    from app.stops_api.contributions import _verify_image_bytes
    bad = _real_jpeg_bytes()[:20]
    with pytest.raises(ValueError):
        _verify_image_bytes(bad, 'image/jpeg')


# --- Photo URL allowlist sanitizer -----------------------------------------

def test_sanitize_photo_urls_drops_all_when_allowlist_empty(app):
    """Default (no allowlist) drops every URL — forces DB-backed upload path."""
    from app.stops_api.contributions import _sanitize_photo_urls
    with app.test_request_context():
        app.config['PHOTO_URL_ALLOWED_HOSTS'] = ''
        urls = [
            'https://i.imgur.com/abc.jpg',
            'https://attacker.com/track.png',
            'http://example.com/p.jpg',
        ]
        assert _sanitize_photo_urls(urls) == []


def test_sanitize_photo_urls_accepts_allowlisted_https(app):
    from app.stops_api.contributions import _sanitize_photo_urls
    with app.test_request_context():
        app.config['PHOTO_URL_ALLOWED_HOSTS'] = 'cdn.truckerpro.net,images.truckerpro.ca'
        urls = [
            'https://cdn.truckerpro.net/p1.jpg',
            'https://images.truckerpro.ca/p2.png',
            'https://attacker.com/p3.jpg',  # not on allowlist
            'http://cdn.truckerpro.net/p4.jpg',  # not https
        ]
        result = _sanitize_photo_urls(urls)
        assert 'https://cdn.truckerpro.net/p1.jpg' in result
        assert 'https://images.truckerpro.ca/p2.png' in result
        assert 'https://attacker.com/p3.jpg' not in result
        assert 'http://cdn.truckerpro.net/p4.jpg' not in result


def test_sanitize_photo_urls_subdomain_match(app):
    from app.stops_api.contributions import _sanitize_photo_urls
    with app.test_request_context():
        app.config['PHOTO_URL_ALLOWED_HOSTS'] = 'truckerpro.net'
        urls = ['https://cdn.truckerpro.net/x.jpg', 'https://evil-truckerpro.net/x.jpg']
        result = _sanitize_photo_urls(urls)
        assert 'https://cdn.truckerpro.net/x.jpg' in result
        assert 'https://evil-truckerpro.net/x.jpg' not in result


def test_sanitize_photo_urls_caps_at_20(app):
    from app.stops_api.contributions import _sanitize_photo_urls
    with app.test_request_context():
        app.config['PHOTO_URL_ALLOWED_HOSTS'] = 'cdn.truckerpro.net'
        urls = [f'https://cdn.truckerpro.net/p{i}.jpg' for i in range(50)]
        result = _sanitize_photo_urls(urls)
        assert len(result) == 20
