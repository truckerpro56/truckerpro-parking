"""Public page routes for stops.truckerpro.net."""
import logging
from flask import render_template, abort, request, Response, current_app
from flask_login import current_user
from sqlalchemy import func

from . import stops_public_bp
from ..extensions import db
from ..middleware import site_required
from ..models.truck_stop import TruckStop
from ..models.fuel_price import FuelPrice
from ..models.stop_photo import StopPhoto
from ..services.banner_service import get_banners
from ..services.google_places import get_place_photos
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
    page = max(1, page)
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
    # Find the actual city name by checking distinct cities in this state
    cities = db.session.query(TruckStop.city).filter(
        TruckStop.is_active == True, TruckStop.state_province == code,
    ).distinct().all()
    city_name = None
    for (c,) in cities:
        if _slugify(c) == city_slug:
            city_name = c
            break
    if not city_name:
        abort(404)
    city_stops = TruckStop.query.filter(
        TruckStop.is_active == True, TruckStop.state_province == code,
        func.lower(TruckStop.city) == city_name.lower(),
    ).order_by(TruckStop.name).all()
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
    photos = get_place_photos(stop.name, stop.latitude, stop.longitude)
    nearby = TruckStop.query.filter(
        TruckStop.is_active == True,
        TruckStop.state_province == stop.state_province,
        TruckStop.id != stop.id,
    ).limit(6).all()

    # Get latest fuel price per type
    latest_prices = db.session.query(
        FuelPrice.fuel_type,
        FuelPrice.price_cents,
        FuelPrice.currency,
        FuelPrice.created_at,
        FuelPrice.is_verified,
    ).filter_by(truck_stop_id=stop.id).order_by(
        FuelPrice.fuel_type, FuelPrice.created_at.desc()
    ).all()
    seen = set()
    fuel_prices = []
    for fp in latest_prices:
        if fp.fuel_type not in seen:
            seen.add(fp.fuel_type)
            fuel_prices.append({
                'fuel_type': fp.fuel_type,
                'price_cents': fp.price_cents,
                'currency': fp.currency,
                'updated': fp.created_at,
                'is_verified': fp.is_verified,
            })

    is_favorited = False
    if current_user.is_authenticated:
        from ..models.favorite_stop import FavoriteStop
        is_favorited = FavoriteStop.query.filter_by(
            user_id=current_user.id, truck_stop_id=stop.id
        ).first() is not None

    driver_photos = StopPhoto.query.filter_by(
        truck_stop_id=stop.id, is_approved=True
    ).order_by(StopPhoto.created_at.desc()).limit(20).all()

    return render_template('stops/stop_detail.html',
                           stop=stop, banners=banners, photos=photos,
                           nearby=[stop_to_card(s) for s in nearby],
                           state_slug=state_slug, city_slug=city_slug,
                           fuel_prices=fuel_prices,
                           is_favorited=is_favorited,
                           driver_photos=driver_photos,
                           google_maps_key=current_app.config.get('GOOGLE_MAPS_API_KEY', ''))


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
    # Find the actual highway name from distinct values
    highways = db.session.query(TruckStop.highway).filter(
        TruckStop.is_active == True, TruckStop.highway.isnot(None)
    ).distinct().all()
    highway_name = None
    for (h,) in highways:
        if highway_to_slug(h) == highway_slug:
            highway_name = h
            break
    if not highway_name:
        abort(404)
    matched = TruckStop.query.filter(
        TruckStop.is_active == True, TruckStop.highway == highway_name,
    ).order_by(TruckStop.name).all()
    return render_template('stops/highway_detail.html',
                           highway_name=highway_name,
                           highway_slug=highway_slug,
                           stops=[stop_to_card(s) for s in matched])


# ── Driver Photo Serving ─────────────────────────────────────

@stops_public_bp.route('/photos/<int:photo_id>')
@site_required('stops')
def serve_photo(photo_id):
    """Serve a driver-uploaded photo from the database."""
    photo = StopPhoto.query.filter_by(id=photo_id, is_approved=True).first_or_404()
    return Response(photo.image_data, mimetype=photo.content_type,
                    headers={'Cache-Control': 'public, max-age=86400'})


# ── Robots.txt ───────────────────────────────────────────────

_BLOCKED_BOT_NAMES = [
    'GPTBot', 'ChatGPT-User', 'OAI-SearchBot', 'ChatGPT Agent', 'Operator',
    'ClaudeBot', 'Claude-Web', 'anthropic-ai', 'Claude-SearchBot', 'Claude-User',
    'GoogleOther', 'Google-Extended', 'GoogleOther-Image', 'GoogleOther-Video',
    'Google-Agent', 'GoogleAgent-Mariner', 'Gemini-Deep-Research',
    'Google-CloudVertexBot', 'CloudVertexBot', 'Google-NotebookLM',
    'Meta-ExternalAgent', 'Meta-ExternalFetcher', 'FacebookBot', 'meta-webindexer',
    'Applebot-Extended', 'Amazonbot', 'amazon-kendra', 'bedrockbot', 'NovaAct',
    'AzureAI-SearchBot', 'Bytespider', 'DeepSeekBot', 'ChatGLM-Spider',
    'PanguBot', 'TikTokSpider', 'PerplexityBot', 'Perplexity-User', 'Bravebot',
    'DuckAssistBot', 'PhindBot', 'YouBot', 'Andibot', 'ExaBot', 'kagi-fetcher',
    'cohere-ai', 'cohere-training-data-crawler', 'MistralAI-User',
    'Ai2Bot', 'DiffBot', 'PetalBot', 'WRTNBot', 'Manus-User', 'Devin',
    'CCBot', 'img2dataset', 'ImagesiftBot', 'ICC-Crawler',
    'FirecrawlAgent', 'Crawl4AI', 'ApifyBot', 'Scrapy',
    'LAIONDownloader', 'Brightbot', 'TavilyBot',
    'SemrushBot-OCOB', 'SemrushBot-SWA', 'omgilibot', 'Webzio-Extended',
    'Timpibot', 'aiHitBot',
]


@stops_public_bp.route('/robots.txt')
@site_required('stops')
def robots_txt():
    lines = []
    for bot in _BLOCKED_BOT_NAMES:
        lines.append(f'User-agent: {bot}')
        lines.append('Disallow: /')
        lines.append('')
    lines.extend([
        'User-agent: Googlebot', 'Allow: /', '',
        'User-agent: Bingbot', 'Allow: /', '',
        'User-agent: *',
        'Disallow: /api/',
        'Disallow: /login',
        'Disallow: /signup',
        'Disallow: /logout',
        '',
        f'Sitemap: {STOPS_BASE}/sitemap.xml',
    ])
    resp = Response('\n'.join(lines), mimetype='text/plain')
    resp.headers['Cache-Control'] = 'public, max-age=86400'
    return resp


# ── Sitemaps ─────────────────────────────────────────────────

@stops_public_bp.route('/sitemap.xml')
@site_required('stops')
def sitemap_index():
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for name in ['stops', 'states', 'brands', 'highways', 'cities']:
        xml.append(f'<sitemap><loc>{STOPS_BASE}/sitemap-{name}.xml</loc></sitemap>')
    xml.append(f'<sitemap><loc>{STOPS_BASE}/sitemap-rest-areas.xml</loc></sitemap>')
    xml.append(f'<sitemap><loc>{STOPS_BASE}/sitemap-weigh-stations.xml</loc></sitemap>')
    xml.append(f'<sitemap><loc>https://stops.truckerpro.net/sitemap-blog.xml</loc></sitemap>')
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
        xml.append(f'<url><loc>{loc}</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>')
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
    # Core pages
    xml.append(f'<url><loc>{STOPS_BASE}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>')
    xml.append(f'<url><loc>{STOPS_BASE}/us</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>')
    xml.append(f'<url><loc>{STOPS_BASE}/canada</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>')
    xml.append(f'<url><loc>{STOPS_BASE}/brands</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    xml.append(f'<url><loc>{STOPS_BASE}/highways</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    xml.append(f'<url><loc>{STOPS_BASE}/rest-areas</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    xml.append(f'<url><loc>{STOPS_BASE}/weigh-stations</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    xml.append(f'<url><loc>{STOPS_BASE}/route-planner</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>')
    for code, country in states:
        country_slug = 'us' if country == 'US' else 'canada'
        state_sl = state_code_to_slug(code)
        xml.append(f'<url><loc>{STOPS_BASE}/{country_slug}/{state_sl}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
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
        xml.append(f'<url><loc>{STOPS_BASE}/brands/{brand_key_to_slug(brand_key)}</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>')
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
        xml.append(f'<url><loc>{STOPS_BASE}/highways/{_slugify(hwy)}</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>')
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
        xml.append(f'<url><loc>{STOPS_BASE}/{country_slug}/{state_sl}/{city_sl}</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>')
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')


@stops_public_bp.route('/sitemap-rest-areas.xml')
@site_required('stops')
def sitemap_rest_areas():
    from ..models.rest_area import RestArea
    areas = RestArea.query.filter_by(is_active=True).all()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml.append(f'<url><loc>{STOPS_BASE}/rest-areas</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>')
    for a in areas:
        state_sl = state_code_to_slug(a.state_province)
        xml.append(f'<url><loc>{STOPS_BASE}/rest-areas/{state_sl}/{a.slug}</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>')
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')


@stops_public_bp.route('/sitemap-weigh-stations.xml')
@site_required('stops')
def sitemap_weigh_stations():
    from ..models.weigh_station import WeighStation
    stations = WeighStation.query.filter_by(is_active=True).all()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml.append(f'<url><loc>{STOPS_BASE}/weigh-stations</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>')
    for ws in stations:
        state_sl = state_code_to_slug(ws.state_province)
        xml.append(f'<url><loc>{STOPS_BASE}/weigh-stations/{state_sl}/{ws.slug}</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>')
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')


@stops_public_bp.route('/sitemap-blog.xml')
@site_required('stops')
def sitemap_blog():
    from ..blog import _posts
    from ..blog.renderer import get_all_posts
    blog_posts = get_all_posts(_posts or [], 'stops')
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml.append('<url><loc>https://stops.truckerpro.net/blog</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    for bp in blog_posts:
        xml.append(f"<url><loc>https://stops.truckerpro.net/blog/{bp['slug']}</loc><lastmod>{bp['date']}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>")
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')


@stops_public_bp.route('/sw.js')
@site_required('stops')
def service_worker():
    """Serve the PWA service worker from the root scope."""
    import os
    from flask import send_file
    sw_path = os.path.join(current_app.static_folder, 'sw.js')
    response = send_file(sw_path, mimetype='application/javascript')
    response.cache_control.no_store = True
    response.cache_control.max_age = 0
    return response
