"""Tests for border crossing distance computation."""
from app.services.border_crossings import (
    BORDER_CROSSINGS, find_nearest_crossing, compute_border_distance,
)


def test_border_crossings_populated():
    assert len(BORDER_CROSSINGS) > 50


def test_find_nearest_crossing_buffalo():
    name, dist = find_nearest_crossing(42.8864, -78.8784)
    assert 'Peace Bridge' in name
    assert dist < 10


def test_find_nearest_crossing_detroit():
    name, dist = find_nearest_crossing(42.3314, -83.0458)
    assert 'Ambassador' in name or 'Detroit' in name
    assert dist < 15


def test_find_nearest_crossing_far_away():
    name, dist = find_nearest_crossing(32.7767, -96.7970)
    assert dist > 500


def test_compute_border_distance_on_stop(db):
    from app.models.truck_stop import TruckStop
    stop = TruckStop(
        brand='loves', name='Loves Buffalo', slug='loves-buffalo',
        address='123 St', city='Buffalo', state_province='NY',
        country='US', latitude=42.8864, longitude=-78.8784,
        data_source='manual',
    )
    db.session.add(stop)
    db.session.commit()
    compute_border_distance(stop)
    db.session.commit()
    assert stop.nearest_border_crossing is not None
    assert stop.border_distance_km < 10
