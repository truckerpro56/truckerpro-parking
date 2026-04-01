"""Tests for stops OTP authentication."""
import hashlib
import pytest
from app.models.user import User


class TestStopsLogin:
    def test_login_page_returns_200(self, stops_client):
        resp = stops_client.get('/login')
        assert resp.status_code == 200

    def test_login_page_contains_form(self, stops_client):
        resp = stops_client.get('/login')
        assert b'email' in resp.data

    def test_login_redirects_to_verify(self, stops_client, db):
        resp = stops_client.post('/login', data={'email': 'driver@test.com'})
        assert resp.status_code == 302
        assert '/verify' in resp.headers.get('Location', '')

    def test_login_creates_user(self, stops_client, db):
        stops_client.post('/login', data={'email': 'newdriver@test.com'})
        user = User.query.filter_by(email='newdriver@test.com').first()
        assert user is not None
        assert user.otp_code is not None

    def test_login_invalid_email_shows_error(self, stops_client):
        resp = stops_client.post('/login', data={'email': 'notanemail'})
        assert resp.status_code == 200  # stays on login page


class TestStopsVerify:
    def test_verify_page_redirects_without_session(self, stops_client):
        resp = stops_client.get('/verify')
        assert resp.status_code == 302

    def test_verify_with_correct_code_logs_in(self, stops_client, db):
        """Full flow: POST login, read generated code, POST verify."""
        from app.services.otp_service import generate_otp
        # Create the user first
        user = User(email='verify@test.com', role='driver')
        db.session.add(user)
        db.session.commit()
        # Generate a known code before login so we can capture it
        code = generate_otp(user)
        # POST login — this sets the session cookie on the stops domain
        login_resp = stops_client.post('/login', data={'email': 'verify@test.com'})
        assert login_resp.status_code == 302
        # Re-generate the code from the DB state after login set a new OTP
        user_fresh = User.query.filter_by(email='verify@test.com').first()
        from app.services.otp_service import generate_otp as gen
        # Reset to a known code for the verify step
        known_code = gen(user_fresh)
        resp = stops_client.post('/verify', data={'code': known_code})
        assert resp.status_code == 302  # redirect to home

    def test_verify_with_wrong_code_shows_error(self, stops_client, db):
        """Full flow: POST login, then submit wrong code — stay on verify page."""
        # First log in to establish session
        stops_client.post('/login', data={'email': 'wrong@test.com'})
        # Now submit a wrong code
        resp = stops_client.post('/verify', data={'code': '000000'})
        assert resp.status_code == 200  # stays on verify page


class TestStopsLogout:
    def test_logout_redirects_to_home(self, stops_client):
        resp = stops_client.get('/logout')
        assert resp.status_code == 302
