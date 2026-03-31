"""Tests for host-based routing middleware."""
from flask import g


def test_parking_domain_sets_site_parking(app, client):
    """Request to parking domain sets g.site = 'parking'."""
    with app.test_request_context('/', headers={'Host': 'parking.truckerpro.ca'}):
        app.preprocess_request()
        assert g.site == 'parking'


def test_stops_domain_sets_site_stops(app, client):
    """Request to stops domain sets g.site = 'stops'."""
    with app.test_request_context('/', headers={'Host': 'stops.truckerpro.net'}):
        app.preprocess_request()
        assert g.site == 'stops'


def test_localhost_defaults_to_parking(app, client):
    """Localhost defaults to parking site."""
    with app.test_request_context('/', headers={'Host': 'localhost'}):
        app.preprocess_request()
        assert g.site == 'parking'


def test_health_works_on_any_domain(client):
    """Health check works regardless of domain."""
    resp = client.get('/health')
    assert resp.status_code == 200
