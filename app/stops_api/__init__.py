from flask import Blueprint

stops_api_bp = Blueprint('stops_api', __name__)

from . import truck_stops, contributions  # noqa: E402, F401
