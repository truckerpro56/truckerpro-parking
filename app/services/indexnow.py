"""IndexNow — instant URL submission to search engines."""
import logging
import requests as http_requests
from flask import current_app

logger = logging.getLogger(__name__)


def submit_urls(host, urls):
    """Submit URLs to IndexNow API. Returns dict with status.

    Args:
        host: Domain name (e.g., 'stops.truckerpro.net')
        urls: List of full URLs to submit (max 10,000 per batch)
    """
    key = current_app.config.get('INDEXNOW_KEY', '')
    if not key:
        logger.warning("INDEXNOW_KEY not configured, skipping submission")
        return {'skipped': True, 'reason': 'no key'}

    # IndexNow accepts max 10,000 URLs per request
    results = []
    for i in range(0, len(urls), 10000):
        batch = urls[i:i + 10000]
        try:
            payload = {
                'host': host,
                'key': key,
                'urlList': batch,
            }
            resp = http_requests.post(
                'https://api.indexnow.org/indexnow',
                json=payload,
                timeout=15,
            )
            results.append({
                'status': resp.status_code,
                'urls_submitted': len(batch),
            })
            logger.info("IndexNow: submitted %d URLs to %s (status %d)",
                        len(batch), host, resp.status_code)
        except Exception as e:
            results.append({'error': str(e)[:200]})
            logger.error("IndexNow submission failed: %s", str(e)[:200])

    return {'results': results, 'total_urls': len(urls)}


def submit_stops_urls():
    """Submit all stops.truckerpro.net URLs to IndexNow."""
    from ..models.truck_stop import TruckStop
    from ..models.rest_area import RestArea
    from ..models.weigh_station import WeighStation
    from ..blog import _posts
    from ..blog.renderer import get_all_posts
    from ..stops.helpers import state_code_to_slug
    from ..services.geo_service import slugify

    base = 'https://stops.truckerpro.net'
    urls = [
        f'{base}/',
        f'{base}/us',
        f'{base}/canada',
        f'{base}/brands',
        f'{base}/highways',
        f'{base}/rest-areas',
        f'{base}/weigh-stations',
        f'{base}/route-planner',
        f'{base}/blog',
    ]

    # Truck stop pages
    stops = TruckStop.query.filter_by(is_active=True).all()
    for s in stops:
        country_slug = 'us' if s.country == 'US' else 'canada'
        state_sl = state_code_to_slug(s.state_province)
        city_sl = slugify(s.city)
        urls.append(f'{base}/{country_slug}/{state_sl}/{city_sl}/{s.slug}')

    # State pages (dedupe)
    states_seen = set()
    for s in stops:
        key = (s.country, s.state_province)
        if key not in states_seen:
            states_seen.add(key)
            country_slug = 'us' if s.country == 'US' else 'canada'
            state_sl = state_code_to_slug(s.state_province)
            urls.append(f'{base}/{country_slug}/{state_sl}')

    # City pages (dedupe)
    cities_seen = set()
    for s in stops:
        key = (s.country, s.state_province, s.city)
        if key not in cities_seen:
            cities_seen.add(key)
            country_slug = 'us' if s.country == 'US' else 'canada'
            state_sl = state_code_to_slug(s.state_province)
            city_sl = slugify(s.city)
            urls.append(f'{base}/{country_slug}/{state_sl}/{city_sl}')

    # Rest areas
    areas = RestArea.query.filter_by(is_active=True).all()
    ra_states = set()
    for a in areas:
        state_sl = state_code_to_slug(a.state_province)
        urls.append(f'{base}/rest-areas/{state_sl}/{a.slug}')
        if a.state_province not in ra_states:
            ra_states.add(a.state_province)
            urls.append(f'{base}/rest-areas/{state_sl}')

    # Weigh stations
    ws_list = WeighStation.query.filter_by(is_active=True).all()
    ws_states = set()
    for w in ws_list:
        state_sl = state_code_to_slug(w.state_province)
        urls.append(f'{base}/weigh-stations/{state_sl}/{w.slug}')
        if w.state_province not in ws_states:
            ws_states.add(w.state_province)
            urls.append(f'{base}/weigh-stations/{state_sl}')

    # Blog posts
    blog_posts = get_all_posts(_posts or [], 'stops')
    for p in blog_posts:
        urls.append(f'{base}/blog/{p["slug"]}')

    return submit_urls('stops.truckerpro.net', urls)


def submit_parking_urls():
    """Submit all parking.truckerpro.ca URLs to IndexNow."""
    from ..models.location import ParkingLocation
    from ..blog import _posts
    from ..blog.renderer import get_all_posts
    from ..services.geo_service import slugify

    base = 'https://parking.truckerpro.ca'
    urls = [f'{base}/']

    # Location pages
    locations = ParkingLocation.query.filter_by(is_active=True).all()
    for loc in locations:
        urls.append(f'{base}/location/{loc.slug}')

    # Province pages (dedupe)
    provinces = set()
    for loc in locations:
        if loc.province not in provinces:
            provinces.add(loc.province)
            urls.append(f'{base}/{slugify(loc.province)}')

    # Blog posts
    blog_posts = get_all_posts(_posts or [], 'parking')
    for p in blog_posts:
        urls.append(f'{base}/blog/{p["slug"]}')

    return submit_urls('parking.truckerpro.ca', urls)


def ping_search_engines():
    """Ping Google and Bing to re-crawl sitemaps."""
    results = []
    sitemaps = [
        'https://stops.truckerpro.net/sitemap.xml',
        'https://parking.truckerpro.ca/sitemap.xml',
    ]
    for sitemap in sitemaps:
        # Bing ping
        try:
            resp = http_requests.get(
                f'https://www.bing.com/ping?sitemap={sitemap}',
                timeout=10,
            )
            results.append({'service': 'bing', 'sitemap': sitemap, 'status': resp.status_code})
        except Exception as e:
            results.append({'service': 'bing', 'sitemap': sitemap, 'error': str(e)[:200]})

    return results
