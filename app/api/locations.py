"""Parking location API endpoints — search, filter, geo, pagination, detail, create/update."""
import math
import logging

from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, text, case

from . import api_bp
from ..extensions import db
from ..models.location import ParkingLocation
from ..models.review import ParkingReview
from ..services.geo_service import haversine_distance, slugify, geocode_address
from ..constants import PROVINCIAL_TAX

logger = logging.getLogger(__name__)


def _serialize_location(loc, distance_km=None):
    """Serialize a ParkingLocation to a dict for the list endpoint."""
    data = {
        'id': loc.id,
        'name': loc.name,
        'slug': loc.slug,
        'city': loc.city,
        'province': loc.province,
        'latitude': float(loc.latitude) if loc.latitude is not None else None,
        'longitude': float(loc.longitude) if loc.longitude is not None else None,
        'location_type': loc.location_type,
        'total_spots': loc.total_spots,
        'daily_rate': loc.daily_rate,
        'monthly_rate': loc.monthly_rate,
        'amenities': loc.amenities if loc.amenities else [],
        'photos': loc.photos if loc.photos else [],
        'is_bookable': loc.is_bookable,
        'is_verified': loc.is_verified,
        'lcv_capable': loc.lcv_capable,
    }
    if distance_km is not None:
        data['distance_km'] = distance_km
    return data


def _serialize_location_detail(loc):
    """Serialize a ParkingLocation to a full detail dict."""
    return {
        'id': loc.id,
        'name': loc.name,
        'slug': loc.slug,
        'description': loc.description,
        'address': loc.address,
        'city': loc.city,
        'province': loc.province,
        'postal_code': loc.postal_code,
        'latitude': float(loc.latitude) if loc.latitude is not None else None,
        'longitude': float(loc.longitude) if loc.longitude is not None else None,
        'location_type': loc.location_type,
        'total_spots': loc.total_spots,
        'bobtail_spots': loc.bobtail_spots,
        'trailer_spots': loc.trailer_spots,
        'oversize_spots': loc.oversize_spots,
        'lcv_capable': loc.lcv_capable,
        'hourly_rate': loc.hourly_rate,
        'daily_rate': loc.daily_rate,
        'weekly_rate': loc.weekly_rate,
        'monthly_rate': loc.monthly_rate,
        'amenities': loc.amenities if loc.amenities else [],
        'photos': loc.photos if loc.photos else [],
        'contact_phone': loc.contact_phone,
        'contact_email': loc.contact_email,
        'is_bookable': loc.is_bookable,
        'is_verified': loc.is_verified,
        'nearby_highways': loc.nearby_highways if loc.nearby_highways else [],
    }


@api_bp.route('/locations')
def list_locations():
    """List locations with filters, search, geo, and pagination."""
    # Parse query parameters
    province = request.args.get('province', '').strip()
    city = request.args.get('city', '').strip()
    loc_type = request.args.get('type', '').strip()
    amenities_param = request.args.get('amenities', '').strip()
    bookable = request.args.get('bookable', '').strip()
    lcv = request.args.get('lcv', '').strip()
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 50, type=float)
    q = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'newest').strip()
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(100, max(1, request.args.get('per_page', 20, type=int)))

    # Build base query — only active locations
    query = ParkingLocation.query.filter(ParkingLocation.is_active.is_(True))

    # Province filter
    if province:
        query = query.filter(ParkingLocation.province == province.upper())

    # City filter (case-insensitive)
    if city:
        query = query.filter(func.lower(ParkingLocation.city) == city.lower())

    # Location type filter
    if loc_type:
        query = query.filter(ParkingLocation.location_type == loc_type)

    # Bookable filter
    if bookable == '1':
        query = query.filter(ParkingLocation.is_bookable.is_(True))

    # LCV-capable filter
    if lcv == '1':
        query = query.filter(ParkingLocation.lcv_capable.is_(True))

    # Price range filters
    if min_price is not None:
        query = query.filter(ParkingLocation.daily_rate >= min_price)
    if max_price is not None:
        query = query.filter(ParkingLocation.daily_rate <= max_price)

    # Text search
    if q:
        q_pattern = f"%{q.lower()}%"
        query = query.filter(
            db.or_(
                func.lower(ParkingLocation.name).like(q_pattern),
                func.lower(ParkingLocation.city).like(q_pattern),
                func.lower(ParkingLocation.description).like(q_pattern),
            )
        )

    # Amenities filter — each requested amenity must be present in the JSON array
    if amenities_param:
        for amenity in amenities_param.split(','):
            amenity = amenity.strip()
            if amenity:
                # Cast amenities JSON to text and check for the amenity string
                query = query.filter(
                    func.cast(ParkingLocation.amenities, db.String).like(
                        f'%"{amenity}"%'
                    )
                )

    # Geo search with bounding box
    use_geo = lat is not None and lng is not None
    if use_geo:
        lat_range = radius / 111.0
        lng_range = radius / (111.0 * max(math.cos(math.radians(lat)), 0.0001))
        query = query.filter(
            ParkingLocation.latitude.between(lat - lat_range, lat + lat_range),
            ParkingLocation.longitude.between(lng - lng_range, lng + lng_range),
        )

    # Get total count before pagination
    total = query.count()

    # Sorting
    if sort == 'price_asc':
        query = query.order_by(
            case((ParkingLocation.daily_rate.is_(None), 999999), else_=ParkingLocation.daily_rate).asc()
        )
    elif sort == 'price_desc':
        query = query.order_by(
            case((ParkingLocation.daily_rate.is_(None), 0), else_=ParkingLocation.daily_rate).desc()
        )
    elif sort == 'spots':
        query = query.order_by(ParkingLocation.total_spots.desc())
    elif sort == 'distance' and use_geo:
        # Distance sorting handled after fetch via Python
        pass
    else:
        # Default: newest first
        query = query.order_by(ParkingLocation.created_at.desc())

    # For geo+distance sort, fetch all matching then sort in Python
    if use_geo and sort == 'distance':
        all_locs = query.all()
        # Calculate distances and filter by exact radius
        locs_with_dist = []
        for loc in all_locs:
            dist = haversine_distance(lat, lng, float(loc.latitude), float(loc.longitude))
            if dist <= radius:
                locs_with_dist.append((loc, dist))
        locs_with_dist.sort(key=lambda x: x[1])
        total = len(locs_with_dist)
        offset = (page - 1) * per_page
        page_items = locs_with_dist[offset:offset + per_page]
        locations = [_serialize_location(loc, round(dist, 1)) for loc, dist in page_items]
    elif use_geo:
        # Non-distance sort but still geo-filtered: compute distances for output
        all_locs = query.all()
        locs_with_dist = []
        for loc in all_locs:
            dist = haversine_distance(lat, lng, float(loc.latitude), float(loc.longitude))
            if dist <= radius:
                locs_with_dist.append((loc, dist))
        total = len(locs_with_dist)
        offset = (page - 1) * per_page
        page_items = locs_with_dist[offset:offset + per_page]
        locations = [_serialize_location(loc, round(dist, 1)) for loc, dist in page_items]
    else:
        # Standard ORM pagination
        offset = (page - 1) * per_page
        page_locs = query.offset(offset).limit(per_page).all()
        locations = [_serialize_location(loc) for loc in page_locs]

    return jsonify({
        'locations': locations,
        'total': total,
        'page': page,
        'per_page': per_page,
    })


@api_bp.route('/locations/<int:location_id>')
def get_location(location_id):
    """Get single location detail with review summary."""
    loc = ParkingLocation.query.filter_by(
        id=location_id, is_active=True
    ).first()

    if not loc:
        return jsonify({'error': 'Not found'}), 404

    data = _serialize_location_detail(loc)

    # Review summary
    review_stats = db.session.query(
        func.count(ParkingReview.id),
        func.coalesce(func.avg(ParkingReview.rating), 0),
    ).filter(ParkingReview.location_id == location_id).first()

    data['review_count'] = review_stats[0] if review_stats else 0
    data['rating_avg'] = round(float(review_stats[1]), 1) if review_stats else 0.0

    return jsonify(data)


def _ensure_unique_slug(slug, exclude_id=None):
    """Ensure slug is unique by appending a counter if needed."""
    candidate = slug
    counter = 1
    while True:
        query = ParkingLocation.query.filter_by(slug=candidate)
        if exclude_id:
            query = query.filter(ParkingLocation.id != exclude_id)
        if not query.first():
            return candidate
        counter += 1
        candidate = f"{slug}-{counter}"


@api_bp.route('/locations', methods=['POST'])
@login_required
def create_or_update_listing():
    """Create or update a parking location listing."""
    if current_user.role not in ('owner', 'admin'):
        return jsonify({'success': False, 'error': 'Only property owners can create listings'}), 403

    data = request.get_json() or {}
    location_id = data.get('id')

    name = data.get('name', '').strip()[:255]
    address = data.get('address', '').strip()[:500]
    city = data.get('city', '').strip()[:100]
    province = data.get('province', '').strip().upper()[:2]

    if not all([name, address, city, province]):
        return jsonify({'success': False, 'error': 'Name, address, city, and province are required'}), 400

    if province not in PROVINCIAL_TAX:
        return jsonify({'success': False, 'error': 'Invalid province code'}), 400

    slug = slugify(f"{name}-{city}")
    slug = _ensure_unique_slug(slug, exclude_id=location_id)

    # Geocode if lat/lng not provided
    lat = data.get('latitude')
    lng = data.get('longitude')
    if lat is None or lng is None:
        try:
            lat, lng = geocode_address(address, city, province)
        except Exception:
            pass
    if lat is None or lng is None:
        return jsonify({
            'success': False,
            'error': 'Could not determine coordinates. Please provide latitude and longitude.',
        }), 400

    # Validate rates are non-negative
    hourly_rate = data.get('hourly_rate')
    daily_rate = data.get('daily_rate')
    weekly_rate = data.get('weekly_rate')
    monthly_rate = data.get('monthly_rate')
    rate_values = [v for v in [hourly_rate, daily_rate, weekly_rate, monthly_rate] if v is not None]
    try:
        rate_values = [float(v) for v in rate_values]
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Rate values must be numeric'}), 400
    if any(v < 0 for v in rate_values):
        return jsonify({'success': False, 'error': 'Rate values cannot be negative'}), 400

    try:
        if location_id:
            # Update existing — verify ownership
            existing = ParkingLocation.query.filter_by(id=location_id).first()
            if not existing or existing.owner_id != current_user.id:
                return jsonify({'success': False, 'error': 'Not authorized'}), 403

            existing.name = name
            existing.slug = slug
            existing.description = data.get('description', '')[:2000]
            existing.address = address
            existing.city = city
            existing.province = province
            existing.postal_code = data.get('postal_code', '')[:10]
            existing.latitude = lat
            existing.longitude = lng
            existing.location_type = data.get('location_type', 'other')
            existing.total_spots = data.get('total_spots', 0)
            existing.bobtail_spots = data.get('bobtail_spots', 0)
            existing.trailer_spots = data.get('trailer_spots', 0)
            existing.oversize_spots = data.get('oversize_spots', 0)
            existing.lcv_capable = data.get('lcv_capable', False)
            existing.hourly_rate = hourly_rate
            existing.daily_rate = daily_rate
            existing.weekly_rate = weekly_rate
            existing.monthly_rate = monthly_rate
            existing.amenities = data.get('amenities', [])
            existing.photos = data.get('photos', [])
            existing.contact_phone = data.get('contact_phone', '')[:20]
            existing.contact_email = data.get('contact_email', '')[:255]
            existing.access_instructions = data.get('access_instructions', '')[:1000]
            existing.nearby_highways = data.get('nearby_highways', [])
            existing.is_bookable = data.get('is_bookable', False)
            db.session.add(existing)
        else:
            # Create new
            loc = ParkingLocation(
                owner_id=current_user.id,
                name=name,
                slug=slug,
                description=data.get('description', '')[:2000],
                address=address,
                city=city,
                province=province,
                postal_code=data.get('postal_code', '')[:10],
                latitude=lat,
                longitude=lng,
                location_type=data.get('location_type', 'other'),
                total_spots=data.get('total_spots', 0),
                bobtail_spots=data.get('bobtail_spots', 0),
                trailer_spots=data.get('trailer_spots', 0),
                oversize_spots=data.get('oversize_spots', 0),
                lcv_capable=data.get('lcv_capable', False),
                hourly_rate=hourly_rate,
                daily_rate=daily_rate,
                weekly_rate=weekly_rate,
                monthly_rate=monthly_rate,
                amenities=data.get('amenities', []),
                photos=data.get('photos', []),
                contact_phone=data.get('contact_phone', '')[:20],
                contact_email=data.get('contact_email', '')[:255],
                access_instructions=data.get('access_instructions', '')[:1000],
                nearby_highways=data.get('nearby_highways', []),
                is_bookable=data.get('is_bookable', False),
            )
            db.session.add(loc)

        db.session.commit()
        return jsonify({'success': True, 'slug': slug})
    except Exception as e:
        db.session.rollback()
        logger.error("Listing creation/update failed: %s", str(e)[:200], exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to save listing'}), 500
