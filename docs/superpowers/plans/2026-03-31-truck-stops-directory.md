# Truck Stops Directory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a truck stop directory at stops.truckerpro.net to the existing Parking Club Flask app using host-based routing, 4 new DB models, CSV import pipeline, driver contributions, smart banners, and SEO directory pages.

**Architecture:** Host-based routing middleware in the existing Parking Club app (`truckerpro-parking`). `request.host` determines which blueprints handle requests. New `stops_public_bp` and `stops_api_bp` blueprints serve stops.truckerpro.net. Truck stop data lives in Parking Club's Postgres via 4 new SQLAlchemy models.

**Tech Stack:** Flask 2.3, SQLAlchemy 2.0, PostgreSQL, Jinja2 templates, existing geo_service.py for haversine/geocoding/slugify.

**Spec:** `docs/superpowers/specs/2026-03-31-truck-stops-directory-design.md`

---

## File Structure

### New Files

```
app/
├── middleware.py                          — Host-based routing (before_request, site_required decorator)
├── models/
│   ├── truck_stop.py                     — TruckStop model
│   ├── fuel_price.py                     — FuelPrice model
│   ├── truck_stop_review.py              — TruckStopReview model
│   └── truck_stop_report.py              — TruckStopReport model
├── services/
│   ├── banner_service.py                 — Smart contextual banners
│   └── border_crossings.py              — Border crossing coordinates + distance computation
├── stops/
│   ├── __init__.py                       — stops_public_bp blueprint
│   ├── routes.py                         — All public page routes for stops.truckerpro.net
│   └── helpers.py                        — Serializers, template helpers
├── stops_api/
│   ├── __init__.py                       — stops_api_bp blueprint
│   ├── truck_stops.py                    — CRUD + search endpoints
│   ├── contributions.py                  — Fuel prices, reviews, reports endpoints
│   └── admin.py                          — Admin import/manage endpoints
├── import/
│   ├── __init__.py                       — CLI command registration
│   ├── loves.py                          — Loves CSV column mapper
│   └── base.py                           — Shared import logic (upsert, geocode, slug, border distance)
├── templates/stops/
│   ├── base.html                         — Base layout for stops.truckerpro.net
│   ├── home.html                         — Homepage
│   ├── country.html                      — US / Canada overview
│   ├── state.html                        — State/province page
│   ├── city.html                         — City page
│   ├── stop_detail.html                  — Individual truck stop page
│   ├── brand_index.html                  — All brands overview
│   ├── brand_detail.html                 — Single brand, all locations
│   ├── brand_state.html                  — Brand + state filtered
│   ├── highway_index.html                — All highways overview
│   ├── highway_detail.html               — Single highway, all stops
│   └── partials/
│       ├── banner_tms.html               — TMS banner partial
│       ├── banner_border.html            — Border banner partial
│       ├── banner_parking.html           — Parking Club banner partial
│       ├── banner_fmcsa.html             — FMCSA banner partial
│       ├── stop_card.html                — Truck stop card for listings
│       ├── amenities_grid.html           — Amenities display grid
│       ├── fuel_prices.html              — Fuel price display
│       └── pagination.html               — Pagination controls
└── static/stops/
    └── css/
        └── stops.css                     — Stops-specific styles

tests/
├── test_middleware.py                    — Host routing tests
├── test_truck_stop_model.py             — TruckStop model tests
├── test_stops_api.py                    — Truck stops API tests
├── test_contributions_api.py            — Fuel prices, reviews, reports API tests
├── test_stops_routes.py                 — Public page route tests
├── test_banner_service.py               — Banner logic tests
├── test_import.py                       — CSV import tests
└── test_sitemap_stops.py                — Sitemap tests
```

### Modified Files

```
app/__init__.py                           — Register middleware, new blueprints, new CLI commands
app/config.py                             — Add STOPS_DOMAIN, PARKING_DOMAIN config vars
app/constants.py                          — Add US_STATES, BRAND_MAP, TRUCK_STOP_AMENITY_LABELS
tests/conftest.py                         — Add stops_client fixture (host header for stops domain)
```

---

### Task 1: Host-Based Routing Middleware

**Files:**
- Create: `app/middleware.py`
- Modify: `app/__init__.py`
- Modify: `app/config.py`
- Create: `tests/test_middleware.py`

- [ ] **Step 1: Write failing tests for middleware**

Create `tests/test_middleware.py`:

```python
"""Tests for host-based routing middleware."""
from flask import g


def test_parking_domain_sets_site_parking(app, client):
    """Request to parking domain sets g.site = 'parking'."""
    with app.test_request_context('/', headers={'Host': 'parking.truckerpro.ca'}):
        app.preprocess_request()
        assert g.site == 'parking'


def test_stops_domain_sets_site_stops(app, client):
    """Request to stops domain sets g.site = 'stops'."""
    with app.test_request_context('/', headers={'Host': 'stops.truckerpro.net'}):
        app.preprocess_request()
        assert g.site == 'stops'


def test_localhost_defaults_to_parking(app, client):
    """Localhost defaults to parking site."""
    with app.test_request_context('/', headers={'Host': 'localhost'}):
        app.preprocess_request()
        assert g.site == 'parking'


def test_health_works_on_any_domain(client):
    """Health check works regardless of domain."""
    resp = client.get('/health')
    assert resp.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_middleware.py -v`
Expected: FAIL — `g.site` not set

- [ ] **Step 3: Add domain config vars**

In `app/config.py`, add to the `Config` class after `RATELIMIT_STORAGE_URI`:

```python
    STOPS_DOMAIN = os.environ.get('STOPS_DOMAIN', 'stops.truckerpro.net')
    PARKING_DOMAIN = os.environ.get('PARKING_DOMAIN', 'parking.truckerpro.ca')
```

Add to `TestConfig` after `RATELIMIT_ENABLED`:

```python
    STOPS_DOMAIN = 'stops.localhost'
    PARKING_DOMAIN = 'localhost'
```

- [ ] **Step 4: Create middleware module**

Create `app/middleware.py`:

```python
"""Host-based routing middleware for multi-domain support."""
from functools import wraps
from flask import request, g, abort, current_app


def init_host_routing(app):
    """Register before_request handler that sets g.site based on Host header."""

    @app.before_request
    def set_site_from_host():
        host = request.host.split(':')[0]  # strip port
        stops_domain = current_app.config.get('STOPS_DOMAIN', 'stops.truckerpro.net')
        if host == stops_domain or host == 'stops.localhost':
            g.site = 'stops'
        else:
            g.site = 'parking'


def site_required(site_name):
    """Decorator that returns 404 if g.site doesn't match."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if getattr(g, 'site', 'parking') != site_name:
                abort(404)
            return f(*args, **kwargs)
        return wrapped
    return decorator
```

- [ ] **Step 5: Register middleware in app factory**

In `app/__init__.py`, add import at top with other imports:

```python
from .middleware import init_host_routing
```

Add after `login_manager.init_app(app)` and before blueprint registration:

```python
    init_host_routing(app)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_middleware.py -v`
Expected: All 4 PASS

- [ ] **Step 7: Run full test suite to verify no regressions**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/ -v`
Expected: All 84 existing + 4 new = 88 PASS

- [ ] **Step 8: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/middleware.py app/__init__.py app/config.py tests/test_middleware.py
git commit -m "feat: add host-based routing middleware for multi-domain support"
```

---

### Task 2: TruckStop Model

**Files:**
- Create: `app/models/truck_stop.py`
- Create: `tests/test_truck_stop_model.py`

- [ ] **Step 1: Write failing tests for TruckStop model**

Create `tests/test_truck_stop_model.py`:

```python
"""Tests for TruckStop model."""
from app.models.truck_stop import TruckStop


def test_create_truck_stop(db):
    stop = TruckStop(
        brand='loves',
        brand_display_name="Love's Travel Stops",
        name="Love's Travel Stop #521",
        slug='loves-521-dallas-tx',
        store_number='521',
        address='1234 I-35 Frontage Rd',
        city='Dallas',
        state_province='TX',
        postal_code='75201',
        country='US',
        latitude=32.7767,
        longitude=-96.7970,
        highway='I-35',
        exit_number='42',
        total_parking_spots=150,
        truck_spots=120,
        has_diesel=True,
        has_showers=True,
        shower_count=8,
        has_scale=True,
        scale_type='cat',
        data_source='csv_import',
    )
    db.session.add(stop)
    db.session.commit()
    assert stop.id is not None
    assert stop.brand == 'loves'
    assert stop.is_active is True
    assert stop.is_verified is False


def test_truck_stop_slug_unique(db):
    import pytest
    from sqlalchemy.exc import IntegrityError
    s1 = TruckStop(
        brand='loves', name='Stop 1', slug='same-slug',
        address='123 St', city='Dallas', state_province='TX',
        country='US', latitude=32.0, longitude=-96.0,
        data_source='manual',
    )
    s2 = TruckStop(
        brand='loves', name='Stop 2', slug='same-slug',
        address='456 St', city='Dallas', state_province='TX',
        country='US', latitude=32.1, longitude=-96.1,
        data_source='manual',
    )
    db.session.add(s1)
    db.session.commit()
    db.session.add(s2)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_truck_stop_json_fields(db):
    stop = TruckStop(
        brand='pilot_flying_j', name='Pilot #18', slug='pilot-18-toronto-on',
        address='401 Hwy', city='Toronto', state_province='ON',
        country='CA', latitude=43.65, longitude=-79.38,
        restaurants=['Subway', "Denny's"],
        loyalty_programs=['myRewards'],
        hours_of_operation={'mon': '24h', 'tue': '24h'},
        data_source='csv_import',
    )
    db.session.add(stop)
    db.session.commit()
    fetched = TruckStop.query.get(stop.id)
    assert fetched.restaurants == ['Subway', "Denny's"]
    assert fetched.hours_of_operation['mon'] == '24h'


def test_truck_stop_defaults(db):
    stop = TruckStop(
        brand='independent', name='Joes Stop', slug='joes-stop',
        address='Rte 1', city='Smalltown', state_province='ME',
        country='US', latitude=44.0, longitude=-69.0,
        data_source='manual',
    )
    db.session.add(stop)
    db.session.commit()
    assert stop.has_diesel is True
    assert stop.has_gas is False
    assert stop.has_def is False
    assert stop.has_ev_charging is False
    assert stop.has_showers is False
    assert stop.has_scale is False
    assert stop.has_repair is False
    assert stop.has_tire_service is False
    assert stop.has_wifi is False
    assert stop.has_laundry is False
    assert stop.is_active is True
    assert stop.is_verified is False


def test_truck_stop_parking_location_link(db):
    from app.models.location import ParkingLocation
    loc = ParkingLocation(
        name='Parking Lot', slug='parking-lot', address='123 St',
        city='Toronto', province='ON', latitude=43.65, longitude=-79.38,
        is_active=True,
    )
    db.session.add(loc)
    db.session.commit()
    stop = TruckStop(
        brand='loves', name='Loves Toronto', slug='loves-toronto',
        address='456 St', city='Toronto', state_province='ON',
        country='CA', latitude=43.65, longitude=-79.38,
        parking_location_id=loc.id, data_source='manual',
    )
    db.session.add(stop)
    db.session.commit()
    assert stop.parking_location_id == loc.id
    assert stop.parking_location.name == 'Parking Lot'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_truck_stop_model.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Create TruckStop model**

Create `app/models/truck_stop.py`:

```python
"""TruckStop model — core location data for truck stops directory."""
from datetime import datetime, timezone
from ..extensions import db


class TruckStop(db.Model):
    __tablename__ = 'truck_stops'

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False, index=True)
    brand_display_name = db.Column(db.String(100))
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    store_number = db.Column(db.String(50))
    address = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    state_province = db.Column(db.String(50), nullable=False, index=True)
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(2), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    highway = db.Column(db.String(50), index=True)
    exit_number = db.Column(db.String(20))
    direction = db.Column(db.String(2))

    # Parking
    total_parking_spots = db.Column(db.Integer)
    truck_spots = db.Column(db.Integer)
    car_spots = db.Column(db.Integer)
    handicap_spots = db.Column(db.Integer)
    reserved_spots = db.Column(db.Integer)

    # Amenities
    has_diesel = db.Column(db.Boolean, default=True)
    has_gas = db.Column(db.Boolean, default=False)
    has_def = db.Column(db.Boolean, default=False)
    has_ev_charging = db.Column(db.Boolean, default=False)
    has_showers = db.Column(db.Boolean, default=False)
    shower_count = db.Column(db.Integer)
    has_scale = db.Column(db.Boolean, default=False)
    scale_type = db.Column(db.String(20))
    has_repair = db.Column(db.Boolean, default=False)
    has_tire_service = db.Column(db.Boolean, default=False)
    has_wifi = db.Column(db.Boolean, default=False)
    has_laundry = db.Column(db.Boolean, default=False)

    # Details
    restaurants = db.Column(db.JSON, default=list)
    loyalty_programs = db.Column(db.JSON, default=list)
    hours_of_operation = db.Column(db.JSON, default=dict)
    phone = db.Column(db.String(20))
    website = db.Column(db.String(300))
    photos = db.Column(db.JSON, default=list)

    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_verified = db.Column(db.Boolean, default=False)

    # Border
    nearest_border_crossing = db.Column(db.String(100))
    border_distance_km = db.Column(db.Float)

    # Links
    parking_location_id = db.Column(
        db.Integer, db.ForeignKey('parking_locations.id'), nullable=True
    )
    parking_location = db.relationship('ParkingLocation', backref='truck_stops')

    # SEO
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.String(500))

    # Metadata
    data_source = db.Column(db.String(20), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    fuel_prices = db.relationship('FuelPrice', backref='truck_stop', lazy='dynamic')
    reviews = db.relationship('TruckStopReview', backref='truck_stop', lazy='dynamic')
    reports = db.relationship('TruckStopReport', backref='truck_stop', lazy='dynamic')

    __table_args__ = (
        db.Index('idx_truck_stops_coords', 'latitude', 'longitude'),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_truck_stop_model.py -v`
Expected: All 5 PASS

- [ ] **Step 5: Run full suite**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/ -v`
Expected: All PASS (no regressions)

- [ ] **Step 6: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/models/truck_stop.py tests/test_truck_stop_model.py
git commit -m "feat: add TruckStop model with all fields and indexes"
```

---

### Task 3: FuelPrice, TruckStopReview, TruckStopReport Models

**Files:**
- Create: `app/models/fuel_price.py`
- Create: `app/models/truck_stop_review.py`
- Create: `app/models/truck_stop_report.py`
- Create: `tests/test_contribution_models.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_contribution_models.py`:

```python
"""Tests for FuelPrice, TruckStopReview, TruckStopReport models."""
import pytest
from datetime import datetime, timezone, timedelta
from app.models.truck_stop import TruckStop
from app.models.fuel_price import FuelPrice
from app.models.truck_stop_review import TruckStopReview
from app.models.truck_stop_report import TruckStopReport
from app.models.user import User
import bcrypt


def _make_stop(db):
    stop = TruckStop(
        brand='loves', name='Test Stop', slug='test-stop-contrib',
        address='123 St', city='Dallas', state_province='TX',
        country='US', latitude=32.0, longitude=-96.0, data_source='manual',
    )
    db.session.add(stop)
    db.session.commit()
    return stop


def _make_user(db, email='driver@test.com'):
    pw = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode('utf-8')
    user = User(email=email, password_hash=pw, name='Test Driver', role='driver')
    db.session.add(user)
    db.session.commit()
    return user


def test_create_fuel_price(db):
    stop = _make_stop(db)
    fp = FuelPrice(
        truck_stop_id=stop.id, fuel_type='diesel',
        price_cents=345, currency='USD', source='driver',
    )
    db.session.add(fp)
    db.session.commit()
    assert fp.id is not None
    assert fp.is_verified is False


def test_fuel_price_with_reporter(db):
    stop = _make_stop(db)
    user = _make_user(db)
    fp = FuelPrice(
        truck_stop_id=stop.id, fuel_type='diesel',
        price_cents=350, currency='USD',
        source='driver', reported_by=user.id,
    )
    db.session.add(fp)
    db.session.commit()
    assert fp.reported_by == user.id


def test_create_review(db):
    stop = _make_stop(db)
    user = _make_user(db)
    review = TruckStopReview(
        truck_stop_id=stop.id, user_id=user.id,
        rating=4, review_text='Clean showers, good food.',
    )
    db.session.add(review)
    db.session.commit()
    assert review.id is not None
    assert review.is_approved is False


def test_review_rating_constraint(db):
    from sqlalchemy.exc import IntegrityError
    stop = _make_stop(db)
    user = _make_user(db)
    review = TruckStopReview(
        truck_stop_id=stop.id, user_id=user.id,
        rating=6, review_text='Invalid rating',
    )
    db.session.add(review)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_review_unique_per_user_per_stop(db):
    from sqlalchemy.exc import IntegrityError
    stop = _make_stop(db)
    user = _make_user(db)
    r1 = TruckStopReview(
        truck_stop_id=stop.id, user_id=user.id,
        rating=4, review_text='First review',
    )
    db.session.add(r1)
    db.session.commit()
    r2 = TruckStopReview(
        truck_stop_id=stop.id, user_id=user.id,
        rating=5, review_text='Second review',
    )
    db.session.add(r2)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_create_report(db):
    stop = _make_stop(db)
    user = _make_user(db)
    report = TruckStopReport(
        truck_stop_id=stop.id, user_id=user.id,
        report_type='parking_availability',
        data={'available_spots': 12},
        expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
    )
    db.session.add(report)
    db.session.commit()
    assert report.id is not None
    assert report.is_verified is False
    assert report.data['available_spots'] == 12
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_contribution_models.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Create FuelPrice model**

Create `app/models/fuel_price.py`:

```python
"""FuelPrice model — timestamped fuel price data."""
from datetime import datetime, timezone
from ..extensions import db


class FuelPrice(db.Model):
    __tablename__ = 'fuel_prices'

    id = db.Column(db.Integer, primary_key=True)
    truck_stop_id = db.Column(
        db.Integer, db.ForeignKey('truck_stops.id'), nullable=False, index=True
    )
    fuel_type = db.Column(db.String(20), nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    source = db.Column(db.String(20), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
```

- [ ] **Step 4: Create TruckStopReview model**

Create `app/models/truck_stop_review.py`:

```python
"""TruckStopReview model — driver reviews with moderation."""
from datetime import datetime, timezone
from ..extensions import db


class TruckStopReview(db.Model):
    __tablename__ = 'truck_stop_reviews'

    id = db.Column(db.Integer, primary_key=True)
    truck_stop_id = db.Column(
        db.Integer, db.ForeignKey('truck_stops.id'), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)
    photos = db.Column(db.JSON, default=list)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_ts_review_rating'),
        db.UniqueConstraint('truck_stop_id', 'user_id', name='uq_ts_review_user_stop'),
    )
```

- [ ] **Step 5: Create TruckStopReport model**

Create `app/models/truck_stop_report.py`:

```python
"""TruckStopReport model — driver-contributed updates."""
from datetime import datetime, timezone
from ..extensions import db


class TruckStopReport(db.Model):
    __tablename__ = 'truck_stop_reports'

    id = db.Column(db.Integer, primary_key=True)
    truck_stop_id = db.Column(
        db.Integer, db.ForeignKey('truck_stops.id'), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_type = db.Column(db.String(30), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_contribution_models.py -v`
Expected: All 7 PASS

- [ ] **Step 7: Run full suite**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/models/fuel_price.py app/models/truck_stop_review.py app/models/truck_stop_report.py tests/test_contribution_models.py
git commit -m "feat: add FuelPrice, TruckStopReview, TruckStopReport models"
```

---

### Task 4: Constants — US States, Brands, Truck Stop Amenities

**Files:**
- Modify: `app/constants.py`

- [ ] **Step 1: Add US_STATES, BRAND_MAP, and border crossings constants**

Append to `app/constants.py`:

```python

# ── Truck Stops Directory ────────────────────────────────────

US_STATES = {
    'alabama': {'name': 'Alabama', 'code': 'AL'},
    'alaska': {'name': 'Alaska', 'code': 'AK'},
    'arizona': {'name': 'Arizona', 'code': 'AZ'},
    'arkansas': {'name': 'Arkansas', 'code': 'AR'},
    'california': {'name': 'California', 'code': 'CA'},
    'colorado': {'name': 'Colorado', 'code': 'CO'},
    'connecticut': {'name': 'Connecticut', 'code': 'CT'},
    'delaware': {'name': 'Delaware', 'code': 'DE'},
    'florida': {'name': 'Florida', 'code': 'FL'},
    'georgia': {'name': 'Georgia', 'code': 'GA'},
    'hawaii': {'name': 'Hawaii', 'code': 'HI'},
    'idaho': {'name': 'Idaho', 'code': 'ID'},
    'illinois': {'name': 'Illinois', 'code': 'IL'},
    'indiana': {'name': 'Indiana', 'code': 'IN'},
    'iowa': {'name': 'Iowa', 'code': 'IA'},
    'kansas': {'name': 'Kansas', 'code': 'KS'},
    'kentucky': {'name': 'Kentucky', 'code': 'KY'},
    'louisiana': {'name': 'Louisiana', 'code': 'LA'},
    'maine': {'name': 'Maine', 'code': 'ME'},
    'maryland': {'name': 'Maryland', 'code': 'MD'},
    'massachusetts': {'name': 'Massachusetts', 'code': 'MA'},
    'michigan': {'name': 'Michigan', 'code': 'MI'},
    'minnesota': {'name': 'Minnesota', 'code': 'MN'},
    'mississippi': {'name': 'Mississippi', 'code': 'MS'},
    'missouri': {'name': 'Missouri', 'code': 'MO'},
    'montana': {'name': 'Montana', 'code': 'MT'},
    'nebraska': {'name': 'Nebraska', 'code': 'NE'},
    'nevada': {'name': 'Nevada', 'code': 'NV'},
    'new-hampshire': {'name': 'New Hampshire', 'code': 'NH'},
    'new-jersey': {'name': 'New Jersey', 'code': 'NJ'},
    'new-mexico': {'name': 'New Mexico', 'code': 'NM'},
    'new-york': {'name': 'New York', 'code': 'NY'},
    'north-carolina': {'name': 'North Carolina', 'code': 'NC'},
    'north-dakota': {'name': 'North Dakota', 'code': 'ND'},
    'ohio': {'name': 'Ohio', 'code': 'OH'},
    'oklahoma': {'name': 'Oklahoma', 'code': 'OK'},
    'oregon': {'name': 'Oregon', 'code': 'OR'},
    'pennsylvania': {'name': 'Pennsylvania', 'code': 'PA'},
    'rhode-island': {'name': 'Rhode Island', 'code': 'RI'},
    'south-carolina': {'name': 'South Carolina', 'code': 'SC'},
    'south-dakota': {'name': 'South Dakota', 'code': 'SD'},
    'tennessee': {'name': 'Tennessee', 'code': 'TN'},
    'texas': {'name': 'Texas', 'code': 'TX'},
    'utah': {'name': 'Utah', 'code': 'UT'},
    'vermont': {'name': 'Vermont', 'code': 'VT'},
    'virginia': {'name': 'Virginia', 'code': 'VA'},
    'washington': {'name': 'Washington', 'code': 'WA'},
    'west-virginia': {'name': 'West Virginia', 'code': 'WV'},
    'wisconsin': {'name': 'Wisconsin', 'code': 'WI'},
    'wyoming': {'name': 'Wyoming', 'code': 'WY'},
}

US_STATE_CODE_TO_SLUG = {v['code']: k for k, v in US_STATES.items()}

# Combined lookup: works for both US states and Canadian provinces
ALL_REGIONS = {**US_STATES, **PROVINCE_MAP}
ALL_REGION_CODE_TO_SLUG = {**US_STATE_CODE_TO_SLUG, **PROVINCE_CODE_TO_SLUG}

BRAND_MAP = {
    'loves': {'name': "Love's Travel Stops", 'slug': 'loves'},
    'pilot_flying_j': {'name': 'Pilot Flying J', 'slug': 'pilot-flying-j'},
    'ta_petro': {'name': 'TA / Petro', 'slug': 'ta-petro'},
    'flying_j': {'name': 'Flying J', 'slug': 'flying-j'},
    'petro': {'name': 'Petro Stopping Centers', 'slug': 'petro'},
    'ambest': {'name': 'Ambest', 'slug': 'ambest'},
    'husky': {'name': 'Husky', 'slug': 'husky'},
    'esso': {'name': 'Esso', 'slug': 'esso'},
    'shell': {'name': 'Shell', 'slug': 'shell'},
    'independent': {'name': 'Independent', 'slug': 'independent'},
}

BRAND_SLUG_TO_KEY = {v['slug']: k for k, v in BRAND_MAP.items()}

MAJOR_FREIGHT_CORRIDORS = [
    'I-95', 'I-90', 'I-80', 'I-75', 'I-70', 'I-65', 'I-55', 'I-45',
    'I-40', 'I-35', 'I-30', 'I-25', 'I-20', 'I-15', 'I-10', 'I-5',
    '401', '400', 'QEW', 'Trans-Canada',
]

MAJOR_METROS = [
    'New York', 'Los Angeles', 'Chicago', 'Houston', 'Dallas', 'Atlanta',
    'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Memphis',
    'Nashville', 'Indianapolis', 'Louisville', 'Columbus', 'Charlotte',
    'Toronto', 'Montreal', 'Vancouver', 'Calgary', 'Edmonton', 'Winnipeg',
]
```

- [ ] **Step 2: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/constants.py
git commit -m "feat: add US states, brand map, freight corridors, metro constants"
```

---

### Task 5: Border Crossings Data + Distance Service

**Files:**
- Create: `app/services/border_crossings.py`
- Create: `tests/test_border_crossings.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_border_crossings.py`:

```python
"""Tests for border crossing distance computation."""
from app.services.border_crossings import (
    BORDER_CROSSINGS, find_nearest_crossing, compute_border_distance,
)


def test_border_crossings_populated():
    assert len(BORDER_CROSSINGS) > 50


def test_find_nearest_crossing_buffalo():
    """Buffalo NY is near Peace Bridge."""
    name, dist = find_nearest_crossing(42.8864, -78.8784)
    assert 'Peace Bridge' in name
    assert dist < 10


def test_find_nearest_crossing_detroit():
    """Detroit MI is near Ambassador Bridge."""
    name, dist = find_nearest_crossing(42.3314, -83.0458)
    assert 'Ambassador' in name or 'Detroit' in name
    assert dist < 15


def test_find_nearest_crossing_far_away():
    """Dallas TX is far from any crossing."""
    name, dist = find_nearest_crossing(32.7767, -96.7970)
    assert dist > 500


def test_compute_border_distance_on_stop(db):
    from app.models.truck_stop import TruckStop
    stop = TruckStop(
        brand='loves', name='Loves Buffalo', slug='loves-buffalo',
        address='123 St', city='Buffalo', state_province='NY',
        country='US', latitude=42.8864, longitude=-78.8784,
        data_source='manual',
    )
    db.session.add(stop)
    db.session.commit()
    compute_border_distance(stop)
    db.session.commit()
    assert stop.nearest_border_crossing is not None
    assert stop.border_distance_km < 10
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_border_crossings.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Create border crossings module**

Create `app/services/border_crossings.py`:

```python
"""US-Canada border crossing coordinates and distance computation."""
from ..services.geo_service import haversine_distance

# Major US-Canada border crossings: (name, latitude, longitude)
BORDER_CROSSINGS = [
    # BC / Washington
    ('Pacific Highway (Surrey/Blaine)', 49.0024, -122.7571),
    ('Douglas (Surrey/Blaine)', 49.0024, -122.7543),
    ('Aldergrove (Langley/Lynden)', 49.0003, -122.4637),
    ('Huntingdon (Abbotsford/Sumas)', 49.0017, -122.2648),
    ('Osoyoos (Osoyoos/Oroville)', 49.0000, -119.4382),
    ('Kingsgate (Kingsgate/Eastport)', 49.0002, -116.1815),
    ('Boundary Bay (Delta/Point Roberts)', 49.0015, -123.0569),
    # AB / Montana
    ('Coutts (Coutts/Sweetgrass)', 49.0000, -111.9614),
    ('Carway (Carway/Piegan)', 49.0000, -113.3944),
    ('Chief Mountain (Waterton/Babb)', 49.0000, -113.6600),
    # SK / Montana / North Dakota
    ('North Portal (North Portal/Portal)', 49.0000, -102.5530),
    ('Regway (Regway/Raymond)', 49.0000, -104.6036),
    # MB / North Dakota / Minnesota
    ('Emerson (Emerson/Pembina)', 49.0006, -97.2384),
    ('Boissevain (Boissevain/Dunseith)', 49.0000, -100.0574),
    ('Sprague (Sprague/Lancaster)', 49.0000, -95.5903),
    # ON / Minnesota / Michigan / New York
    ('Fort Frances (Fort Frances/International Falls)', 48.6010, -93.4105),
    ('Pigeon River (Thunder Bay/Grand Portage)', 48.0000, -89.5845),
    ('Sault Ste. Marie (SSM ON/SSM MI)', 46.5126, -84.3476),
    ('Blue Water Bridge (Point Edward/Port Huron)', 42.9990, -82.4218),
    ('Ambassador Bridge (Windsor/Detroit)', 42.3113, -83.0756),
    ('Detroit-Windsor Tunnel (Windsor/Detroit)', 42.3224, -83.0442),
    ('Queenston-Lewiston Bridge (Niagara/Lewiston)', 43.1534, -79.0474),
    ('Rainbow Bridge (Niagara Falls)', 43.0886, -79.0683),
    ('Peace Bridge (Fort Erie/Buffalo)', 42.9063, -78.9047),
    ('Whirlpool Bridge (Niagara Falls)', 43.1117, -79.0633),
    ('Thousand Islands Bridge (Lansdowne/Alexandria Bay)', 44.3581, -75.9778),
    ('Prescott-Ogdensburg Bridge (Prescott/Ogdensburg)', 44.7217, -75.4703),
    ('Cornwall (Cornwall/Massena)', 44.9976, -74.7694),
    # QC / New York / Vermont / Maine
    ('Lacolle (Lacolle/Champlain)', 45.0086, -73.3726),
    ('St-Armand/Philipsburg (Philipsburg/Highgate Springs)', 45.0061, -73.0839),
    ('Stanstead (Stanstead/Derby Line)', 45.0060, -72.1008),
    ('Rock Island (Stanstead/Derby Line)', 45.0087, -72.0953),
    ('Hereford Road (East Hereford/Beecher Falls)', 45.0000, -71.4902),
    ('Armstrong (Armstrong/Fort Covington)', 45.0050, -74.2233),
    # NB / Maine
    ('St. Stephen (St. Stephen/Calais)', 45.1915, -67.2799),
    ('Woodstock (Woodstock/Houlton)', 46.1501, -67.5792),
    ('Edmundston (Edmundston/Madawaska)', 47.3655, -68.3249),
    ('St. Leonard (St. Leonard/Van Buren)', 47.1657, -67.9245),
    ('Campobello Island (Campobello/Lubec)', 44.8894, -66.9522),
    # NS
    ('Yarmouth Ferry (Yarmouth/Bar Harbor)', 43.8361, -66.1174),
    # MB / Saskatchewan additional
    ('Windygates (Windygates/Hannah)', 49.0000, -98.0574),
    ('Snowflake (Snowflake/Hannah)', 49.0000, -98.3036),
    # AB additional
    ('Del Bonita (Del Bonita/Del Bonita)', 49.0000, -112.5000),
    ('Aden (Aden/Wild Horse)', 49.0000, -110.0000),
    # ON additional
    ('Lansdowne (Lansdowne/Cape Vincent)', 44.3581, -76.2000),
    ('Rainy River (Rainy River/Baudette)', 48.7200, -94.5700),
    # BC additional
    ('Roosville (Grasmere/Roosville)', 49.0000, -115.0670),
    ('Nelway (Nelway/Metaline Falls)', 49.0000, -117.2664),
    ('Cascade (Cascade/Laurier)', 49.0000, -118.2131),
    ('Midway (Midway/Ferry)', 49.0000, -118.7700),
    ('Nighthawk (Nighthawk/Oroville)', 49.0000, -119.6000),
    # Major ferry crossings
    ('BC Ferries (Sidney/Anacortes)', 48.6431, -123.3965),
    ('Wolfe Island Ferry (Kingston/Cape Vincent)', 44.1876, -76.4312),
]


def find_nearest_crossing(latitude, longitude):
    """Find nearest border crossing to given coordinates.

    Returns (crossing_name, distance_km).
    """
    nearest_name = None
    nearest_dist = float('inf')
    for name, lat, lng in BORDER_CROSSINGS:
        dist = haversine_distance(latitude, longitude, lat, lng)
        if dist < nearest_dist:
            nearest_dist = dist
            nearest_name = name
    return nearest_name, round(nearest_dist, 1)


def compute_border_distance(truck_stop):
    """Compute and set nearest border crossing on a TruckStop object.

    Does NOT commit — caller must commit the session.
    """
    name, dist = find_nearest_crossing(truck_stop.latitude, truck_stop.longitude)
    truck_stop.nearest_border_crossing = name
    truck_stop.border_distance_km = dist
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_border_crossings.py -v`
Expected: All 5 PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/services/border_crossings.py tests/test_border_crossings.py
git commit -m "feat: add border crossing data and distance computation"
```

---

### Task 6: Banner Service

**Files:**
- Create: `app/services/banner_service.py`
- Create: `tests/test_banner_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_banner_service.py`:

```python
"""Tests for smart contextual banner service."""
from app.services.banner_service import get_banners
from app.models.truck_stop import TruckStop


def _make_stop(**overrides):
    """Create an in-memory TruckStop (no DB) for banner testing."""
    defaults = dict(
        brand='loves', name='Test Stop', slug='test-stop',
        address='123 St', city='Dallas', state_province='TX',
        country='US', latitude=32.7767, longitude=-96.7970,
        highway='I-35', data_source='manual',
        nearest_border_crossing=None, border_distance_km=None,
        parking_location_id=None,
    )
    defaults.update(overrides)
    stop = TruckStop.__new__(TruckStop)
    for k, v in defaults.items():
        setattr(stop, k, v)
    return stop


def test_tms_banner_always_present():
    stop = _make_stop()
    banners = get_banners(stop)
    tms = [b for b in banners if b['type'] == 'tms']
    assert len(tms) == 1
    assert 'tms.truckerpro.ca' in tms[0]['url']


def test_tms_banner_corridor_copy():
    stop = _make_stop(highway='I-35')
    banners = get_banners(stop)
    tms = [b for b in banners if b['type'] == 'tms'][0]
    assert 'I-35' in tms['copy']


def test_tms_banner_metro_copy():
    stop = _make_stop(highway=None, city='Chicago')
    banners = get_banners(stop)
    tms = [b for b in banners if b['type'] == 'tms'][0]
    assert 'Chicago' in tms['copy']


def test_border_banner_when_close():
    stop = _make_stop(
        nearest_border_crossing='Peace Bridge (Fort Erie/Buffalo)',
        border_distance_km=8.5, country='US',
    )
    banners = get_banners(stop)
    border = [b for b in banners if b['type'] == 'border']
    assert len(border) == 1
    assert 'Peace Bridge' in border[0]['copy']
    assert 'border.truckerpro.ca' in border[0]['url']


def test_no_border_banner_when_far():
    stop = _make_stop(
        nearest_border_crossing='Peace Bridge',
        border_distance_km=250.0,
    )
    banners = get_banners(stop)
    border = [b for b in banners if b['type'] == 'border']
    assert len(border) == 0


def test_parking_banner_with_linked_location():
    stop = _make_stop(parking_location_id=42)
    banners = get_banners(stop)
    parking = [b for b in banners if b['type'] == 'parking']
    assert len(parking) == 1
    assert 'Reserve' in parking[0]['copy']


def test_parking_banner_without_linked_location():
    stop = _make_stop(parking_location_id=None)
    banners = get_banners(stop)
    parking = [b for b in banners if b['type'] == 'parking']
    assert len(parking) == 1
    assert 'nearby' in parking[0]['copy'].lower()


def test_fmcsa_banner_always_present():
    stop = _make_stop()
    banners = get_banners(stop)
    fmcsa = [b for b in banners if b['type'] == 'fmcsa']
    assert len(fmcsa) == 1
    assert 'fmcsa.truckerpro.net' in fmcsa[0]['url']


def test_banner_order():
    stop = _make_stop(
        nearest_border_crossing='Peace Bridge',
        border_distance_km=8.0, parking_location_id=1,
    )
    banners = get_banners(stop)
    types = [b['type'] for b in banners]
    assert types == ['tms', 'border', 'parking', 'fmcsa']
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_banner_service.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Create banner service**

Create `app/services/banner_service.py`:

```python
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
    """TMS banner — always shown, copy varies by context."""
    highway = getattr(stop, 'highway', None) or ''
    city = getattr(stop, 'city', '') or ''

    if highway.upper() in [c.upper() for c in MAJOR_FREIGHT_CORRIDORS]:
        copy = f"Dispatching loads on {highway}? Manage your fleet"
    elif city in MAJOR_METROS:
        copy = f"Running routes through {city}? Track every load"
    else:
        copy = "Trucking company? Manage your fleet with TruckerPro TMS"

    return {
        'type': 'tms',
        'copy': copy,
        'url': 'https://tms.truckerpro.ca',
        'cta': 'Try Free',
    }


def _border_banner(stop):
    """Border banner — only if within 100km of a crossing."""
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

    return {
        'type': 'border',
        'copy': copy,
        'url': 'https://border.truckerpro.ca',
        'cta': 'Learn More',
    }


def _parking_banner(stop):
    """Parking Club banner — copy depends on linked parking location."""
    if getattr(stop, 'parking_location_id', None):
        copy = "Reserve parking at this stop"
    else:
        copy = "Find reservable parking nearby"

    return {
        'type': 'parking',
        'copy': copy,
        'url': 'https://parking.truckerpro.ca',
        'cta': 'Reserve',
    }


def _fmcsa_banner(stop):
    """FMCSA banner — always shown."""
    return {
        'type': 'fmcsa',
        'copy': "Look up carriers at this stop",
        'url': 'https://fmcsa.truckerpro.net',
        'cta': 'Lookup',
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_banner_service.py -v`
Expected: All 10 PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/services/banner_service.py tests/test_banner_service.py
git commit -m "feat: add smart contextual banner service"
```

---

### Task 7: CSV Import Pipeline

**Files:**
- Create: `app/import/__init__.py`
- Create: `app/import/base.py`
- Create: `app/import/loves.py`
- Modify: `app/__init__.py`
- Create: `tests/test_import.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_import.py`:

```python
"""Tests for CSV import pipeline."""
import os
import csv
import tempfile
import pytest
from app.models.truck_stop import TruckStop
from app.import_stops.base import upsert_truck_stop, generate_stop_slug
from app.import_stops.loves import parse_loves_row


def test_generate_stop_slug():
    slug = generate_stop_slug('loves', '521', 'Dallas', 'TX')
    assert slug == 'loves-521-dallas-tx'


def test_generate_stop_slug_spaces():
    slug = generate_stop_slug('pilot_flying_j', '18', 'New York', 'NY')
    assert slug == 'pilot-flying-j-18-new-york-ny'


def test_upsert_creates_new(db):
    data = {
        'brand': 'loves',
        'brand_display_name': "Love's Travel Stops",
        'name': "Love's #999",
        'slug': 'loves-999-test-tx',
        'store_number': '999',
        'address': '123 Hwy',
        'city': 'Test',
        'state_province': 'TX',
        'country': 'US',
        'latitude': 32.0,
        'longitude': -96.0,
        'data_source': 'csv_import',
    }
    stop = upsert_truck_stop(data)
    db.session.commit()
    assert stop.id is not None
    assert TruckStop.query.filter_by(store_number='999').count() == 1


def test_upsert_updates_existing(db):
    data = {
        'brand': 'loves',
        'brand_display_name': "Love's Travel Stops",
        'name': "Love's #888",
        'slug': 'loves-888-test-tx',
        'store_number': '888',
        'address': '123 Hwy',
        'city': 'Test',
        'state_province': 'TX',
        'country': 'US',
        'latitude': 32.0,
        'longitude': -96.0,
        'data_source': 'csv_import',
    }
    stop1 = upsert_truck_stop(data)
    db.session.commit()
    data['name'] = "Love's #888 Updated"
    data['has_showers'] = True
    stop2 = upsert_truck_stop(data)
    db.session.commit()
    assert stop1.id == stop2.id
    assert stop2.name == "Love's #888 Updated"
    assert TruckStop.query.filter_by(store_number='888', brand='loves').count() == 1


def test_parse_loves_row():
    row = {
        'Store Number': '521',
        'Store Name': "Love's Travel Stop",
        'Address': '1234 I-35 Frontage Rd',
        'City': 'Dallas',
        'State': 'TX',
        'Zip': '75201',
        'Country': 'US',
        'Latitude': '32.7767',
        'Longitude': '-96.7970',
        'Phone': '(214) 555-0100',
        'Has Diesel': 'Y',
        'Has Showers': 'Y',
        'Number Of Showers': '8',
        'Has Scale': 'Y',
        'Has Tire Care': 'Y',
        'Has DEF': 'Y',
        'Truck Parking Spaces': '150',
    }
    data = parse_loves_row(row)
    assert data['brand'] == 'loves'
    assert data['store_number'] == '521'
    assert data['city'] == 'Dallas'
    assert data['latitude'] == 32.7767
    assert data['has_diesel'] is True
    assert data['has_showers'] is True
    assert data['shower_count'] == 8
    assert data['truck_spots'] == 150


def test_loves_csv_import_cli(app, db):
    """Test the full CLI import with a temp CSV."""
    tmpdir = tempfile.mkdtemp()
    csv_path = os.path.join(tmpdir, 'loves_test.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Store Number', 'Store Name', 'Address', 'City', 'State',
            'Zip', 'Country', 'Latitude', 'Longitude', 'Phone',
            'Has Diesel', 'Has Showers', 'Number Of Showers',
            'Has Scale', 'Has Tire Care', 'Has DEF', 'Truck Parking Spaces',
        ])
        writer.writeheader()
        writer.writerow({
            'Store Number': '777', 'Store Name': "Love's Travel Stop",
            'Address': '555 Test Rd', 'City': 'Austin', 'State': 'TX',
            'Zip': '78701', 'Country': 'US', 'Latitude': '30.2672',
            'Longitude': '-97.7431', 'Phone': '(512) 555-0100',
            'Has Diesel': 'Y', 'Has Showers': 'Y', 'Number Of Showers': '6',
            'Has Scale': 'N', 'Has Tire Care': 'Y', 'Has DEF': 'Y',
            'Truck Parking Spaces': '80',
        })

    runner = app.test_cli_runner()
    result = runner.invoke(args=['import-stops', 'loves', '--file', csv_path])
    assert 'Imported 1' in result.output
    stop = TruckStop.query.filter_by(store_number='777', brand='loves').first()
    assert stop is not None
    assert stop.city == 'Austin'
    os.unlink(csv_path)
    os.rmdir(tmpdir)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_import.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Create import base module**

Create `app/import_stops/__init__.py`:

```python
"""Truck stop CSV import pipeline."""
```

Create `app/import_stops/base.py`:

```python
"""Shared import logic — upsert, slug generation, border distance."""
from ..extensions import db
from ..models.truck_stop import TruckStop
from ..services.geo_service import slugify
from ..services.border_crossings import compute_border_distance


def generate_stop_slug(brand, store_number, city, state_province):
    """Generate a URL slug for a truck stop."""
    brand_slug = brand.replace('_', '-')
    parts = [brand_slug]
    if store_number:
        parts.append(store_number)
    parts.extend([city, state_province])
    return slugify(' '.join(parts))


def upsert_truck_stop(data):
    """Insert or update a truck stop by brand + store_number.

    Does NOT commit — caller must commit the session.
    Returns the TruckStop instance.
    """
    existing = None
    if data.get('store_number'):
        existing = TruckStop.query.filter_by(
            brand=data['brand'], store_number=data['store_number']
        ).first()

    if existing:
        for key, val in data.items():
            if key != 'id' and val is not None:
                setattr(existing, key, val)
        compute_border_distance(existing)
        return existing

    stop = TruckStop(**data)
    compute_border_distance(stop)
    db.session.add(stop)
    return stop
```

- [ ] **Step 4: Create Loves CSV mapper**

Create `app/import_stops/loves.py`:

```python
"""Love's Travel Stops CSV column mapper."""


def _yn_to_bool(val):
    return str(val).strip().upper() in ('Y', 'YES', 'TRUE', '1')


def _safe_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def parse_loves_row(row):
    """Map a Loves CSV row dict to truck_stops field dict."""
    return {
        'brand': 'loves',
        'brand_display_name': "Love's Travel Stops",
        'name': f"Love's {row.get('Store Name', 'Travel Stop')} #{row['Store Number']}",
        'store_number': str(row['Store Number']).strip(),
        'address': row.get('Address', '').strip(),
        'city': row.get('City', '').strip(),
        'state_province': row.get('State', '').strip(),
        'postal_code': row.get('Zip', '').strip(),
        'country': row.get('Country', 'US').strip() or 'US',
        'latitude': _safe_float(row.get('Latitude')),
        'longitude': _safe_float(row.get('Longitude')),
        'phone': row.get('Phone', '').strip() or None,
        'has_diesel': _yn_to_bool(row.get('Has Diesel', 'Y')),
        'has_showers': _yn_to_bool(row.get('Has Showers', 'N')),
        'shower_count': _safe_int(row.get('Number Of Showers')),
        'has_scale': _yn_to_bool(row.get('Has Scale', 'N')),
        'has_tire_service': _yn_to_bool(row.get('Has Tire Care', 'N')),
        'has_def': _yn_to_bool(row.get('Has DEF', 'N')),
        'truck_spots': _safe_int(row.get('Truck Parking Spaces')),
        'total_parking_spots': _safe_int(row.get('Truck Parking Spaces')),
        'data_source': 'csv_import',
    }
```

- [ ] **Step 5: Register CLI command in app factory**

In `app/__init__.py`, add after the existing `seed_command`:

```python
    @app.cli.command('import-stops')
    @click.argument('brand')
    @click.option('--file', 'file_path', required=True, help='Path to CSV file')
    def import_stops_command(brand, file_path):
        """Import truck stops from a CSV file."""
        import csv
        from .import_stops.base import upsert_truck_stop, generate_stop_slug

        brand_parsers = {
            'loves': 'app.import_stops.loves:parse_loves_row',
        }
        parser_path = brand_parsers.get(brand)
        if not parser_path:
            print(f"Unknown brand: {brand}. Available: {', '.join(brand_parsers.keys())}")
            return

        module_path, func_name = parser_path.rsplit(':', 1)
        import importlib
        mod = importlib.import_module(module_path)
        parse_row = getattr(mod, func_name)

        count = 0
        with open(file_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data = parse_row(row)
                if not data.get('latitude') or not data.get('longitude'):
                    print(f"Skipping {data.get('store_number', '?')} — no coordinates")
                    continue
                data['slug'] = generate_stop_slug(
                    data['brand'], data.get('store_number', ''),
                    data['city'], data['state_province'],
                )
                upsert_truck_stop(data)
                count += 1
            db.session.commit()
        print(f"Imported {count} {brand} stops.")
```

Also add `import click` at the top of `app/__init__.py` with the other imports.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_import.py -v`
Expected: All 6 PASS

- [ ] **Step 7: Run full suite**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/import_stops/ app/__init__.py tests/test_import.py
git commit -m "feat: add CSV import pipeline with Loves mapper and CLI command"
```

---

### Task 8: Test Fixtures — Stops Client

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Add stops_client fixture**

Add to `tests/conftest.py` after the existing `db` fixture:

```python

@pytest.fixture(scope='function')
def stops_client(app):
    """Test client that sends Host header for stops.truckerpro.net domain."""
    app.config['STOPS_DOMAIN'] = 'stops.localhost'
    c = app.test_client()

    class StopsClient:
        """Wrapper that adds Host header to all requests."""
        def __init__(self, client):
            self._client = client

        def get(self, *args, **kwargs):
            kwargs.setdefault('headers', {})['Host'] = 'stops.localhost'
            return self._client.get(*args, **kwargs)

        def post(self, *args, **kwargs):
            kwargs.setdefault('headers', {})['Host'] = 'stops.localhost'
            return self._client.post(*args, **kwargs)

    return StopsClient(c)
```

- [ ] **Step 2: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add tests/conftest.py
git commit -m "feat: add stops_client test fixture with host header"
```

---

### Task 9: Stops API Blueprint — Truck Stop Endpoints

**Files:**
- Create: `app/stops_api/__init__.py`
- Create: `app/stops_api/truck_stops.py`
- Modify: `app/__init__.py`
- Create: `tests/test_stops_api.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_stops_api.py`:

```python
"""Tests for truck stops API endpoints."""
from app.models.truck_stop import TruckStop


def _seed_stop(db, **overrides):
    defaults = dict(
        brand='loves', name="Love's #1", slug='loves-1-dallas-tx',
        store_number='1', address='123 Hwy', city='Dallas',
        state_province='TX', country='US', latitude=32.7767,
        longitude=-96.7970, highway='I-35', data_source='manual',
        is_active=True,
    )
    defaults.update(overrides)
    stop = TruckStop(**defaults)
    db.session.add(stop)
    db.session.commit()
    return stop


def test_list_truck_stops_empty(stops_client):
    resp = stops_client.get('/api/v1/truck-stops')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 0


def test_list_truck_stops_with_data(stops_client, db):
    _seed_stop(db)
    resp = stops_client.get('/api/v1/truck-stops')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['stops'][0]['brand'] == 'loves'


def test_filter_by_state(stops_client, db):
    _seed_stop(db, slug='s1', store_number='1', state_province='TX')
    _seed_stop(db, slug='s2', store_number='2', state_province='ON', country='CA')
    resp = stops_client.get('/api/v1/truck-stops?state=TX')
    data = resp.get_json()
    assert data['total'] == 1


def test_filter_by_brand(stops_client, db):
    _seed_stop(db, slug='s1', store_number='1', brand='loves')
    _seed_stop(db, slug='s2', store_number='2', brand='pilot_flying_j')
    resp = stops_client.get('/api/v1/truck-stops?brand=loves')
    data = resp.get_json()
    assert data['total'] == 1


def test_filter_by_highway(stops_client, db):
    _seed_stop(db, slug='s1', store_number='1', highway='I-35')
    _seed_stop(db, slug='s2', store_number='2', highway='I-10')
    resp = stops_client.get('/api/v1/truck-stops?highway=I-35')
    data = resp.get_json()
    assert data['total'] == 1


def test_get_truck_stop_detail(stops_client, db):
    stop = _seed_stop(db)
    resp = stops_client.get(f'/api/v1/truck-stops/{stop.id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['slug'] == 'loves-1-dallas-tx'
    assert 'banners' in data


def test_get_truck_stop_not_found(stops_client):
    resp = stops_client.get('/api/v1/truck-stops/99999')
    assert resp.status_code == 404


def test_geo_search(stops_client, db):
    _seed_stop(db, slug='near', store_number='1',
               latitude=32.78, longitude=-96.80)
    _seed_stop(db, slug='far', store_number='2',
               latitude=40.71, longitude=-74.01)
    resp = stops_client.get('/api/v1/truck-stops?lat=32.77&lng=-96.79&radius=50')
    data = resp.get_json()
    assert data['total'] == 1
    assert data['stops'][0]['slug'] == 'near'


def test_pagination(stops_client, db):
    for i in range(25):
        _seed_stop(db, slug=f's-{i}', store_number=str(i))
    resp = stops_client.get('/api/v1/truck-stops?page=1&per_page=10')
    data = resp.get_json()
    assert data['total'] == 25
    assert len(data['stops']) == 10
    assert data['page'] == 1
    assert data['pages'] == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_stops_api.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Create stops_api blueprint**

Create `app/stops_api/__init__.py`:

```python
from flask import Blueprint

stops_api_bp = Blueprint('stops_api', __name__)

from . import truck_stops  # noqa: E402, F401
```

Create `app/stops_api/truck_stops.py`:

```python
"""Truck stop API endpoints — list, detail, search."""
import logging
from flask import jsonify, request
from sqlalchemy import func

from . import stops_api_bp
from ..extensions import db
from ..middleware import site_required
from ..models.truck_stop import TruckStop
from ..models.fuel_price import FuelPrice
from ..models.truck_stop_review import TruckStopReview
from ..services.geo_service import haversine_distance
from ..services.banner_service import get_banners

logger = logging.getLogger(__name__)


def _serialize_stop(stop, distance_km=None):
    data = {
        'id': stop.id,
        'brand': stop.brand,
        'brand_display_name': stop.brand_display_name,
        'name': stop.name,
        'slug': stop.slug,
        'city': stop.city,
        'state_province': stop.state_province,
        'country': stop.country,
        'latitude': stop.latitude,
        'longitude': stop.longitude,
        'highway': stop.highway,
        'exit_number': stop.exit_number,
        'total_parking_spots': stop.total_parking_spots,
        'has_diesel': stop.has_diesel,
        'has_showers': stop.has_showers,
        'has_scale': stop.has_scale,
        'has_repair': stop.has_repair,
    }
    if distance_km is not None:
        data['distance_km'] = distance_km
    return data


def _serialize_stop_detail(stop):
    # Latest fuel prices
    latest_prices = db.session.query(FuelPrice).filter_by(
        truck_stop_id=stop.id, is_verified=True
    ).order_by(FuelPrice.created_at.desc()).limit(4).all()

    # Review stats
    review_stats = db.session.query(
        func.count(TruckStopReview.id),
        func.avg(TruckStopReview.rating),
    ).filter_by(truck_stop_id=stop.id, is_approved=True).first()

    return {
        'id': stop.id,
        'brand': stop.brand,
        'brand_display_name': stop.brand_display_name,
        'name': stop.name,
        'slug': stop.slug,
        'store_number': stop.store_number,
        'address': stop.address,
        'city': stop.city,
        'state_province': stop.state_province,
        'postal_code': stop.postal_code,
        'country': stop.country,
        'latitude': stop.latitude,
        'longitude': stop.longitude,
        'highway': stop.highway,
        'exit_number': stop.exit_number,
        'direction': stop.direction,
        'total_parking_spots': stop.total_parking_spots,
        'truck_spots': stop.truck_spots,
        'car_spots': stop.car_spots,
        'has_diesel': stop.has_diesel,
        'has_gas': stop.has_gas,
        'has_def': stop.has_def,
        'has_ev_charging': stop.has_ev_charging,
        'has_showers': stop.has_showers,
        'shower_count': stop.shower_count,
        'has_scale': stop.has_scale,
        'scale_type': stop.scale_type,
        'has_repair': stop.has_repair,
        'has_tire_service': stop.has_tire_service,
        'has_wifi': stop.has_wifi,
        'has_laundry': stop.has_laundry,
        'restaurants': stop.restaurants or [],
        'loyalty_programs': stop.loyalty_programs or [],
        'hours_of_operation': stop.hours_of_operation or {},
        'phone': stop.phone,
        'website': stop.website,
        'photos': stop.photos or [],
        'nearest_border_crossing': stop.nearest_border_crossing,
        'border_distance_km': stop.border_distance_km,
        'meta_title': stop.meta_title,
        'meta_description': stop.meta_description,
        'fuel_prices': [
            {'fuel_type': fp.fuel_type, 'price_cents': fp.price_cents,
             'currency': fp.currency, 'created_at': fp.created_at.isoformat()}
            for fp in latest_prices
        ],
        'review_count': review_stats[0] if review_stats else 0,
        'avg_rating': round(float(review_stats[1]), 1) if review_stats and review_stats[1] else None,
        'banners': get_banners(stop),
    }


@stops_api_bp.route('/truck-stops')
@site_required('stops')
def list_truck_stops():
    """List truck stops with filters, geo search, pagination."""
    query = TruckStop.query.filter_by(is_active=True)

    # Filters
    state = request.args.get('state')
    if state:
        query = query.filter(func.upper(TruckStop.state_province) == state.upper())

    city = request.args.get('city')
    if city:
        query = query.filter(func.lower(TruckStop.city) == city.lower())

    brand = request.args.get('brand')
    if brand:
        query = query.filter_by(brand=brand)

    country = request.args.get('country')
    if country:
        query = query.filter(func.upper(TruckStop.country) == country.upper())

    highway = request.args.get('highway')
    if highway:
        query = query.filter(func.upper(TruckStop.highway) == highway.upper())

    # Geo search
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', type=float, default=50)

    distances = {}
    if lat is not None and lng is not None:
        # Bounding box pre-filter
        delta_lat = radius / 111.0
        delta_lng = radius / (111.0 * abs(float(lat)) * 0.01745 + 0.001)
        query = query.filter(
            TruckStop.latitude.between(lat - delta_lat, lat + delta_lat),
            TruckStop.longitude.between(lng - delta_lng, lng + delta_lng),
        )
        stops = query.all()
        # Haversine filter
        filtered = []
        for s in stops:
            d = haversine_distance(lat, lng, s.latitude, s.longitude)
            if d <= radius:
                distances[s.id] = d
                filtered.append(s)
        filtered.sort(key=lambda s: distances[s.id])
        total = len(filtered)

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)
        start = (page - 1) * per_page
        page_stops = filtered[start:start + per_page]

        return jsonify({
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'stops': [_serialize_stop(s, distances.get(s.id)) for s in page_stops],
        })

    # Pagination (non-geo)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)
    total = query.count()
    stops = query.order_by(TruckStop.name).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
        'stops': [_serialize_stop(s) for s in stops],
    })


@stops_api_bp.route('/truck-stops/<int:stop_id>')
@site_required('stops')
def get_truck_stop(stop_id):
    """Get truck stop detail with fuel prices, review stats, banners."""
    stop = TruckStop.query.filter_by(id=stop_id, is_active=True).first()
    if not stop:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(_serialize_stop_detail(stop))
```

- [ ] **Step 4: Register blueprint in app factory**

In `app/__init__.py`, add after the existing `app.register_blueprint(pages_bp)`:

```python
    from .stops_api import stops_api_bp
    app.register_blueprint(stops_api_bp, url_prefix='/api/v1')
    csrf.exempt(stops_api_bp)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_stops_api.py -v`
Expected: All 9 PASS

- [ ] **Step 6: Run full suite**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/stops_api/ app/__init__.py tests/test_stops_api.py
git commit -m "feat: add truck stops API with list, detail, filters, geo search"
```

---

### Task 10: Driver Contributions API

**Files:**
- Create: `app/stops_api/contributions.py`
- Modify: `app/stops_api/__init__.py`
- Create: `tests/test_contributions_api.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_contributions_api.py`:

```python
"""Tests for driver contribution API endpoints (fuel prices, reviews, reports)."""
import json
import bcrypt
from app.models.truck_stop import TruckStop
from app.models.fuel_price import FuelPrice
from app.models.truck_stop_review import TruckStopReview
from app.models.user import User


def _seed(db):
    stop = TruckStop(
        brand='loves', name='Test', slug='contrib-test',
        address='123 St', city='Dallas', state_province='TX',
        country='US', latitude=32.0, longitude=-96.0, data_source='manual',
    )
    pw = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode('utf-8')
    user = User(email='contrib@test.com', password_hash=pw, name='Driver', role='driver')
    db.session.add_all([stop, user])
    db.session.commit()
    return stop, user


def _login(client, app):
    with app.test_request_context():
        return client._client.post('/login', data={
            'email': 'contrib@test.com', 'password': 'password123',
        }, headers={'Host': 'stops.localhost'}, follow_redirects=True)


def test_submit_fuel_price_requires_auth(stops_client, db):
    stop, _ = _seed(db)
    resp = stops_client.post(
        f'/api/v1/truck-stops/{stop.id}/fuel-prices',
        data=json.dumps({'fuel_type': 'diesel', 'price_cents': 350, 'currency': 'USD'}),
        content_type='application/json',
    )
    assert resp.status_code in (401, 302)


def test_submit_review_requires_auth(stops_client, db):
    stop, _ = _seed(db)
    resp = stops_client.post(
        f'/api/v1/truck-stops/{stop.id}/reviews',
        data=json.dumps({'rating': 4, 'review_text': 'Great stop'}),
        content_type='application/json',
    )
    assert resp.status_code in (401, 302)


def test_fuel_price_auto_verify_within_threshold(app, db):
    """Fuel price within 20% of last known price is auto-verified."""
    stop, user = _seed(db)
    # Seed a known price
    fp = FuelPrice(
        truck_stop_id=stop.id, fuel_type='diesel',
        price_cents=350, currency='USD', source='import', is_verified=True,
    )
    db.session.add(fp)
    db.session.commit()

    # Import to test the threshold logic directly
    from app.stops_api.contributions import _should_auto_verify_price
    assert _should_auto_verify_price(stop.id, 'diesel', 360) is True   # within 20%
    assert _should_auto_verify_price(stop.id, 'diesel', 500) is False  # outside 20%


def test_submit_report(app, db):
    """Parking availability report gets expires_at set."""
    from datetime import datetime, timezone, timedelta
    from app.models.truck_stop_report import TruckStopReport
    stop, user = _seed(db)
    report = TruckStopReport(
        truck_stop_id=stop.id, user_id=user.id,
        report_type='parking_availability',
        data={'available_spots': 12},
        expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
    )
    db.session.add(report)
    db.session.commit()
    assert report.expires_at > datetime.now(timezone.utc)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_contributions_api.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Create contributions module**

Create `app/stops_api/contributions.py`:

```python
"""Driver contribution endpoints — fuel prices, reviews, reports."""
import logging
from datetime import datetime, timezone, timedelta
from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func

from . import stops_api_bp
from ..extensions import db
from ..middleware import site_required
from ..models.truck_stop import TruckStop
from ..models.fuel_price import FuelPrice
from ..models.truck_stop_review import TruckStopReview
from ..models.truck_stop_report import TruckStopReport

logger = logging.getLogger(__name__)


def _should_auto_verify_price(truck_stop_id, fuel_type, price_cents):
    """Check if a submitted price is within 20% of the last known verified price."""
    last = FuelPrice.query.filter_by(
        truck_stop_id=truck_stop_id, fuel_type=fuel_type, is_verified=True
    ).order_by(FuelPrice.created_at.desc()).first()
    if not last:
        return False
    threshold = last.price_cents * 0.2
    return abs(price_cents - last.price_cents) <= threshold


@stops_api_bp.route('/truck-stops/<int:stop_id>/fuel-prices', methods=['POST'])
@site_required('stops')
@login_required
def submit_fuel_price(stop_id):
    """Submit a fuel price report."""
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json()
    fuel_type = data.get('fuel_type')
    price_cents = data.get('price_cents')
    currency = data.get('currency', 'USD')

    if not fuel_type or not price_cents:
        return jsonify({'error': 'fuel_type and price_cents required'}), 400

    is_verified = _should_auto_verify_price(stop_id, fuel_type, price_cents)

    fp = FuelPrice(
        truck_stop_id=stop_id, fuel_type=fuel_type,
        price_cents=price_cents, currency=currency,
        reported_by=current_user.id, source='driver',
        is_verified=is_verified,
    )
    db.session.add(fp)
    db.session.commit()
    return jsonify({'id': fp.id, 'is_verified': fp.is_verified}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/reviews', methods=['POST'])
@site_required('stops')
@login_required
def submit_review(stop_id):
    """Submit a truck stop review."""
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json()
    rating = data.get('rating')
    review_text = data.get('review_text', '')

    if not rating or rating < 1 or rating > 5:
        return jsonify({'error': 'rating must be 1-5'}), 400

    existing = TruckStopReview.query.filter_by(
        truck_stop_id=stop_id, user_id=current_user.id
    ).first()
    if existing:
        return jsonify({'error': 'You already reviewed this stop'}), 409

    review = TruckStopReview(
        truck_stop_id=stop_id, user_id=current_user.id,
        rating=rating, review_text=review_text,
        photos=data.get('photos', []),
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({'id': review.id, 'is_approved': review.is_approved}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/reports', methods=['POST'])
@site_required('stops')
@login_required
def submit_report(stop_id):
    """Submit a driver report (parking availability, amenity status, etc.)."""
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json()
    report_type = data.get('report_type')
    report_data = data.get('data')

    if not report_type or not report_data:
        return jsonify({'error': 'report_type and data required'}), 400

    expires_at = None
    if report_type == 'parking_availability':
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)

    report = TruckStopReport(
        truck_stop_id=stop_id, user_id=current_user.id,
        report_type=report_type, data=report_data,
        expires_at=expires_at,
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({'id': report.id}), 201
```

- [ ] **Step 4: Update stops_api __init__ to import contributions**

In `app/stops_api/__init__.py`, change to:

```python
from flask import Blueprint

stops_api_bp = Blueprint('stops_api', __name__)

from . import truck_stops, contributions  # noqa: E402, F401
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_contributions_api.py -v`
Expected: All 4 PASS

- [ ] **Step 6: Run full suite**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/stops_api/contributions.py app/stops_api/__init__.py tests/test_contributions_api.py
git commit -m "feat: add driver contribution endpoints (fuel prices, reviews, reports)"
```

---

### Task 11: Stops Public Blueprint — Routes

**Files:**
- Create: `app/stops/__init__.py`
- Create: `app/stops/helpers.py`
- Create: `app/stops/routes.py`
- Modify: `app/__init__.py`
- Create: `tests/test_stops_routes.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_stops_routes.py`:

```python
"""Tests for stops.truckerpro.net public page routes."""
from app.models.truck_stop import TruckStop


def _seed_stop(db, **overrides):
    defaults = dict(
        brand='loves', name="Love's #1", slug='loves-1-dallas-tx',
        store_number='1', address='123 Hwy', city='Dallas',
        state_province='TX', country='US', latitude=32.7767,
        longitude=-96.7970, highway='I-35', data_source='manual',
        is_active=True, has_diesel=True, total_parking_spots=100,
    )
    defaults.update(overrides)
    stop = TruckStop(**defaults)
    db.session.add(stop)
    db.session.commit()
    return stop


class TestHomepage:
    def test_stops_homepage(self, stops_client):
        resp = stops_client.get('/')
        assert resp.status_code == 200

    def test_stops_homepage_content(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/')
        assert b'Truck Stop' in resp.data or b'truck stop' in resp.data


class TestCountryPages:
    def test_us_page(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/us')
        assert resp.status_code == 200

    def test_canada_page(self, stops_client, db):
        _seed_stop(db, slug='ca-stop', state_province='ON', country='CA')
        resp = stops_client.get('/canada')
        assert resp.status_code == 200


class TestStatePage:
    def test_state_page(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/us/texas')
        assert resp.status_code == 200

    def test_state_page_404(self, stops_client):
        resp = stops_client.get('/us/nonexistent-state')
        assert resp.status_code == 404


class TestCityPage:
    def test_city_page(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/us/texas/dallas')
        assert resp.status_code == 200


class TestStopDetail:
    def test_stop_detail(self, stops_client, db):
        stop = _seed_stop(db)
        resp = stops_client.get(f'/us/texas/dallas/{stop.slug}')
        assert resp.status_code == 200

    def test_stop_detail_404(self, stops_client):
        resp = stops_client.get('/us/texas/dallas/nonexistent-slug')
        assert resp.status_code == 404


class TestBrandPages:
    def test_brands_index(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/brands')
        assert resp.status_code == 200

    def test_brand_detail(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/brands/loves')
        assert resp.status_code == 200

    def test_brand_state(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/brands/loves/texas')
        assert resp.status_code == 200


class TestHighwayPages:
    def test_highways_index(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/highways')
        assert resp.status_code == 200

    def test_highway_detail(self, stops_client, db):
        _seed_stop(db)
        resp = stops_client.get('/highways/i-35')
        assert resp.status_code == 200


class TestHealthOnStopsDomain:
    def test_health(self, stops_client):
        resp = stops_client.get('/health')
        assert resp.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_stops_routes.py -v`
Expected: FAIL

- [ ] **Step 3: Create stops helpers**

Create `app/stops/__init__.py`:

```python
from flask import Blueprint

stops_public_bp = Blueprint('stops', __name__, template_folder='../templates/stops')

from . import routes  # noqa: E402, F401
```

Create `app/stops/helpers.py`:

```python
"""Template helpers for stops.truckerpro.net pages."""
from ..services.geo_service import format_price, slugify
from ..constants import (
    US_STATES, US_STATE_CODE_TO_SLUG, PROVINCE_MAP, PROVINCE_CODE_TO_SLUG,
    ALL_REGIONS, ALL_REGION_CODE_TO_SLUG, BRAND_MAP, BRAND_SLUG_TO_KEY,
)


def state_code_to_slug(code):
    """Convert state/province code to URL slug. 'TX' -> 'texas'."""
    return ALL_REGION_CODE_TO_SLUG.get(code, slugify(code))


def state_slug_to_code(slug):
    """Convert URL slug to state/province code. 'texas' -> 'TX'."""
    region = ALL_REGIONS.get(slug)
    return region['code'] if region else None


def state_slug_to_name(slug):
    """Convert URL slug to display name. 'texas' -> 'Texas'."""
    region = ALL_REGIONS.get(slug)
    return region['name'] if region else slug.replace('-', ' ').title()


def country_for_state(code):
    """Return 'US' or 'CA' for a state/province code."""
    if code in US_STATE_CODE_TO_SLUG:
        return 'US'
    if code in PROVINCE_CODE_TO_SLUG:
        return 'CA'
    return None


def brand_key_to_slug(brand_key):
    """Convert brand key to URL slug. 'loves' -> 'loves'."""
    info = BRAND_MAP.get(brand_key)
    return info['slug'] if info else slugify(brand_key)


def brand_slug_to_key(slug):
    """Convert URL slug to brand key. 'pilot-flying-j' -> 'pilot_flying_j'."""
    return BRAND_SLUG_TO_KEY.get(slug)


def brand_slug_to_name(slug):
    """Convert brand slug to display name."""
    key = BRAND_SLUG_TO_KEY.get(slug)
    if key:
        return BRAND_MAP[key]['name']
    return slug.replace('-', ' ').title()


def highway_to_slug(highway):
    """Convert highway name to URL slug. 'I-35' -> 'i-35'."""
    return slugify(highway)


def stop_to_card(stop):
    """Convert a TruckStop to a template-friendly dict for card display."""
    return {
        'id': stop.id,
        'name': stop.name,
        'slug': stop.slug,
        'brand': stop.brand,
        'brand_display_name': stop.brand_display_name,
        'city': stop.city,
        'state_province': stop.state_province,
        'country': stop.country,
        'highway': stop.highway,
        'exit_number': stop.exit_number,
        'total_parking_spots': stop.total_parking_spots,
        'has_diesel': stop.has_diesel,
        'has_showers': stop.has_showers,
        'has_scale': stop.has_scale,
        'has_repair': stop.has_repair,
        'has_wifi': stop.has_wifi,
        'latitude': stop.latitude,
        'longitude': stop.longitude,
        'state_slug': state_code_to_slug(stop.state_province),
        'city_slug': slugify(stop.city),
        'brand_slug': brand_key_to_slug(stop.brand),
        'country_slug': 'us' if stop.country == 'US' else 'canada',
    }
```

- [ ] **Step 4: Create stops routes**

Create `app/stops/routes.py`:

```python
"""Public page routes for stops.truckerpro.net."""
import logging
from flask import render_template, abort, request
from sqlalchemy import func

from . import stops_public_bp
from ..extensions import db
from ..middleware import site_required
from ..models.truck_stop import TruckStop
from ..services.banner_service import get_banners
from ..services.geo_service import slugify
from ..constants import US_STATES, PROVINCE_MAP, BRAND_MAP, BRAND_SLUG_TO_KEY
from .helpers import (
    state_slug_to_code, state_slug_to_name, country_for_state,
    brand_slug_to_key, brand_slug_to_name, stop_to_card,
    highway_to_slug, state_code_to_slug,
)

logger = logging.getLogger(__name__)
PER_PAGE = 24


def _paginate(query, page, per_page=PER_PAGE):
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    pages = (total + per_page - 1) // per_page
    return items, total, pages


# ── Homepage ─────────────────────────────────────────────────

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


# ── Country pages ────────────────────────────────────────────

@stops_public_bp.route('/us')
@site_required('stops')
def us_overview():
    states = db.session.query(
        TruckStop.state_province,
        func.count(TruckStop.id),
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
        TruckStop.state_province,
        func.count(TruckStop.id),
    ).filter(TruckStop.is_active == True, TruckStop.country == 'CA'
    ).group_by(TruckStop.state_province).order_by(TruckStop.state_province).all()
    prov_data = [
        {'code': code, 'slug': state_code_to_slug(code),
         'name': state_slug_to_name(state_code_to_slug(code)), 'count': cnt}
        for code, cnt in provinces
    ]
    return render_template('stops/country.html', country='CA',
                           country_name='Canada', regions=prov_data)


# ── State/Province page ──────────────────────────────────────

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

    # Cities in this state
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


# ── City page ────────────────────────────────────────────────

@stops_public_bp.route('/us/<state_slug>/<city_slug>')
@stops_public_bp.route('/canada/<state_slug>/<city_slug>')
@site_required('stops')
def city_page(state_slug, city_slug):
    code = state_slug_to_code(state_slug)
    if not code:
        abort(404)
    # Find stops in this city (case-insensitive match on slugified city)
    query = TruckStop.query.filter(
        TruckStop.is_active == True,
        TruckStop.state_province == code,
    ).order_by(TruckStop.name)
    all_stops = query.all()
    city_stops = [s for s in all_stops if slugify(s.city) == city_slug]
    if not city_stops:
        abort(404)
    city_name = city_stops[0].city
    return render_template('stops/city.html',
                           city_name=city_name, state_name=state_slug_to_name(state_slug),
                           state_slug=state_slug, state_code=code,
                           stops=[stop_to_card(s) for s in city_stops])


# ── Stop detail ──────────────────────────────────────────────

@stops_public_bp.route('/us/<state_slug>/<city_slug>/<slug>')
@stops_public_bp.route('/canada/<state_slug>/<city_slug>/<slug>')
@site_required('stops')
def stop_detail(state_slug, city_slug, slug):
    stop = TruckStop.query.filter_by(slug=slug, is_active=True).first()
    if not stop:
        abort(404)
    banners = get_banners(stop)

    # Nearby stops (same state, limit 6)
    nearby = TruckStop.query.filter(
        TruckStop.is_active == True,
        TruckStop.state_province == stop.state_province,
        TruckStop.id != stop.id,
    ).limit(6).all()

    return render_template('stops/stop_detail.html',
                           stop=stop, banners=banners,
                           nearby=[stop_to_card(s) for s in nearby],
                           state_slug=state_slug, city_slug=city_slug)


# ── Brand pages ──────────────────────────────────────────────

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


# ── Highway pages ────────────────────────────────────────────

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
    # Match highway by slugified comparison
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
```

- [ ] **Step 5: Register stops blueprint in app factory**

In `app/__init__.py`, add after the `stops_api_bp` registration:

```python
    from .stops import stops_public_bp
    app.register_blueprint(stops_public_bp)
```

- [ ] **Step 6: Create minimal templates**

Templates will be built out in Task 12 with proper design. For now, create functional stubs so tests pass.

Create `app/templates/stops/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Truck Stops Directory{% endblock %} — stops.truckerpro.net</title>
    <meta name="description" content="{% block meta_description %}Find truck stops across the US and Canada{% endblock %}">
    <link rel="stylesheet" href="{{ url_for('static', filename='stops/css/stops.css') }}">
    {% block head %}{% endblock %}
</head>
<body>
    <header>
        <nav>
            <a href="/">Truck Stops</a>
            <a href="/us">US</a>
            <a href="/canada">Canada</a>
            <a href="/brands">Brands</a>
            <a href="/highways">Highways</a>
        </nav>
    </header>
    <main>{% block content %}{% endblock %}</main>
    <footer>
        <p>Truck Stops Directory &mdash; stops.truckerpro.net</p>
    </footer>
    {% block scripts %}{% endblock %}
</body>
</html>
```

Create `app/templates/stops/home.html`:

```html
{% extends "stops/base.html" %}
{% block title %}Truck Stops Directory — US & Canada{% endblock %}
{% block content %}
<h1>Truck Stops Directory</h1>
<p>{{ total_stops }} truck stops across {{ total_states }} states and provinces.</p>
<section>
    <h2>Featured Stops</h2>
    {% for stop in featured %}
    {% include "stops/partials/stop_card.html" %}
    {% endfor %}
</section>
{% endblock %}
```

Create `app/templates/stops/country.html`:

```html
{% extends "stops/base.html" %}
{% block title %}Truck Stops in {{ country_name }}{% endblock %}
{% block content %}
<h1>Truck Stops in {{ country_name }}</h1>
{% for r in regions %}
<a href="/{{ 'us' if country == 'US' else 'canada' }}/{{ r.slug }}">{{ r.name }} ({{ r.count }})</a>
{% endfor %}
{% endblock %}
```

Create `app/templates/stops/state.html`:

```html
{% extends "stops/base.html" %}
{% block title %}Truck Stops in {{ state_name }}{% endblock %}
{% block content %}
<h1>Truck Stops in {{ state_name }}</h1>
<p>{{ total }} stops</p>
{% for stop in stops %}
{% include "stops/partials/stop_card.html" %}
{% endfor %}
{% endblock %}
```

Create `app/templates/stops/city.html`:

```html
{% extends "stops/base.html" %}
{% block title %}Truck Stops in {{ city_name }}, {{ state_name }}{% endblock %}
{% block content %}
<h1>Truck Stops in {{ city_name }}, {{ state_name }}</h1>
{% for stop in stops %}
{% include "stops/partials/stop_card.html" %}
{% endfor %}
{% endblock %}
```

Create `app/templates/stops/stop_detail.html`:

```html
{% extends "stops/base.html" %}
{% block title %}{{ stop.name }}{% endblock %}
{% block content %}
{% for banner in banners %}
{% if banner.type == 'tms' %}{% include "stops/partials/banner_tms.html" %}
{% elif banner.type == 'border' %}{% include "stops/partials/banner_border.html" %}
{% elif banner.type == 'parking' %}{% include "stops/partials/banner_parking.html" %}
{% elif banner.type == 'fmcsa' %}{% include "stops/partials/banner_fmcsa.html" %}
{% endif %}
{% endfor %}
<h1>{{ stop.name }}</h1>
<p>{{ stop.address }}, {{ stop.city }}, {{ stop.state_province }} {{ stop.postal_code }}</p>
{% if stop.highway %}<p>{{ stop.highway }}{% if stop.exit_number %} Exit {{ stop.exit_number }}{% endif %}</p>{% endif %}
{% include "stops/partials/amenities_grid.html" %}
<section>
    <h2>Nearby Stops</h2>
    {% for stop in nearby %}
    {% include "stops/partials/stop_card.html" %}
    {% endfor %}
</section>
{% endblock %}
```

Create `app/templates/stops/brand_index.html`:

```html
{% extends "stops/base.html" %}
{% block title %}Truck Stop Brands{% endblock %}
{% block content %}
<h1>Truck Stop Brands</h1>
{% for brand_key, brand_name, count in brands %}
<a href="/brands/{{ brand_key | replace('_', '-') }}">{{ brand_name or brand_key }} ({{ count }})</a>
{% endfor %}
{% endblock %}
```

Create `app/templates/stops/brand_detail.html`:

```html
{% extends "stops/base.html" %}
{% block title %}{{ brand_name }} Locations{% endblock %}
{% block content %}
<h1>{{ brand_name }}</h1>
<p>{{ total }} locations</p>
{% for stop in stops %}
{% include "stops/partials/stop_card.html" %}
{% endfor %}
{% endblock %}
```

Create `app/templates/stops/brand_state.html`:

```html
{% extends "stops/base.html" %}
{% block title %}{{ brand_name }} in {{ state_name }}{% endblock %}
{% block content %}
<h1>{{ brand_name }} in {{ state_name }}</h1>
{% for stop in stops %}
{% include "stops/partials/stop_card.html" %}
{% endfor %}
{% endblock %}
```

Create `app/templates/stops/highway_index.html`:

```html
{% extends "stops/base.html" %}
{% block title %}Truck Stops by Highway{% endblock %}
{% block content %}
<h1>Truck Stops by Highway</h1>
{% for hwy, count in highways %}
<a href="/highways/{{ hwy | lower | replace(' ', '-') }}">{{ hwy }} ({{ count }})</a>
{% endfor %}
{% endblock %}
```

Create `app/templates/stops/highway_detail.html`:

```html
{% extends "stops/base.html" %}
{% block title %}Truck Stops on {{ highway_name }}{% endblock %}
{% block content %}
<h1>Truck Stops on {{ highway_name }}</h1>
{% for stop in stops %}
{% include "stops/partials/stop_card.html" %}
{% endfor %}
{% endblock %}
```

Create `app/templates/stops/partials/stop_card.html`:

```html
<div class="stop-card">
    <h3><a href="/{{ stop.country_slug }}/{{ stop.state_slug }}/{{ stop.city_slug }}/{{ stop.slug }}">{{ stop.name }}</a></h3>
    <p>{{ stop.city }}, {{ stop.state_province }}</p>
    {% if stop.highway %}<p>{{ stop.highway }}{% if stop.exit_number %} Exit {{ stop.exit_number }}{% endif %}</p>{% endif %}
</div>
```

Create `app/templates/stops/partials/banner_tms.html`:

```html
<div class="banner banner-tms" data-ga-event="banner_click" data-ga-target="tms">
    <p>{{ banner.copy }}</p>
    <a href="{{ banner.url }}">{{ banner.cta }}</a>
</div>
```

Create `app/templates/stops/partials/banner_border.html`:

```html
<div class="banner banner-border" data-ga-event="banner_click" data-ga-target="border">
    <p>{{ banner.copy }}</p>
    <a href="{{ banner.url }}">{{ banner.cta }}</a>
</div>
```

Create `app/templates/stops/partials/banner_parking.html`:

```html
<div class="banner banner-parking" data-ga-event="banner_click" data-ga-target="parking">
    <p>{{ banner.copy }}</p>
    <a href="{{ banner.url }}">{{ banner.cta }}</a>
</div>
```

Create `app/templates/stops/partials/banner_fmcsa.html`:

```html
<div class="banner banner-fmcsa" data-ga-event="banner_click" data-ga-target="fmcsa">
    <p>{{ banner.copy }}</p>
    <a href="{{ banner.url }}">{{ banner.cta }}</a>
</div>
```

Create `app/templates/stops/partials/amenities_grid.html`:

```html
<div class="amenities-grid">
    {% if stop.has_diesel %}<span class="amenity">Diesel</span>{% endif %}
    {% if stop.has_showers %}<span class="amenity">Showers{% if stop.shower_count %} ({{ stop.shower_count }}){% endif %}</span>{% endif %}
    {% if stop.has_scale %}<span class="amenity">Scale{% if stop.scale_type %} ({{ stop.scale_type | upper }}){% endif %}</span>{% endif %}
    {% if stop.has_repair %}<span class="amenity">Repair</span>{% endif %}
    {% if stop.has_tire_service %}<span class="amenity">Tire Service</span>{% endif %}
    {% if stop.has_wifi %}<span class="amenity">WiFi</span>{% endif %}
    {% if stop.has_def %}<span class="amenity">DEF</span>{% endif %}
    {% if stop.has_laundry %}<span class="amenity">Laundry</span>{% endif %}
    {% if stop.has_ev_charging %}<span class="amenity">EV Charging</span>{% endif %}
</div>
```

Create `app/templates/stops/partials/fuel_prices.html`:

```html
{% if fuel_prices %}
<div class="fuel-prices">
    {% for fp in fuel_prices %}
    <div class="fuel-price">
        <span class="fuel-type">{{ fp.fuel_type | title }}</span>
        <span class="price">${{ "%.3f" | format(fp.price_cents / 100) }}</span>
    </div>
    {% endfor %}
</div>
{% endif %}
```

Create `app/templates/stops/partials/pagination.html`:

```html
{% if pages > 1 %}
<nav class="pagination">
    {% if page > 1 %}<a href="?page={{ page - 1 }}">Previous</a>{% endif %}
    <span>Page {{ page }} of {{ pages }}</span>
    {% if page < pages %}<a href="?page={{ page + 1 }}">Next</a>{% endif %}
</nav>
{% endif %}
```

Create `app/static/stops/css/stops.css`:

```css
/* Minimal structural CSS — will be replaced with full design */
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; color: #1e293b; line-height: 1.5; }
main { max-width: 1200px; margin: 0 auto; padding: 24px 16px; }
header nav { display: flex; gap: 16px; padding: 16px; border-bottom: 1px solid #e2e8f0; }
header nav a { color: #334155; text-decoration: none; font-weight: 500; }
h1 { font-size: 1.75rem; margin-bottom: 8px; }
h2 { font-size: 1.25rem; margin: 24px 0 12px; }
.stop-card { border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.stop-card a { color: #1e40af; text-decoration: none; }
.banner { padding: 12px 16px; border-radius: 6px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
.banner-tms { background: #1e40af; color: #fff; }
.banner-border { background: #065f46; color: #fff; }
.banner-parking { background: #7c3aed; color: #fff; }
.banner-fmcsa { background: #374151; color: #fff; }
.banner a { color: #fff; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 4px; text-decoration: none; font-weight: 600; }
.amenities-grid { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.amenity { background: #f1f5f9; padding: 4px 10px; border-radius: 4px; font-size: 0.875rem; }
.pagination { display: flex; gap: 12px; align-items: center; margin-top: 24px; }
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_stops_routes.py -v`
Expected: All 13 PASS

- [ ] **Step 8: Run full suite**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/stops/ app/templates/stops/ app/static/stops/ app/__init__.py tests/test_stops_routes.py
git commit -m "feat: add stops public blueprint with all directory routes and templates"
```

---

### Task 12: Sitemap Generation

**Files:**
- Modify: `app/stops/routes.py`
- Create: `tests/test_sitemap_stops.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_sitemap_stops.py`:

```python
"""Tests for stops.truckerpro.net sitemap generation."""
from app.models.truck_stop import TruckStop


def _seed(db):
    stops = [
        TruckStop(brand='loves', name="Love's #1", slug='loves-1-dallas-tx',
                  store_number='1', address='123 Hwy', city='Dallas',
                  state_province='TX', country='US', latitude=32.77,
                  longitude=-96.80, highway='I-35', data_source='manual', is_active=True),
        TruckStop(brand='pilot_flying_j', name='Pilot #2', slug='pilot-2-toronto-on',
                  store_number='2', address='401 Hwy', city='Toronto',
                  state_province='ON', country='CA', latitude=43.65,
                  longitude=-79.38, highway='401', data_source='manual', is_active=True),
    ]
    db.session.add_all(stops)
    db.session.commit()


def test_sitemap_index(stops_client, db):
    _seed(db)
    resp = stops_client.get('/sitemap.xml')
    assert resp.status_code == 200
    assert b'sitemapindex' in resp.data


def test_sitemap_stops(stops_client, db):
    _seed(db)
    resp = stops_client.get('/sitemap-stops.xml')
    assert resp.status_code == 200
    assert b'loves-1-dallas-tx' in resp.data
    assert b'pilot-2-toronto-on' in resp.data


def test_sitemap_states(stops_client, db):
    _seed(db)
    resp = stops_client.get('/sitemap-states.xml')
    assert resp.status_code == 200
    assert b'/us/texas' in resp.data or b'/canada/ontario' in resp.data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_sitemap_stops.py -v`
Expected: FAIL — 404

- [ ] **Step 3: Add sitemap routes**

Append to `app/stops/routes.py`:

```python

# ── Sitemaps ─────────────────────────────────────────────────

from flask import Response
from ..services.geo_service import slugify as _slugify


STOPS_BASE = 'https://stops.truckerpro.net'


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
    ).filter(TruckStop.is_active == True
    ).distinct().all()
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
        from .helpers import brand_key_to_slug as bk2s
        xml.append(f'<url><loc>{STOPS_BASE}/brands/{bk2s(brand_key)}</loc></url>')
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
    ).filter(TruckStop.is_active == True
    ).distinct().all()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for city, code, country in cities:
        country_slug = 'us' if country == 'US' else 'canada'
        state_sl = state_code_to_slug(code)
        city_sl = _slugify(city)
        xml.append(f'<url><loc>{STOPS_BASE}/{country_slug}/{state_sl}/{city_sl}</loc></url>')
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/test_sitemap_stops.py -v`
Expected: All 3 PASS

- [ ] **Step 5: Run full suite**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/stops/routes.py tests/test_sitemap_stops.py
git commit -m "feat: add sitemap generation for stops directory"
```

---

### Task 13: Admin Import Endpoint + `compute-border-distances` CLI

**Files:**
- Create: `app/stops_api/admin.py`
- Modify: `app/stops_api/__init__.py`
- Modify: `app/__init__.py`

- [ ] **Step 1: Create admin endpoint for truck stops**

Create `app/stops_api/admin.py`:

```python
"""Admin endpoints for truck stop management."""
from flask import jsonify, request, current_app
from . import stops_api_bp
from ..extensions import db
from ..middleware import site_required
from ..models.truck_stop import TruckStop
from ..import_stops.base import upsert_truck_stop, generate_stop_slug
from ..services.border_crossings import compute_border_distance


@stops_api_bp.route('/admin/truck-stops', methods=['POST'])
@site_required('stops')
def admin_create_truck_stops():
    """Bulk create/update truck stops. Requires X-Admin-Key."""
    auth = request.headers.get('X-Admin-Key', '')
    admin_key = current_app.config.get('ADMIN_SECRET_KEY') or current_app.config.get('SECRET_KEY', '')
    if not auth or auth != admin_key:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    stops_data = data if isinstance(data, list) else [data]
    count = 0
    for item in stops_data:
        if 'slug' not in item:
            item['slug'] = generate_stop_slug(
                item.get('brand', 'independent'),
                item.get('store_number', ''),
                item.get('city', ''),
                item.get('state_province', ''),
            )
        if 'data_source' not in item:
            item['data_source'] = 'manual'
        upsert_truck_stop(item)
        count += 1
    db.session.commit()
    return jsonify({'success': True, 'count': count})
```

- [ ] **Step 2: Update stops_api __init__**

```python
from flask import Blueprint

stops_api_bp = Blueprint('stops_api', __name__)

from . import truck_stops, contributions, admin  # noqa: E402, F401
```

- [ ] **Step 3: Add compute-border-distances CLI command**

In `app/__init__.py`, add after the `import-stops` command:

```python
    @app.cli.command('compute-border-distances')
    def compute_border_distances_command():
        """Recompute border distances for all truck stops."""
        from .models.truck_stop import TruckStop
        from .services.border_crossings import compute_border_distance
        stops = TruckStop.query.all()
        for stop in stops:
            compute_border_distance(stop)
        db.session.commit()
        print(f"Updated border distances for {len(stops)} stops.")
```

- [ ] **Step 4: Run full suite**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add app/stops_api/admin.py app/stops_api/__init__.py app/__init__.py
git commit -m "feat: add admin truck stop endpoint and border distance CLI command"
```

---

### Task 14: Verify Full Test Suite + Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python -m pytest tests/ -v`
Expected: All tests PASS (84 original + new tests)

- [ ] **Step 2: Update CLAUDE.md with new architecture**

Add to `CLAUDE.md` after the "Related Projects" section:

```markdown

## Truck Stops Directory (stops.truckerpro.net)
Added 2026-03-31. Host-based routing serves stops.truckerpro.net from this same app.

### Architecture
- `app/middleware.py` — Host-based routing middleware (`g.site` = 'parking' or 'stops')
- `app/stops/` — Public page routes for stops.truckerpro.net (home, state, city, detail, brands, highways)
- `app/stops_api/` — API endpoints (truck-stops CRUD, contributions, admin)
- `app/import_stops/` — CSV import pipeline (base upsert logic + brand-specific mappers)
- `app/services/banner_service.py` — Smart contextual banners (TMS, border, parking, FMCSA)
- `app/services/border_crossings.py` — US-Canada border crossing data + distance computation

### Models
- `TruckStop` (`truck_stops`) — Core truck stop data
- `FuelPrice` (`fuel_prices`) — Timestamped fuel prices
- `TruckStopReview` (`truck_stop_reviews`) — Driver reviews with moderation
- `TruckStopReport` (`truck_stop_reports`) — Driver-contributed updates

### Key Endpoints (stops.truckerpro.net)
- `GET /` — Homepage
- `GET /us`, `/canada` — Country overview
- `GET /us/<state>`, `/canada/<province>` — State/province page
- `GET /us/<state>/<city>` — City page
- `GET /us/<state>/<city>/<slug>` — Individual truck stop page
- `GET /brands`, `/brands/<brand>`, `/brands/<brand>/<state>` — Brand directory
- `GET /highways`, `/highways/<highway>` — Highway directory
- `GET /api/v1/truck-stops` — List/search API
- `GET /api/v1/truck-stops/<id>` — Detail API with banners
- `POST /api/v1/truck-stops/<id>/fuel-prices` — Submit fuel price (auth)
- `POST /api/v1/truck-stops/<id>/reviews` — Submit review (auth)
- `POST /api/v1/truck-stops/<id>/reports` — Submit report (auth)
- `POST /api/v1/admin/truck-stops` — Admin bulk create (X-Admin-Key)
- `GET /sitemap.xml` — Sitemap index

### CLI Commands
- `flask import-stops loves --file path/to/csv` — Import Loves CSV
- `flask compute-border-distances` — Recompute border distances

### Design Spec
- `docs/superpowers/specs/2026-03-31-truck-stops-directory-design.md`
```

- [ ] **Step 3: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with truck stops directory architecture"
```
