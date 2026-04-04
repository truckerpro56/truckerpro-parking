from flask import Blueprint

stops_api_bp = Blueprint('stops_api', __name__)

from . import truck_stops, contributions, admin, route_planner, weigh_station_contributions  # noqa: E402, F401
