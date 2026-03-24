from flask import Blueprint

api_bp = Blueprint('api', __name__)

from . import locations, bookings, reviews  # noqa: E402, F401
