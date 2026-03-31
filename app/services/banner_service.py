"""Smart contextual banner service for truck stop pages."""
from ..constants import MAJOR_FREIGHT_CORRIDORS, MAJOR_METROS


def get_banners(truck_stop):
    """Return ordered list of banner dicts for a truck stop.
    Each banner: {'type': str, 'copy': str, 'url': str, 'cta': str}
    Order: tms, border (if applicable), parking, fmcsa
    """
    banners = []
    banners.append(_tms_banner(truck_stop))
    border = _border_banner(truck_stop)
    if border:
        banners.append(border)
    banners.append(_parking_banner(truck_stop))
    banners.append(_fmcsa_banner(truck_stop))
    return banners


def _tms_banner(stop):
    highway = getattr(stop, 'highway', None) or ''
    city = getattr(stop, 'city', '') or ''
    if highway.upper() in [c.upper() for c in MAJOR_FREIGHT_CORRIDORS]:
        copy = f"Dispatching loads on {highway}? Manage your fleet"
    elif city in MAJOR_METROS:
        copy = f"Running routes through {city}? Track every load"
    else:
        copy = "Trucking company? Manage your fleet with TruckerPro TMS"
    return {'type': 'tms', 'copy': copy, 'url': 'https://tms.truckerpro.ca', 'cta': 'Try Free'}


def _border_banner(stop):
    crossing = getattr(stop, 'nearest_border_crossing', None)
    distance = getattr(stop, 'border_distance_km', None)
    if not crossing or distance is None or distance > 100:
        return None
    country = getattr(stop, 'country', 'US')
    dist_display = int(distance)
    if country == 'US':
        copy = f"{dist_display}km from {crossing} \u2014 clear customs faster"
    else:
        copy = f"Pre-clear at {crossing} \u2014 skip the line"
    return {'type': 'border', 'copy': copy, 'url': 'https://border.truckerpro.ca', 'cta': 'Learn More'}


def _parking_banner(stop):
    if getattr(stop, 'parking_location_id', None):
        copy = "Reserve parking at this stop"
    else:
        copy = "Find reservable parking nearby"
    return {'type': 'parking', 'copy': copy, 'url': 'https://parking.truckerpro.ca', 'cta': 'Reserve'}


def _fmcsa_banner(stop):
    return {'type': 'fmcsa', 'copy': "Look up carriers at this stop", 'url': 'https://fmcsa.truckerpro.net', 'cta': 'Lookup'}
