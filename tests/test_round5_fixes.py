"""Round-5 regression coverage:
- M: Stripe customer race — search by email before creating
- N: ProxyFix wired so flask-limiter sees the real client IP
- O: ParkingReview duplicate-submission returns 409 (not 500)
- P: Route planner caps origin/destination length
"""
from unittest.mock import patch, MagicMock


def test_stripe_get_or_create_customer_searches_by_email_first(app):
    with app.app_context():
        with patch(
            'app.services.payment_service.stripe.Customer.list'
        ) as mock_list, patch(
            'app.services.payment_service.stripe.Customer.create'
        ) as mock_create:
            mock_list.return_value = MagicMock(data=[MagicMock(id='cus_existing')])
            from app.services.payment_service import get_or_create_customer
            cid = get_or_create_customer('a@b.com', 'A B')
            assert cid == 'cus_existing'
            assert not mock_create.called, (
                "Must reuse an existing Stripe customer instead of creating a "
                "duplicate; otherwise concurrent first-bookings spawn two "
                "Stripe customers per user."
            )


def test_stripe_get_or_create_customer_falls_through_to_create_when_no_match(app):
    with app.app_context():
        with patch(
            'app.services.payment_service.stripe.Customer.list'
        ) as mock_list, patch(
            'app.services.payment_service.stripe.Customer.create'
        ) as mock_create:
            mock_list.return_value = MagicMock(data=[])
            mock_create.return_value = MagicMock(id='cus_new')
            from app.services.payment_service import get_or_create_customer
            cid = get_or_create_customer('first@b.com', 'F B')
            assert cid == 'cus_new'
            assert mock_create.called


def test_stripe_get_or_create_customer_swallows_lookup_failure_then_creates(app):
    """If the Stripe list() call fails (network / rate limit), we must still
    fall through to create — better a duplicate than a failed booking."""
    with app.app_context():
        with patch(
            'app.services.payment_service.stripe.Customer.list',
            side_effect=Exception('network'),
        ), patch(
            'app.services.payment_service.stripe.Customer.create'
        ) as mock_create:
            mock_create.return_value = MagicMock(id='cus_fallback')
            from app.services.payment_service import get_or_create_customer
            assert get_or_create_customer('x@y.com', 'X Y') == 'cus_fallback'


def test_proxyfix_is_installed_for_real_app():
    """Without ProxyFix, flask-limiter sees Railway's proxy IP for every
    client and rate-limits everyone as one. The middleware must be in the
    wsgi chain (Flask-SocketIO wraps it on top, so we walk the chain)."""
    from app import create_app
    from app.config import Config
    from werkzeug.middleware.proxy_fix import ProxyFix
    real = create_app(Config)
    middleware = real.wsgi_app
    seen = set()
    while middleware is not None and id(middleware) not in seen:
        seen.add(id(middleware))
        if isinstance(middleware, ProxyFix):
            return
        middleware = getattr(middleware, 'wsgi_app', None) or getattr(middleware, 'app', None)
    raise AssertionError("ProxyFix not found in the wsgi_app chain")


def test_proxyfix_is_NOT_installed_in_tests():
    """The test config skips ProxyFix so test clients work normally."""
    from app import create_app
    from app.config import TestConfig
    test_app = create_app(TestConfig)
    from werkzeug.middleware.proxy_fix import ProxyFix
    assert not isinstance(test_app.wsgi_app, ProxyFix)


def test_parking_review_handler_narrows_integrity_error():
    """Round-5 #O: a duplicate ParkingReview must surface as 409 'Already
    reviewed', not the generic 500 'Failed to submit review' that the old
    bare-except path returned."""
    import inspect
    from app.api import reviews
    src = inspect.getsource(reviews.submit_review)
    assert 'IntegrityError' in src
    assert '409' in src
    assert "'Already reviewed'" in src or 'Already reviewed' in src


def test_route_planner_rejects_oversized_inputs():
    """Round-5 #P: cap origin/destination so a caller can't burn Google
    Maps quota with 10k-character strings under the existing rate limit."""
    import inspect
    from app.stops_api import route_planner
    src = inspect.getsource(route_planner.plan_route_api)
    assert '500' in src  # the cap value
    assert 'len(origin)' in src or 'len(destination)' in src
    assert '500 characters' in src
