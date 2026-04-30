import re
from urllib.parse import urlparse
from flask import render_template, request, redirect, url_for, flash, g
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt
from . import pages_bp
from ..extensions import db, limiter
from ..models.user import User

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _is_safe_next(target):
    """Return True only for same-origin relative paths.

    Blocks protocol-relative (//evil.com), backslash-tricks (/\\evil.com),
    absolute URLs, and anything with a scheme or netloc.
    """
    if not target:
        return False
    if not target.startswith('/'):
        return False
    if len(target) > 1 and target[1] in ('/', '\\'):
        return False
    parsed = urlparse(target)
    return not parsed.scheme and not parsed.netloc


@pages_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10/minute")
def login():
    # Delegate to OTP login flow for stops.truckerpro.net
    if getattr(g, 'site', 'parking') == 'stops':
        from ..stops.auth import stops_login
        return stops_login()
    if current_user.is_authenticated:
        return redirect(url_for('pages.landing'))
    next_page = request.args.get('next', '')
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, is_active=True).first()
        if user and user.password_hash and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            login_user(user)
            if _is_safe_next(next_page):
                return redirect(next_page)
            return redirect(url_for('pages.landing'))
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html', next_page=next_page)


@pages_bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5/minute")
def signup():
    # Delegate to OTP signup flow for stops.truckerpro.net
    if getattr(g, 'site', 'parking') == 'stops':
        from ..stops.auth import stops_signup
        return stops_signup()
    if current_user.is_authenticated:
        return redirect(url_for('pages.landing'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()[:255]
        role = request.form.get('role', 'driver')
        if role not in ('driver', 'owner'):
            role = 'driver'
        if not email or not password or not name:
            flash('All fields are required.', 'error')
            return render_template('auth/signup.html')
        if not _EMAIL_RE.match(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/signup.html')
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/signup.html')
        if len(password) > 72:
            flash('Password must be 72 characters or fewer.', 'error')
            return render_template('auth/signup.html')
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('An account with this email already exists.', 'error')
            return render_template('auth/signup.html')
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(email=email, password_hash=password_hash, name=name, role=role)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('pages.landing', signup=1))
    return render_template('auth/signup.html')


@pages_bp.route('/verify', methods=['GET', 'POST'])
@limiter.limit("10/minute")
def verify():
    # OTP verify flow for stops.truckerpro.net
    if getattr(g, 'site', 'parking') == 'stops':
        from ..stops.auth import stops_verify
        return stops_verify()
    # Parking site has no /verify — redirect to login
    return redirect(url_for('pages.login'))


@pages_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    # Delegate to stops logout for stops.truckerpro.net
    if getattr(g, 'site', 'parking') == 'stops':
        from ..stops.auth import stops_logout
        return stops_logout()
    logout_user()
    return redirect(url_for('pages.landing'))
