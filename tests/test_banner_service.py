"""Tests for smart contextual banner service."""
from app.services.banner_service import get_banners


class _Stop:
    """Lightweight stand-in for TruckStop — banner service only uses getattr."""
    pass


def _make_stop(**overrides):
    defaults = dict(
        brand='loves', name='Test Stop', slug='test-stop',
        address='123 St', city='Dallas', state_province='TX',
        country='US', latitude=32.7767, longitude=-96.7970,
        highway='I-35', data_source='manual',
        nearest_border_crossing=None, border_distance_km=None,
        parking_location_id=None,
    )
    defaults.update(overrides)
    stop = _Stop()
    for k, v in defaults.items():
        setattr(stop, k, v)
    return stop


def test_tms_banner_always_present():
    stop = _make_stop()
    banners = get_banners(stop)
    tms = [b for b in banners if b['type'] == 'tms']
    assert len(tms) == 1
    assert 'tms.truckerpro.ca' in tms[0]['url']


def test_tms_banner_corridor_copy():
    stop = _make_stop(highway='I-35')
    banners = get_banners(stop)
    tms = [b for b in banners if b['type'] == 'tms'][0]
    assert 'I-35' in tms['copy']


def test_tms_banner_metro_copy():
    stop = _make_stop(highway=None, city='Chicago')
    banners = get_banners(stop)
    tms = [b for b in banners if b['type'] == 'tms'][0]
    assert 'Chicago' in tms['copy']


def test_border_banner_when_close():
    stop = _make_stop(
        nearest_border_crossing='Peace Bridge (Fort Erie/Buffalo)',
        border_distance_km=8.5, country='US',
    )
    banners = get_banners(stop)
    border = [b for b in banners if b['type'] == 'border']
    assert len(border) == 1
    assert 'Peace Bridge' in border[0]['copy']
    assert 'border.truckerpro.ca' in border[0]['url']


def test_no_border_banner_when_far():
    stop = _make_stop(nearest_border_crossing='Peace Bridge', border_distance_km=250.0)
    banners = get_banners(stop)
    border = [b for b in banners if b['type'] == 'border']
    assert len(border) == 0


def test_parking_banner_with_linked_location():
    stop = _make_stop(parking_location_id=42)
    banners = get_banners(stop)
    parking = [b for b in banners if b['type'] == 'parking']
    assert len(parking) == 1
    assert 'Reserve' in parking[0]['copy']


def test_parking_banner_without_linked_location():
    stop = _make_stop(parking_location_id=None)
    banners = get_banners(stop)
    parking = [b for b in banners if b['type'] == 'parking']
    assert len(parking) == 1
    assert 'nearby' in parking[0]['copy'].lower()


def test_fmcsa_banner_always_present():
    stop = _make_stop()
    banners = get_banners(stop)
    fmcsa = [b for b in banners if b['type'] == 'fmcsa']
    assert len(fmcsa) == 1
    assert 'fmcsa.truckerpro.net' in fmcsa[0]['url']


def test_banner_order():
    stop = _make_stop(
        nearest_border_crossing='Peace Bridge', border_distance_km=8.0, parking_location_id=1,
    )
    banners = get_banners(stop)
    types = [b['type'] for b in banners]
    assert types == ['tms', 'border', 'parking', 'fmcsa']
