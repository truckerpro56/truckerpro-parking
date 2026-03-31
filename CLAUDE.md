# CLAUDE.md — Truck Parking Club

> **START HERE:** Read this file first before doing any work. Then read `docs/superpowers/specs/2026-03-24-truck-parking-club-extraction-design.md` for the full design spec.

## Overview
Standalone SaaS for Canadian truck parking directory and marketplace.
Extracted from truckerpro-web's /parkingclub module on 2026-03-25.
Domain: parking.truckerpro.ca (LIVE)
Repo: https://github.com/truckerpro56/truckerpro-parking

## Tech Stack
- Flask 2.3 / Python 3.11 / SQLAlchemy 2.0
- PostgreSQL 15 (Railway), Redis 7
- Stripe (payments), Google Maps (geo), Resend (email)
- Celery for background jobs
- Deployed on Railway via Docker

## Architecture
- Flask app factory in `app/__init__.py` (includes `@login_manager.user_loader`)
- Models in `app/models/` (User, ParkingLocation, ParkingBooking, ParkingReview, ParkingAvailability)
- API endpoints in `app/api/` (under /api/v1): locations, bookings, reviews, stripe_webhook, admin
- Page routes in `app/routes/` (public, auth, owner)
- Business logic in `app/services/` (geo_service, booking_service, payment_service, email_service)
- Background tasks in `app/tasks/` (Celery app + notifications)
- Constants in `app/constants.py` (PROVINCE_MAP, PROVINCIAL_TAX, AMENITY_LABELS, LOCATION_TYPE_LABELS)
- Seed data in `app/seed/locations.py` (75 Canadian truck parking locations)

## Key Endpoints
- `GET /` — Landing page (SEO-optimized, province cards, featured locations)
- `GET /search` — Search with filters
- `GET /<province>` — Province page
- `GET /<province>/<city>` — City page
- `GET /location/<slug>` — Location detail with reviews
- `GET /my-bookings` — Driver booking history (auth required)
- `GET /owner/dashboard` — Owner stats, listings, bookings (auth required)
- `GET /api/v1/locations` — JSON API with geo search, filters, pagination
- `POST /api/v1/bookings` — Create booking with Stripe payment (auth required)
- `POST /api/v1/reviews` — Submit review (auth required)
- `POST /api/v1/locations` — Create/update listing (auth required)
- `POST /api/v1/stripe/webhook` — Stripe webhook handler
- `POST /api/v1/admin/seed` — One-time seed endpoint (requires X-Admin-Key header)

## Rules
- Use SQLAlchemy ORM queries, not raw SQL
- Use `current_app.config['KEY']` for config values, never hardcode
- Use `Decimal` for money display, store as integer cents in DB
- All rates stored in cents (e.g., daily_rate=2500 = $25.00)
- Canadian tax: GST/HST/PST/QST calculated via PROVINCIAL_TAX in constants.py
- Rate limit auth endpoints (login, signup)
- CSRF exempt the API blueprint only
- Auth templates must include `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
- Run tests: `python -m pytest tests/ -v` (84 tests, all must pass)

## Related Projects
- **truckerpro-web** — Main TMS app. Old `/parkingclub/*` URLs 301 redirect to this app via `parking_redirects.py`
- **truckerpro-border** — Border Clearing System at border.truckerpro.app (same architectural pattern)

## Docs
- `docs/superpowers/specs/2026-03-24-truck-parking-club-extraction-design.md` — Full design spec
- `docs/superpowers/plans/2026-03-24-truck-parking-club-extraction.md` — Implementation plan (all 15 tasks complete)

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
