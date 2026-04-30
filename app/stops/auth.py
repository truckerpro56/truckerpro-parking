"""OTP authentication view functions for stops.truckerpro.net.

These are NOT registered as blueprint routes directly — the parking pages_bp
routes (/login, /verify, /logout) delegate to these functions when g.site == 'stops'.
This avoids Flask URL conflicts between the two blueprints.
"""
import re
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user

from ..extensions import db
from ..models.user import User
from ..services.otp_service import generate_otp, verify_otp
from ..services.otp_email import send_otp_email

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def stops_login():
    """OTP login for stops.truckerpro.net. Called by pages.login when g.site == 'stops'.

    Sign-in only — does NOT create a new account from a login attempt. Account
    creation goes through /signup. To prevent enumeration, the response is
    identical regardless of whether the email is registered.
    """
    if current_user.is_authenticated:
        return redirect('/')
    next_url = request.args.get('next', '')
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email or not _EMAIL_RE.match(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('stops/auth/login.html', next_url=next_url)

        user = User.query.filter_by(email=email).first()
        # Only emit an OTP for known accounts. We always return the same UX
        # (redirect to /verify with a generic flash) so a caller cannot
        # enumerate registered emails.
        if user is not None:
            code = generate_otp(user)
            send_otp_email(email, code)
        session['otp_email'] = email
        session['otp_next'] = next_url
        flash('If an account exists for that email, a 6-digit login code is on its way.', 'info')
        return redirect('/verify')
    return render_template('stops/auth/login.html', next_url=next_url)


def stops_signup():
    """Explicit account creation for stops.truckerpro.net.

    Splits user creation off the login form so a typo on /login no longer
    silently spawns a User row.
    """
    if current_user.is_authenticated:
        return redirect('/')
    next_url = request.args.get('next', '')
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email or not _EMAIL_RE.match(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('stops/auth/signup.html', next_url=next_url)
        existing = User.query.filter_by(email=email).first()
        if existing is None:
            user = User(email=email, role='driver')
            db.session.add(user)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                user = User.query.filter_by(email=email).first()
        else:
            user = existing
        if user is not None:
            code = generate_otp(user)
            send_otp_email(email, code)
        session['otp_email'] = email
        session['otp_next'] = next_url
        flash('Check your email for a 6-digit code to finish signing up.', 'info')
        return redirect('/verify')
    return render_template('stops/auth/signup.html', next_url=next_url)


def stops_verify():
    """OTP verify for stops.truckerpro.net. Called by pages.verify when g.site == 'stops'."""
    email = session.get('otp_email')
    if not email:
        return redirect('/login')
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if not code or len(code) != 6:
            flash('Please enter the 6-digit code.', 'error')
            return render_template('stops/auth/verify.html', email=email)
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Something went wrong. Please try again.', 'error')
            return redirect('/login')
        if verify_otp(user, code):
            login_user(user, remember=True)
            session.pop('otp_email', None)
            next_url = session.pop('otp_next', '') or '/'
            # Reuse the parking-side same-origin check; the inline test we used
            # to do (startswith('/') and not '//') let `/\\evil.com` through —
            # browsers normalize backslashes to forward slashes, turning that
            # into //evil.com and a working open-redirect.
            from ..routes.auth import _is_safe_next
            if _is_safe_next(next_url):
                return redirect(next_url)
            return redirect('/')
        flash('Invalid or expired code. Please try again.', 'error')
        return render_template('stops/auth/verify.html', email=email)
    return render_template('stops/auth/verify.html', email=email)


def stops_logout():
    """OTP logout for stops.truckerpro.net. Called by pages.logout when g.site == 'stops'."""
    logout_user()
    return redirect('/')
