# Truck Stops Directory — stops.truckerpro.net

**Date:** 2026-03-31
**Status:** Approved
**Host project:** truckerpro-parking (parking.truckerpro.ca)

## Overview

A truck stop directory serving 34K+ SEO pages at stops.truckerpro.net. Built as a new blueprint inside the existing Parking Club Flask app using host-based routing. Truck stop data lives in Parking Club's Postgres — no additional database cost. Initial data from Loves CSV import, expandable to other chains.

Driver contributions (fuel prices, reviews, photos, parking reports) included from launch with moderation controls.

Smart contextual banners on every page funnel traffic to paid products: TMS, border clearing, parking reservations, and FMCSA carrier lookup.

## 1. Architecture

### Host-Based Routing

Single Flask app serves two domains:

- `parking.truckerpro.ca` — existing Parking Club blueprints (unchanged)
- `stops.truckerpro.net` — new truck stops blueprints

A `before_request` middleware checks `request.host` and sets `g.site` to `"parking"` or `"stops"`. Each domain gets its own blueprints, templates, and static assets.

### Blueprint Registration

All blueprints register at the same URL prefixes. The `before_request` middleware on `g.site` determines which blueprint handles the request. Blueprints for the wrong domain return 404 via a decorator check.

```
# Existing (parking.truckerpro.ca only)
parking_public_bp   → /
parking_auth_bp     → /
parking_owner_bp    → /owner
parking_api_bp      → /api/v1

# New (stops.truckerpro.net only)
stops_public_bp     → /              (homepage, directory pages, individual stop pages)
stops_api_bp        → /api/v1        (truck stop data API, driver contributions)

# Shared (both domains)
auth_bp             → /              (login, signup, logout — shared User model)
```

### Template Directories

```
app/templates/
├── public/          (existing parking templates)
├── auth/            (existing, shared)
├── owner/           (existing)
├── stops/           (NEW — all stops.truckerpro.net templates)
│   ├── home.html
│   ├── state.html
│   ├── city.html
│   ├── stop_detail.html
│   ├── brand_index.html
│   ├── brand_state.html
│   ├── highway_index.html
│   ├── highway_detail.html
│   └── partials/
│       ├── banner_tms.html
│       ├── banner_border.html
│       ├── banner_parking.html
│       ├── banner_fmcsa.html
│       ├── stop_card.html
│       ├── amenities_grid.html
│       └── fuel_prices.html
└── seo/             (existing)
```

### Infrastructure

No new Railway services. Same Postgres, same Redis, same Gunicorn worker. Railway custom domain `stops.truckerpro.net` pointed at existing parking service.

Other services (truckerpro-web, border, FMCSA) can read truck stop data via `/api/v1/truck-stops` endpoints on stops.truckerpro.net if needed.

## 2. Data Model

### 2.1 `truck_stops` table

Core location data for every truck stop.

| Column | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-increment |
| brand | String(50) | loves, pilot_flying_j, ta_petro, independent, etc. Indexed |
| brand_display_name | String(100) | "Love's Travel Stops", "Pilot Flying J" |
| name | String(200) | "Love's Travel Stop #521" |
| slug | String(200) | Unique, indexed. "loves-521-dallas-tx" |
| store_number | String(50) | Nullable. Brand's internal number |
| address | String(300) | Street address |
| city | String(100) | Indexed |
| state_province | String(50) | Indexed. "TX", "ON" |
| postal_code | String(20) | |
| country | String(2) | "US" or "CA". Indexed |
| latitude | Float | Composite index with longitude |
| longitude | Float | |
| highway | String(50) | "I-35", "401". Indexed |
| exit_number | String(20) | "42", "42A" |
| direction | String(2) | N, S, E, W. Nullable |
| total_parking_spots | Integer | Nullable |
| truck_spots | Integer | Nullable |
| car_spots | Integer | Nullable |
| handicap_spots | Integer | Nullable |
| reserved_spots | Integer | Nullable |
| has_diesel | Boolean | Default True |
| has_gas | Boolean | Default False |
| has_def | Boolean | Default False |
| has_ev_charging | Boolean | Default False |
| has_showers | Boolean | Default False |
| shower_count | Integer | Nullable |
| has_scale | Boolean | Default False |
| scale_type | String(20) | "cat", "other". Nullable |
| has_repair | Boolean | Default False |
| has_tire_service | Boolean | Default False |
| has_wifi | Boolean | Default False |
| has_laundry | Boolean | Default False |
| restaurants | JSON | ["Subway", "Denny's"] |
| loyalty_programs | JSON | ["Love's My Love Rewards"] |
| hours_of_operation | JSON | {"mon": "24h", "tue": "24h", ...} |
| phone | String(20) | Nullable |
| website | String(300) | Nullable |
| photos | JSON | URL list |
| is_active | Boolean | Default True. Indexed |
| is_verified | Boolean | Default False |
| nearest_border_crossing | String(100) | Precomputed. Nullable |
| border_distance_km | Float | Precomputed. Nullable |
| parking_location_id | Integer FK | Nullable. Links to existing ParkingLocation if reservable |
| meta_title | String(200) | SEO |
| meta_description | String(500) | SEO |
| data_source | String(20) | csv_import, manual, api |
| created_at | DateTime(tz) | |
| updated_at | DateTime(tz) | |

**Indexes:** (latitude, longitude), brand, state_province, highway, slug (unique), is_active, city, country

### 2.2 `fuel_prices` table

Timestamped fuel price data, from imports or driver reports.

| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| truck_stop_id | Integer FK | Indexed |
| fuel_type | String(20) | diesel, regular, premium, def |
| price_cents | Integer | Price in cents |
| currency | String(3) | USD, CAD |
| reported_by | Integer FK | Nullable. FK to users |
| source | String(20) | import, driver, api |
| is_verified | Boolean | Default False |
| created_at | DateTime(tz) | |

**Auto-approve logic:** Driver-reported prices within 20% of last known price are auto-verified.

### 2.3 `truck_stop_reviews` table

Driver reviews with moderation.

| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| truck_stop_id | Integer FK | Indexed |
| user_id | Integer FK | |
| rating | Integer | 1-5, CheckConstraint |
| review_text | Text | |
| photos | JSON | URL list. Nullable |
| is_approved | Boolean | Default False |
| created_at | DateTime(tz) | |

**Unique constraint:** (truck_stop_id, user_id) — one review per driver per stop.

### 2.4 `truck_stop_reports` table

Driver-contributed updates (parking availability, amenity status, hours corrections).

| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| truck_stop_id | Integer FK | Indexed |
| user_id | Integer FK | |
| report_type | String(30) | parking_availability, amenity_status, hours_update, other |
| data | JSON | Flexible. e.g. {"available_spots": 12} or {"showers_working": false} |
| is_verified | Boolean | Default False |
| expires_at | DateTime(tz) | Nullable. Parking reports auto-expire after 4 hours |
| created_at | DateTime(tz) | |

### Relationship to Existing Models

`truck_stops` is independent from `parking_locations`. A truck stop may optionally link to a `ParkingLocation` via `parking_location_id` FK if it has reservable parking through Parking Club.

`fuel_prices`, `truck_stop_reviews`, and `truck_stop_reports` FK to `users` (the existing Parking Club User model). Drivers need a Parking Club account to contribute.

## 3. URL Structure & SEO Pages

### 3.1 Geographic Tree

```
/                                    → homepage (search, featured, stats)
/us                                  → US overview (state cards)
/canada                              → Canada overview (province cards)
/us/texas                            → state page (city list + all stops)
/us/texas/dallas                     → city page (all stops in Dallas)
/us/texas/dallas/loves-521           → individual stop page
/canada/ontario                      → province page
/canada/ontario/toronto/pilot-fj-18  → individual stop page
```

### 3.2 Brand Tree

```
/brands                              → all brands overview
/brands/loves                        → all Loves locations
/brands/loves/texas                  → Loves in Texas
/brands/loves/texas/dallas           → Loves in Dallas (if enough stops)
/brands/pilot-flying-j               → all Pilot/Flying J
/brands/ta-petro                     → all TA/Petro
```

### 3.3 Highway Tree

```
/highways                            → major interstates/highways index
/highways/i-35                       → all stops on I-35
/highways/i-35/exit-42               → stops at exit 42
/highways/401                        → Highway 401 (Canada)
```

### 3.4 Cross-Linking Strategy

Every page links to related pages across all three trees:

- **Stop detail** → nearby stops, same-brand stops, same-highway stops, city page, state page
- **City page** → brand-filtered views ("Loves in Dallas"), nearby cities, state page
- **State page** → all cities, all brands in state, major highways
- **Brand page** → all states with this brand, highway presence
- **Highway page** → all cities along route, all exits with stops
- **FMCSA cross-link** → "Carriers operating near this stop" → fmcsa.truckerpro.net

### 3.5 Page Count Estimate

| Type | Count |
|---|---|
| Individual stops | ~10,000 |
| City pages | ~5,000 |
| State/province pages | ~60 |
| Brand + state combos | ~500 |
| Brand + city combos | ~8,000 |
| Highway pages | ~200 |
| Highway + exit pages | ~10,000 |
| Index pages | ~10 |
| **Total** | **~34,000+** |

Grows with each new data source added.

## 4. Smart Banners

### Banner Service

A `BannerService` class takes a `truck_stop` object and returns contextual banners with tailored copy.

### 4.1 TMS Banner (every page, top position)

Target: **tms.truckerpro.ca**

| Stop Context | Copy |
|---|---|
| Near major freight corridor | "Dispatching loads on I-35? Manage your fleet →" |
| In a major metro | "Running routes through Dallas? Track every load →" |
| Near distribution hubs | "Fleet parked here? Automate dispatch →" |
| Default | "Trucking company? Manage your fleet with TruckerPro TMS →" |

Context detection: `highway` field for corridors, `city`+`state_province` for metros. Hardcoded list of major freight corridors (I-35, I-95, I-10, I-40, I-80, 401, etc.) and metro areas.

### 4.2 Border Banner (within 100km of a crossing)

Target: **border.truckerpro.ca**

| Stop Context | Copy |
|---|---|
| US side, near crossing | "23km from Peace Bridge — clear customs faster →" |
| Canadian side, near crossing | "Pre-clear at Pacific Highway — skip the line →" |
| Multiple crossings nearby | "Near 3 border crossings — compare wait times →" |

Context detection: `nearest_border_crossing` and `border_distance_km` fields (precomputed at import).

### 4.3 Parking Club Banner (conditional)

Target: **parking.truckerpro.ca**

| Stop Context | Copy |
|---|---|
| Has linked parking_location | "Reserve parking at this stop →" |
| No reservable parking | "Find reservable parking nearby →" |
| High-demand area | "Parking fills fast here — reserve ahead →" |

Context detection: `parking_location_id` FK presence, city population data.

### 4.4 FMCSA Banner (bottom of page)

Target: **fmcsa.truckerpro.net**

| Stop Context | Copy |
|---|---|
| Default | "Look up carriers at this stop →" |
| Near weigh station | "Check carrier safety scores before the scale →" |

## 5. Data Pipeline

### 5.1 CSV Import

CLI commands for importing chain data:

```bash
flask import-stops loves --file path/to/loves.csv
flask import-stops pilot --file path/to/pilot.csv
flask import-stops ta-petro --file path/to/ta.csv
```

Each brand gets a mapper function that normalizes CSV columns to the `truck_stops` schema.

**Upsert logic:** Match by `brand` + `store_number`. Existing records update, new records insert. `data_source` set to `csv_import`.

**Geocoding:** If lat/lng missing from CSV, geocode via Google Maps API (existing `geo_service.py`).

**Slug generation:** Auto-generated as `{brand}-{store_number}-{city}-{state}`. Uniqueness enforced with counter suffix if needed (existing `slugify` in `geo_service.py`).

### 5.2 Border Distance Precomputation

Hardcoded list of ~120 US/Canada border crossings with coordinates. On import:

1. For each truck stop, calculate haversine distance to all crossings
2. Store nearest crossing name and distance in `nearest_border_crossing` and `border_distance_km`
3. Re-run as batch command: `flask compute-border-distances`

### 5.3 Manual Additions

Admin endpoint: `POST /api/v1/admin/truck-stops`
- Same `X-Admin-Key` header auth as existing seed endpoint
- Accepts single or bulk JSON
- `data_source` set to `manual`

### 5.4 Driver Contributions

**Fuel prices:**
- `POST /api/v1/truck-stops/<id>/fuel-prices` (auth required)
- Auto-approve if within 20% of last known price for that fuel type
- Otherwise `is_verified=False`

**Reviews:**
- `POST /api/v1/truck-stops/<id>/reviews` (auth required)
- One review per driver per stop
- `is_approved=False` until moderated
- Approved reviews show on stop detail page with rating aggregation

**Reports (parking, amenity status, hours):**
- `POST /api/v1/truck-stops/<id>/reports` (auth required)
- Parking availability reports: `expires_at` set to 4 hours from submission
- Other reports: `is_verified=False` until moderated

### 5.5 Sitemap Generation

Dynamic XML sitemaps split by type:

```
/sitemap.xml              → sitemap index
/sitemap-stops.xml        → individual stop pages (paginated if >50K)
/sitemap-cities.xml       → city directory pages
/sitemap-states.xml       → state/province pages
/sitemap-brands.xml       → brand directory pages
/sitemap-highways.xml     → highway directory pages
```

Auto-updates as stops are added. `lastmod` from `updated_at`.

## 6. Design Direction

- **Light theme, card-based layout** — clean, professional, not vibecoded
- **Directory/data feel** — distinct from the .ca product family
- **Proper typography hierarchy** — not everything bold, real spacing system
- **Subtle borders and shadows** — no gratuitous gradients or drop shadows
- **No emoji as UI icons** — use proper SVG icons or icon font
- **Contextual smart banners** — styled to stand out but not feel like ads

## 7. Shared Auth

Parking Club's existing User model and Flask-Login setup is shared. Drivers who want to contribute (reviews, fuel prices, reports) need a Parking Club account. Existing login/signup pages serve both domains.

## 8. GA4 Analytics

Use existing GA4 property (G-RREBK9SZZJ). Events:

- `page_view` with custom dimensions: brand, state, city, highway
- `banner_click` with target (tms, border, parking, fmcsa)
- `fuel_price_submit`
- `review_submit`
- `report_submit`
- `search` with query/filters
