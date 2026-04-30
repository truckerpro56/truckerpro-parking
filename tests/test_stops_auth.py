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

    def test_login_does_not_create_user(self, stops_client, db):
        """Regression: a login attempt must NOT auto-register an account.

        Account creation goes through /signup. /login for an unknown email
        returns the same generic UX (no enumeration) but creates no User row.
        """
        stops_client.post('/login', data={'email': 'newdriver@test.com'})
        user = User.query.filter_by(email='newdriver@test.com').first()
        assert user is None

    def test_login_existing_user_generates_otp(self, stops_client, db):
        existing = User(email='existing@test.com', role='driver')
        db.session.add(existing)
        db.session.commit()
        stops_client.post('/login', data={'email': 'existing@test.com'})
        user_after = User.query.filter_by(email='existing@test.com').first()
        assert user_after is not None
        assert user_after.otp_code is not None

    def test_login_unknown_email_returns_same_generic_response(self, stops_client, db):
        """Anti-enumeration: unknown vs known emails must both redirect to /verify."""
        existing = User(email='known@test.com', role='driver')
        db.session.add(existing)
        db.session.commit()
        unknown_resp = stops_client.post('/login', data={'email': 'unknown@test.com'})
        known_resp = stops_client.post('/login', data={'email': 'known@test.com'})
        assert unknown_resp.status_code == known_resp.status_code == 302
        assert '/verify' in unknown_resp.headers.get('Location', '')
        assert '/verify' in known_resp.headers.get('Location', '')

    def test_signup_creates_user_with_otp(self, stops_client, db):
        stops_client.post('/signup', data={'email': 'signup@test.com'})
        user = User.query.filter_by(email='signup@test.com').first()
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
        """Full flow: POST login for an EXISTING user, then submit wrong code.

        Pre-creates the user — Round-2 #6 stopped /login from auto-registering
        unknown emails (anti-enumeration), so a wrong-code test must seed the
        account itself rather than relying on /login to create it.
        """
        existing = User(email='wrong@test.com', role='driver')
        db.session.add(existing)
        db.session.commit()
        stops_client.post('/login', data={'email': 'wrong@test.com'})
        resp = stops_client.post('/verify', data={'code': '000000'})
        assert resp.status_code == 200  # stays on verify page


class TestStopsLogout:
    def test_logout_redirects_to_home(self, stops_client):
        resp = stops_client.get('/logout')
        assert resp.status_code == 302
