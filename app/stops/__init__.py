from flask import Blueprint

stops_public_bp = Blueprint('stops', __name__, template_folder='../templates/stops')

from . import routes  # noqa: E402, F401
