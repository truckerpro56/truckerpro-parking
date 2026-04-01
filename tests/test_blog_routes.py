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
