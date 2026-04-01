# Stops Site UI Redesign

**Date:** 2026-04-01
**Status:** Approved
**Domain:** stops.truckerpro.net

## Overview

Complete visual redesign of all stops.truckerpro.net templates. Replace bare semantic HTML + 19-line CSS with a polished blue/white theme matching the stops blog templates. Bootstrap 5.3.3, Font Awesome 6.7.2, Google Fonts Inter. No route or Python code changes — purely template work.

## Visual Identity

- Background: #f8fafc (light gray-blue)
- Cards: #ffffff with subtle shadow
- Accent: #2563eb (blue)
- Accent hover: #1d4ed8
- Text primary: #0f172a (dark navy)
- Text secondary: #64748b (slate)
- Border: #e2e8f0
- Navy (navbar/hero/footer): #0f2440
- Bootstrap 5.3.3 grid, Font Awesome 6.7.2 icons, Inter 400-800

## Architecture

All shared CSS lives in `base.html`'s `<style>` block. Page templates extend base and provide only page-specific content via `{% block content %}`. The external `stops.css` file is deleted.

## Files

```
Modify: app/templates/stops/base.html
Modify: app/templates/stops/home.html
Modify: app/templates/stops/country.html
Modify: app/templates/stops/state.html
Modify: app/templates/stops/city.html
Modify: app/templates/stops/stop_detail.html
Modify: app/templates/stops/brand_index.html
Modify: app/templates/stops/brand_detail.html
Modify: app/templates/stops/brand_state.html
Modify: app/templates/stops/highway_index.html
Modify: app/templates/stops/highway_detail.html
Modify: app/templates/stops/partials/stop_card.html
Modify: app/templates/stops/partials/pagination.html
Modify: app/templates/stops/partials/amenities_grid.html
Modify: app/templates/stops/partials/banner_tms.html
Modify: app/templates/stops/partials/banner_border.html
Modify: app/templates/stops/partials/banner_parking.html
Modify: app/templates/stops/partials/banner_fmcsa.html
Modify: app/templates/stops/partials/fuel_prices.html
Delete: app/static/stops/css/stops.css
```

## Component Designs

### base.html

Full HTML5 document with:
- CDN includes: Bootstrap 5.3.3 CSS/JS, Font Awesome 6.7.2, Google Fonts Inter
- GA4 tag G-RREBK9SZZJ
- Dark navy navbar (#0f2440) with gas-pump icon brand, nav links (US Stops, Canada, Brands, Highways, Blog)
- `{% block content %}` main area
- Full footer: 4-column grid (about, browse links, TruckerPro products, more), copyright
- All shared CSS in `<style>` block: reset, typography, cards, amenity tags, banners, pagination, responsive breakpoints
- `{% block head %}` for page-specific meta tags
- `{% block scripts %}` for page-specific JS
- Event delegation click handler for GA4 data-action tracking

### home.html

- Hero section: dark navy gradient, "Find Truck Stops Across the US & Canada" heading, search bar, stats counters (total stops, states, provinces, brands)
- Browse by Country: US and Canada cards with flag emoji and counts
- Popular States: pill-style links with stop counts
- Featured Stops: 3-column grid of stop_card partials
- Browse by Brand: 6-column brand cards with icons and counts
- CTA banner: TMS signup + border eManifest

### country.html

- Page heading with flag emoji (US or Canada)
- State/province grid: cards with name, stop count, link to state page
- Responsive 4-column grid (3 tablet, 2 mobile)

### state.html

- Breadcrumb: Home > Country > State
- Page heading with state name and stop count
- City filter pills (if multiple cities)
- Stop cards grid (3-column)
- Pagination at bottom
- Contextual banner (TMS or border)

### city.html

- Breadcrumb: Home > Country > State > City
- Page heading with city, state name
- Stop cards grid
- Contextual banner

### stop_detail.html

- Breadcrumb: Home > Country > State > City > Stop Name
- Stop header: name, brand badge, address, highway/exit
- Amenities grid with icons (full-size badges)
- Contextual banners (TMS, border, parking based on banner_service data)
- Fuel prices section (if available)
- Reviews section (if available)
- Nearby stops: 3-column grid of stop_cards
- Schema.org LocalBusiness JSON-LD

### brand_index.html

- Page heading: "Browse by Brand"
- Brand cards grid: icon, name, location count, link
- 6-column responsive grid

### brand_detail.html

- Breadcrumb: Home > Brands > Brand Name
- Brand header with icon and total count
- State filter pills
- Stop cards grid + pagination

### brand_state.html

- Breadcrumb: Home > Brands > Brand > State
- Heading, stop cards grid

### highway_index.html

- Page heading: "Browse by Highway"
- Highway pills/cards with stop counts
- Grouped by region or interstate number

### highway_detail.html

- Breadcrumb: Home > Highways > Highway
- Highway heading with stop count
- Stop cards listed in order along the route
- State groupings within highway

### Partials

**stop_card.html:**
- White card with dark navy header gradient
- Stop name (linked), city/state with location icon
- Highway and exit number with road icon
- Amenity tags row with Font Awesome icons
- Hover: subtle lift + shadow

**pagination.html:**
- Numbered page buttons with Previous/Next
- Active page highlighted in blue
- Bootstrap-style pagination component

**amenities_grid.html:**
- Icon-based badges: diesel, showers, scales, parking, WiFi, food, repair, DEF, laundry, ATM
- Color-coded by category or uniform blue accent
- Responsive wrap

**banner_*.html (tms, border, parking, fmcsa):**
- Full-width rounded banners matching CTA banner style
- Color-coded: TMS (blue), border (green), parking (purple), FMCSA (gray)
- Headline + description + CTA button
- data-action attributes for GA4 tracking

**fuel_prices.html:**
- Clean table or card layout showing fuel type, price, last updated
- Color-coded price indicators

## SEO

- Each page: proper `<title>`, `<meta description>`, `<link rel="canonical">`
- Open Graph meta tags on detail pages
- Schema.org LocalBusiness JSON-LD on stop detail
- Breadcrumb navigation for Google breadcrumbs

## GA4

- Same G-RREBK9SZZJ tag in base.html
- Event delegation for data-action clicks (no inline onclick)
- Banner click tracking via existing data-ga-event attributes

## No Changes

- No route changes (app/stops/routes.py unchanged)
- No model changes
- No API changes
- No new Python dependencies
- Template variable names unchanged — same data, new presentation
