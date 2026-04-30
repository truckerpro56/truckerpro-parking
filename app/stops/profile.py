"""Driver profile routes for stops.truckerpro.net."""
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import update

from . import stops_public_bp
from ..extensions import db
from ..middleware import site_required
from ..models.user import User
from ..models.favorite_stop import FavoriteStop
from ..models.truck_stop import TruckStop
from ..models.fuel_price import FuelPrice
from ..models.truck_stop_review import TruckStopReview
from ..models.stop_photo import StopPhoto
from .helpers import stop_to_card


@stops_public_bp.route('/profile')
@site_required('stops')
@login_required
def driver_profile():
    """Driver's profile dashboard — favorites, contributions, settings."""
    favorites = FavoriteStop.query.filter_by(user_id=current_user.id).order_by(
        FavoriteStop.created_at.desc()
    ).all()
    fav_stops = []
    for fav in favorites:
        stop = TruckStop.query.get(fav.truck_stop_id)
        if stop and stop.is_active:
            fav_stops.append(stop_to_card(stop))

    # Contribution stats
    price_count = FuelPrice.query.filter_by(reported_by=current_user.id).count()
    review_count = TruckStopReview.query.filter_by(user_id=current_user.id).count()
    photo_count = StopPhoto.query.filter_by(user_id=current_user.id).count()

    return render_template('stops/profile.html',
                           favorites=fav_stops,
                           price_count=price_count,
                           review_count=review_count,
                           photo_count=photo_count)


@stops_public_bp.route('/profile/settings', methods=['POST'])
@site_required('stops')
@login_required
def update_profile():
    """Update driver profile settings."""
    current_user.display_name = request.form.get('display_name', '').strip()[:100]
    current_user.home_state = request.form.get('home_state', '').strip()[:50]
    current_user.truck_type = request.form.get('truck_type', '').strip()[:50]
    db.session.commit()
    flash('Profile updated.', 'success')
    return redirect(url_for('stops.driver_profile'))


@stops_public_bp.route('/favorites/add/<int:stop_id>', methods=['POST'])
@site_required('stops')
@login_required
def add_favorite(stop_id):
    """Add a truck stop to favorites."""
    stop = TruckStop.query.get_or_404(stop_id)
    existing = FavoriteStop.query.filter_by(
        user_id=current_user.id, truck_stop_id=stop_id
    ).first()
    if not existing:
        fav = FavoriteStop(user_id=current_user.id, truck_stop_id=stop_id)
        db.session.add(fav)
        # Atomic increment to prevent race conditions
        db.session.execute(
            update(User).where(User.id == current_user.id).values(
                contribution_points=db.func.coalesce(User.contribution_points, 0) + 1
            )
        )
        db.session.commit()
    return jsonify({'success': True, 'favorited': True})


@stops_public_bp.route('/favorites/remove/<int:stop_id>', methods=['POST'])
@site_required('stops')
@login_required
def remove_favorite(stop_id):
    """Remove a truck stop from favorites."""
    fav = FavoriteStop.query.filter_by(
        user_id=current_user.id, truck_stop_id=stop_id
    ).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
    return jsonify({'success': True, 'favorited': False})


@stops_public_bp.route('/profile/subscribe-fuel', methods=['POST'])
@site_required('stops')
@login_required
def subscribe_fuel_email():
    """Subscribe (or unsubscribe) from weekly fuel price digest."""
    if 'unsubscribe' in request.form:
        current_user.fuel_email_subscribed = False
        db.session.commit()
        flash('Unsubscribed from weekly fuel price emails.', 'success')
    else:
        current_user.fuel_email_subscribed = True
        # Optionally set preferred states from form
        states = request.form.getlist('states')
        if states:
            current_user.fuel_email_states = [s.strip().upper() for s in states if s.strip()]
        db.session.commit()
        flash('Subscribed to weekly fuel price emails!', 'success')
    return redirect(url_for('stops.driver_profile'))


@stops_public_bp.route('/profile/unsubscribe-fuel')
@site_required('stops')
def unsubscribe_fuel_email():
    """Unsubscribe from the fuel price digest.

    Three accepted paths, in order of preference:
      1. Signed `?token=` issued in the digest email (preferred — stateless,
         survives logout, can't enumerate emails).
      2. Authenticated user with no token — unsubscribe self.
      3. Anything else: render the page but make no DB changes (anti-IDOR).

    Notably absent: `?email=`. Accepting raw email lets anyone unsubscribe
    anyone, which was the original bug.
    """
    from ..services.fuel_digest import parse_unsubscribe_token
    token = request.args.get('token', '').strip()
    target_user = None
    if token:
        uid = parse_unsubscribe_token(token)
        if uid is not None:
            target_user = User.query.get(uid)
    elif current_user.is_authenticated:
        target_user = current_user
    if target_user is not None and target_user.fuel_email_subscribed:
        target_user.fuel_email_subscribed = False
        db.session.commit()
    return render_template('stops/unsubscribed.html')
