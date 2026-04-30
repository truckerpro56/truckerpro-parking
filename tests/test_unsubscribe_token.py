"""Tests for the fuel-digest unsubscribe flow.

Regression coverage for Round-2 #A: anyone-can-unsubscribe-anyone IDOR.
The endpoint must require either a signed token tied to a specific user_id,
or an authenticated session — never a raw `?email=` parameter.
"""
from app.models.user import User


def test_make_and_parse_unsubscribe_token_round_trip(app, db):
    user = User(email='digest@test.com', role='driver', fuel_email_subscribed=True)
    db.session.add(user)
    db.session.commit()
    with app.app_context():
        from app.services.fuel_digest import make_unsubscribe_token, parse_unsubscribe_token
        token = make_unsubscribe_token(user.id)
        assert isinstance(token, str) and len(token) > 10
        parsed_uid = parse_unsubscribe_token(token)
        assert parsed_uid == user.id


def test_parse_unsubscribe_token_rejects_garbage(app, db):
    with app.app_context():
        from app.services.fuel_digest import parse_unsubscribe_token
        assert parse_unsubscribe_token('') is None
        assert parse_unsubscribe_token('not-a-token') is None
        assert parse_unsubscribe_token('a.b.c.d') is None


def test_parse_unsubscribe_token_rejects_wrong_salt(app, db):
    """A token signed with the wrong salt (e.g., from another flow) must not validate."""
    from itsdangerous import URLSafeTimedSerializer
    with app.app_context():
        wrong = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='other-salt')
        token = wrong.dumps({'uid': 42})
        from app.services.fuel_digest import parse_unsubscribe_token
        assert parse_unsubscribe_token(token) is None


def test_unsubscribe_endpoint_does_not_accept_email_param():
    """Regression check: source must NOT read ?email= from the request.

    Original bug let any caller unsubscribe any email. The replacement uses
    a signed `?token=` only — confirm the route source no longer reads
    request.args['email']."""
    import inspect
    from app.stops import profile
    src = inspect.getsource(profile.unsubscribe_fuel_email)
    assert "request.args.get('email'" not in src
    assert "request.args.get('token'" in src
    assert 'parse_unsubscribe_token' in src
