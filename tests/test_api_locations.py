"""Tests for the locations API endpoints."""


def test_list_locations_empty(client):
    resp = client.get('/api/v1/locations')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 0
    assert data['locations'] == []


def test_list_locations_with_data(client, db):
    from app.models.location import ParkingLocation
    loc = ParkingLocation(
        name='Test Lot', slug='test-lot', address='123 Main St',
        city='Toronto', province='ON', latitude=43.65, longitude=-79.38,
        location_type='truck_stop', total_spots=10, is_active=True,
    )
    db.session.add(loc)
    db.session.commit()
    resp = client.get('/api/v1/locations')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['name'] == 'Test Lot'


def test_filter_by_province(client, db):
    from app.models.location import ParkingLocation
    for prov in ['ON', 'AB']:
        db.session.add(ParkingLocation(
            name=f'Lot {prov}', slug=f'lot-{prov.lower()}', address='123 St',
            city='City', province=prov, latitude=43.0, longitude=-79.0,
            is_active=True,
        ))
    db.session.commit()
    resp = client.get('/api/v1/locations?province=ON')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['province'] == 'ON'


def test_filter_by_city(client, db):
    from app.models.location import ParkingLocation
    for city in ['Toronto', 'Calgary']:
        db.session.add(ParkingLocation(
            name=f'Lot {city}', slug=f'lot-{city.lower()}', address='123 St',
            city=city, province='ON', latitude=43.0, longitude=-79.0,
            is_active=True,
        ))
    db.session.commit()
    resp = client.get('/api/v1/locations?city=toronto')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['city'] == 'Toronto'


def test_filter_by_type(client, db):
    from app.models.location import ParkingLocation
    db.session.add(ParkingLocation(
        name='Rest Stop', slug='rest-stop', address='Hwy 401',
        city='Kingston', province='ON', latitude=44.23, longitude=-76.49,
        location_type='rest_area', is_active=True,
    ))
    db.session.add(ParkingLocation(
        name='Truck Stop', slug='truck-stop', address='Hwy 401',
        city='Kingston', province='ON', latitude=44.24, longitude=-76.50,
        location_type='truck_stop', is_active=True,
    ))
    db.session.commit()
    resp = client.get('/api/v1/locations?type=rest_area')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['location_type'] == 'rest_area'


def test_filter_bookable(client, db):
    from app.models.location import ParkingLocation
    db.session.add(ParkingLocation(
        name='Bookable', slug='bookable', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, is_bookable=True,
    ))
    db.session.add(ParkingLocation(
        name='Not Bookable', slug='not-bookable', address='2 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, is_bookable=False,
    ))
    db.session.commit()
    resp = client.get('/api/v1/locations?bookable=1')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['name'] == 'Bookable'


def test_filter_lcv(client, db):
    from app.models.location import ParkingLocation
    db.session.add(ParkingLocation(
        name='LCV Lot', slug='lcv-lot', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, lcv_capable=True,
    ))
    db.session.add(ParkingLocation(
        name='Normal Lot', slug='normal-lot', address='2 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, lcv_capable=False,
    ))
    db.session.commit()
    resp = client.get('/api/v1/locations?lcv=1')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['name'] == 'LCV Lot'


def test_filter_price_range(client, db):
    from app.models.location import ParkingLocation
    db.session.add(ParkingLocation(
        name='Cheap', slug='cheap', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, daily_rate=1000,
    ))
    db.session.add(ParkingLocation(
        name='Expensive', slug='expensive', address='2 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, daily_rate=5000,
    ))
    db.session.commit()
    resp = client.get('/api/v1/locations?min_price=2000&max_price=6000')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['name'] == 'Expensive'


def test_text_search(client, db):
    from app.models.location import ParkingLocation
    db.session.add(ParkingLocation(
        name='Maple Grove Parking', slug='maple-grove', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True,
    ))
    db.session.add(ParkingLocation(
        name='Highway Lot', slug='highway-lot', address='2 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True,
    ))
    db.session.commit()
    resp = client.get('/api/v1/locations?q=maple')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['name'] == 'Maple Grove Parking'


def test_pagination(client, db):
    from app.models.location import ParkingLocation
    for i in range(5):
        db.session.add(ParkingLocation(
            name=f'Lot {i}', slug=f'lot-{i}', address='1 St',
            city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
            is_active=True,
        ))
    db.session.commit()
    resp = client.get('/api/v1/locations?page=1&per_page=2')
    data = resp.get_json()
    assert data['total'] == 5
    assert len(data['locations']) == 2
    assert data['page'] == 1
    assert data['per_page'] == 2

    resp2 = client.get('/api/v1/locations?page=3&per_page=2')
    data2 = resp2.get_json()
    assert len(data2['locations']) == 1


def test_per_page_max_100(client, db):
    resp = client.get('/api/v1/locations?per_page=999')
    data = resp.get_json()
    assert data['per_page'] == 100


def test_inactive_locations_excluded(client, db):
    from app.models.location import ParkingLocation
    db.session.add(ParkingLocation(
        name='Active', slug='active', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True,
    ))
    db.session.add(ParkingLocation(
        name='Inactive', slug='inactive', address='2 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=False,
    ))
    db.session.commit()
    resp = client.get('/api/v1/locations')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['name'] == 'Active'


def test_get_location_detail(client, db):
    from app.models.location import ParkingLocation
    loc = ParkingLocation(
        name='Detail Lot', slug='detail-lot', address='456 Ave',
        city='Calgary', province='AB', latitude=51.05, longitude=-114.07,
        is_active=True, daily_rate=2500,
    )
    db.session.add(loc)
    db.session.commit()
    resp = client.get(f'/api/v1/locations/{loc.id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['name'] == 'Detail Lot'
    assert data['daily_rate'] == 2500


def test_get_location_detail_includes_reviews(client, db):
    from app.models.location import ParkingLocation
    from app.models.review import ParkingReview
    from app.models.booking import ParkingBooking
    from app.models.user import User
    from datetime import datetime, timezone

    user = User(email='driver@test.com', password_hash='x', name='Driver')
    db.session.add(user)
    db.session.flush()

    loc = ParkingLocation(
        name='Reviewed Lot', slug='reviewed-lot', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True,
    )
    db.session.add(loc)
    db.session.flush()

    booking = ParkingBooking(
        booking_ref='TEST-001',
        location_id=loc.id, driver_id=user.id,
        start_datetime=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_datetime=datetime(2026, 1, 2, tzinfo=timezone.utc),
        booking_type='daily',
        status='completed', subtotal=2500, total_amount=2500,
    )
    db.session.add(booking)
    db.session.flush()

    db.session.add(ParkingReview(
        booking_id=booking.id, location_id=loc.id,
        driver_id=user.id, rating=4,
    ))
    db.session.add(ParkingReview(
        booking_id=booking.id, location_id=loc.id,
        driver_id=user.id, rating=5,
    ))
    db.session.commit()

    resp = client.get(f'/api/v1/locations/{loc.id}')
    data = resp.get_json()
    assert data['review_count'] == 2
    assert data['rating_avg'] == 4.5


def test_get_location_not_found(client):
    resp = client.get('/api/v1/locations/99999')
    assert resp.status_code == 404


def test_get_inactive_location_returns_404(client, db):
    from app.models.location import ParkingLocation
    loc = ParkingLocation(
        name='Hidden', slug='hidden', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=False,
    )
    db.session.add(loc)
    db.session.commit()
    resp = client.get(f'/api/v1/locations/{loc.id}')
    assert resp.status_code == 404


def test_sort_price_asc(client, db):
    from app.models.location import ParkingLocation
    db.session.add(ParkingLocation(
        name='Expensive', slug='expensive', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, daily_rate=5000,
    ))
    db.session.add(ParkingLocation(
        name='Cheap', slug='cheap', address='2 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, daily_rate=1000,
    ))
    db.session.commit()
    resp = client.get('/api/v1/locations?sort=price_asc')
    data = resp.get_json()
    assert data['locations'][0]['name'] == 'Cheap'
    assert data['locations'][1]['name'] == 'Expensive'


def test_sort_price_desc(client, db):
    from app.models.location import ParkingLocation
    db.session.add(ParkingLocation(
        name='Expensive', slug='expensive', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, daily_rate=5000,
    ))
    db.session.add(ParkingLocation(
        name='Cheap', slug='cheap', address='2 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, daily_rate=1000,
    ))
    db.session.commit()
    resp = client.get('/api/v1/locations?sort=price_desc')
    data = resp.get_json()
    assert data['locations'][0]['name'] == 'Expensive'
    assert data['locations'][1]['name'] == 'Cheap'


def test_geo_search(client, db):
    from app.models.location import ParkingLocation
    # Toronto area
    db.session.add(ParkingLocation(
        name='Toronto Lot', slug='toronto-lot', address='1 Yonge St',
        city='Toronto', province='ON', latitude=43.65, longitude=-79.38,
        is_active=True,
    ))
    # Calgary - far away
    db.session.add(ParkingLocation(
        name='Calgary Lot', slug='calgary-lot', address='1 Centre St',
        city='Calgary', province='AB', latitude=51.05, longitude=-114.07,
        is_active=True,
    ))
    db.session.commit()
    # Search 50km around Toronto
    resp = client.get('/api/v1/locations?lat=43.65&lng=-79.38&radius=50')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['name'] == 'Toronto Lot'
    assert 'distance_km' in data['locations'][0]


def test_amenities_filter(client, db):
    from app.models.location import ParkingLocation
    db.session.add(ParkingLocation(
        name='Full Service', slug='full-service', address='1 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, amenities=['wifi', 'shower', 'fuel'],
    ))
    db.session.add(ParkingLocation(
        name='Basic', slug='basic', address='2 St',
        city='Toronto', province='ON', latitude=43.0, longitude=-79.0,
        is_active=True, amenities=['parking'],
    ))
    db.session.commit()
    resp = client.get('/api/v1/locations?amenities=wifi,shower')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['name'] == 'Full Service'
