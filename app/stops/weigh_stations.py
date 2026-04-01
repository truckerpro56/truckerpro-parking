"""Weigh station routes for stops.truckerpro.net."""
from flask import render_template, abort, request
from sqlalchemy import func

from . import stops_public_bp
from ..extensions import db
from ..middleware import site_required
from ..models.weigh_station import WeighStation
from .helpers import state_code_to_slug, state_slug_to_code, state_slug_to_name


@stops_public_bp.route('/weigh-stations')
@site_required('stops')
def weigh_stations_index():
    """Weigh stations directory — browse by state."""
    states = db.session.query(
        WeighStation.state_province, WeighStation.country, func.count(WeighStation.id),
    ).filter(WeighStation.is_active == True
    ).group_by(WeighStation.state_province, WeighStation.country
    ).order_by(func.count(WeighStation.id).desc()).all()
    state_data = [
        {'code': code, 'slug': state_code_to_slug(code),
         'name': state_slug_to_name(state_code_to_slug(code)),
         'country': country, 'count': cnt}
        for code, country, cnt in states
    ]
    total = WeighStation.query.filter_by(is_active=True).count()
    return render_template('stops/weigh_stations/index.html',
                           states=state_data, total=total)


@stops_public_bp.route('/weigh-stations/<state_slug>')
@site_required('stops')
def weigh_stations_state(state_slug):
    """Weigh stations in a specific state."""
    code = state_slug_to_code(state_slug)
    if not code:
        abort(404)
    page = request.args.get('page', 1, type=int)
    query = WeighStation.query.filter_by(
        is_active=True, state_province=code
    ).order_by(WeighStation.highway, WeighStation.name)
    total = query.count()
    stations = query.offset((page - 1) * 24).limit(24).all()
    pages = (total + 23) // 24
    return render_template('stops/weigh_stations/state.html',
                           state_name=state_slug_to_name(state_slug),
                           state_slug=state_slug, state_code=code,
                           stations=stations, total=total, page=page, pages=pages)


@stops_public_bp.route('/weigh-stations/<state_slug>/<slug>')
@site_required('stops')
def weigh_station_detail(state_slug, slug):
    """Individual weigh station detail page."""
    ws = WeighStation.query.filter_by(slug=slug, is_active=True).first()
    if not ws:
        abort(404)
    nearby = WeighStation.query.filter(
        WeighStation.is_active == True,
        WeighStation.state_province == ws.state_province,
        WeighStation.id != ws.id,
    ).limit(6).all()
    from flask import current_app
    google_maps_key = current_app.config.get('GOOGLE_MAPS_API_KEY', '')
    return render_template('stops/weigh_stations/detail.html',
                           ws=ws, nearby=nearby,
                           state_slug=state_slug,
                           google_maps_key=google_maps_key)
