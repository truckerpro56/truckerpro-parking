"""Tests for PWA support — manifest, service worker, and meta tags."""
import json


class TestPWA:
    def test_manifest_accessible(self, stops_client):
        resp = stops_client.get('/static/manifest.json')
        assert resp.status_code == 200

    def test_manifest_is_valid_json(self, stops_client):
        resp = stops_client.get('/static/manifest.json')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['name'] == 'Truck Stops Directory'
        assert data['short_name'] == 'Truck Stops'
        assert data['display'] == 'standalone'
        assert data['theme_color'] == '#0f2440'
        assert len(data['icons']) >= 2

    def test_service_worker_accessible(self, stops_client):
        resp = stops_client.get('/sw.js')
        assert resp.status_code == 200

    def test_service_worker_content_type(self, stops_client):
        resp = stops_client.get('/sw.js')
        assert resp.status_code == 200
        assert 'javascript' in resp.content_type

    def test_service_worker_not_cached(self, stops_client):
        resp = stops_client.get('/sw.js')
        assert resp.status_code == 200
        # SW must not be cached by browser so updates are detected promptly
        cc = resp.cache_control
        assert cc.no_store or cc.max_age == 0

    def test_base_has_manifest_link(self, stops_client):
        resp = stops_client.get('/')
        assert resp.status_code == 200
        assert b'manifest.json' in resp.data

    def test_base_has_theme_color(self, stops_client):
        resp = stops_client.get('/')
        assert resp.status_code == 200
        assert b'theme-color' in resp.data

    def test_base_has_apple_pwa_tags(self, stops_client):
        resp = stops_client.get('/')
        assert resp.status_code == 200
        assert b'apple-mobile-web-app-capable' in resp.data
        assert b'apple-mobile-web-app-title' in resp.data

    def test_base_has_sw_registration(self, stops_client):
        resp = stops_client.get('/')
        assert resp.status_code == 200
        assert b'serviceWorker' in resp.data
        assert b'/sw.js' in resp.data

    def test_sw_js_content(self, stops_client):
        resp = stops_client.get('/sw.js')
        assert resp.status_code == 200
        assert b'CACHE_NAME' in resp.data
        assert b'install' in resp.data
        assert b'activate' in resp.data
        assert b'fetch' in resp.data
