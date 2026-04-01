"""Rest area routes for stops.truckerpro.net."""
from flask import render_template, abort, request
from sqlalchemy import func

from . import stops_public_bp
from ..extensions import db
from ..middleware import site_required
from ..models.rest_area import RestArea
from .helpers import state_code_to_slug, state_slug_to_code, state_slug_to_name, country_for_state


@stops_public_bp.route('/rest-areas')
@site_required('stops')
def rest_areas_index():
    """Rest areas directory — browse by state."""
    states = db.session.query(
        RestArea.state_province, RestArea.country, func.count(RestArea.id),
    ).filter(RestArea.is_active == True
    ).group_by(RestArea.state_province, RestArea.country
    ).order_by(func.count(RestArea.id).desc()).all()
    state_data = [
        {'code': code, 'slug': state_code_to_slug(code),
         'name': state_slug_to_name(state_code_to_slug(code)),
         'country': country, 'count': cnt}
        for code, country, cnt in states
    ]
    total = RestArea.query.filter_by(is_active=True).count()
    return render_template('stops/rest_areas/index.html',
                           states=state_data, total=total)


@stops_public_bp.route('/rest-areas/<state_slug>')
@site_required('stops')
def rest_areas_state(state_slug):
    """Rest areas in a specific state."""
    code = state_slug_to_code(state_slug)
    if not code:
        abort(404)
    page = request.args.get('page', 1, type=int)
    query = RestArea.query.filter_by(
        is_active=True, state_province=code
    ).order_by(RestArea.highway, RestArea.name)
    total = query.count()
    areas = query.offset((page - 1) * 24).limit(24).all()
    pages = (total + 23) // 24
    return render_template('stops/rest_areas/state.html',
                           state_name=state_slug_to_name(state_slug),
                           state_slug=state_slug, state_code=code,
                           areas=areas, total=total, page=page, pages=pages)


@stops_public_bp.route('/rest-areas/<state_slug>/<slug>')
@site_required('stops')
def rest_area_detail(state_slug, slug):
    """Individual rest area detail page."""
    area = RestArea.query.filter_by(slug=slug, is_active=True).first()
    if not area:
        abort(404)
    nearby = RestArea.query.filter(
        RestArea.is_active == True,
        RestArea.state_province == area.state_province,
        RestArea.id != area.id,
    ).limit(6).all()
    google_maps_key = ''
    from flask import current_app
    google_maps_key = current_app.config.get('GOOGLE_MAPS_API_KEY', '')
    return render_template('stops/rest_areas/detail.html',
                           area=area, nearby=nearby,
                           state_slug=state_slug,
                           google_maps_key=google_maps_key)
