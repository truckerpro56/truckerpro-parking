# Route Planner Enhancements — Design Spec

**Date:** 2026-04-04
**Page:** stops.truckerpro.net/route-planner

## Summary

Enhance the route planner to show all truck stops, rest areas, and weigh stations on the map at page load — browseable without planning a route. Add a filter panel to toggle visibility by brand/category, Google Places autocomplete on address inputs, brand logo map markers, and marker clustering for performance.

## Current State

- Map loads empty, shows pins only after a route is planned
- No autocomplete on origin/destination inputs
- All pins are generic colored circles (blue=stop, green=rest, amber=weigh)
- No way to filter by brand or category
- ~1,800 truck stops, ~1,900 rest areas, ~760 weigh stations in the database

## Design Decisions

| Decision | Choice |
|----------|--------|
| Filter panel style | Compact toggle list — checkboxes with colored dots |
| Autocomplete scope | North America only (US + Canada) |
| Pin style | Actual brand logos as custom markers |
| Data loading | All pins on page load, Redis-cached |
| Clustering | Yes, via @googlemaps/markerclusterer |

---

## 1. Map Pins API

### Endpoint

`GET /api/v1/map-pins`

Returns all active truck stops, rest areas, and weigh stations as minimal JSON for map rendering.

### Response

```json
{
  "truck_stops": [
    {"id": 1, "name": "Love's #123", "brand": "loves", "lat": 41.23, "lng": -96.01, "city": "Omaha", "state": "NE", "url": "/us/nebraska/omaha/loves-123"}
  ],
  "rest_areas": [
    {"id": 1, "name": "I-80 Rest Area", "lat": 41.10, "lng": -96.50, "state": "NE", "url": "/rest-areas/nebraska/i-80-rest-area"}
  ],
  "weigh_stations": [
    {"id": 1, "name": "I-80 Weigh Station", "lat": 41.05, "lng": -96.80, "state": "NE", "url": "/weigh-stations/nebraska/i-80-weigh-station"}
  ],
  "counts": {"truck_stops": 1847, "rest_areas": 1900, "weigh_stations": 760}
}
```

Only the fields needed for map rendering — keep the payload small (~200KB).

### Caching

- Redis key: `map_pins:all` 
- TTL: 1 hour (3600s)
- Cache stores the serialized JSON response
- Invalidation: not needed — hourly refresh is sufficient since stop data changes rarely
- Fallback: if Redis is unavailable, query Postgres directly (no error, just slower)

### Rate Limiting

No rate limiting — this is a cacheable GET. Add `Cache-Control: public, max-age=300` header so browsers cache for 5 minutes too.

---

## 2. Filter Panel (Sidebar)

### Location

Below the "Plan My Route" form, above the route results area. Visible at all times (before and after route planning).

### Layout

Compact toggle list style:

```
──────────────────────────
  SHOW ON MAP
──────────────────────────
  [x] ● Love's
  [x] ● Pilot Flying J  
  [x] ● TA / Petro
  [x] ● Other Brands
  ────────────────────
  [x] ● Rest Areas
  [x] ● Weigh Stations
  
  Select All · Clear All
──────────────────────────
```

### Behavior

- All layers ON by default at page load
- Toggling a checkbox immediately shows/hides that layer's markers on the map
- "Other Brands" groups: Flying J, Petro, Ambest, Husky, Esso, Shell, Independent
- "Select All" checks all, "Clear All" unchecks all
- After a route is planned, filters still work — they control visibility of the route-result markers too
- Filter state is purely client-side (no API calls on toggle)

### Brand-to-Color Mapping

| Brand | Color | Hex |
|-------|-------|-----|
| Love's | Red | #e11d48 |
| Pilot Flying J | Orange | #f97316 |
| TA / Petro | Blue | #3b82f6 |
| Other Brands | Purple | #8b5cf6 |
| Rest Areas | Green | #10b981 |
| Weigh Stations | Amber | #f59e0b |

---

## 3. Google Places Autocomplete

### Setup

Add `places` to the Google Maps libraries parameter:
```
libraries=geometry,places
```

### Implementation

Attach `google.maps.places.Autocomplete` to both `#route-origin` and `#route-destination` inputs.

Options:
```js
{
  types: ['geocode', 'establishment'],
  componentRestrictions: { country: ['us', 'ca'] }
}
```

This restricts suggestions to US and Canada addresses/places.

### UX

- Autocomplete dropdown appears as user types (standard Google behavior)
- On place selection, update the input value with the formatted address
- Enter key still triggers route planning (existing behavior)
- No changes needed to the backend — it already accepts free-text addresses and passes them to Google Directions API

---

## 4. Brand Logo Map Markers

### Assets

Add 32x32 PNG pin icons to `app/static/stops/pins/`:

```
app/static/stops/pins/
├── loves.png
├── pilot.png
├── ta-petro.png
├── other.png          (generic truck stop icon, purple)
├── rest-area.png      (green tree/bench icon)
└── weigh-station.png  (amber scale icon)
```

For Love's, Pilot Flying J, and TA/Petro — use simplified versions of their actual brand logos sized for map pins. For the others, use clean generic icons with the appropriate brand color.

### Marker Creation

Replace the current `google.maps.SymbolPath.CIRCLE` markers with `google.maps.Marker` using custom icon:

```js
new google.maps.Marker({
  position: {lat, lng},
  map: map,
  icon: {
    url: '/static/stops/pins/loves.png',
    scaledSize: new google.maps.Size(28, 28),
    anchor: new google.maps.Point(14, 14)
  },
  title: stop.name
});
```

### Brand Key to Icon Mapping

```js
var PIN_ICONS = {
  loves: '/static/stops/pins/loves.png',
  pilot_flying_j: '/static/stops/pins/pilot.png',
  flying_j: '/static/stops/pins/pilot.png',        // same icon
  ta_petro: '/static/stops/pins/ta-petro.png',
  petro: '/static/stops/pins/ta-petro.png',         // same icon
  _default: '/static/stops/pins/other.png',         // ambest, husky, esso, shell, independent
  rest_area: '/static/stops/pins/rest-area.png',
  weigh_station: '/static/stops/pins/weigh-station.png'
};
```

---

## 5. Marker Clustering

### Library

Use `@googlemaps/markerclusterer` via CDN:
```html
<script src="https://unpkg.com/@googlemaps/markerclusterer/dist/index.min.js"></script>
```

### Behavior

- All markers are added to a `MarkerClusterer` instance
- Zoomed-out views show cluster circles with counts (e.g., "47")
- Zooming in expands clusters into individual brand-logo pins
- Clustering groups all marker types together (stops + rest areas + weigh stations)
- When a filter is toggled off, those markers are removed from the clusterer; toggled on = re-added

### Configuration

```js
new markerClusterer.MarkerClusterer({
  map: map,
  markers: allMarkers,
  algorithmOptions: { maxZoom: 14 }
});
```

Max zoom 14 means clusters fully expand by zoom level 14 — individual pins visible at city-level zoom.

---

## 6. Page Load Flow

```
1. Page loads → init map (centered on North America, zoom 4)
2. Fetch GET /api/v1/map-pins
3. Create all markers with brand-logo icons
4. Add markers to MarkerClusterer
5. Show filter panel with all toggles checked
6. User browses map, toggles filters
7. (Optional) User enters origin/destination with autocomplete
8. User clicks "Find Stops Along Route"
9. POST /api/v1/plan-route (existing endpoint, no changes)
10. Draw route polyline on map
11. Show route results in sidebar tabs (existing behavior)
12. Markers from step 3 remain visible — filters still work
```

---

## 7. InfoWindow on Pin Click

When a user clicks a brand-logo pin, show an InfoWindow popup with:

```
┌─────────────────────────┐
│ Love's Travel Stop #234 │
│ Oklahoma City, OK       │
│ I-40 Exit 145           │
│ View details →          │
└─────────────────────────┘
```

The "View details" link goes to the stop's detail page. This reuses the existing `buildInfoWindow()` function pattern.

---

## 8. Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `app/stops_api/map_pins.py` | Create | New API endpoint with Redis caching |
| `app/stops_api/__init__.py` | Modify | Register map_pins routes |
| `app/templates/stops/route_planner.html` | Modify | Add filter panel HTML, autocomplete, clustering, brand pins, page-load fetch |
| `app/static/stops/pins/*.png` | Create | 6 brand/category pin icons (32x32) |
| `tests/test_map_pins.py` | Create | API endpoint tests |

No backend changes to the existing route planner API — it continues to work as-is.

---

## 9. Out of Scope

- Filtering by amenity (diesel, showers, scale) — future enhancement
- Saving filter preferences (localStorage or account) — future enhancement  
- Directions/navigation turn-by-turn — already handled by Google
- Real-time weigh station open/closed status — no data source
- Fuel price overlays — separate feature
