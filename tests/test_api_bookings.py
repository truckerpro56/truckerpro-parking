"""Tests for the bookings API endpoints."""


def test_create_booking_requires_auth(client):
    """POST /api/v1/bookings should require authentication."""
    resp = client.post('/api/v1/bookings', json={'location_id': 1})
    assert resp.status_code in (401, 302)


def test_create_booking_missing_fields(client, db):
    """POST /api/v1/bookings with no fields should return 400."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='booker@test.com', password_hash=pw, name='Booker', role='driver')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'booker@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/bookings', json={})
    assert resp.status_code == 400


def test_create_booking_invalid_dates(client, db):
    """POST /api/v1/bookings with bad date format should return 400."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='booker2@test.com', password_hash=pw, name='Booker2', role='driver')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'booker2@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/bookings', json={
        'location_id': 1,
        'start_datetime': 'not-a-date',
        'end_datetime': 'also-bad',
        'payment_method_id': 'pm_test',
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] == 'Invalid date format'


def test_create_booking_end_before_start(client, db):
    """POST /api/v1/bookings with end before start should return 400."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='booker3@test.com', password_hash=pw, name='Booker3', role='driver')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'booker3@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/bookings', json={
        'location_id': 1,
        'start_datetime': '2026-06-02T12:00:00',
        'end_datetime': '2026-06-01T12:00:00',
        'payment_method_id': 'pm_test',
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] == 'End date must be after start date'


def test_create_booking_location_not_found(client, db):
    """POST /api/v1/bookings with nonexistent location should return 404."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='booker4@test.com', password_hash=pw, name='Booker4', role='driver')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'booker4@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/bookings', json={
        'location_id': 99999,
        'start_datetime': '2026-06-01T12:00:00',
        'end_datetime': '2026-06-02T12:00:00',
        'payment_method_id': 'pm_test',
    })
    assert resp.status_code == 404


def test_create_booking_not_bookable(client, db):
    """POST /api/v1/bookings for non-bookable location should return 400."""
    import bcrypt
    from app.models.user import User
    from app.models.location import ParkingLocation
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='booker5@test.com', password_hash=pw, name='Booker5', role='driver')
    db.session.add(user)
    loc = ParkingLocation(
        name='No Book Lot', slug='no-book-lot', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, is_bookable=False, daily_rate=2500,
    )
    db.session.add(loc)
    db.session.commit()
    client.post('/login', data={'email': 'booker5@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/bookings', json={
        'location_id': loc.id,
        'start_datetime': '2026-06-01T12:00:00',
        'end_datetime': '2026-06-02T12:00:00',
        'payment_method_id': 'pm_test',
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'does not accept bookings' in data['error']


def test_create_booking_no_rate(client, db):
    """POST /api/v1/bookings for booking type with no rate should return 400."""
    import bcrypt
    from app.models.user import User
    from app.models.location import ParkingLocation
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='booker6@test.com', password_hash=pw, name='Booker6', role='driver')
    db.session.add(user)
    loc = ParkingLocation(
        name='No Rate Lot', slug='no-rate-lot', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, is_bookable=True, daily_rate=2500,
        # hourly_rate is None
    )
    db.session.add(loc)
    db.session.commit()
    client.post('/login', data={'email': 'booker6@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/bookings', json={
        'location_id': loc.id,
        'start_datetime': '2026-06-01T12:00:00',
        'end_datetime': '2026-06-02T12:00:00',
        'booking_type': 'hourly',
        'payment_method_id': 'pm_test',
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'No hourly rate' in data['error']
