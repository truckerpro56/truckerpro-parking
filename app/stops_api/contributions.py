"""Driver contribution endpoints — fuel prices, reviews, reports, photos."""
import logging
from datetime import datetime, timezone, timedelta
from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, update

from . import stops_api_bp
from ..extensions import db, limiter
from ..middleware import site_required
from ..models.user import User
from ..models.truck_stop import TruckStop
from ..models.fuel_price import FuelPrice
from ..models.truck_stop_review import TruckStopReview
from ..models.truck_stop_report import TruckStopReport
from ..models.stop_photo import StopPhoto

logger = logging.getLogger(__name__)

ALLOWED_FUEL_TYPES = ('diesel', 'gas', 'def', 'cng', 'lng', 'biodiesel')
ALLOWED_REPORT_TYPES = ('parking_availability', 'fuel_price_correction', 'amenity_update',
                        'closure', 'hazard', 'hours_change', 'other')
ALLOWED_IMAGE_TYPES = ('image/jpeg', 'image/png', 'image/webp')
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_PHOTOS_PER_USER_PER_STOP = 5


def _should_auto_verify_price(truck_stop_id, fuel_type, price_cents):
    last = FuelPrice.query.filter_by(
        truck_stop_id=truck_stop_id, fuel_type=fuel_type, is_verified=True
    ).order_by(FuelPrice.created_at.desc()).first()
    if not last:
        return False
    threshold = last.price_cents * 0.2
    return abs(price_cents - last.price_cents) <= threshold


@stops_api_bp.route('/truck-stops/<int:stop_id>/fuel-prices', methods=['POST'])
@site_required('stops')
@login_required
@limiter.limit("10/minute")
def submit_fuel_price(stop_id):
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json() or {}
    fuel_type = data.get('fuel_type')
    price_cents = data.get('price_cents')
    currency = data.get('currency', 'USD')
    if not fuel_type or price_cents is None:
        return jsonify({'error': 'fuel_type and price_cents required'}), 400
    if fuel_type not in ALLOWED_FUEL_TYPES:
        return jsonify({'error': f'fuel_type must be one of: {", ".join(ALLOWED_FUEL_TYPES)}'}), 400
    try:
        price_cents = int(price_cents)
    except (ValueError, TypeError):
        return jsonify({'error': 'price_cents must be a number'}), 400
    if price_cents < 1 or price_cents > 99999:
        return jsonify({'error': 'price_cents must be between 1 and 99999'}), 400
    is_verified = _should_auto_verify_price(stop_id, fuel_type, price_cents)
    fp = FuelPrice(
        truck_stop_id=stop_id, fuel_type=fuel_type,
        price_cents=price_cents, currency=currency,
        reported_by=current_user.id, source='driver',
        is_verified=is_verified,
    )
    db.session.add(fp)
    db.session.commit()
    # Award points for fuel price contribution (atomic to prevent race conditions)
    db.session.execute(
        update(User).where(User.id == current_user.id).values(
            contribution_points=db.func.coalesce(User.contribution_points, 0) + 5
        )
    )
    db.session.commit()
    return jsonify({'id': fp.id, 'is_verified': fp.is_verified}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/reviews', methods=['POST'])
@site_required('stops')
@login_required
@limiter.limit("5/minute")
def submit_review(stop_id):
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json() or {}
    rating = data.get('rating')
    review_text = data.get('review_text', '')
    try:
        rating = int(rating)
    except (ValueError, TypeError):
        return jsonify({'error': 'rating must be a number'}), 400
    if rating < 1 or rating > 5:
        return jsonify({'error': 'rating must be 1-5'}), 400
    review_text = str(review_text)[:2000]
    existing = TruckStopReview.query.filter_by(
        truck_stop_id=stop_id, user_id=current_user.id
    ).first()
    if existing:
        return jsonify({'error': 'You already reviewed this stop'}), 409
    photos = data.get('photos', [])
    if not isinstance(photos, list):
        photos = []
    photos = [str(p)[:500] for p in photos[:20] if isinstance(p, str) and p.startswith('http')]
    review = TruckStopReview(
        truck_stop_id=stop_id, user_id=current_user.id,
        rating=rating, review_text=review_text,
        photos=photos,
    )
    db.session.add(review)
    db.session.commit()
    # Award points for review contribution (atomic to prevent race conditions)
    db.session.execute(
        update(User).where(User.id == current_user.id).values(
            contribution_points=db.func.coalesce(User.contribution_points, 0) + 10
        )
    )
    db.session.commit()
    return jsonify({'id': review.id, 'is_approved': review.is_approved}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/reports', methods=['POST'])
@site_required('stops')
@login_required
@limiter.limit("10/minute")
def submit_report(stop_id):
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json() or {}
    report_type = data.get('report_type')
    report_data = data.get('data')
    if not report_type or not report_data:
        return jsonify({'error': 'report_type and data required'}), 400
    if report_type not in ALLOWED_REPORT_TYPES:
        return jsonify({'error': f'report_type must be one of: {", ".join(ALLOWED_REPORT_TYPES)}'}), 400
    expires_at = None
    if report_type == 'parking_availability':
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
    report = TruckStopReport(
        truck_stop_id=stop_id, user_id=current_user.id,
        report_type=report_type, data=report_data,
        expires_at=expires_at,
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({'id': report.id}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/photos', methods=['POST'])
@site_required('stops')
@login_required
@limiter.limit("10/minute")
def upload_photo(stop_id):
    """Upload a photo for a truck stop."""
    stop = TruckStop.query.get_or_404(stop_id)

    if 'photo' not in request.files:
        return jsonify({'error': 'No photo file provided'}), 400

    file = request.files['photo']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        return jsonify({'error': 'Only JPEG, PNG, and WebP images allowed'}), 400

    chunks = []
    total_size = 0
    while True:
        chunk = file.read(8192)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_IMAGE_SIZE:
            return jsonify({'error': 'Image must be under 2MB'}), 400
        chunks.append(chunk)
    image_data = b''.join(chunks)

    # Check per-user limit
    existing_count = StopPhoto.query.filter_by(
        truck_stop_id=stop_id, user_id=current_user.id
    ).count()
    if existing_count >= MAX_PHOTOS_PER_USER_PER_STOP:
        return jsonify({'error': f'Maximum {MAX_PHOTOS_PER_USER_PER_STOP} photos per stop'}), 400

    caption = request.form.get('caption', '').strip()[:200]

    photo = StopPhoto(
        truck_stop_id=stop_id,
        user_id=current_user.id,
        filename=file.filename[:255],
        content_type=file.content_type,
        image_data=image_data,
        caption=caption,
    )
    db.session.add(photo)

    # Award points (atomic to prevent race conditions)
    db.session.execute(
        update(User).where(User.id == current_user.id).values(
            contribution_points=db.func.coalesce(User.contribution_points, 0) + 15
        )
    )
    db.session.commit()

    return jsonify({'id': photo.id, 'points_awarded': 15}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/photos', methods=['GET'])
@site_required('stops')
def get_stop_photos(stop_id):
    """Get list of photo metadata for a truck stop (not the image data)."""
    photos = StopPhoto.query.filter_by(
        truck_stop_id=stop_id, is_approved=True
    ).order_by(StopPhoto.created_at.desc()).all()
    return jsonify([{
        'id': p.id,
        'caption': p.caption,
        'user_id': p.user_id,
        'created_at': p.created_at.isoformat() if p.created_at else None,
    } for p in photos])
