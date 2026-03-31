"""Tests for TruckStop model."""
from app.models.truck_stop import TruckStop


def test_create_truck_stop(db):
    stop = TruckStop(
        brand='loves', brand_display_name="Love's Travel Stops",
        name="Love's Travel Stop #521", slug='loves-521-dallas-tx',
        store_number='521', address='1234 I-35 Frontage Rd',
        city='Dallas', state_province='TX', postal_code='75201',
        country='US', latitude=32.7767, longitude=-96.7970,
        highway='I-35', exit_number='42', total_parking_spots=150,
        truck_spots=120, has_diesel=True, has_showers=True,
        shower_count=8, has_scale=True, scale_type='cat',
        data_source='csv_import',
    )
    db.session.add(stop)
    db.session.commit()
    assert stop.id is not None
    assert stop.brand == 'loves'
    assert stop.is_active is True
    assert stop.is_verified is False


def test_truck_stop_slug_unique(db):
    import pytest
    from sqlalchemy.exc import IntegrityError
    s1 = TruckStop(brand='loves', name='Stop 1', slug='same-slug',
        address='123 St', city='Dallas', state_province='TX',
        country='US', latitude=32.0, longitude=-96.0, data_source='manual')
    s2 = TruckStop(brand='loves', name='Stop 2', slug='same-slug',
        address='456 St', city='Dallas', state_province='TX',
        country='US', latitude=32.1, longitude=-96.1, data_source='manual')
    db.session.add(s1)
    db.session.commit()
    db.session.add(s2)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_truck_stop_json_fields(db):
    stop = TruckStop(
        brand='pilot_flying_j', name='Pilot #18', slug='pilot-18-toronto-on',
        address='401 Hwy', city='Toronto', state_province='ON',
        country='CA', latitude=43.65, longitude=-79.38,
        restaurants=['Subway', "Denny's"],
        loyalty_programs=['myRewards'],
        hours_of_operation={'mon': '24h', 'tue': '24h'},
        data_source='csv_import',
    )
    db.session.add(stop)
    db.session.commit()
    fetched = TruckStop.query.get(stop.id)
    assert fetched.restaurants == ['Subway', "Denny's"]
    assert fetched.hours_of_operation['mon'] == '24h'


def test_truck_stop_defaults(db):
    stop = TruckStop(
        brand='independent', name='Joes Stop', slug='joes-stop',
        address='Rte 1', city='Smalltown', state_province='ME',
        country='US', latitude=44.0, longitude=-69.0, data_source='manual')
    db.session.add(stop)
    db.session.commit()
    assert stop.has_diesel is True
    assert stop.has_gas is False
    assert stop.has_def is False
    assert stop.has_ev_charging is False
    assert stop.has_showers is False
    assert stop.has_scale is False
    assert stop.has_repair is False
    assert stop.has_tire_service is False
    assert stop.has_wifi is False
    assert stop.has_laundry is False
    assert stop.is_active is True
    assert stop.is_verified is False


def test_truck_stop_parking_location_link(db):
    from app.models.location import ParkingLocation
    loc = ParkingLocation(
        name='Parking Lot', slug='parking-lot', address='123 St',
        city='Toronto', province='ON', latitude=43.65, longitude=-79.38,
        is_active=True,
    )
    db.session.add(loc)
    db.session.commit()
    stop = TruckStop(
        brand='loves', name='Loves Toronto', slug='loves-toronto',
        address='456 St', city='Toronto', state_province='ON',
        country='CA', latitude=43.65, longitude=-79.38,
        parking_location_id=loc.id, data_source='manual',
    )
    db.session.add(stop)
    db.session.commit()
    assert stop.parking_location_id == loc.id
    assert stop.parking_location.name == 'Parking Lot'
