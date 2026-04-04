"""Smart contextual banner service for truck stop pages."""
from datetime import datetime, timezone
from ..constants import MAJOR_FREIGHT_CORRIDORS, MAJOR_METROS

_VARIANTS = ('a', 'b', 'c')


def _get_variant():
    """Return today's banner variant based on day of year."""
    day = datetime.now(timezone.utc).timetuple().tm_yday
    return _VARIANTS[day % 3]


def get_banners(truck_stop):
    """Return ordered list of variant-aware banner dicts for a truck stop."""
    variant = _get_variant()
    banners = []
    banners.append(_tms_banner(truck_stop, variant))
    border = _border_banner(truck_stop, variant)
    if border:
        banners.append(border)
    banners.append(_parking_banner(truck_stop, variant))
    banners.append(_fmcsa_banner(truck_stop, variant))
    return banners


def _tms_banner(stop, variant):
    highway = getattr(stop, 'highway', None) or ''
    city = getattr(stop, 'city', '') or ''
    if highway.upper() in [c.upper() for c in MAJOR_FREIGHT_CORRIDORS]:
        copy = f"Dispatching loads on {highway}? Manage your fleet"
    elif city in MAJOR_METROS:
        copy = f"Running routes through {city}? Track every load"
    else:
        copy = "Trucking company? Manage your fleet with TruckerPro TMS"

    variants = {
        'a': {
            'headline': '527 carriers switched\nthis quarter.',
            'desc': 'Dispatch, ELD, compliance, invoicing \u2014 one platform.',
            'cta': 'Start Free Trial',
            'sub_cta': 'No credit card',
            'hook': None,
            'watermark': None,
        },
        'b': {
            'headline': 'Your fleet deserves better\nthan copy-paste logistics.',
            'desc': None,
            'cta': 'See How It Works',
            'sub_cta': '2 min demo',
            'hook': '\u201cStill dispatching from spreadsheets?\u201d',
            'watermark': None,
        },
        'c': {
            'headline': 'One app.\nWhole fleet.',
            'desc': 'Dispatch \u00b7 ELD \u00b7 IFTA \u00b7 Invoicing\n14 days free \u00b7 No card required',
            'cta': 'Get Started',
            'sub_cta': None,
            'hook': None,
            'watermark': 'TMS',
        },
    }
    v = variants[variant]
    return {
        'type': 'tms',
        'variant': variant,
        'copy': copy,
        'url': 'https://tms.truckerpro.ca',
        'eyebrow': 'TruckerPro TMS',
        **v,
    }


def _border_banner(stop, variant):
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

    variants = {
        'a': {
            'headline': '12,400 manifests filed\nthis month.',
            'desc': 'ACE & ACI eManifest in under 5 minutes. Zero penalties.',
            'cta': 'File Your First Manifest',
            'sub_cta': 'Free to start',
            'hook': None,
            'watermark': None,
        },
        'b': {
            'headline': 'Pre-clear customs before\nyou even hit the border.',
            'desc': None,
            'cta': 'See How It Works',
            'sub_cta': '5 min setup',
            'hook': '\u201cStuck at the crossing again?\u201d',
            'watermark': None,
        },
        'c': {
            'headline': 'File once.\nCross fast.',
            'desc': 'ACE \u00b7 ACI \u00b7 PAPS \u00b7 PARS\nFree to start \u00b7 CBSA & CBP compliant',
            'cta': 'Get Started',
            'sub_cta': None,
            'hook': None,
            'watermark': 'ACE',
        },
    }
    v = variants[variant]
    return {
        'type': 'border',
        'variant': variant,
        'copy': copy,
        'url': 'https://border.truckerpro.ca',
        'eyebrow': 'TruckerPro Border',
        **v,
    }


def _parking_banner(stop, variant):
    if getattr(stop, 'parking_location_id', None):
        copy = "Reserve parking at this stop"
    else:
        copy = "Find reservable parking nearby"

    variants = {
        'a': {
            'headline': '2,100 spots booked\nlast week.',
            'desc': '75+ verified lots across Canada. Reserve before you arrive.',
            'cta': 'Reserve a Spot',
            'sub_cta': None,
            'hook': None,
            'watermark': None,
        },
        'b': {
            'headline': 'Book your spot before\nyou leave the shipper.',
            'desc': None,
            'cta': 'Find Parking Now',
            'sub_cta': None,
            'hook': '\u201cCircled the lot three times?\u201d',
            'watermark': None,
        },
        'c': {
            'headline': 'Park safe.\nSleep easy.',
            'desc': '75+ Canadian locations \u00b7 Gated lots\nOnline booking \u00b7 Driver reviews',
            'cta': 'Find Parking',
            'sub_cta': None,
            'hook': None,
            'watermark': 'P',
        },
    }
    v = variants[variant]
    return {
        'type': 'parking',
        'variant': variant,
        'copy': copy,
        'url': 'https://parking.truckerpro.ca',
        'eyebrow': 'Truck Parking Club',
        **v,
    }


def _fmcsa_banner(stop, variant):
    variants = {
        'a': {
            'headline': '4.4 million carriers.\nOne search.',
            'desc': 'CSA scores, inspections, crash records, operating authority.',
            'cta': 'Look Up a Carrier',
            'sub_cta': None,
            'hook': None,
            'watermark': None,
        },
        'b': {
            'headline': "Check any carrier\u2019s safety\nrecord in 10 seconds.",
            'desc': None,
            'cta': 'Run a Free Check',
            'sub_cta': None,
            'hook': '\u201cWho\u2019s hauling your freight?\u201d',
            'watermark': None,
        },
        'c': {
            'headline': 'Know your\ncarrier.',
            'desc': 'CSA \u00b7 BASICs \u00b7 Inspections \u00b7 Crashes\n4.4M profiles \u00b7 Free instant lookup',
            'cta': 'Lookup Carrier',
            'sub_cta': None,
            'hook': None,
            'watermark': 'DOT',
        },
    }
    v = variants[variant]
    return {
        'type': 'fmcsa',
        'variant': variant,
        'copy': "Look up carriers at this stop",
        'url': 'https://fmcsa.truckerpro.net',
        'eyebrow': 'FMCSA Data',
        **v,
    }
