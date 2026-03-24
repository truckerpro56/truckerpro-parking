from flask import Blueprint

pages_bp = Blueprint('pages', __name__)

from . import public, auth, owner  # noqa: E402, F401
