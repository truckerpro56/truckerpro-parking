from flask import Blueprint

api_bp = Blueprint('api', __name__)

from . import locations, bookings, reviews, stripe_webhook  # noqa: E402, F401
