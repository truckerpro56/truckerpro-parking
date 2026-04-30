"""Tests for weekly fuel price digest."""
import uuid
import pytest
from app.models.user import User
from app.models.fuel_price import FuelPrice
from app.models.truck_stop import TruckStop


def _setup_data(db_session):
    """Create a truck stop with a fuel price and a subscribed user."""
    stop = TruckStop(
        brand='loves', brand_display_name="Love's", name="Test Stop Fuel",
        slug='test-stop-fuel-digest-' + uuid.uuid4().hex[:8], store_number='FD1',
        address='123 Test', city='Dallas', state_province='TX',
        postal_code='75201', country='US', latitude=32.78, longitude=-96.80,
        has_diesel=True, data_source='test', is_active=True,
    )
    db_session.session.add(stop)
    db_session.session.commit()

    fp = FuelPrice(
        truck_stop_id=stop.id, fuel_type='diesel',
        price_cents=399, currency='USD', source='driver',
    )
    db_session.session.add(fp)

    user = User(
        email='digest-' + uuid.uuid4().hex[:8] + '@test.com',
        role='driver',
        fuel_email_subscribed=True,
    )
    db_session.session.add(user)
    db_session.session.commit()
    return stop, fp, user


class TestFuelDigestService:
    def test_get_cheapest_diesel(self, app, db):
        stop, fp, user = _setup_data(db)
        from app.services.fuel_digest import get_cheapest_diesel_by_state
        with app.app_context():
            prices = get_cheapest_diesel_by_state(days=7)
            assert 'TX' in prices
            assert prices['TX'][0]['price_cents'] == 399

    def test_get_cheapest_diesel_price_display(self, app, db):
        stop, fp, user = _setup_data(db)
        from app.services.fuel_digest import get_cheapest_diesel_by_state
        with app.app_context():
            prices = get_cheapest_diesel_by_state(days=7)
            assert prices['TX'][0]['price_display'] == '$3.990'

    def test_get_cheapest_diesel_stop_fields(self, app, db):
        stop, fp, user = _setup_data(db)
        from app.services.fuel_digest import get_cheapest_diesel_by_state
        with app.app_context():
            prices = get_cheapest_diesel_by_state(days=7)
            entry = prices['TX'][0]
            assert entry['stop_name'] == 'Test Stop Fuel'
            assert entry['city'] == 'Dallas'
            assert entry['brand'] == "Love's"

    def test_build_digest_html(self, app, db):
        stop, fp, user = _setup_data(db)
        from app.services.fuel_digest import get_cheapest_diesel_by_state, build_digest_html
        with app.app_context():
            prices = get_cheapest_diesel_by_state(days=7)
            html = build_digest_html(prices)
            assert 'Weekly Fuel Report' in html
            assert '$3.990' in html
            assert 'TX' in html

    def test_build_digest_html_unsubscribe_url(self, app, db):
        stop, fp, user = _setup_data(db)
        from app.services.fuel_digest import get_cheapest_diesel_by_state, build_digest_html
        with app.app_context():
            prices = get_cheapest_diesel_by_state(days=7)
            html = build_digest_html(prices, unsubscribe_url='https://stops.truckerpro.net/profile/unsubscribe-fuel?email=test@test.com')
            assert 'unsubscribe-fuel' in html

    def test_build_digest_html_state_header(self, app, db):
        stop, fp, user = _setup_data(db)
        from app.services.fuel_digest import get_cheapest_diesel_by_state, build_digest_html
        with app.app_context():
            prices = get_cheapest_diesel_by_state(days=7)
            html = build_digest_html(prices)
            assert 'Test Stop Fuel' in html
            assert 'Dallas' in html

    def test_user_model_has_fuel_fields(self, app, db):
        user = User(email='fields-' + uuid.uuid4().hex[:8] + '@test.com', role='driver')
        db.session.add(user)
        db.session.commit()
        assert user.fuel_email_subscribed is False
        assert user.fuel_email_states == [] or user.fuel_email_states is None

    def test_fuel_email_states_stored(self, app, db):
        user = User(
            email='states-' + uuid.uuid4().hex[:8] + '@test.com',
            role='driver',
            fuel_email_subscribed=True,
            fuel_email_states=['TX', 'CA'],
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        assert 'TX' in user.fuel_email_states
        assert 'CA' in user.fuel_email_states


class TestSubscription:
    def test_unsubscribe_page_returns_200(self, stops_client, db):
        # With no matching email, still returns 200
        resp = stops_client.get('/profile/unsubscribe-fuel?email=nonexistent@test.com')
        assert resp.status_code == 200

    def test_unsubscribe_page_empty_email_returns_200(self, stops_client, db):
        resp = stops_client.get('/profile/unsubscribe-fuel')
        assert resp.status_code == 200

    def test_unsubscribe_sets_flag_via_signed_token(self, stops_client, db, app):
        """Unsubscribe must come from a signed token (Round-2 #A) — not raw email.
        Round 2 closed the IDOR where any email could be silently unsubscribed."""
        email = 'unsub-' + uuid.uuid4().hex[:8] + '@test.com'
        user = User(email=email, role='driver', fuel_email_subscribed=True)
        db.session.add(user)
        db.session.commit()
        with app.app_context():
            from app.services.fuel_digest import make_unsubscribe_token
            token = make_unsubscribe_token(user.id)
        stops_client.get(f'/profile/unsubscribe-fuel?token={token}')
        db.session.refresh(user)
        assert user.fuel_email_subscribed is False

    def test_unsubscribe_email_param_is_now_a_noop(self, stops_client, db):
        """Regression for Round-2 #A: ?email= must NOT silently unsubscribe."""
        email = 'unsub-' + uuid.uuid4().hex[:8] + '@test.com'
        user = User(email=email, role='driver', fuel_email_subscribed=True)
        db.session.add(user)
        db.session.commit()
        stops_client.get(f'/profile/unsubscribe-fuel?email={email}')
        db.session.refresh(user)
        assert user.fuel_email_subscribed is True

    def test_unsubscribe_unknown_token_does_not_crash(self, stops_client, db):
        resp = stops_client.get('/profile/unsubscribe-fuel?token=garbage')
        assert resp.status_code == 200
