"""Tests for the reviews API endpoints."""
from datetime import datetime, timezone


def test_submit_review_requires_auth(client):
    """POST /api/v1/reviews should require authentication."""
    resp = client.post('/api/v1/reviews', json={'booking_id': 1, 'rating': 5})
    assert resp.status_code in (401, 302)


def test_submit_review_invalid_rating(client, db):
    """POST /api/v1/reviews with rating > 5 should return 400."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='reviewer@test.com', password_hash=pw, name='Rev', role='driver')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'reviewer@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/reviews', json={'booking_id': 1, 'rating': 6})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'Rating must be 1-5' in data['error']


def test_submit_review_rating_zero(client, db):
    """POST /api/v1/reviews with rating 0 should return 400."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='reviewer0@test.com', password_hash=pw, name='Rev0', role='driver')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'reviewer0@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/reviews', json={'booking_id': 1, 'rating': 0})
    assert resp.status_code == 400


def test_submit_review_missing_fields(client, db):
    """POST /api/v1/reviews with no fields should return 400."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='reviewer2@test.com', password_hash=pw, name='Rev2', role='driver')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'reviewer2@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/reviews', json={})
    assert resp.status_code == 400


def test_submit_review_booking_not_found(client, db):
    """POST /api/v1/reviews for nonexistent booking should return 404."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='reviewer3@test.com', password_hash=pw, name='Rev3', role='driver')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'reviewer3@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/reviews', json={'booking_id': 99999, 'rating': 4})
    assert resp.status_code == 404


def test_submit_review_booking_not_completed(client, db):
    """POST /api/v1/reviews for a confirmed (not completed) booking should return 400."""
    import bcrypt
    from app.models.user import User
    from app.models.location import ParkingLocation
    from app.models.booking import ParkingBooking
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='reviewer4@test.com', password_hash=pw, name='Rev4', role='driver')
    db.session.add(user)
    db.session.flush()
    loc = ParkingLocation(
        name='Review Lot', slug='review-lot', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True,
    )
    db.session.add(loc)
    db.session.flush()
    booking = ParkingBooking(
        booking_ref='REV-001', location_id=loc.id, driver_id=user.id,
        start_datetime=datetime(2026, 6, 1, tzinfo=timezone.utc),
        end_datetime=datetime(2026, 6, 2, tzinfo=timezone.utc),
        booking_type='daily', subtotal=2500, total_amount=2825,
        status='confirmed',
    )
    db.session.add(booking)
    db.session.commit()
    client.post('/login', data={'email': 'reviewer4@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/reviews', json={'booking_id': booking.id, 'rating': 5})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'completed' in data['error'].lower()


def test_submit_review_success(client, db):
    """POST /api/v1/reviews for a completed booking should succeed."""
    import bcrypt
    from app.models.user import User
    from app.models.location import ParkingLocation
    from app.models.booking import ParkingBooking
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='reviewer5@test.com', password_hash=pw, name='Rev5', role='driver')
    db.session.add(user)
    db.session.flush()
    loc = ParkingLocation(
        name='Good Lot', slug='good-lot', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True,
    )
    db.session.add(loc)
    db.session.flush()
    booking = ParkingBooking(
        booking_ref='REV-002', location_id=loc.id, driver_id=user.id,
        start_datetime=datetime(2026, 6, 1, tzinfo=timezone.utc),
        end_datetime=datetime(2026, 6, 2, tzinfo=timezone.utc),
        booking_type='daily', subtotal=2500, total_amount=2825,
        status='completed',
    )
    db.session.add(booking)
    db.session.commit()
    client.post('/login', data={'email': 'reviewer5@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/reviews', json={
        'booking_id': booking.id, 'rating': 4, 'review_text': 'Great spot!',
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True


def test_submit_review_duplicate(client, db):
    """POST /api/v1/reviews twice for same booking should fail on second."""
    import bcrypt
    from app.models.user import User
    from app.models.location import ParkingLocation
    from app.models.booking import ParkingBooking
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='reviewer6@test.com', password_hash=pw, name='Rev6', role='driver')
    db.session.add(user)
    db.session.flush()
    loc = ParkingLocation(
        name='Dup Lot', slug='dup-lot', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True,
    )
    db.session.add(loc)
    db.session.flush()
    booking = ParkingBooking(
        booking_ref='REV-003', location_id=loc.id, driver_id=user.id,
        start_datetime=datetime(2026, 6, 1, tzinfo=timezone.utc),
        end_datetime=datetime(2026, 6, 2, tzinfo=timezone.utc),
        booking_type='daily', subtotal=2500, total_amount=2825,
        status='completed',
    )
    db.session.add(booking)
    db.session.commit()
    client.post('/login', data={'email': 'reviewer6@test.com', 'password': 'Pass123!'})
    # First review succeeds
    resp1 = client.post('/api/v1/reviews', json={'booking_id': booking.id, 'rating': 5})
    assert resp1.status_code == 200
    # Second review fails
    resp2 = client.post('/api/v1/reviews', json={'booking_id': booking.id, 'rating': 3})
    assert resp2.status_code == 400
    data = resp2.get_json()
    assert 'Already reviewed' in data['error']
