"""Truck stop API endpoints — list, detail, search."""
import logging
from flask import jsonify, request
from sqlalchemy import func

from . import stops_api_bp
from ..extensions import db
from ..middleware import site_required
from ..models.truck_stop import TruckStop
from ..models.fuel_price import FuelPrice
from ..models.truck_stop_review import TruckStopReview
from ..services.geo_service import haversine_distance
from ..services.banner_service import get_banners

logger = logging.getLogger(__name__)


def _serialize_stop(stop, distance_km=None):
    data = {
        'id': stop.id,
        'brand': stop.brand,
        'brand_display_name': stop.brand_display_name,
        'name': stop.name,
        'slug': stop.slug,
        'city': stop.city,
        'state_province': stop.state_province,
        'country': stop.country,
        'latitude': stop.latitude,
        'longitude': stop.longitude,
        'highway': stop.highway,
        'exit_number': stop.exit_number,
        'total_parking_spots': stop.total_parking_spots,
        'has_diesel': stop.has_diesel,
        'has_showers': stop.has_showers,
        'has_scale': stop.has_scale,
        'has_repair': stop.has_repair,
    }
    if distance_km is not None:
        data['distance_km'] = distance_km
    return data


def _serialize_stop_detail(stop):
    latest_prices = db.session.query(FuelPrice).filter_by(
        truck_stop_id=stop.id, is_verified=True
    ).order_by(FuelPrice.created_at.desc()).limit(4).all()

    review_stats = db.session.query(
        func.count(TruckStopReview.id),
        func.avg(TruckStopReview.rating),
    ).filter_by(truck_stop_id=stop.id, is_approved=True).first()

    return {
        'id': stop.id,
        'brand': stop.brand,
        'brand_display_name': stop.brand_display_name,
        'name': stop.name,
        'slug': stop.slug,
        'store_number': stop.store_number,
        'address': stop.address,
        'city': stop.city,
        'state_province': stop.state_province,
        'postal_code': stop.postal_code,
        'country': stop.country,
        'latitude': stop.latitude,
        'longitude': stop.longitude,
        'highway': stop.highway,
        'exit_number': stop.exit_number,
        'direction': stop.direction,
        'total_parking_spots': stop.total_parking_spots,
        'truck_spots': stop.truck_spots,
        'car_spots': stop.car_spots,
        'has_diesel': stop.has_diesel,
        'has_gas': stop.has_gas,
        'has_def': stop.has_def,
        'has_ev_charging': stop.has_ev_charging,
        'has_showers': stop.has_showers,
        'shower_count': stop.shower_count,
        'has_scale': stop.has_scale,
        'scale_type': stop.scale_type,
        'has_repair': stop.has_repair,
        'has_tire_service': stop.has_tire_service,
        'has_wifi': stop.has_wifi,
        'has_laundry': stop.has_laundry,
        'restaurants': stop.restaurants or [],
        'loyalty_programs': stop.loyalty_programs or [],
        'hours_of_operation': stop.hours_of_operation or {},
        'phone': stop.phone,
        'website': stop.website,
        'photos': stop.photos or [],
        'nearest_border_crossing': stop.nearest_border_crossing,
        'border_distance_km': stop.border_distance_km,
        'meta_title': stop.meta_title,
        'meta_description': stop.meta_description,
        'fuel_prices': [
            {'fuel_type': fp.fuel_type, 'price_cents': fp.price_cents,
             'currency': fp.currency, 'created_at': fp.created_at.isoformat()}
            for fp in latest_prices
        ],
        'review_count': review_stats[0] if review_stats else 0,
        'avg_rating': round(float(review_stats[1]), 1) if review_stats and review_stats[1] else None,
        'banners': get_banners(stop),
    }


@stops_api_bp.route('/truck-stops')
@site_required('stops')
def list_truck_stops():
    """List truck stops with filters, geo search, pagination."""
    query = TruckStop.query.filter_by(is_active=True)

    state = request.args.get('state')
    if state:
        query = query.filter(func.upper(TruckStop.state_province) == state.upper())

    city = request.args.get('city')
    if city:
        query = query.filter(func.lower(TruckStop.city) == city.lower())

    brand = request.args.get('brand')
    if brand:
        query = query.filter_by(brand=brand)

    country = request.args.get('country')
    if country:
        query = query.filter(func.upper(TruckStop.country) == country.upper())

    highway = request.args.get('highway')
    if highway:
        query = query.filter(func.upper(TruckStop.highway) == highway.upper())

    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', type=float, default=50)

    distances = {}
    if lat is not None and lng is not None:
        delta_lat = radius / 111.0
        delta_lng = radius / (111.0 * abs(float(lat)) * 0.01745 + 0.001)
        query = query.filter(
            TruckStop.latitude.between(lat - delta_lat, lat + delta_lat),
            TruckStop.longitude.between(lng - delta_lng, lng + delta_lng),
        )
        stops = query.all()
        filtered = []
        for s in stops:
            d = haversine_distance(lat, lng, s.latitude, s.longitude)
            if d <= radius:
                distances[s.id] = d
                filtered.append(s)
        filtered.sort(key=lambda s: distances[s.id])
        total = len(filtered)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)
        start = (page - 1) * per_page
        page_stops = filtered[start:start + per_page]
        return jsonify({
            'total': total, 'page': page, 'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'stops': [_serialize_stop(s, distances.get(s.id)) for s in page_stops],
        })

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)
    total = query.count()
    stops = query.order_by(TruckStop.name).offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
        'stops': [_serialize_stop(s) for s in stops],
    })


@stops_api_bp.route('/truck-stops/<int:stop_id>')
@site_required('stops')
def get_truck_stop(stop_id):
    stop = TruckStop.query.filter_by(id=stop_id, is_active=True).first()
    if not stop:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(_serialize_stop_detail(stop))
