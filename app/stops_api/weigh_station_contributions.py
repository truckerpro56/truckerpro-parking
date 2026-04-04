"""Weigh station driver contributions — reviews and live status updates."""
import logging
from datetime import datetime, timezone, timedelta
from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import update

from . import stops_api_bp
from ..extensions import db, limiter
from ..middleware import site_required
from ..models.user import User
from ..models.weigh_station import WeighStation
from ..models.weigh_station_review import WeighStationReview
from ..models.weigh_station_status import WeighStationStatus
from ..services.content_filter import clean_text

logger = logging.getLogger(__name__)


@stops_api_bp.route('/weigh-stations/<int:ws_id>/reviews', methods=['POST'])
@site_required('stops')
@login_required
@limiter.limit("5/minute")
def submit_ws_review(ws_id):
    """Submit a review for a weigh station."""
    ws = WeighStation.query.get_or_404(ws_id)
    data = request.get_json() or {}

    rating = data.get('rating')
    try:
        rating = int(rating)
    except (ValueError, TypeError):
        return jsonify({'error': 'Rating must be a number'}), 400
    if rating < 1 or rating > 5:
        return jsonify({'error': 'Rating must be 1-5'}), 400

    review_text, is_clean, bad_word = clean_text(data.get('review_text', ''), max_length=2000)
    if not is_clean:
        return jsonify({'error': 'Review contains inappropriate language. Please revise and resubmit.'}), 400

    existing = WeighStationReview.query.filter_by(
        weigh_station_id=ws_id, user_id=current_user.id
    ).first()
    if existing:
        return jsonify({'error': 'You already reviewed this station'}), 409

    review = WeighStationReview(
        weigh_station_id=ws_id, user_id=current_user.id,
        rating=rating, review_text=review_text,
    )
    db.session.add(review)
    db.session.commit()

    # Award contribution points
    db.session.execute(
        update(User).where(User.id == current_user.id).values(
            contribution_points=db.func.coalesce(User.contribution_points, 0) + 10
        )
    )
    db.session.commit()
    return jsonify({'id': review.id, 'points_awarded': 10}), 201


@stops_api_bp.route('/weigh-stations/<int:ws_id>/reviews', methods=['GET'])
@site_required('stops')
def get_ws_reviews(ws_id):
    """Get reviews for a weigh station."""
    reviews = WeighStationReview.query.filter_by(
        weigh_station_id=ws_id, is_approved=True
    ).order_by(WeighStationReview.created_at.desc()).limit(50).all()
    return jsonify([{
        'id': r.id,
        'rating': r.rating,
        'review_text': r.review_text,
        'user_name': (r.user.display_name or r.user.name or 'Driver') if r.user else 'Driver',
        'created_at': r.created_at.isoformat() if r.created_at else None,
    } for r in reviews])


@stops_api_bp.route('/weigh-stations/<int:ws_id>/status', methods=['POST'])
@site_required('stops')
@login_required
@limiter.limit("10/minute")
def submit_ws_status(ws_id):
    """Submit a live status update for a weigh station."""
    ws = WeighStation.query.get_or_404(ws_id)
    data = request.get_json() or {}

    status = (data.get('status') or '').strip().lower()
    if status not in WeighStationStatus.VALID_STATUSES:
        return jsonify({'error': f'Status must be one of: {", ".join(WeighStationStatus.VALID_STATUSES)}'}), 400

    wait_minutes = data.get('wait_minutes')
    if wait_minutes is not None:
        try:
            wait_minutes = max(0, min(int(wait_minutes), 999))
        except (ValueError, TypeError):
            wait_minutes = None

    note = ''
    if data.get('note'):
        note, is_clean, bad_word = clean_text(data.get('note', ''), max_length=500)
        if not is_clean:
            return jsonify({'error': 'Note contains inappropriate language. Please revise.'}), 400

    # Rate limit: one status per user per station per hour
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    recent = WeighStationStatus.query.filter(
        WeighStationStatus.weigh_station_id == ws_id,
        WeighStationStatus.user_id == current_user.id,
        WeighStationStatus.created_at >= one_hour_ago,
    ).first()
    if recent:
        return jsonify({'error': 'You can only update status once per hour for this station'}), 429

    ws_status = WeighStationStatus(
        weigh_station_id=ws_id, user_id=current_user.id,
        status=status, wait_minutes=wait_minutes,
        note=note or None,
    )
    db.session.add(ws_status)
    db.session.commit()

    # Award contribution points
    db.session.execute(
        update(User).where(User.id == current_user.id).values(
            contribution_points=db.func.coalesce(User.contribution_points, 0) + 5
        )
    )
    db.session.commit()
    return jsonify({'id': ws_status.id, 'points_awarded': 5}), 201


@stops_api_bp.route('/weigh-stations/<int:ws_id>/status', methods=['GET'])
@site_required('stops')
def get_ws_status(ws_id):
    """Get recent status updates for a weigh station (last 7 days)."""
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    statuses = WeighStationStatus.query.filter(
        WeighStationStatus.weigh_station_id == ws_id,
        WeighStationStatus.created_at >= seven_days_ago,
    ).order_by(WeighStationStatus.created_at.desc()).limit(20).all()
    return jsonify([{
        'id': s.id,
        'status': s.status,
        'status_label': WeighStationStatus.STATUS_LABELS.get(s.status, s.status),
        'wait_minutes': s.wait_minutes,
        'note': s.note,
        'user_name': s.user.display_name or s.user.name or 'Driver' if s.user else 'Driver',
        'created_at': s.created_at.isoformat() if s.created_at else None,
    } for s in statuses])
