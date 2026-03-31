"""Public page routes for stops.truckerpro.net."""
import logging
from flask import render_template, abort, request, Response
from sqlalchemy import func

from . import stops_public_bp
from ..extensions import db
from ..middleware import site_required
from ..models.truck_stop import TruckStop
from ..services.banner_service import get_banners
from ..services.geo_service import slugify as _slugify
from ..constants import US_STATES, PROVINCE_MAP, BRAND_MAP, BRAND_SLUG_TO_KEY
from .helpers import (
    state_slug_to_code, state_slug_to_name, country_for_state,
    brand_slug_to_key, brand_slug_to_name, stop_to_card,
    highway_to_slug, state_code_to_slug, brand_key_to_slug,
)

logger = logging.getLogger(__name__)
PER_PAGE = 24
STOPS_BASE = 'https://stops.truckerpro.net'


def _paginate(query, page, per_page=PER_PAGE):
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    pages = (total + per_page - 1) // per_page
    return items, total, pages


@stops_public_bp.route('/')
@site_required('stops')
def home():
    total_stops = TruckStop.query.filter_by(is_active=True).count()
    total_brands = db.session.query(func.count(func.distinct(TruckStop.brand))).filter(
        TruckStop.is_active == True
    ).scalar()
    total_states = db.session.query(func.count(func.distinct(TruckStop.state_province))).filter(
        TruckStop.is_active == True
    ).scalar()
    featured = TruckStop.query.filter_by(is_active=True).order_by(
        TruckStop.total_parking_spots.desc().nullslast()
    ).limit(12).all()
    return render_template('stops/home.html',
                           total_stops=total_stops, total_brands=total_brands,
                           total_states=total_states,
                           featured=[stop_to_card(s) for s in featured])


@stops_public_bp.route('/us')
@site_required('stops')
def us_overview():
    states = db.session.query(
        TruckStop.state_province, func.count(TruckStop.id),
    ).filter(TruckStop.is_active == True, TruckStop.country == 'US'
    ).group_by(TruckStop.state_province).order_by(TruckStop.state_province).all()
    state_data = [
        {'code': code, 'slug': state_code_to_slug(code),
         'name': state_slug_to_name(state_code_to_slug(code)), 'count': cnt}
        for code, cnt in states
    ]
    return render_template('stops/country.html', country='US',
                           country_name='United States', regions=state_data)


@stops_public_bp.route('/canada')
@site_required('stops')
def canada_overview():
    provinces = db.session.query(
        TruckStop.state_province, func.count(TruckStop.id),
    ).filter(TruckStop.is_active == True, TruckStop.country == 'CA'
    ).group_by(TruckStop.state_province).order_by(TruckStop.state_province).all()
    prov_data = [
        {'code': code, 'slug': state_code_to_slug(code),
         'name': state_slug_to_name(state_code_to_slug(code)), 'count': cnt}
        for code, cnt in provinces
    ]
    return render_template('stops/country.html', country='CA',
                           country_name='Canada', regions=prov_data)


@stops_public_bp.route('/us/<state_slug>')
@stops_public_bp.route('/canada/<state_slug>')
@site_required('stops')
def state_page(state_slug):
    code = state_slug_to_code(state_slug)
    if not code:
        abort(404)
    country = country_for_state(code)
    page = request.args.get('page', 1, type=int)
    query = TruckStop.query.filter_by(
        is_active=True, state_province=code
    ).order_by(TruckStop.city, TruckStop.name)
    stops, total, pages = _paginate(query, page)
    cities = db.session.query(
        TruckStop.city, func.count(TruckStop.id)
    ).filter_by(is_active=True, state_province=code
    ).group_by(TruckStop.city).order_by(TruckStop.city).all()
    return render_template('stops/state.html',
                           state_name=state_slug_to_name(state_slug),
                           state_code=code, state_slug=state_slug,
                           country=country,
                           stops=[stop_to_card(s) for s in stops],
                           cities=cities, total=total, page=page, pages=pages)


@stops_public_bp.route('/us/<state_slug>/<city_slug>')
@stops_public_bp.route('/canada/<state_slug>/<city_slug>')
@site_required('stops')
def city_page(state_slug, city_slug):
    code = state_slug_to_code(state_slug)
    if not code:
        abort(404)
    query = TruckStop.query.filter(
        TruckStop.is_active == True, TruckStop.state_province == code,
    ).order_by(TruckStop.name)
    all_stops = query.all()
    city_stops = [s for s in all_stops if _slugify(s.city) == city_slug]
    if not city_stops:
        abort(404)
    city_name = city_stops[0].city
    return render_template('stops/city.html',
                           city_name=city_name, state_name=state_slug_to_name(state_slug),
                           state_slug=state_slug, state_code=code,
                           stops=[stop_to_card(s) for s in city_stops])


@stops_public_bp.route('/us/<state_slug>/<city_slug>/<slug>')
@stops_public_bp.route('/canada/<state_slug>/<city_slug>/<slug>')
@site_required('stops')
def stop_detail(state_slug, city_slug, slug):
    stop = TruckStop.query.filter_by(slug=slug, is_active=True).first()
    if not stop:
        abort(404)
    banners = get_banners(stop)
    nearby = TruckStop.query.filter(
        TruckStop.is_active == True,
        TruckStop.state_province == stop.state_province,
        TruckStop.id != stop.id,
    ).limit(6).all()
    return render_template('stops/stop_detail.html',
                           stop=stop, banners=banners,
                           nearby=[stop_to_card(s) for s in nearby],
                           state_slug=state_slug, city_slug=city_slug)


@stops_public_bp.route('/brands')
@site_required('stops')
def brands_index():
    brands = db.session.query(
        TruckStop.brand, TruckStop.brand_display_name,
        func.count(TruckStop.id),
    ).filter(TruckStop.is_active == True
    ).group_by(TruckStop.brand, TruckStop.brand_display_name
    ).order_by(func.count(TruckStop.id).desc()).all()
    return render_template('stops/brand_index.html', brands=brands)


@stops_public_bp.route('/brands/<brand_slug>')
@site_required('stops')
def brand_detail(brand_slug):
    brand_key = brand_slug_to_key(brand_slug)
    if not brand_key:
        abort(404)
    page = request.args.get('page', 1, type=int)
    query = TruckStop.query.filter_by(
        is_active=True, brand=brand_key
    ).order_by(TruckStop.state_province, TruckStop.city)
    stops, total, pages = _paginate(query, page)
    return render_template('stops/brand_detail.html',
                           brand_name=brand_slug_to_name(brand_slug),
                           brand_slug=brand_slug,
                           stops=[stop_to_card(s) for s in stops],
                           total=total, page=page, pages=pages)


@stops_public_bp.route('/brands/<brand_slug>/<state_slug>')
@site_required('stops')
def brand_state(brand_slug, state_slug):
    brand_key = brand_slug_to_key(brand_slug)
    code = state_slug_to_code(state_slug)
    if not brand_key or not code:
        abort(404)
    stops = TruckStop.query.filter_by(
        is_active=True, brand=brand_key, state_province=code
    ).order_by(TruckStop.city, TruckStop.name).all()
    return render_template('stops/brand_state.html',
                           brand_name=brand_slug_to_name(brand_slug),
                           brand_slug=brand_slug,
                           state_name=state_slug_to_name(state_slug),
                           state_slug=state_slug,
                           stops=[stop_to_card(s) for s in stops])


@stops_public_bp.route('/highways')
@site_required('stops')
def highways_index():
    highways = db.session.query(
        TruckStop.highway, func.count(TruckStop.id),
    ).filter(
        TruckStop.is_active == True, TruckStop.highway.isnot(None)
    ).group_by(TruckStop.highway
    ).order_by(func.count(TruckStop.id).desc()).all()
    return render_template('stops/highway_index.html', highways=highways)


@stops_public_bp.route('/highways/<highway_slug>')
@site_required('stops')
def highway_detail(highway_slug):
    all_stops = TruckStop.query.filter(
        TruckStop.is_active == True, TruckStop.highway.isnot(None)
    ).all()
    matched = [s for s in all_stops if highway_to_slug(s.highway) == highway_slug]
    if not matched:
        abort(404)
    highway_name = matched[0].highway
    return render_template('stops/highway_detail.html',
                           highway_name=highway_name,
                           highway_slug=highway_slug,
                           stops=[stop_to_card(s) for s in matched])


# ── Sitemaps (Task 12) ──────────────────────────────────────

@stops_public_bp.route('/sitemap.xml')
@site_required('stops')
def sitemap_index():
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for name in ['stops', 'states', 'brands', 'highways', 'cities']:
        xml.append(f'<sitemap><loc>{STOPS_BASE}/sitemap-{name}.xml</loc></sitemap>')
    xml.append('</sitemapindex>')
    return Response('\n'.join(xml), mimetype='application/xml')


@stops_public_bp.route('/sitemap-stops.xml')
@site_required('stops')
def sitemap_stops():
    stops = TruckStop.query.filter_by(is_active=True).all()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for s in stops:
        country_slug = 'us' if s.country == 'US' else 'canada'
        state_sl = state_code_to_slug(s.state_province)
        city_sl = _slugify(s.city)
        loc = f'{STOPS_BASE}/{country_slug}/{state_sl}/{city_sl}/{s.slug}'
        xml.append(f'<url><loc>{loc}</loc></url>')
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')


@stops_public_bp.route('/sitemap-states.xml')
@site_required('stops')
def sitemap_states():
    states = db.session.query(
        TruckStop.state_province, TruckStop.country
    ).filter(TruckStop.is_active == True).distinct().all()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for code, country in states:
        country_slug = 'us' if country == 'US' else 'canada'
        state_sl = state_code_to_slug(code)
        xml.append(f'<url><loc>{STOPS_BASE}/{country_slug}/{state_sl}</loc></url>')
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')


@stops_public_bp.route('/sitemap-brands.xml')
@site_required('stops')
def sitemap_brands():
    brands = db.session.query(TruckStop.brand).filter(
        TruckStop.is_active == True
    ).distinct().all()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for (brand_key,) in brands:
        xml.append(f'<url><loc>{STOPS_BASE}/brands/{brand_key_to_slug(brand_key)}</loc></url>')
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')


@stops_public_bp.route('/sitemap-highways.xml')
@site_required('stops')
def sitemap_highways():
    hwys = db.session.query(TruckStop.highway).filter(
        TruckStop.is_active == True, TruckStop.highway.isnot(None)
    ).distinct().all()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for (hwy,) in hwys:
        xml.append(f'<url><loc>{STOPS_BASE}/highways/{_slugify(hwy)}</loc></url>')
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')


@stops_public_bp.route('/sitemap-cities.xml')
@site_required('stops')
def sitemap_cities():
    cities = db.session.query(
        TruckStop.city, TruckStop.state_province, TruckStop.country
    ).filter(TruckStop.is_active == True).distinct().all()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for city, code, country in cities:
        country_slug = 'us' if country == 'US' else 'canada'
        state_sl = state_code_to_slug(code)
        city_sl = _slugify(city)
        xml.append(f'<url><loc>{STOPS_BASE}/{country_slug}/{state_sl}/{city_sl}</loc></url>')
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')
