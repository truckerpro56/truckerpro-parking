"""Tests for IndexNow URL submission."""
import pytest


class TestIndexNowVerification:
    def test_verify_returns_key(self, app, client):
        app.config['INDEXNOW_KEY'] = 'test123abc'
        resp = client.get('/test123abc.txt')
        assert resp.status_code == 200
        assert b'test123abc' in resp.data

    def test_wrong_key_returns_404(self, app, client):
        app.config['INDEXNOW_KEY'] = 'test123abc'
        resp = client.get('/wrongkey.txt')
        assert resp.status_code == 404

    def test_empty_key_returns_404(self, app, client):
        app.config['INDEXNOW_KEY'] = ''
        resp = client.get('/.txt')
        assert resp.status_code == 404


class TestIndexNowStopsVerification:
    def test_verify_on_stops_domain(self, app, stops_client):
        app.config['INDEXNOW_KEY'] = 'stopskey456'
        resp = stops_client.get('/stopskey456.txt')
        assert resp.status_code == 200


class TestIndexNowService:
    def test_submit_skips_without_key(self, app):
        app.config['INDEXNOW_KEY'] = ''
        with app.app_context():
            from app.services.indexnow import submit_urls
            result = submit_urls('example.com', ['https://example.com/'])
            assert result['skipped'] is True
