from flask import render_template
from . import pages_bp


@pages_bp.route('/login')
def login():
    return render_template('auth/login.html')


@pages_bp.route('/signup')
def signup():
    return render_template('auth/signup.html')
