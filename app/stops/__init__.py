from flask import Blueprint

stops_public_bp = Blueprint('stops', __name__, template_folder='../templates/stops')

from . import routes, auth, profile, rest_areas, weigh_stations, route_planner  # noqa: E402, F401
