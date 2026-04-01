"""Driver profile routes for stops.truckerpro.net."""
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from . import stops_public_bp
from ..extensions import db
from ..middleware import site_required
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
        current_user.contribution_points = (current_user.contribution_points or 0) + 1
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
