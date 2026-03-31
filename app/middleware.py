"""Host-based routing middleware for multi-domain support."""
from functools import wraps
from flask import request, g, abort, current_app


def init_host_routing(app):
    """Register before_request handler that sets g.site based on Host header."""

    @app.before_request
    def set_site_from_host():
        host = request.host.split(':')[0]  # strip port
        stops_domain = current_app.config.get('STOPS_DOMAIN', 'stops.truckerpro.net')
        if host == stops_domain or host == 'stops.localhost' or host == 'stops.truckerpro.net':
            g.site = 'stops'
        else:
            g.site = 'parking'


def site_required(site_name):
    """Decorator that returns 404 if g.site doesn't match."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if getattr(g, 'site', 'parking') != site_name:
                abort(404)
            return f(*args, **kwargs)
        return wrapped
    return decorator
