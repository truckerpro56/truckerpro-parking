"""Tests for owner dashboard and create/update listing endpoints."""


def test_owner_dashboard_requires_auth(client):
    """GET /owner/dashboard should require authentication."""
    resp = client.get('/owner/dashboard')
    assert resp.status_code in (302, 401)


def test_create_listing_requires_auth(client):
    """POST /api/v1/locations should require authentication."""
    resp = client.post('/api/v1/locations', json={'name': 'Test'})
    assert resp.status_code in (302, 401)


def test_owner_dashboard_authenticated(client, db):
    """GET /owner/dashboard should return 200 for authenticated user."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='owner@test.com', password_hash=pw, name='Owner', role='owner')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'owner@test.com', 'password': 'Pass123!'})
    resp = client.get('/owner/dashboard')
    assert resp.status_code == 200


def test_create_listing_missing_fields(client, db):
    """POST /api/v1/locations with missing required fields should return 400."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='owner2@test.com', password_hash=pw, name='Owner2', role='owner')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'owner2@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/locations', json={'name': 'Test'})
    assert resp.status_code == 400


def test_create_listing_invalid_province(client, db):
    """POST /api/v1/locations with invalid province should return 400."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='owner3@test.com', password_hash=pw, name='Owner3', role='owner')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'owner3@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/locations', json={
        'name': 'Test Lot', 'address': '123 St', 'city': 'City', 'province': 'XX',
        'latitude': 43.0, 'longitude': -79.0,
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'Invalid province' in data['error']


def test_create_listing_success(client, db):
    """POST /api/v1/locations with valid data should create a listing."""
    import bcrypt
    from app.models.user import User
    from app.models.location import ParkingLocation
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='owner4@test.com', password_hash=pw, name='Owner4', role='owner')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'owner4@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/locations', json={
        'name': 'My Truck Lot',
        'address': '100 Industrial Rd',
        'city': 'Toronto',
        'province': 'ON',
        'latitude': 43.65,
        'longitude': -79.38,
        'daily_rate': 2500,
        'total_spots': 20,
        'is_bookable': True,
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'slug' in data
    # Verify in DB
    loc = ParkingLocation.query.filter_by(slug=data['slug']).first()
    assert loc is not None
    assert loc.name == 'My Truck Lot'
    assert loc.owner_id == user.id


def test_update_listing_not_authorized(client, db):
    """POST /api/v1/locations updating another owner's listing should return 403."""
    import bcrypt
    from app.models.user import User
    from app.models.location import ParkingLocation
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    owner1 = User(email='owner5@test.com', password_hash=pw, name='Owner5', role='owner')
    owner2 = User(email='owner6@test.com', password_hash=pw, name='Owner6', role='owner')
    db.session.add_all([owner1, owner2])
    db.session.flush()
    loc = ParkingLocation(
        owner_id=owner1.id, name='Owner1 Lot', slug='owner1-lot',
        address='1 St', city='Toronto', province='ON',
        latitude=43.0, longitude=-79.0, is_active=True,
    )
    db.session.add(loc)
    db.session.commit()
    # Login as owner2 and try to update owner1's listing
    client.post('/login', data={'email': 'owner6@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/locations', json={
        'id': loc.id,
        'name': 'Stolen Lot',
        'address': '1 St',
        'city': 'Toronto',
        'province': 'ON',
        'latitude': 43.0,
        'longitude': -79.0,
    })
    assert resp.status_code == 403


def test_create_listing_negative_rate(client, db):
    """POST /api/v1/locations with negative rate should return 400."""
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='owner7@test.com', password_hash=pw, name='Owner7', role='owner')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'owner7@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/locations', json={
        'name': 'Bad Rate Lot',
        'address': '1 St',
        'city': 'Toronto',
        'province': 'ON',
        'latitude': 43.0,
        'longitude': -79.0,
        'daily_rate': -100,
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'negative' in data['error'].lower()
