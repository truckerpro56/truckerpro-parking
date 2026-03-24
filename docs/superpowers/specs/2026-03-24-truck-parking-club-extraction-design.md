# Truck Parking Club — Standalone SaaS Extraction Design

**Date:** 2026-03-24
**Status:** Approved
**Repo:** https://github.com/truckerpro56/truckerpro-parking
**Domain:** parking.truckerpro.ca

## Overview

Extract the Truck Parking Club module from `truckerpro-web` into a fully independent SaaS application at `truckerpro-parking/`. The new app will have its own GitHub repo, Railway deployment, PostgreSQL database, and auth system. After extraction, all parking-related code is safely removed from `truckerpro-web`.

**Data assumption:** Current parking data is seed-only (no real bookings, no real owner accounts, no real Stripe charges). If this is wrong, a data migration step must be added before the removal phase.

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
- **Payments:** Stripe (+ webhook endpoint for async events)
- **Maps:** Google Maps API (geocoding + display)
- **Email:** Resend
- **Auth:** Flask-Login with bcrypt, standalone user table, `@login_manager.user_loader` callback
- **Deployment:** Docker → Railway, Gunicorn + eventlet

### Project Structure

```
truckerpro-parking/
├── app/
│   ├── __init__.py              # Flask factory (create_app) + user_loader
│   ├── config.py                # Config + TestConfig (postgres:// fix)
│   ├── extensions.py            # db, socketio, limiter, csrf, login_manager
│   ├── api/                     # /api/v1 endpoints
│   │   ├── locations.py         # Search, filter, geo, CRUD
│   │   ├── bookings.py          # Create, cancel, list bookings
│   │   ├── reviews.py           # Submit, list reviews
│   │   └── stripe_webhook.py    # Stripe webhook handler (CSRF-exempt)
│   ├── routes/                  # Page routes (SSR templates)
│   │   ├── public.py            # Landing, search, province, city, location detail
│   │   ├── auth.py              # Login, signup, logout, password reset (POST handlers)
│   │   └── owner.py             # Owner dashboard, manage listings
│   ├── models/
│   │   ├── user.py              # Standalone User model (driver, owner, admin)
│   │   ├── location.py          # ParkingLocation
│   │   ├── booking.py           # ParkingBooking
│   │   ├── review.py            # ParkingReview (with CheckConstraint rating 1-5)
│   │   └── availability.py      # ParkingAvailability
│   ├── services/                # Business logic
│   │   ├── booking_service.py   # Pricing, tax (PROVINCIAL_TAX), availability checks
│   │   ├── payment_service.py   # Stripe integration + webhook verification
│   │   ├── email_service.py     # Resend notifications
│   │   └── geo_service.py       # Geocoding (Google Maps API) + Haversine distance
│   ├── tasks/                   # Celery background jobs
│   │   ├── __init__.py          # Celery app definition
│   │   └── notifications.py     # Async email tasks
│   ├── templates/               # Jinja2 templates (from truckerpro-web)
│   │   ├── public/              # landing, search, province, city, location, list_space, my_bookings
│   │   ├── auth/                # login, signup
│   │   └── owner/               # dashboard
│   ├── static/                  # CSS, JS, images (including parkingclub-og.jpg)
│   ├── migrations/              # Database migrations
│   └── seed/                    # Seed data (Canadian locations)
├── tests/
├── Dockerfile
├── docker-compose.yml           # Local dev (PostgreSQL 5435, Redis 6381)
├── railway.toml
├── start.sh
├── gunicorn.conf.py
├── requirements.txt
├── .env.example                 # All required env vars documented
└── CLAUDE.md                    # Coding conventions for this repo
```

## What Moves (truckerpro-web → truckerpro-parking)

### Files to Extract & Adapt

| Source (truckerpro-web) | Destination (truckerpro-parking) | Changes Needed |
|-------------------------|----------------------------------|----------------|
| `app/parking_club_routes.py` (1,277 lines) | Split into `app/api/locations.py`, `app/api/bookings.py`, `app/api/reviews.py`, `app/routes/public.py`, `app/routes/owner.py` | Remove `from app_full import db` references; use SQLAlchemy models instead of raw SQL; use Flask-Login standalone auth |
| `app/migrations/032_parking_club.py` | Not needed — models define schema via `db.create_all()` | SQLAlchemy models replace raw DDL migration |
| `app/seed_parking_data.py` | `app/seed/locations.py` | Adapt to use SQLAlchemy ORM |
| `app/templates/public/parkingclub.html` | `app/templates/public/landing.html` | Update URLs (remove `/parkingclub` prefix → `/`), update branding, update canonical to parking.truckerpro.ca |
| `app/templates/public/parkingclub_search.html` | `app/templates/public/search.html` | Same URL/branding updates |
| `app/templates/public/parkingclub_province.html` | `app/templates/public/province.html` | Same |
| `app/templates/public/parkingclub_city.html` | `app/templates/public/city.html` | Same |
| `app/templates/public/parkingclub_location.html` | `app/templates/public/location.html` | Same |
| `app/templates/public/parkingclub_list_space.html` | `app/templates/public/list_space.html` | Same |
| `app/templates/public/parkingclub_my_bookings.html` | `app/templates/public/my_bookings.html` | Same |
| `app/templates/public/parkingclub_owner_dashboard.html` | `app/templates/owner/dashboard.html` | Same |
| `app_full.py` `geocode_address` function (~line 932) | `app/services/geo_service.py` | Extract Google Maps geocoding logic |
| Static asset `images/parkingclub-og.jpg` (if exists) | `app/static/images/parkingclub-og.jpg` | Copy or create OG image |

### Key Code Adaptations

1. **Raw SQL → ORM:** Existing code uses raw `db.session.execute(text(...))`. New code should use SQLAlchemy ORM queries (`ParkingLocation.query.filter_by(...)`) for cleaner, safer code.

2. **Auth:** Standalone User model with Flask-Login. Must register `@login_manager.user_loader` callback in `__init__.py`. Auth routes need POST handlers (login, signup, logout), not just GET stubs.

3. **URL prefix:** Existing routes are under `/parkingclub/*`. New app serves from root: `/` (landing), `/search`, `/ontario`, `/ontario/toronto`, `/location/<slug>`, etc.

4. **Config:** Replace `from secrets_manager import get_secret` with `current_app.config['KEY']` pattern. Fix `DATABASE_URL` postgres:// → postgresql:// mapping.

5. **Stripe:** Extract payment logic into `services/payment_service.py`. Same Stripe account, separate webhook endpoint at `/api/v1/stripe/webhook` (CSRF-exempt, signature verified). Register webhook URL in Stripe dashboard.

6. **Tax calculation:** Move `PROVINCIAL_TAX` dict and logic into `services/booking_service.py`.

7. **Geocoding:** Move Haversine distance calc AND `geocode_address` (Google Maps API) into `services/geo_service.py`.

8. **Celery app:** Define Celery app in `tasks/__init__.py` so worker/beat services can start.

9. **Rate limiting:** Apply rate limits to auth endpoints (login, signup) and public API endpoints.

10. **Review model:** Add `CheckConstraint` for rating 1-5 on `ParkingReview`.

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
| `app/app_full.py:~6394-6408` | Auto-seed block that calls `seed_parking_data.seed_locations()` | **Remove entire block** (will crash after tables are dropped) |
| `app/app_full.py:7605` | `app.register_blueprint(parking_club_bp)` | Remove registration |
| `app/app_full.py:7607-7618` | CSRF exemption + rate limiter imports for parking | Remove entire block |
| `app/public_page_routes.py:709-728` | Sitemap entries + `from parking_club_routes import PROVINCE_CODE_TO_SLUG` + `parking_locations` query | **Remove entire parking sitemap block** (import will crash after file deletion) |
| `app/templates/partials/_tools_navbar.html:99-101` | Parking Club link in nav | Replace with external link to `parking.truckerpro.ca` |
| `app/templates/landing_driver.html:218-220` | Parking Club link | Replace with external link |
| `app/templates/landing_company.html:383-385,952-963` | Parking Club card + link | Replace with external link |
| `app/static/robots.txt:9` | `Allow: /parking-club` | Remove line |
| `app/tests/load/locustfile.py:70,114-139` | Parking load test tasks | Remove parking test class/methods |

### Migration 032 — Keep or Remove?

**Keep `app/migrations/032_parking_club.py` in truckerpro-web** but add a new migration (e.g., `087_drop_parking_tables.py`) that drops the parking tables. This is safer than deleting the migration file since the migration runner tracks which migrations have run.

```python
# migrations/087_drop_parking_tables.py
"""Drop parking club tables — module extracted to standalone app at parking.truckerpro.ca"""
def up(conn):
    cur = conn.cursor()
    # Drop order respects foreign key dependencies (children first)
    # CASCADE drops dependent indexes/constraints only, not referenced table rows
    for table in ['parking_availability', 'parking_reviews', 'parking_bookings', 'parking_locations']:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    conn.commit()
    cur.close()
```

**Important:** Only run this migration AFTER verifying the standalone app is live and handling traffic. See Rollback Plan below.

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
| Stripe | Booking payments + webhook (`/api/v1/stripe/webhook`) | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` |
| Google Maps | Map display + geocoding API | `GOOGLE_MAPS_API_KEY` |
| Resend | Transactional email (booking confirmations, owner alerts) | `RESEND_API_KEY` |
| Cloudflare | DNS, CDN, SSL for parking.truckerpro.ca | DNS CNAME to Railway |

## Railway Environment Variables

```
SECRET_KEY=<generate>
DATABASE_URL=<railway-provided>
REDIS_URL=<railway-provided>
STRIPE_SECRET_KEY=<same-stripe-account>
STRIPE_PUBLISHABLE_KEY=<same-stripe-account>
STRIPE_WEBHOOK_SECRET=<new-webhook-endpoint>
GOOGLE_MAPS_API_KEY=<same-key>
RESEND_API_KEY=<same-key>
FLASK_ENV=production
RAILWAY_SERVICE_ROLE=web|worker|beat
```

## SEO Considerations

The existing `/parkingclub` pages may have search engine indexing. To preserve SEO value:

1. **Add 301 redirects in truckerpro-web** — these MUST be deployed in the SAME commit as the parking code deletion (atomic deploy):
   - `/parkingclub` → `https://parking.truckerpro.ca/`
   - `/parkingclub/search` → `https://parking.truckerpro.ca/search`
   - `/parkingclub/<province>` → `https://parking.truckerpro.ca/<province>`
   - `/parkingclub/<province>/<city>` → `https://parking.truckerpro.ca/<province>/<city>`
   - `/parkingclub/location/<slug>` → `https://parking.truckerpro.ca/location/<slug>`
   - `/parkingclub/list-your-space` → `https://parking.truckerpro.ca/list-your-space`
   - `/parkingclub/my-bookings` → `https://parking.truckerpro.ca/my-bookings`
   - `/parkingclub/owner/dashboard` → `https://parking.truckerpro.ca/owner/dashboard`
   - `/parkingclub/api/*` → `https://parking.truckerpro.ca/api/v1/*`

2. **Update canonical URLs** in new templates to `parking.truckerpro.ca`

3. **Update structured data** (JSON-LD) to reference new domain

## Rollback Plan

If the extraction goes wrong:

1. **Before removal:** Create git tag `pre-parking-extraction` on truckerpro-web main branch
2. **Before table drop:** Take PostgreSQL backup of parking tables (`pg_dump --table=parking_*`)
3. **Revert to monolith:** `git revert` the removal commit on truckerpro-web, redeploy
4. **DNS rollback:** Remove parking.truckerpro.ca CNAME if Railway deploy fails

**Burn-in period:** After deploying the standalone app, run it in parallel for at least 48 hours before removing code from truckerpro-web. During burn-in:
- Verify all pages load correctly on parking.truckerpro.ca
- Test booking flow end-to-end
- Confirm Stripe webhook delivery
- Monitor Railway health checks

## Testing

- Unit tests for models and services
- API endpoint tests (locations, bookings, reviews)
- Auth flow tests (signup, login, owner dashboard access)
- Health/ready endpoint tests (already created)
- Stripe webhook tests (mock)
- Rate limiting tests on auth + API endpoints

## Implementation Order

### Phase 1: Build Standalone App (truckerpro-parking)
1. Fix scaffolding issues (user_loader, Celery app, config postgres:// fix, .env.example, CLAUDE.md)
2. Extract and adapt templates (update URLs, branding, canonical URLs)
3. Implement auth (signup, login, logout, password reset with bcrypt + Flask-Login)
4. Port public routes (landing, search, province, city, location detail)
5. Port API endpoints (locations search/filter with Haversine geo)
6. Port booking system (Stripe payments, tax calculation, webhook)
7. Port owner dashboard (list/manage spaces, revenue stats)
8. Port review system
9. Adapt seed data script
10. Deploy to Railway, configure parking.truckerpro.ca DNS
11. **Burn-in period (48+ hours)** — verify everything works

### Phase 2: Remove from truckerpro-web
12. Create git tag `pre-parking-extraction` on truckerpro-web
13. In ONE atomic commit: add 301 redirects + delete parking files + remove all parking references from app_full.py, public_page_routes.py, templates, robots.txt, locustfile
14. Deploy truckerpro-web, verify no startup errors
15. After confirming stability: add migration 087 to drop parking tables
16. Push truckerpro-parking to GitHub
