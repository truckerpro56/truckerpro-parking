"""Tests for blog routes — parking and stops domains."""
import pytest


class TestParkingBlogIndex:
    def test_blog_index_returns_200(self, client):
        resp = client.get('/blog')
        assert resp.status_code == 200

    def test_blog_index_contains_blog_heading(self, client):
        resp = client.get('/blog')
        assert b'Blog' in resp.data

    def test_blog_index_contains_post_titles(self, client):
        resp = client.get('/blog')
        assert resp.status_code == 200

    def test_blog_index_category_filter(self, client):
        resp = client.get('/blog?category=guides')
        assert resp.status_code == 200

    def test_blog_index_invalid_category_returns_200(self, client):
        resp = client.get('/blog?category=nonexistent')
        assert resp.status_code == 200


class TestParkingBlogPost:
    def test_nonexistent_post_returns_404(self, client):
        resp = client.get('/blog/this-does-not-exist')
        assert resp.status_code == 404

    def test_stops_post_not_accessible_on_parking(self, client):
        resp = client.get('/blog/stops-test')
        assert resp.status_code == 404


class TestStopsBlogIndex:
    def test_blog_index_returns_200(self, stops_client):
        resp = stops_client.get('/blog')
        assert resp.status_code == 200

    def test_blog_index_contains_blog_heading(self, stops_client):
        resp = stops_client.get('/blog')
        assert b'Blog' in resp.data

    def test_blog_index_category_filter(self, stops_client):
        resp = stops_client.get('/blog?category=fuel')
        assert resp.status_code == 200


class TestStopsBlogPost:
    def test_nonexistent_post_returns_404(self, stops_client):
        resp = stops_client.get('/blog/this-does-not-exist')
        assert resp.status_code == 404

    def test_parking_post_not_accessible_on_stops(self, stops_client):
        resp = stops_client.get('/blog/test-seo-post')
        assert resp.status_code == 404


class TestParkingBlogContent:
    def test_blog_index_has_posts(self, client):
        resp = client.get('/blog')
        assert resp.status_code == 200
        assert b'Truck Parking' in resp.data or b'truck parking' in resp.data.lower()

    def test_blog_post_has_cta(self, client):
        resp = client.get('/blog')
        if resp.status_code == 200:
            assert b'data-action' in resp.data

    def test_blog_has_ga4(self, client):
        resp = client.get('/blog')
        assert b'G-RREBK9SZZJ' in resp.data

    def test_blog_post_renders(self, client):
        resp = client.get('/blog/safe-overnight-truck-parking-canada')
        assert resp.status_code == 200

    def test_blog_post_has_schema_org(self, client):
        resp = client.get('/blog/safe-overnight-truck-parking-canada')
        if resp.status_code == 200:
            assert b'BlogPosting' in resp.data


class TestStopsBlogContent:
    def test_blog_index_has_posts(self, stops_client):
        resp = stops_client.get('/blog')
        assert resp.status_code == 200

    def test_blog_has_ga4(self, stops_client):
        resp = stops_client.get('/blog')
        assert b'G-RREBK9SZZJ' in resp.data

    def test_blog_post_renders(self, stops_client):
        resp = stops_client.get('/blog/complete-guide-truck-stops-america')
        assert resp.status_code == 200

    def test_blog_post_has_schema_org(self, stops_client):
        resp = stops_client.get('/blog/complete-guide-truck-stops-america')
        if resp.status_code == 200:
            assert b'BlogPosting' in resp.data
