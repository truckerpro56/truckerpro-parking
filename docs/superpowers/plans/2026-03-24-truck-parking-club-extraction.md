# Truck Parking Club Extraction — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the Truck Parking Club module from truckerpro-web into a standalone SaaS at truckerpro-parking, then safely remove it from the source.

**Architecture:** Flask app factory pattern with SQLAlchemy ORM models, Stripe payments, Google Maps integration, Celery background tasks. Deployed to Railway at parking.truckerpro.ca. Two phases: build standalone app, then remove from monolith.

**Tech Stack:** Flask 2.3, SQLAlchemy 2.0, PostgreSQL 15, Redis 7, Celery, Stripe, Google Maps API, Resend, bcrypt, Flask-Login

**Spec:** `docs/superpowers/specs/2026-03-24-truck-parking-club-extraction-design.md`

**Source code reference:** `/Users/tps/projects/truckerpro-web/app/parking_club_routes.py` (1,277 lines to extract)

---

## Phase 1: Build Standalone App

All work in `/Users/tps/projects/truckerpro-parking/`.

---

### Task 1: CLAUDE.md + Constants Module

**Files:**
- Create: `CLAUDE.md`
- Create: `app/constants.py`

- [ ] **Step 1: Create CLAUDE.md**

```markdown
# CLAUDE.md — Truck Parking Club

## Overview
Standalone SaaS for Canadian truck parking directory and marketplace.
Extracted from truckerpro-web's /parkingclub module.
Domain: parking.truckerpro.ca

## Tech Stack
- Flask 2.3 / Python 3.11 / SQLAlchemy 2.0
- PostgreSQL 15 (Railway), Redis 7
- Stripe (payments), Google Maps (geo), Resend (email)
- Celery for background jobs
- Deployed on Railway via Docker

## Architecture
- Flask app factory in `app/__init__.py`
- Models in `app/models/` (User, ParkingLocation, ParkingBooking, ParkingReview, ParkingAvailability)
- API endpoints in `app/api/` (under /api/v1)
- Page routes in `app/routes/` (public, auth, owner)
- Business logic in `app/services/`
- Background tasks in `app/tasks/`

## Rules
- Use SQLAlchemy ORM queries, not raw SQL
- Use `current_app.config['KEY']` for config values, never hardcode
- Use `Decimal` for money display, store as integer cents in DB
- All rates stored in cents (e.g., daily_rate=2500 = $25.00)
- Canadian tax: GST/HST/PST/QST calculated via PROVINCIAL_TAX in constants.py
- Rate limit auth endpoints (login, signup)
- CSRF exempt the API blueprint only
```

- [ ] **Step 2: Create constants module with province/tax/amenity data**

Create `app/constants.py` — extract PROVINCE_MAP, PROVINCIAL_TAX, LOCATION_TYPE_LABELS, AMENITY_LABELS from `parking_club_routes.py` lines 24-95.

```python
# app/constants.py
"""Shared constants for Truck Parking Club."""

PROVINCE_MAP = {
    'ontario': {'name': 'Ontario', 'code': 'ON'},
    'alberta': {'name': 'Alberta', 'code': 'AB'},
    'british-columbia': {'name': 'British Columbia', 'code': 'BC'},
    'manitoba': {'name': 'Manitoba', 'code': 'MB'},
    'quebec': {'name': 'Quebec', 'code': 'QC'},
    'saskatchewan': {'name': 'Saskatchewan', 'code': 'SK'},
    'new-brunswick': {'name': 'New Brunswick', 'code': 'NB'},
    'nova-scotia': {'name': 'Nova Scotia', 'code': 'NS'},
    'prince-edward-island': {'name': 'Prince Edward Island', 'code': 'PE'},
    'newfoundland-labrador': {'name': 'Newfoundland and Labrador', 'code': 'NL'},
    'northwest-territories': {'name': 'Northwest Territories', 'code': 'NT'},
    'yukon': {'name': 'Yukon', 'code': 'YT'},
    'nunavut': {'name': 'Nunavut', 'code': 'NU'},
}

PROVINCE_CODE_TO_SLUG = {v['code']: k for k, v in PROVINCE_MAP.items()}

PROVINCIAL_TAX = {
    'AB': {'type': 'GST', 'rate': 0.05},
    'BC': {'type': 'GST+PST', 'gst': 0.05, 'pst': 0.07, 'rate': 0.12},
    'MB': {'type': 'GST+PST', 'gst': 0.05, 'pst': 0.07, 'rate': 0.12},
    'NB': {'type': 'HST', 'rate': 0.15},
    'NL': {'type': 'HST', 'rate': 0.15},
    'NS': {'type': 'HST', 'rate': 0.15},
    'NT': {'type': 'GST', 'rate': 0.05},
    'NU': {'type': 'GST', 'rate': 0.05},
    'ON': {'type': 'HST', 'rate': 0.13},
    'PE': {'type': 'HST', 'rate': 0.15},
    'QC': {'type': 'GST+QST', 'gst': 0.05, 'qst': 0.09975, 'rate': 0.14975},
    'SK': {'type': 'GST+PST', 'gst': 0.05, 'pst': 0.06, 'rate': 0.11},
    'YT': {'type': 'GST', 'rate': 0.05},
}

LOCATION_TYPE_LABELS = {
    'truck_stop': 'Truck Stop',
    'rest_area': 'Rest Area',
    'private_yard': 'Private Yard',
    'warehouse': 'Warehouse',
    'repair_shop': 'Repair Shop',
    'towing_company': 'Towing Company',
    'cdl_school': 'CDL School',
    'storage_facility': 'Storage Facility',
    'farm_property': 'Farm Property',
    'industrial_lot': 'Industrial Lot',
    'other': 'Other',
}

AMENITY_LABELS = {
    'security_camera': {'label': 'Security Camera', 'icon': 'fas fa-video'},
    '24_7_access': {'label': '24/7 Access', 'icon': 'fas fa-clock'},
    'restrooms': {'label': 'Restrooms', 'icon': 'fas fa-restroom'},
    'showers': {'label': 'Showers', 'icon': 'fas fa-shower'},
    'wifi': {'label': 'Wi-Fi', 'icon': 'fas fa-wifi'},
    'food_nearby': {'label': 'Food Nearby', 'icon': 'fas fa-utensils'},
    'restaurant_onsite': {'label': 'Restaurant On-site', 'icon': 'fas fa-burger'},
    'truck_wash': {'label': 'Truck Wash', 'icon': 'fas fa-droplet'},
    'repair_shop': {'label': 'Repair Shop', 'icon': 'fas fa-wrench'},
    'cat_scale': {'label': 'CAT Scale', 'icon': 'fas fa-weight-scale'},
    'ev_charging': {'label': 'EV Charging', 'icon': 'fas fa-bolt'},
    'block_heater_plugin': {'label': 'Block Heater Plug-in', 'icon': 'fas fa-plug'},
    'heated_facility': {'label': 'Heated Facility', 'icon': 'fas fa-temperature-high'},
    'fenced': {'label': 'Fenced', 'icon': 'fas fa-shield-halved'},
    'gated': {'label': 'Gated', 'icon': 'fas fa-door-closed'},
    'lit_lot': {'label': 'Lit Lot', 'icon': 'fas fa-lightbulb'},
    'paved': {'label': 'Paved', 'icon': 'fas fa-road'},
    'gravel': {'label': 'Gravel', 'icon': 'fas fa-mountain'},
    'snow_removal': {'label': 'Snow Removal', 'icon': 'fas fa-snowplow'},
    'fuel_nearby': {'label': 'Fuel Nearby', 'icon': 'fas fa-gas-pump'},
}
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md app/constants.py
git commit -m "Add CLAUDE.md and constants module (provinces, tax, amenities)"
```

---

### Task 2: Geo Service

**Files:**
- Create: `app/services/geo_service.py`
- Create: `tests/test_geo_service.py`

- [ ] **Step 1: Write tests for geo service**

```python
# tests/test_geo_service.py
import math

def test_haversine_same_point():
    from app.services.geo_service import haversine_distance
    assert haversine_distance(43.65, -79.38, 43.65, -79.38) == 0.0

def test_haversine_known_distance():
    from app.services.geo_service import haversine_distance
    # Toronto to Ottawa ~350-360 km
    dist = haversine_distance(43.65, -79.38, 45.42, -75.69)
    assert 340 < dist < 370

def test_slugify():
    from app.services.geo_service import slugify
    assert slugify("Flying J Travel Centre") == "flying-j-travel-centre"
    assert slugify("  Hello   World  ") == "hello-world"
    assert slugify("Test!@#$%^&*()") == "test"

def test_format_price():
    from app.services.geo_service import format_price
    assert format_price(2500) == "25.00"
    assert format_price(None) is None
    assert format_price(0) == "0.00"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_geo_service.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement geo service**

```python
# app/services/geo_service.py
"""Geocoding and distance utilities."""
import math
import re
import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km using Haversine formula."""
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return round(R * c, 1)


def geocode_address(address, city, province):
    """Geocode an address using Google Maps API. Returns (lat, lng) or (None, None)."""
    api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        return None, None
    try:
        resp = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params={
            'address': f"{address}, {city}, {province}, Canada",
            'key': api_key,
        }, timeout=10)
        data = resp.json()
        if data.get('results'):
            loc = data['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    except Exception as e:
        logger.warning("Geocoding failed: %s", str(e)[:200])
    return None, None


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def format_price(cents):
    """Format price from cents to display string."""
    if cents is None:
        return None
    return f"{cents / 100:,.2f}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_geo_service.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/services/geo_service.py tests/test_geo_service.py
git commit -m "Add geo service: haversine distance, geocoding, slugify, format_price"
```

---

### Task 3: Booking Service (Tax + Pricing)

**Files:**
- Create: `app/services/booking_service.py`
- Create: `tests/test_booking_service.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_booking_service.py
from decimal import Decimal

def test_calculate_tax_ontario():
    from app.services.booking_service import calculate_tax
    tax_amount, tax_type = calculate_tax(10000, 'ON')  # $100 subtotal
    assert tax_type == 'HST'
    assert tax_amount == 1300  # 13%

def test_calculate_tax_alberta():
    from app.services.booking_service import calculate_tax
    tax_amount, tax_type = calculate_tax(10000, 'AB')
    assert tax_type == 'GST'
    assert tax_amount == 500  # 5%

def test_calculate_tax_quebec():
    from app.services.booking_service import calculate_tax
    tax_amount, tax_type = calculate_tax(10000, 'QC')
    assert tax_type == 'GST+QST'
    assert tax_amount == 1498  # 14.975% rounded

def test_calculate_subtotal_daily():
    from app.services.booking_service import calculate_subtotal
    from datetime import datetime, timezone
    start = datetime(2026, 4, 1, 14, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 3, 14, 0, tzinfo=timezone.utc)
    subtotal = calculate_subtotal(2500, 'daily', start, end)  # $25/day × 2 days
    assert subtotal == 5000

def test_calculate_subtotal_hourly():
    from app.services.booking_service import calculate_subtotal
    from datetime import datetime, timezone
    start = datetime(2026, 4, 1, 14, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 1, 17, 30, tzinfo=timezone.utc)
    subtotal = calculate_subtotal(500, 'hourly', start, end)  # $5/hr × 4 hrs (ceil)
    assert subtotal == 2000

def test_generate_booking_ref():
    from app.services.booking_service import generate_booking_ref
    ref = generate_booking_ref()
    assert ref.startswith('TPP-2026-')
    assert len(ref) == 17  # TPP-2026-XXXXXXXX
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_booking_service.py -v`

- [ ] **Step 3: Implement booking service**

```python
# app/services/booking_service.py
"""Booking pricing, tax calculation, and availability checks."""
import math
import uuid
from datetime import datetime, timezone
from app.constants import PROVINCIAL_TAX

COMMISSION_RATE = 0.10  # 10%


def calculate_tax(subtotal_cents, province_code):
    """Calculate tax amount in cents. Returns (tax_cents, tax_type)."""
    tax_info = PROVINCIAL_TAX.get(province_code, {'rate': 0.05, 'type': 'GST'})
    tax_amount = round(subtotal_cents * tax_info['rate'])
    return tax_amount, tax_info['type']


def calculate_subtotal(rate_cents, booking_type, start_dt, end_dt):
    """Calculate subtotal in cents based on rate and duration."""
    if booking_type == 'hourly':
        hours = max(1, math.ceil((end_dt - start_dt).total_seconds() / 3600))
        return rate_cents * hours
    elif booking_type == 'daily':
        days = max(1, math.ceil((end_dt - start_dt).total_seconds() / 86400))
        return rate_cents * days
    elif booking_type == 'weekly':
        weeks = max(1, math.ceil((end_dt - start_dt).days / 7))
        return rate_cents * weeks
    else:  # monthly
        months = max(1, math.ceil((end_dt - start_dt).days / 30))
        return rate_cents * months


def calculate_commission(subtotal_cents):
    """Calculate platform commission in cents."""
    return round(subtotal_cents * COMMISSION_RATE)


def generate_booking_ref():
    """Generate unique booking reference like TPP-2026-A1B2C3D4."""
    year = datetime.now(timezone.utc).year
    suffix = uuid.uuid4().hex[:8].upper()
    return f"TPP-{year}-{suffix}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_booking_service.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add app/services/booking_service.py tests/test_booking_service.py
git commit -m "Add booking service: tax calculation, pricing, commission, booking refs"
```

---

### Task 4: Auth System

**Files:**
- Modify: `app/routes/auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Write auth tests**

```python
# tests/test_auth.py
def test_signup_page_loads(client):
    resp = client.get('/signup')
    assert resp.status_code == 200

def test_login_page_loads(client):
    resp = client.get('/login')
    assert resp.status_code == 200

def test_signup_creates_user(client, db):
    resp = client.post('/signup', data={
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'name': 'Test User',
        'role': 'driver',
    }, follow_redirects=True)
    assert resp.status_code == 200
    from app.models.user import User
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None
    assert user.name == 'Test User'

def test_signup_duplicate_email(client, db):
    client.post('/signup', data={
        'email': 'dup@example.com', 'password': 'Pass123!', 'name': 'First', 'role': 'driver',
    })
    resp = client.post('/signup', data={
        'email': 'dup@example.com', 'password': 'Pass123!', 'name': 'Second', 'role': 'driver',
    })
    assert resp.status_code in (200, 302)  # stays on page or redirects with flash

def test_login_valid_credentials(client, db):
    client.post('/signup', data={
        'email': 'login@example.com', 'password': 'Pass123!', 'name': 'Login User', 'role': 'driver',
    })
    resp = client.post('/login', data={
        'email': 'login@example.com', 'password': 'Pass123!',
    }, follow_redirects=True)
    assert resp.status_code == 200

def test_login_invalid_password(client, db):
    client.post('/signup', data={
        'email': 'bad@example.com', 'password': 'Pass123!', 'name': 'Bad', 'role': 'driver',
    })
    resp = client.post('/login', data={
        'email': 'bad@example.com', 'password': 'WrongPassword!',
    })
    assert resp.status_code in (200, 302)

def test_logout(client, db):
    client.post('/signup', data={
        'email': 'logout@example.com', 'password': 'Pass123!', 'name': 'Logout', 'role': 'driver',
    })
    client.post('/login', data={'email': 'logout@example.com', 'password': 'Pass123!'})
    resp = client.get('/logout', follow_redirects=True)
    assert resp.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_auth.py -v`

- [ ] **Step 3: Implement auth routes with POST handlers**

Rewrite `app/routes/auth.py` with full signup, login, logout:

```python
# app/routes/auth.py
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt
from . import pages_bp
from ..extensions import db, limiter
from ..models.user import User


@pages_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10/minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('pages.landing'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, is_active=True).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('pages.landing'))
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html')


@pages_bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5/minute")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('pages.landing'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()[:255]
        role = request.form.get('role', 'driver')
        if role not in ('driver', 'owner'):
            role = 'driver'
        if not email or not password or not name:
            flash('All fields are required.', 'error')
            return render_template('auth/signup.html')
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/signup.html')
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('An account with this email already exists.', 'error')
            return render_template('auth/signup.html')
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(email=email, password_hash=password_hash, name=name, role=role)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('pages.landing'))
    return render_template('auth/signup.html')


@pages_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('pages.landing'))
```

- [ ] **Step 4: Update auth templates with CSRF tokens and forms**

Update `app/templates/auth/login.html` and `app/templates/auth/signup.html` to include proper HTML forms with `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` in each form. WTF_CSRF_ENABLED is False in tests so tests pass without tokens, but production forms will 400 without them.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_auth.py -v`
Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add app/routes/auth.py app/templates/auth/ tests/test_auth.py
git commit -m "Implement auth: signup, login, logout with bcrypt + rate limiting"
```

---

### Task 5: Public Routes (Landing, Province, City, Location Detail)

**Files:**
- Modify: `app/routes/public.py`
- Create: `tests/test_public_routes.py`

Port from `parking_club_routes.py` lines 250-602 (landing, province_page, city_page, location_detail, search, list_your_space). Convert raw SQL to ORM queries. Change URL prefix from `/parkingclub/` to `/`.

- [ ] **Step 1: Write tests**

```python
# tests/test_public_routes.py
def test_landing_page(client):
    resp = client.get('/')
    assert resp.status_code == 200

def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200

def test_search_page(client):
    resp = client.get('/search')
    assert resp.status_code == 200

def test_province_page_valid(client, db):
    resp = client.get('/ontario')
    assert resp.status_code == 200

def test_province_page_invalid(client):
    resp = client.get('/fake-province')
    assert resp.status_code == 404

def test_list_your_space(client):
    resp = client.get('/list-your-space')
    assert resp.status_code == 200

def test_location_detail_not_found(client):
    resp = client.get('/location/nonexistent-slug')
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_public_routes.py -v`

- [ ] **Step 3: Implement public routes**

Rewrite `app/routes/public.py` — port all public page routes from `parking_club_routes.py`, replacing raw SQL with ORM queries and removing the `/parkingclub` prefix. Use `app.constants` for PROVINCE_MAP etc. Reference `parking_club_routes.py` lines 250-602 for exact logic.

Key routes to implement:
- `GET /` — landing page (line 251)
- `GET /search` — search results (line 312)
- `GET /list-your-space` — owner CTA page (line 392)
- `GET /location/<slug>` — location detail (line 410)
- `GET /my-bookings` — driver booking history, `@login_required` (line 797)
- `GET /<province_slug>` — province page (line 489)
- `GET /<province_slug>/<city_slug>` — city page (line 541)

- [ ] **Step 4: Copy and adapt templates from truckerpro-web**

Copy all 8 `parkingclub_*.html` templates from `/Users/tps/projects/truckerpro-web/app/templates/public/` to `/Users/tps/projects/truckerpro-parking/app/templates/public/` with renamed filenames. In each template:
- Replace `/parkingclub` URL prefix with `/`
- Replace `url_for('parking_club.XXX')` with `url_for('pages.XXX')`
- Replace `https://www.truckerpro.ca/parkingclub` canonical URLs with `https://parking.truckerpro.ca/`
- Update JSON-LD structured data to reference `parking.truckerpro.ca`

Template mapping:
- `parkingclub.html` → `landing.html` (replace existing stub)
- `parkingclub_search.html` → `search.html`
- `parkingclub_province.html` → `province.html`
- `parkingclub_city.html` → `city.html`
- `parkingclub_location.html` → `location.html`
- `parkingclub_list_space.html` → `list_space.html`
- `parkingclub_my_bookings.html` → `my_bookings.html`
- `parkingclub_owner_dashboard.html` → `owner/dashboard.html` (replace existing stub)

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_public_routes.py -v`
Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add app/routes/public.py app/templates/ tests/test_public_routes.py
git commit -m "Port public routes and templates: landing, search, province, city, location detail"
```

---

### Task 6: Locations API

**Files:**
- Modify: `app/api/locations.py`
- Create: `tests/test_api_locations.py`

Port from `parking_club_routes.py` lines 609-790 (api_locations, api_location_detail). Convert raw SQL to ORM.

- [ ] **Step 1: Write tests**

```python
# tests/test_api_locations.py
import json

def test_list_locations_empty(client):
    resp = client.get('/api/v1/locations')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 0
    assert data['locations'] == []

def test_list_locations_with_data(client, db):
    from app.models.location import ParkingLocation
    loc = ParkingLocation(
        name='Test Lot', slug='test-lot', address='123 Main St',
        city='Toronto', province='ON', latitude=43.65, longitude=-79.38,
        location_type='truck_stop', total_spots=10, is_active=True,
    )
    db.session.add(loc)
    db.session.commit()
    resp = client.get('/api/v1/locations')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['name'] == 'Test Lot'

def test_filter_by_province(client, db):
    from app.models.location import ParkingLocation
    for prov in ['ON', 'AB']:
        db.session.add(ParkingLocation(
            name=f'Lot {prov}', slug=f'lot-{prov.lower()}', address='123 St',
            city='City', province=prov, latitude=43.0, longitude=-79.0,
            is_active=True,
        ))
    db.session.commit()
    resp = client.get('/api/v1/locations?province=ON')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['locations'][0]['province'] == 'ON'

def test_get_location_detail(client, db):
    from app.models.location import ParkingLocation
    loc = ParkingLocation(
        name='Detail Lot', slug='detail-lot', address='456 Ave',
        city='Calgary', province='AB', latitude=51.05, longitude=-114.07,
        is_active=True, daily_rate=2500,
    )
    db.session.add(loc)
    db.session.commit()
    resp = client.get(f'/api/v1/locations/{loc.id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['name'] == 'Detail Lot'
    assert data['daily_rate'] == 2500

def test_get_location_not_found(client):
    resp = client.get('/api/v1/locations/99999')
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_api_locations.py -v`

- [ ] **Step 3: Implement locations API**

Rewrite `app/api/locations.py` — port from `parking_club_routes.py` lines 609-790, converting raw SQL to ORM. Support filters: province, city, type, bookable, lcv, price range, text search, geo (lat/lng/radius with Haversine), pagination, sort.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_api_locations.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/locations.py tests/test_api_locations.py
git commit -m "Port locations API: search, filter, geo, pagination, detail"
```

---

### Task 7: Bookings API + Payment Service

**Files:**
- Modify: `app/api/bookings.py`
- Create: `app/services/payment_service.py`
- Create: `app/api/stripe_webhook.py`
- Create: `tests/test_api_bookings.py`

Port from `parking_club_routes.py` lines 828-998 (create_booking, my_bookings).

- [ ] **Step 1: Write tests**

```python
# tests/test_api_bookings.py
import json

def _create_test_user(db):
    """Helper: create and return a test user."""
    from app.models.user import User
    import bcrypt
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='booker@test.com', password_hash=pw, name='Booker', role='driver')
    db.session.add(user)
    db.session.commit()
    return user

def _create_test_location(db):
    from app.models.location import ParkingLocation
    loc = ParkingLocation(
        name='Book Lot', slug='book-lot', address='789 Rd',
        city='Toronto', province='ON', latitude=43.65, longitude=-79.38,
        total_spots=10, daily_rate=2500, is_active=True, is_bookable=True,
    )
    db.session.add(loc)
    db.session.commit()
    return loc

def test_create_booking_requires_auth(client):
    resp = client.post('/api/v1/bookings', json={'location_id': 1})
    assert resp.status_code in (401, 302)  # redirect to login or 401

def test_create_booking_missing_fields(client, db):
    user = _create_test_user(db)
    client.post('/login', data={'email': 'booker@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/bookings', json={})
    assert resp.status_code == 400
```

- [ ] **Step 2: Implement payment service**

```python
# app/services/payment_service.py
"""Stripe payment integration."""
import stripe
import logging
from flask import current_app

logger = logging.getLogger(__name__)


def create_payment_intent(amount_cents, currency, customer_id, payment_method_id, description, metadata):
    """Create and confirm a Stripe PaymentIntent. Returns the PaymentIntent object."""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    return stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency,
        customer=customer_id,
        payment_method=payment_method_id,
        off_session=True,
        confirm=True,
        description=description,
        metadata=metadata,
    )


def get_or_create_customer(email, name, stripe_customer_id=None):
    """Get existing or create new Stripe customer."""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    if stripe_customer_id:
        return stripe_customer_id
    customer = stripe.Customer.create(email=email, name=name)
    return customer.id


def refund_payment(payment_intent_id):
    """Refund a payment intent."""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    return stripe.Refund.create(payment_intent=payment_intent_id)


def verify_webhook_signature(payload, sig_header):
    """Verify Stripe webhook signature. Returns the event or raises."""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET', '')
    return stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
```

- [ ] **Step 3: Implement bookings API and Stripe webhook**

Rewrite `app/api/bookings.py` — port create_booking from `parking_club_routes.py` lines 828-998. Use ORM models and `booking_service` + `payment_service`. Add `/api/v1/stripe/webhook` in `app/api/stripe_webhook.py`.

Also update `app/api/__init__.py` to import the new module:
```python
from . import locations, bookings, reviews, stripe_webhook  # noqa: E402, F401
```

- [ ] **Step 4: Run tests**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_api_bookings.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/api/bookings.py app/api/stripe_webhook.py app/api/__init__.py app/services/payment_service.py tests/test_api_bookings.py
git commit -m "Port bookings API + Stripe payment service + webhook endpoint"
```

---

### Task 8: Reviews API

**Files:**
- Modify: `app/api/reviews.py`
- Create: `tests/test_api_reviews.py`

Port from `parking_club_routes.py` lines 1001-1054 (submit_review).

- [ ] **Step 1: Write tests**

```python
# tests/test_api_reviews.py
def test_submit_review_requires_auth(client):
    resp = client.post('/api/v1/reviews', json={'booking_id': 1, 'rating': 5})
    assert resp.status_code in (401, 302)

def test_submit_review_invalid_rating(client, db):
    # Create user, login, then try invalid rating
    import bcrypt
    from app.models.user import User
    pw = bcrypt.hashpw(b'Pass123!', bcrypt.gensalt()).decode()
    user = User(email='reviewer@test.com', password_hash=pw, name='Rev', role='driver')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'reviewer@test.com', 'password': 'Pass123!'})
    resp = client.post('/api/v1/reviews', json={'booking_id': 1, 'rating': 6})
    assert resp.status_code == 400
```

- [ ] **Step 2: Implement reviews API**

Rewrite `app/api/reviews.py` — port from `parking_club_routes.py` lines 1001-1054. Use ORM models.

- [ ] **Step 3: Run tests**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_api_reviews.py -v`
Expected: 2 passed

- [ ] **Step 4: Commit**

```bash
git add app/api/reviews.py tests/test_api_reviews.py
git commit -m "Port reviews API: submit review with validation"
```

---

### Task 9: Owner Dashboard Routes

**Files:**
- Modify: `app/routes/owner.py`
- Modify: `app/api/locations.py` (add create/update listing endpoint)
- Create: `tests/test_owner_routes.py`

Port from `parking_club_routes.py` lines 1061-1277 (owner_dashboard, create_or_update_listing).

- [ ] **Step 1: Write tests**

```python
# tests/test_owner_routes.py
def test_owner_dashboard_requires_auth(client):
    resp = client.get('/owner/dashboard')
    assert resp.status_code in (302, 401)  # redirects to login

def test_create_listing_requires_auth(client):
    resp = client.post('/api/v1/locations', json={'name': 'Test'})
    assert resp.status_code in (302, 401)
```

- [ ] **Step 2: Implement owner routes**

Rewrite `app/routes/owner.py` with dashboard showing owner's locations, stats, recent bookings. Port from `parking_club_routes.py` lines 1061-1128.

Add `POST /api/v1/locations` to `app/api/locations.py` for create/update listing. Port from `parking_club_routes.py` lines 1131-1277.

- [ ] **Step 3: Run tests**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/test_owner_routes.py -v`
Expected: 2 passed

- [ ] **Step 4: Commit**

```bash
git add app/routes/owner.py app/api/locations.py tests/test_owner_routes.py
git commit -m "Port owner dashboard and create/update listing endpoint"
```

---

### Task 10: Email Service + Notification Tasks

**Files:**
- Create: `app/services/email_service.py`
- Modify: `app/tasks/notifications.py` (currently empty)

- [ ] **Step 1: Implement email service**

```python
# app/services/email_service.py
"""Transactional email via Resend."""
import logging
from flask import current_app

logger = logging.getLogger(__name__)


def send_email(to, subject, html_body):
    """Send email via Resend API."""
    api_key = current_app.config.get('RESEND_API_KEY')
    if not api_key:
        logger.warning("RESEND_API_KEY not set, skipping email to %s", to)
        return False
    try:
        import resend
        resend.api_key = api_key
        resend.Emails.send({
            'from': 'Truck Parking Club <noreply@truckerpro.ca>',
            'to': [to],
            'subject': subject,
            'html': html_body,
        })
        return True
    except Exception as e:
        logger.error("Email send failed: %s", str(e)[:200])
        return False
```

- [ ] **Step 2: Create notification Celery tasks**

```python
# app/tasks/notifications.py
"""Async notification tasks."""
from . import celery_app


@celery_app.task
def send_booking_confirmation(booking_ref, driver_email, location_name, start_dt, total_display):
    """Send booking confirmation email."""
    from app import create_app
    from app.services.email_service import send_email
    app = create_app()
    with app.app_context():
        html = f"""
        <h2>Booking Confirmed!</h2>
        <p>Your parking booking <strong>{booking_ref}</strong> at <strong>{location_name}</strong> is confirmed.</p>
        <p>Start: {start_dt}<br>Total: ${total_display} CAD</p>
        <p>— Truck Parking Club</p>
        """
        send_email(driver_email, f"Booking Confirmed: {booking_ref}", html)


@celery_app.task
def send_owner_booking_alert(owner_email, booking_ref, location_name, driver_name, start_dt):
    """Notify owner of new booking."""
    from app import create_app
    from app.services.email_service import send_email
    app = create_app()
    with app.app_context():
        html = f"""
        <h2>New Booking!</h2>
        <p>Booking <strong>{booking_ref}</strong> at <strong>{location_name}</strong> by {driver_name}.</p>
        <p>Start: {start_dt}</p>
        <p>— Truck Parking Club</p>
        """
        send_email(owner_email, f"New Booking: {booking_ref}", html)
```

- [ ] **Step 3: Commit**

```bash
git add app/services/email_service.py app/tasks/notifications.py
git commit -m "Add email service (Resend) and notification Celery tasks"
```

---

### Task 11: Seed Data

**Files:**
- Create: `app/seed/locations.py`
- Create: `app/seed/__init__.py`

- [ ] **Step 1: Port seed data from truckerpro-web**

Copy seed data from `/Users/tps/projects/truckerpro-web/app/seed_parking_data.py` and adapt to use ORM:

```python
# app/seed/__init__.py
"""Seed data management."""


# app/seed/locations.py
"""Seed parking locations. Adapted from truckerpro-web seed_parking_data.py."""
import logging
from app.extensions import db
from app.models.location import ParkingLocation
from app.services.geo_service import slugify

logger = logging.getLogger(__name__)

# Copy SEED_LOCATIONS list from /Users/tps/projects/truckerpro-web/app/seed_parking_data.py
# (the full list of Canadian truck parking locations)
SEED_LOCATIONS = [
    # ... copy from truckerpro-web/app/seed_parking_data.py SEED_LOCATIONS ...
]


def seed_locations():
    """Insert seed locations if the table is empty."""
    if ParkingLocation.query.first():
        logger.info("Locations already seeded, skipping")
        return
    for loc_data in SEED_LOCATIONS:
        slug = slugify(f"{loc_data['name']}-{loc_data['city']}")
        existing = ParkingLocation.query.filter_by(slug=slug).first()
        if existing:
            continue
        loc = ParkingLocation(
            name=loc_data['name'],
            slug=slug,
            address=loc_data['address'],
            city=loc_data['city'],
            province=loc_data['province'],
            latitude=loc_data['latitude'],
            longitude=loc_data['longitude'],
            location_type=loc_data.get('location_type', 'truck_stop'),
            total_spots=loc_data.get('total_spots', 0),
            bobtail_spots=loc_data.get('bobtail_spots', 0),
            trailer_spots=loc_data.get('trailer_spots', 0),
            oversize_spots=loc_data.get('oversize_spots', 0),
            daily_rate=loc_data.get('daily_rate'),
            monthly_rate=loc_data.get('monthly_rate'),
            amenities=loc_data.get('amenities', []),
            nearby_highways=loc_data.get('nearby_highways', []),
            is_active=True,
        )
        db.session.add(loc)
    db.session.commit()
    logger.info("Seeded %d parking locations", len(SEED_LOCATIONS))
```

- [ ] **Step 2: Add seed CLI command to app factory**

Add to `app/__init__.py` inside `create_app()`, after `db.create_all()`:

```python
@app.cli.command('seed')
def seed_command():
    """Seed the database with initial data."""
    from .seed.locations import seed_locations
    seed_locations()
    print('Seeded.')
```

- [ ] **Step 3: Commit**

```bash
git add app/seed/ app/__init__.py
git commit -m "Port seed data: Canadian truck parking locations with CLI command"
```

---

### Task 12: Run Full Test Suite + Push

- [ ] **Step 1: Run all tests**

Run: `cd /Users/tps/projects/truckerpro-parking && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Fix any failures**

Address any test failures found in Step 1.

- [ ] **Step 3: Push to GitHub**

```bash
cd /Users/tps/projects/truckerpro-parking && git push
```

---

## Phase 2: Remove from truckerpro-web

All work in `/Users/tps/projects/truckerpro-web/app/`.

**IMPORTANT:** Only start Phase 2 after deploying truckerpro-parking to Railway and completing the 48-hour burn-in period.

---

### Task 13: Create Safety Tag

- [ ] **Step 1: Tag current state**

```bash
cd /Users/tps/projects/truckerpro-web && git tag pre-parking-extraction
git push origin pre-parking-extraction
```

---

### Task 14: Atomic Removal + Redirects (ONE commit)

**Files to delete:** (10 files)
- `app/parking_club_routes.py`
- `app/seed_parking_data.py`
- `app/templates/public/parkingclub.html`
- `app/templates/public/parkingclub_search.html`
- `app/templates/public/parkingclub_province.html`
- `app/templates/public/parkingclub_city.html`
- `app/templates/public/parkingclub_location.html`
- `app/templates/public/parkingclub_list_space.html`
- `app/templates/public/parkingclub_my_bookings.html`
- `app/templates/public/parkingclub_owner_dashboard.html`

**Files to edit:** (7 files)
- `app/app_full.py` — remove lines 26, ~6394-6408, 7605, 7607-7618
- `app/public_page_routes.py` — remove lines 709-728, add 301 redirect blueprint
- `app/templates/partials/_tools_navbar.html` — update link to parking.truckerpro.ca
- `app/templates/landing_driver.html` — update link to parking.truckerpro.ca
- `app/templates/landing_company.html` — update links to parking.truckerpro.ca
- `app/static/robots.txt` — remove `Allow: /parking-club` line
- `app/tests/load/locustfile.py` — remove parking test methods

- [ ] **Step 1: Create redirect blueprint**

Create `app/parking_redirects.py` as a Blueprint (truckerpro-web uses Blueprint pattern, not bare `@app.route`):

```python
# app/parking_redirects.py
"""301 redirects for extracted Truck Parking Club → parking.truckerpro.ca"""
from flask import Blueprint, redirect

parking_redirects_bp = Blueprint('parking_redirects', __name__)

@parking_redirects_bp.route('/parkingclub')
@parking_redirects_bp.route('/parkingclub/')
def parking_redirect_landing():
    return redirect('https://parking.truckerpro.ca/', 301)

@parking_redirects_bp.route('/parkingclub/search')
def parking_redirect_search():
    return redirect('https://parking.truckerpro.ca/search', 301)

@parking_redirects_bp.route('/parkingclub/list-your-space')
def parking_redirect_list():
    return redirect('https://parking.truckerpro.ca/list-your-space', 301)

@parking_redirects_bp.route('/parkingclub/my-bookings')
def parking_redirect_bookings():
    return redirect('https://parking.truckerpro.ca/my-bookings', 301)

@parking_redirects_bp.route('/parkingclub/owner/dashboard')
def parking_redirect_owner():
    return redirect('https://parking.truckerpro.ca/owner/dashboard', 301)

@parking_redirects_bp.route('/parkingclub/location/<slug>')
def parking_redirect_location(slug):
    return redirect(f'https://parking.truckerpro.ca/location/{slug}', 301)

@parking_redirects_bp.route('/parkingclub/<province>')
def parking_redirect_province(province):
    return redirect(f'https://parking.truckerpro.ca/{province}', 301)

@parking_redirects_bp.route('/parkingclub/<province>/<city>')
def parking_redirect_city(province, city):
    return redirect(f'https://parking.truckerpro.ca/{province}/{city}', 301)
```

Then in `app/app_full.py`, replace the old `parking_club_bp` import+register with:
```python
from parking_redirects import parking_redirects_bp
app.register_blueprint(parking_redirects_bp)
```

- [ ] **Step 2: Delete all parking files**

```bash
cd /Users/tps/projects/truckerpro-web/app
rm parking_club_routes.py seed_parking_data.py
rm templates/public/parkingclub.html templates/public/parkingclub_search.html
rm templates/public/parkingclub_province.html templates/public/parkingclub_city.html
rm templates/public/parkingclub_location.html templates/public/parkingclub_list_space.html
rm templates/public/parkingclub_my_bookings.html templates/public/parkingclub_owner_dashboard.html
```

- [ ] **Step 3: Edit app_full.py — remove all parking references**

Remove:
- Line 26: `from parking_club_routes import parking_club_bp`
- Lines ~6394-6408: auto-seed block for parking data
- Line 7605: `app.register_blueprint(parking_club_bp)`
- Lines 7607-7618: CSRF exemption + rate limiter imports for parking

- [ ] **Step 4: Edit public_page_routes.py — remove parking sitemap**

Remove lines 709-728 (parking sitemap entries + the `from parking_club_routes import` + DB query).

- [ ] **Step 5: Update template links to external**

In `_tools_navbar.html`, `landing_driver.html`, `landing_company.html`: replace `/parkingclub` links with `https://parking.truckerpro.ca`.

- [ ] **Step 6: Remove robots.txt parking line and locustfile parking tests**

- [ ] **Step 7: Test truckerpro-web starts without errors**

```bash
cd /Users/tps/projects/truckerpro-web/app && python -c "from app_full import app; print('OK')"
```

- [ ] **Step 8: Commit as ONE atomic commit**

```bash
cd /Users/tps/projects/truckerpro-web
git add -A
git commit -m "Extract Truck Parking Club to standalone SaaS at parking.truckerpro.ca

- Remove parking_club_routes.py and all parkingclub templates
- Remove seed_parking_data.py
- Remove parking references from app_full.py (import, blueprint, auto-seed, CSRF)
- Remove parking sitemap entries from public_page_routes.py
- Add 301 redirects: /parkingclub/* → parking.truckerpro.ca/*
- Update nav/landing links to external parking.truckerpro.ca
- Remove parking load tests from locustfile

Standalone app: https://github.com/truckerpro56/truckerpro-parking"
```

---

### Task 15: Drop Parking Tables (after stability confirmed)

**Files:**
- Create: `app/migrations/087_drop_parking_tables.py` (in truckerpro-web)

- [ ] **Step 1: Verify truckerpro-web is stable after removal deploy**

Wait for successful deploy, check `/health` and `/ready` endpoints.

- [ ] **Step 2: Backup parking tables before dropping**

```bash
# Connect to Railway PostgreSQL and export parking tables
pg_dump "$DATABASE_URL" --table=parking_locations --table=parking_bookings --table=parking_reviews --table=parking_availability > parking_tables_backup_$(date +%Y%m%d).sql
```

- [ ] **Step 3: Create drop migration**

```python
# app/migrations/087_drop_parking_tables.py
"""Drop parking club tables — module extracted to standalone app at parking.truckerpro.ca"""
import logging
logger = logging.getLogger(__name__)

def up(conn):
    cur = conn.cursor()
    for table in ['parking_availability', 'parking_reviews', 'parking_bookings', 'parking_locations']:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        logger.info("Dropped table %s", table)
    conn.commit()
    cur.close()
```

- [ ] **Step 4: Commit and push**

```bash
git add app/migrations/087_drop_parking_tables.py
git commit -m "Add migration 087: drop parking tables (extracted to standalone app)"
```

---

## Summary

| Phase | Tasks | What Happens |
|-------|-------|--------------|
| Phase 1 (Tasks 1-12) | Build standalone app | Full working Truck Parking Club at truckerpro-parking |
| Burn-in | 48+ hours | Verify standalone app works at parking.truckerpro.ca |
| Phase 2 (Tasks 13-15) | Remove from monolith | Clean removal with 301 redirects + table drop |
