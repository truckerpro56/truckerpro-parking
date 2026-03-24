# Truck Parking Club — Standalone SaaS Extraction Design

**Date:** 2026-03-24
**Status:** Draft
**Repo:** https://github.com/truckerpro56/truckerpro-parking
**Domain:** parking.truckerpro.ca

## Overview

Extract the Truck Parking Club module from `truckerpro-web` into a fully independent SaaS application at `truckerpro-parking/`. The new app will have its own GitHub repo, Railway deployment, PostgreSQL database, and auth system. After extraction, all parking-related code is safely removed from `truckerpro-web`.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Separate repo + Railway (like truckerpro-border) | Proven pattern, full independence |
| Domain | parking.truckerpro.ca | Stays under main brand, future SSO possible |
| Auth | Fully standalone | Simplest to launch, no TruckerPro dependency |
| Scope | Full extraction of existing code | Move everything, remove from source |

## Architecture

### Deployment (Railway)

```
parking.truckerpro.ca → Cloudflare DNS → Railway
  ├── WEB service (Flask + Gunicorn)
  ├── WORKER service (Celery)
  ├── BEAT service (Celery scheduler)
  ├── PostgreSQL 15 (own database)
  └── Redis 7 (Celery broker + cache)
```

### Tech Stack (matches truckerpro-border pattern)

- **Backend:** Flask 2.3, Python 3.11, SQLAlchemy 2.0
- **Database:** PostgreSQL 15 (Railway managed)
- **Cache/Queue:** Redis 7 (Railway managed)
- **Background Jobs:** Celery
- **Payments:** Stripe
- **Maps:** Google Maps API
- **Email:** Resend
- **Auth:** Flask-Login with bcrypt, standalone user table
- **Deployment:** Docker → Railway, Gunicorn + eventlet

### Project Structure

```
truckerpro-parking/
├── app/
│   ├── __init__.py              # Flask factory (create_app)
│   ├── config.py                # Config + TestConfig
│   ├── extensions.py            # db, socketio, limiter, csrf, login_manager
│   ├── api/                     # /api/v1 endpoints
│   │   ├── locations.py         # Search, filter, geo, CRUD
│   │   ├── bookings.py          # Create, cancel, list bookings
│   │   └── reviews.py           # Submit, list reviews
│   ├── routes/                  # Page routes (SSR templates)
│   │   ├── public.py            # Landing, search, province, city, location detail
│   │   ├── auth.py              # Login, signup, logout, password reset
│   │   └── owner.py             # Owner dashboard, manage listings
│   ├── models/
│   │   ├── user.py              # Standalone User model (driver, owner, admin)
│   │   ├── location.py          # ParkingLocation
│   │   ├── booking.py           # ParkingBooking
│   │   ├── review.py            # ParkingReview
│   │   └── availability.py      # ParkingAvailability
│   ├── services/                # Business logic
│   │   ├── booking_service.py   # Pricing, tax, availability checks
│   │   ├── payment_service.py   # Stripe integration
│   │   ├── email_service.py     # Resend notifications
│   │   └── geo_service.py       # Geocoding, Haversine distance
│   ├── tasks/                   # Celery background jobs
│   ├── templates/               # Jinja2 templates (from truckerpro-web)
│   │   ├── public/              # 8 parkingclub_*.html templates
│   │   ├── auth/                # login, signup
│   │   └── owner/               # dashboard
│   ├── static/                  # CSS, JS, images
│   ├── migrations/              # Database migrations
│   └── seed/                    # Seed data (Canadian locations)
├── tests/
├── Dockerfile
├── docker-compose.yml           # Local dev (PostgreSQL 5435, Redis 6381)
├── railway.toml
├── start.sh
├── gunicorn.conf.py
└── requirements.txt
```

## What Moves (truckerpro-web → truckerpro-parking)

### Files to Extract & Adapt

| Source (truckerpro-web) | Destination (truckerpro-parking) | Changes Needed |
|-------------------------|----------------------------------|----------------|
| `app/parking_club_routes.py` (1,277 lines) | Split into `app/api/locations.py`, `app/api/bookings.py`, `app/api/reviews.py`, `app/routes/public.py`, `app/routes/owner.py` | Remove `from app_full import db` references; use SQLAlchemy models instead of raw SQL; use Flask-Login standalone auth |
| `app/migrations/032_parking_club.py` | Not needed — models define schema via `db.create_all()` | SQLAlchemy models replace raw DDL migration |
| `app/seed_parking_data.py` | `app/seed/locations.py` | Adapt to use SQLAlchemy ORM |
| `app/templates/public/parkingclub.html` | `app/templates/public/landing.html` | Update URLs (remove `/parkingclub` prefix → `/`), update branding |
| `app/templates/public/parkingclub_search.html` | `app/templates/public/search.html` | Same URL/branding updates |
| `app/templates/public/parkingclub_province.html` | `app/templates/public/province.html` | Same |
| `app/templates/public/parkingclub_city.html` | `app/templates/public/city.html` | Same |
| `app/templates/public/parkingclub_location.html` | `app/templates/public/location.html` | Same |
| `app/templates/public/parkingclub_list_space.html` | `app/templates/public/list_space.html` | Same |
| `app/templates/public/parkingclub_my_bookings.html` | `app/templates/public/my_bookings.html` | Same |
| `app/templates/public/parkingclub_owner_dashboard.html` | `app/templates/owner/dashboard.html` | Same |

### Key Code Adaptations

1. **Raw SQL → ORM:** Existing code uses raw `db.session.execute(text(...))`. New code should use SQLAlchemy ORM queries (`ParkingLocation.query.filter_by(...)`) for cleaner, safer code.

2. **Auth:** Replace `from app_full import db` and `current_user` (tied to TruckerPro User model) with standalone User model and Flask-Login.

3. **URL prefix:** Existing routes are under `/parkingclub/*`. New app serves from root: `/` (landing), `/search`, `/ontario`, `/ontario/toronto`, `/location/<slug>`, etc.

4. **Config:** Replace `from secrets_manager import get_secret` with `current_app.config['KEY']` pattern.

5. **Stripe:** Extract payment logic into `services/payment_service.py`. Same Stripe account, separate webhook endpoint.

6. **Tax calculation:** Move `PROVINCIAL_TAX` dict and logic into `services/booking_service.py`.

7. **Geocoding:** Move Haversine distance calc and geocode into `services/geo_service.py`.

## What Gets Removed from truckerpro-web

### Files to Delete

| File | Type |
|------|------|
| `app/parking_club_routes.py` | Route file (1,277 lines) |
| `app/seed_parking_data.py` | Seed script |
| `app/templates/public/parkingclub.html` | Template |
| `app/templates/public/parkingclub_search.html` | Template |
| `app/templates/public/parkingclub_province.html` | Template |
| `app/templates/public/parkingclub_city.html` | Template |
| `app/templates/public/parkingclub_location.html` | Template |
| `app/templates/public/parkingclub_list_space.html` | Template |
| `app/templates/public/parkingclub_my_bookings.html` | Template |
| `app/templates/public/parkingclub_owner_dashboard.html` | Template |

### Files to Edit (remove parking references)

| File | Lines | What to Change |
|------|-------|----------------|
| `app/app_full.py:26` | `from parking_club_routes import parking_club_bp` | Remove import |
| `app/app_full.py:7605` | `app.register_blueprint(parking_club_bp)` | Remove registration |
| `app/app_full.py:7607-7613` | CSRF exemption + sitemap imports for parking | Remove block |
| `app/public_page_routes.py:709-726` | Sitemap entries for `/parkingclub/*` | Remove parking sitemap block |
| `app/templates/partials/_tools_navbar.html:99-101` | Parking Club link in nav | Replace with link to `parking.truckerpro.ca` |
| `app/templates/landing_driver.html:218-220` | Parking Club link | Replace with external link |
| `app/templates/landing_company.html:383-385,952-963` | Parking Club card + link | Replace with external link |
| `app/static/robots.txt:9` | `Allow: /parking-club` | Remove line |
| `app/tests/load/locustfile.py:70,112-139` | Parking load test tasks | Remove parking test class/methods |

### Migration 032 — Keep or Remove?

**Keep `app/migrations/032_parking_club.py` in truckerpro-web** but add a new migration (e.g., `087_drop_parking_tables.py`) that drops the parking tables. This is safer than deleting the migration file since the migration runner tracks which migrations have run.

```python
# migrations/087_drop_parking_tables.py
def up(conn):
    cur = conn.cursor()
    for table in ['parking_availability', 'parking_reviews', 'parking_bookings', 'parking_locations']:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    conn.commit()
    cur.close()
```

## Database Schema

Identical to existing Migration 032 tables, now defined as SQLAlchemy models:

- **users** — standalone auth (email, password_hash, name, phone, role, stripe_customer_id)
- **parking_locations** — full location directory (geo, amenities, pricing, photos, verification)
- **parking_bookings** — booking with Stripe payment tracking, tax, commission
- **parking_reviews** — verified reviews tied to completed bookings
- **parking_availability** — date-level availability per location

## External Integrations

| Service | Purpose | Config |
|---------|---------|--------|
| Stripe | Booking payments, owner payouts | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` |
| Google Maps | Map display, geocoding | `GOOGLE_MAPS_API_KEY` |
| Resend | Transactional email (booking confirmations, owner alerts) | `RESEND_API_KEY` |
| Cloudflare | DNS, CDN, SSL for parking.truckerpro.ca | DNS CNAME to Railway |

## Railway Environment Variables

```
SECRET_KEY=<generate>
DATABASE_URL=<railway-provided>
REDIS_URL=<railway-provided>
STRIPE_SECRET_KEY=<same-stripe-account>
STRIPE_PUBLISHABLE_KEY=<same-stripe-account>
GOOGLE_MAPS_API_KEY=<same-key>
RESEND_API_KEY=<same-key>
FLASK_ENV=production
RAILWAY_SERVICE_ROLE=web|worker|beat
```

## SEO Considerations

The existing `/parkingclub` pages may have search engine indexing. To preserve SEO value:

1. **Add 301 redirects in truckerpro-web** after removal:
   - `/parkingclub` → `https://parking.truckerpro.ca/`
   - `/parkingclub/search` → `https://parking.truckerpro.ca/search`
   - `/parkingclub/<province>` → `https://parking.truckerpro.ca/<province>`
   - `/parkingclub/<province>/<city>` → `https://parking.truckerpro.ca/<province>/<city>`
   - `/parkingclub/location/<slug>` → `https://parking.truckerpro.ca/location/<slug>`

2. **Update canonical URLs** in new templates to `parking.truckerpro.ca`

3. **Update structured data** (JSON-LD) to reference new domain

## Testing

- Unit tests for models and services
- API endpoint tests (locations, bookings, reviews)
- Auth flow tests (signup, login, owner dashboard access)
- Health/ready endpoint tests (already created)
- Stripe webhook tests (mock)

## Implementation Order

1. Extract and adapt templates (update URLs, branding)
2. Implement auth (signup, login, logout with bcrypt + Flask-Login)
3. Port public routes (landing, search, province, city, location detail)
4. Port API endpoints (locations search/filter with Haversine geo)
5. Port booking system (Stripe payments, tax calculation)
6. Port owner dashboard (list/manage spaces, revenue stats)
7. Port review system
8. Adapt seed data script
9. Add 301 redirects in truckerpro-web
10. Remove parking code from truckerpro-web
11. Drop parking tables via new migration in truckerpro-web
12. Deploy to Railway, configure parking.truckerpro.ca DNS
