from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt
from . import pages_bp
from ..extensions import db, limiter
from ..models.user import User


@pages_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10/minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('pages.landing'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, is_active=True).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('pages.landing'))
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html')


@pages_bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5/minute")
def signup():
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
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
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
        return redirect(url_for('pages.landing'))
    return render_template('auth/signup.html')


@pages_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('pages.landing'))
