"""Route planner page route for stops.truckerpro.net."""
from flask import render_template, current_app

from . import stops_public_bp
from ..middleware import site_required


@stops_public_bp.route('/route-planner')
@site_required('stops')
def route_planner():
    """Route planner page — plan a trip and find stops along the way."""
    google_maps_key = current_app.config.get('GOOGLE_MAPS_API_KEY', '')
    return render_template('stops/route_planner.html', google_maps_key=google_maps_key)
