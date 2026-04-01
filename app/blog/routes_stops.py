"""Blog routes for stops.truckerpro.net domain.

Routes are dispatched from routes_parking.py via g.site branching.
This module exists for clarity and future stops-specific route additions.
"""
# Routes for /blog and /blog/<slug> are registered in routes_parking.py
# using g.site branching to serve either parking or stops templates.
# Flask does not support two routes with identical URL patterns on the
# same blueprint, so both domains share a single registered URL rule.
