"""Tests for the map_pins single-flight rebuild lock.

Regression coverage for Round-3 #D: the previous implementation released
the lock in `finally` regardless of whether the worker had acquired it,
and silently set got_lock=True on a Redis exception, both of which broke
single-flight protection.
"""
from unittest.mock import MagicMock, patch


def test_release_script_only_deletes_when_token_matches(app):
    """The release Lua script must compare the stored value to the token
    before deleting; without that, any worker can blow away the active lock."""
    from app.stops_api.map_pins import _RELEASE_LOCK_LUA, LOCK_KEY
    # Pure string check — the Lua source must do a GET/compare/DEL pattern.
    assert "redis.call('GET'" in _RELEASE_LOCK_LUA
    assert 'ARGV[1]' in _RELEASE_LOCK_LUA
    assert "redis.call('DEL'" in _RELEASE_LOCK_LUA
    # Returns 0 (no-op) when the token doesn't match
    assert 'return 0' in _RELEASE_LOCK_LUA


def test_lock_acquisition_failure_does_not_pretend_to_hold_it(app):
    """When Redis raises during SET NX, the route must NOT mark itself as
    the lock holder (the prior code wrote got_lock=True on exception)."""
    fake_r = MagicMock()
    fake_r.get.return_value = None  # cache miss
    fake_r.set.side_effect = Exception('redis down')
    fake_r.setex.return_value = True

    with app.test_request_context('/api/v1/map-pins',
                                  headers={'Host': 'stops.localhost'}):
        from flask import g
        g.site = 'stops'
        with patch('app.stops_api.map_pins._get_redis', return_value=fake_r), \
             patch('app.stops_api.map_pins._build_pins_json', return_value={'truck_stops': []}):
            from app.stops_api.map_pins import map_pins
            resp = map_pins()
            assert resp.status_code == 200
    # The release path should NOT delete the lock (we never held it).
    # With the bug, eval() would have been called; with the fix, it isn't.
    fake_r.eval.assert_not_called()


def test_lock_acquired_uses_token_on_release(app):
    """When we DO acquire the lock, release goes through the Lua script
    with the same token we set. This proves we're not racing TTL expiry."""
    fake_r = MagicMock()
    fake_r.get.return_value = None  # cache miss
    fake_r.set.return_value = True   # lock acquired
    fake_r.setex.return_value = True
    fake_r.eval.return_value = 1

    with app.test_request_context('/api/v1/map-pins',
                                  headers={'Host': 'stops.localhost'}):
        from flask import g
        g.site = 'stops'
        with patch('app.stops_api.map_pins._get_redis', return_value=fake_r), \
             patch('app.stops_api.map_pins._build_pins_json', return_value={'truck_stops': []}):
            from app.stops_api.map_pins import map_pins
            map_pins()

    # eval() called with our Lua script + the token we stored
    assert fake_r.eval.called
    args = fake_r.eval.call_args
    set_token = fake_r.set.call_args.args[1]  # second positional arg to SET
    eval_token = args.args[3]                 # ARGV[1]
    assert set_token == eval_token, "release token must match acquisition token"


def test_no_redis_means_direct_rebuild_no_lock_calls(app):
    """If Redis isn't available at all, the route falls through to direct
    rebuild without trying to acquire or release a lock."""
    with app.test_request_context('/api/v1/map-pins',
                                  headers={'Host': 'stops.localhost'}):
        from flask import g
        g.site = 'stops'
        with patch('app.stops_api.map_pins._get_redis', return_value=None), \
             patch('app.stops_api.map_pins._build_pins_json', return_value={'truck_stops': []}):
            from app.stops_api.map_pins import map_pins
            resp = map_pins()
            assert resp.status_code == 200
