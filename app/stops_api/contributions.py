"""Driver contribution endpoints — fuel prices, reviews, reports."""
import logging
from datetime import datetime, timezone, timedelta
from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func

from . import stops_api_bp
from ..extensions import db
from ..middleware import site_required
from ..models.truck_stop import TruckStop
from ..models.fuel_price import FuelPrice
from ..models.truck_stop_review import TruckStopReview
from ..models.truck_stop_report import TruckStopReport

logger = logging.getLogger(__name__)


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
def submit_fuel_price(stop_id):
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json()
    fuel_type = data.get('fuel_type')
    price_cents = data.get('price_cents')
    currency = data.get('currency', 'USD')
    if not fuel_type or not price_cents:
        return jsonify({'error': 'fuel_type and price_cents required'}), 400
    is_verified = _should_auto_verify_price(stop_id, fuel_type, price_cents)
    fp = FuelPrice(
        truck_stop_id=stop_id, fuel_type=fuel_type,
        price_cents=price_cents, currency=currency,
        reported_by=current_user.id, source='driver',
        is_verified=is_verified,
    )
    db.session.add(fp)
    db.session.commit()
    return jsonify({'id': fp.id, 'is_verified': fp.is_verified}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/reviews', methods=['POST'])
@site_required('stops')
@login_required
def submit_review(stop_id):
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json()
    rating = data.get('rating')
    review_text = data.get('review_text', '')
    if not rating or rating < 1 or rating > 5:
        return jsonify({'error': 'rating must be 1-5'}), 400
    existing = TruckStopReview.query.filter_by(
        truck_stop_id=stop_id, user_id=current_user.id
    ).first()
    if existing:
        return jsonify({'error': 'You already reviewed this stop'}), 409
    review = TruckStopReview(
        truck_stop_id=stop_id, user_id=current_user.id,
        rating=rating, review_text=review_text,
        photos=data.get('photos', []),
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({'id': review.id, 'is_approved': review.is_approved}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/reports', methods=['POST'])
@site_required('stops')
@login_required
def submit_report(stop_id):
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json()
    report_type = data.get('report_type')
    report_data = data.get('data')
    if not report_type or not report_data:
        return jsonify({'error': 'report_type and data required'}), 400
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
