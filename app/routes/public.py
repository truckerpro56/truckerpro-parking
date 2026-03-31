"""Public page routes — landing, search, province, city, location detail, bookings."""
import json
import logging
from datetime import date
from flask import render_template, jsonify, request, abort, current_app, make_response, Response
from flask_login import login_required, current_user
from sqlalchemy import func

from . import pages_bp
from ..extensions import db
from ..constants import (
    PROVINCE_MAP, PROVINCE_CODE_TO_SLUG, AMENITY_LABELS,
    LOCATION_TYPE_LABELS, PROVINCIAL_TAX,
)
from ..services.geo_service import slugify, format_price
from ..models.location import ParkingLocation
from ..models.booking import ParkingBooking
from ..models.review import ParkingReview
from ..models.user import User

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────

def _safe_json(val, default=None):
    """Safely parse JSON, returning default on failure."""
    if default is None:
        default = []
    if isinstance(val, (list, dict)):
        return val
    try:
        return json.loads(val or '[]')
    except (json.JSONDecodeError, TypeError):
        return default


def _safe_float(val, default=0.0):
    """Safely convert to float, returning default for None."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _google_maps_key():
    return current_app.config.get('GOOGLE_MAPS_API_KEY', '')


def _get_province_name(code):
    """Get full province name from code."""
    slug = PROVINCE_CODE_TO_SLUG.get(code, '')
    info = PROVINCE_MAP.get(slug, {})
    return info.get('name', code)


def _location_to_dict(loc):
    """Convert a ParkingLocation ORM object to a template-friendly dict."""
    return {
        'id': loc.id,
        'name': loc.name,
        'slug': loc.slug,
        'city': loc.city,
        'province': loc.province,
        'latitude': _safe_float(loc.latitude),
        'longitude': _safe_float(loc.longitude),
        'location_type': loc.location_type,
        'type_label': LOCATION_TYPE_LABELS.get(loc.location_type, loc.location_type),
        'total_spots': loc.total_spots,
        'daily_rate': loc.daily_rate,
        'daily_rate_display': format_price(loc.daily_rate),
        'monthly_rate': loc.monthly_rate,
        'monthly_rate_display': format_price(loc.monthly_rate),
        'amenities': _safe_json(loc.amenities),
        'photos': _safe_json(loc.photos),
        'is_bookable': loc.is_bookable,
        'is_verified': loc.is_verified,
        'lcv_capable': loc.lcv_capable,
    }


# ── Health / Ready ───────────────────────────────────────────

@pages_bp.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200


@pages_bp.route('/ready')
def ready():
    return jsonify({'status': 'ready'}), 200


# ── SEO ─────────────────────────────────────────────────────

BASE_URL = 'https://parking.truckerpro.ca'


@pages_bp.route('/sitemap.xml')
def sitemap():
    from flask import g
    if getattr(g, 'site', 'parking') == 'stops':
        from ..stops.routes import sitemap_index
        return sitemap_index()
    today = date.today().isoformat()
    urls = []

    # Static pages
    for path, priority, changefreq in [
        ('/',               '1.0', 'daily'),
        ('/search',         '0.9', 'daily'),
        ('/list-your-space','0.8', 'monthly'),
    ]:
        urls.append({'loc': BASE_URL + path, 'lastmod': today,
                     'changefreq': changefreq, 'priority': priority})

    # Province pages
    for slug_key in PROVINCE_MAP:
        urls.append({'loc': f'{BASE_URL}/{slug_key}', 'lastmod': today,
                     'changefreq': 'weekly', 'priority': '0.8'})

    # Dynamic: all active locations + city pages
    try:
        locations = ParkingLocation.query.filter_by(
            is_active=True
        ).with_entities(
            ParkingLocation.slug,
            ParkingLocation.province,
            ParkingLocation.city,
            ParkingLocation.updated_at,
        ).all()

        seen_cities = set()
        for loc in locations:
            # Location detail page
            lastmod = loc.updated_at.date().isoformat() if loc.updated_at else today
            urls.append({'loc': f'{BASE_URL}/location/{loc.slug}', 'lastmod': lastmod,
                         'changefreq': 'weekly', 'priority': '0.9'})

            # City page (deduplicate)
            province_slug = PROVINCE_CODE_TO_SLUG.get(loc.province, '')
            city_slug = slugify(loc.city) if loc.city else ''
            city_key = f'{province_slug}/{city_slug}'
            if province_slug and city_slug and city_key not in seen_cities:
                seen_cities.add(city_key)
                urls.append({'loc': f'{BASE_URL}/{city_key}', 'lastmod': today,
                             'changefreq': 'weekly', 'priority': '0.7'})
    except Exception as e:
        logger.warning("Sitemap: failed to load locations: %s", str(e)[:200])

    xml = render_template('seo/sitemap.xml', urls=urls)
    resp = make_response(xml)
    resp.headers['Content-Type'] = 'application/xml'
    return resp


@pages_bp.route('/robots.txt')
def robots():
    txt = (
        'User-agent: *\n'
        'Allow: /\n'
        '\n'
        'Disallow: /my-bookings\n'
        'Disallow: /owner/\n'
        'Disallow: /api/\n'
        'Disallow: /login\n'
        'Disallow: /signup\n'
        '\n'
        '# Crawl-delay for polite bots\n'
        'Crawl-delay: 2\n'
        '\n'
        f'Sitemap: {BASE_URL}/sitemap.xml\n'
    )
    return Response(txt, mimetype='text/plain')


# ── Landing ──────────────────────────────────────────────────

@pages_bp.route('/')
def landing():
    """Main landing page -- public, SEO-optimized."""
    # Province counts
    province_counts = {}
    try:
        rows = db.session.query(
            ParkingLocation.province,
            func.count(ParkingLocation.id)
        ).filter(
            ParkingLocation.is_active == True  # noqa: E712
        ).group_by(ParkingLocation.province).all()
        province_counts = {row[0]: row[1] for row in rows}
    except Exception as e:
        logger.warning("Failed to load province counts: %s", str(e)[:200])

    total_locations = sum(province_counts.values())
    total_provinces = len(province_counts)

    # Featured locations
    featured_locations = []
    try:
        featured = ParkingLocation.query.filter_by(
            is_active=True
        ).order_by(
            ParkingLocation.is_featured.desc(),
            ParkingLocation.total_spots.desc()
        ).limit(8).all()

        featured_locations = [_location_to_dict(loc) for loc in featured]
    except Exception as e:
        logger.warning("Failed to load featured locations: %s", str(e)[:200])

    # Province data for cards
    province_data = []
    for slug_key, info in PROVINCE_MAP.items():
        count = province_counts.get(info['code'], 0)
        province_data.append({
            'slug': slug_key,
            'name': info['name'],
            'code': info['code'],
            'count': count,
        })
    province_data.sort(key=lambda x: x['count'], reverse=True)

    return render_template('public/landing.html',
        total_locations=total_locations,
        total_provinces=total_provinces,
        province_data=province_data,
        featured_locations=featured_locations,
        province_map=PROVINCE_MAP,
        amenity_labels=AMENITY_LABELS,
        google_api_key=_google_maps_key(),
    )


# ── Search ───────────────────────────────────────────────────

@pages_bp.route('/search')
def search():
    """Search results page."""
    q = request.args.get('q', '').strip()
    province = request.args.get('province', '').strip()
    city = request.args.get('city', '').strip()
    loc_type = request.args.get('type', '').strip()
    bookable = request.args.get('bookable', '').strip()
    lcv = request.args.get('lcv', '').strip()

    query = ParkingLocation.query.filter(ParkingLocation.is_active == True)  # noqa: E712

    if q:
        like_q = f"%{q.lower()}%"
        query = query.filter(
            db.or_(
                func.lower(ParkingLocation.name).like(like_q),
                func.lower(ParkingLocation.city).like(like_q),
                func.lower(ParkingLocation.description).like(like_q),
            )
        )

    if province:
        province_code = province.upper()
        if len(province_code) > 2 or province_code not in PROVINCE_CODE_TO_SLUG:
            slug_lookup = province.lower()
            if slug_lookup in PROVINCE_MAP:
                province_code = PROVINCE_MAP[slug_lookup]['code']
        query = query.filter(ParkingLocation.province == province_code)

    if city:
        query = query.filter(func.lower(ParkingLocation.city) == city.lower())

    if loc_type:
        query = query.filter(ParkingLocation.location_type == loc_type)

    if bookable == '1':
        query = query.filter(ParkingLocation.is_bookable == True)  # noqa: E712

    if lcv == '1':
        query = query.filter(ParkingLocation.lcv_capable == True)  # noqa: E712

    results = query.order_by(
        ParkingLocation.is_featured.desc(),
        ParkingLocation.total_spots.desc()
    ).limit(200).all()

    locations = [_location_to_dict(loc) for loc in results]

    return render_template('public/search.html',
        locations=locations,
        query=q,
        province=province,
        city=city,
        total_results=len(locations),
        province_map=PROVINCE_MAP,
        amenity_labels=AMENITY_LABELS,
        location_type_labels=LOCATION_TYPE_LABELS,
        google_api_key=_google_maps_key(),
    )


# ── List Your Space ──────────────────────────────────────────

@pages_bp.route('/list-your-space')
def list_your_space():
    """Property owner CTA / info page -- public."""
    owner_count = db.session.query(
        func.count(func.distinct(ParkingLocation.owner_id))
    ).filter(
        ParkingLocation.is_active == True,  # noqa: E712
        ParkingLocation.owner_id.isnot(None)
    ).scalar() or 0

    total = ParkingLocation.query.filter_by(is_active=True).count()

    return render_template('public/list_space.html',
        owner_count=owner_count,
        total_locations=total,
        province_map=PROVINCE_MAP,
    )


# ── Location Detail ──────────────────────────────────────────

@pages_bp.route('/location/<slug>')
def location_detail(slug):
    """Individual location detail page -- public."""
    location_obj = ParkingLocation.query.filter_by(
        slug=slug, is_active=True
    ).first()

    if not location_obj:
        abort(404)

    location = {
        'id': location_obj.id,
        'owner_id': location_obj.owner_id,
        'name': location_obj.name,
        'slug': location_obj.slug,
        'description': location_obj.description,
        'address': location_obj.address,
        'city': location_obj.city,
        'province': location_obj.province,
        'postal_code': location_obj.postal_code,
        'country': location_obj.country,
        'latitude': _safe_float(location_obj.latitude),
        'longitude': _safe_float(location_obj.longitude),
        'location_type': location_obj.location_type,
        'type_label': LOCATION_TYPE_LABELS.get(location_obj.location_type, location_obj.location_type),
        'total_spots': location_obj.total_spots,
        'bobtail_spots': location_obj.bobtail_spots,
        'trailer_spots': location_obj.trailer_spots,
        'oversize_spots': location_obj.oversize_spots,
        'lcv_capable': location_obj.lcv_capable,
        'hourly_rate': location_obj.hourly_rate,
        'hourly_rate_display': format_price(location_obj.hourly_rate),
        'daily_rate': location_obj.daily_rate,
        'daily_rate_display': format_price(location_obj.daily_rate),
        'weekly_rate': location_obj.weekly_rate,
        'weekly_rate_display': format_price(location_obj.weekly_rate),
        'monthly_rate': location_obj.monthly_rate,
        'monthly_rate_display': format_price(location_obj.monthly_rate),
        'amenities': _safe_json(location_obj.amenities),
        'photos': _safe_json(location_obj.photos),
        'contact_phone': location_obj.contact_phone,
        'contact_email': location_obj.contact_email,
        'is_active': location_obj.is_active,
        'is_verified': location_obj.is_verified,
        'is_bookable': location_obj.is_bookable,
        'is_featured': location_obj.is_featured,
        'meta_title': location_obj.meta_title,
        'meta_description': location_obj.meta_description,
        'nearby_highways': _safe_json(location_obj.nearby_highways),
        'created_at': location_obj.created_at,
        'province_name': _get_province_name(location_obj.province),
    }

    # Get reviews via ORM
    reviews_query = db.session.query(
        ParkingReview.rating,
        ParkingReview.review_text,
        ParkingReview.created_at,
        User.name
    ).outerjoin(
        User, ParkingReview.driver_id == User.id
    ).filter(
        ParkingReview.location_id == location_obj.id
    ).order_by(ParkingReview.created_at.desc()).limit(20).all()

    review_list = []
    total_rating = 0
    for rev in reviews_query:
        review_list.append({
            'rating': rev[0],
            'review_text': rev[1],
            'created_at': rev[2],
            'driver_name': rev[3] or 'Driver',
        })
        total_rating += rev[0]

    avg_rating = round(total_rating / len(reviews_query), 1) if reviews_query else 0
    review_count = len(reviews_query)

    province_slug = PROVINCE_CODE_TO_SLUG.get(location['province'], '')

    return render_template('public/location.html',
        location=location,
        reviews=review_list,
        avg_rating=avg_rating,
        review_count=review_count,
        province_slug=province_slug,
        amenity_labels=AMENITY_LABELS,
        tax_info=PROVINCIAL_TAX.get(location['province'], {}),
        google_api_key=_google_maps_key(),
    )


# ── My Bookings (authenticated) ─────────────────────────────

@pages_bp.route('/my-bookings')
@login_required
def my_bookings():
    """Driver's booking history."""
    bookings_query = db.session.query(
        ParkingBooking.id,
        ParkingBooking.booking_ref,
        ParkingBooking.start_datetime,
        ParkingBooking.end_datetime,
        ParkingBooking.booking_type,
        ParkingBooking.total_amount,
        ParkingBooking.status,
        ParkingBooking.payment_status,
        ParkingLocation.name,
        ParkingLocation.city,
        ParkingLocation.province,
        ParkingLocation.slug,
    ).join(
        ParkingLocation, ParkingBooking.location_id == ParkingLocation.id
    ).filter(
        ParkingBooking.driver_id == current_user.id
    ).order_by(ParkingBooking.created_at.desc()).limit(200).all()

    bookings = []
    for row in bookings_query:
        bookings.append({
            'id': row[0],
            'booking_ref': row[1],
            'start': row[2],
            'end': row[3],
            'booking_type': row[4],
            'total_amount': row[5],
            'total_display': format_price(row[5]),
            'status': row[6],
            'payment_status': row[7],
            'location_name': row[8],
            'location_city': row[9],
            'location_province': row[10],
            'location_slug': row[11],
        })

    return render_template('public/my_bookings.html', bookings=bookings)


# ── Province Page ────────────────────────────────────────────
# IMPORTANT: These dynamic-segment routes MUST be registered AFTER
# the more specific routes above (search, list-your-space, etc.)

@pages_bp.route('/<province_slug>')
def province_page(province_slug):
    """Province page -- shows all locations in a province."""
    province_info = PROVINCE_MAP.get(province_slug)
    if not province_info:
        abort(404)

    code = province_info['code']
    locs = ParkingLocation.query.filter_by(
        province=code, is_active=True
    ).order_by(ParkingLocation.city, ParkingLocation.name).all()

    locations = []
    city_counts = {}
    for loc in locs:
        locations.append(_location_to_dict(loc))
        city_counts[loc.city] = city_counts.get(loc.city, 0) + 1

    cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)

    return render_template('public/province.html',
        province_name=province_info['name'],
        province_code=code,
        province_slug=province_slug,
        locations=locations,
        cities=cities,
        total_locations=len(locations),
        amenity_labels=AMENITY_LABELS,
        google_api_key=_google_maps_key(),
    )


# ── City Page ────────────────────────────────────────────────

@pages_bp.route('/<province_slug>/<city_slug>')
def city_page(province_slug, city_slug):
    """City page -- shows all locations in a city."""
    province_info = PROVINCE_MAP.get(province_slug)
    if not province_info:
        abort(404)

    code = province_info['code']

    # Find the real city name by looking at active locations in this province
    distinct_cities = db.session.query(
        ParkingLocation.city
    ).filter(
        ParkingLocation.province == code,
        ParkingLocation.is_active == True  # noqa: E712
    ).distinct().all()

    city_name = None
    for (c,) in distinct_cities:
        if slugify(c) == city_slug:
            city_name = c
            break

    if not city_name:
        abort(404)

    locs = ParkingLocation.query.filter_by(
        province=code, city=city_name, is_active=True
    ).order_by(ParkingLocation.name).all()

    locations = []
    for loc in locs:
        d = _location_to_dict(loc)
        d['nearby_highways'] = _safe_json(loc.nearby_highways)
        locations.append(d)

    return render_template('public/city.html',
        city_name=city_name,
        province_name=province_info['name'],
        province_code=code,
        province_slug=province_slug,
        city_slug=city_slug,
        locations=locations,
        total_locations=len(locations),
        amenity_labels=AMENITY_LABELS,
        google_api_key=_google_maps_key(),
    )
