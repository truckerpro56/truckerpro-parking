import math

def test_haversine_same_point():
    from app.services.geo_service import haversine_distance
    assert haversine_distance(43.65, -79.38, 43.65, -79.38) == 0.0

def test_haversine_known_distance():
    from app.services.geo_service import haversine_distance
    # Toronto to Ottawa ~350-360 km
    dist = haversine_distance(43.65, -79.38, 45.42, -75.69)
    assert 340 < dist < 370

def test_slugify():
    from app.services.geo_service import slugify
    assert slugify("Flying J Travel Centre") == "flying-j-travel-centre"
    assert slugify("  Hello   World  ") == "hello-world"
    assert slugify("Test!@#$%^&*()") == "test"

def test_format_price():
    from app.services.geo_service import format_price
    assert format_price(2500) == "25.00"
    assert format_price(None) is None
    assert format_price(0) == "0.00"
