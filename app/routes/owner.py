from flask import render_template
from flask_login import login_required
from . import pages_bp


@pages_bp.route('/owner/dashboard')
@login_required
def owner_dashboard():
    return render_template('owner/dashboard.html')
