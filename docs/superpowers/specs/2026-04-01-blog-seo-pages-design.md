# Static SEO Blog for Parking & Stops Domains

**Date:** 2026-04-01
**Status:** Approved
**Domains:** parking.truckerpro.ca, stops.truckerpro.net

## Overview

Static SEO blog system serving 40+ markdown-based articles across two domains. Each domain gets its own content, templates, and visual identity. Posts funnel traffic to the main TMS (www.truckerpro.ca / tms.truckerpro.ca) and border clearing app (border.truckerpro.ca) via strong CTAs.

No database. No CMS. Markdown files with YAML frontmatter, rendered once at startup, cached in memory.

## Architecture

```
app/blog/
├── __init__.py          # Blog blueprint, registers routes
├── routes_parking.py    # /blog, /blog/<slug> for parking domain
├── routes_stops.py      # /blog, /blog/<slug> for stops domain
├── renderer.py          # Markdown → HTML, frontmatter parser, CTA injection
├── content/
│   ├── parking/         # 20+ .md files for parking.truckerpro.ca
│   └── stops/           # 20+ .md files for stops.truckerpro.net

app/templates/
├── blog_parking/        # Parking domain blog templates
│   ├── index.html       # Blog listing page (dark/green theme)
│   └── post.html        # Individual post
└── blog_stops/          # Stops domain blog templates
    ├── index.html       # Blog listing page (blue/white theme)
    └── post.html        # Individual post
```

Host-based routing via existing `g.site` middleware determines which blueprint handles `/blog` and `/blog/<slug>`. Both domains share the same URL paths but serve different content and templates.

## Markdown Frontmatter Schema

```yaml
---
title: "Safe Overnight Truck Parking in Canada: Complete Guide"
slug: safe-overnight-truck-parking-canada
category: guides
meta_description: "Find safe overnight truck parking across Canada. 75+ locations, regulations by province, and booking tips."
meta_keywords: "truck parking canada, overnight truck parking, safe truck parking"
date: "2026-04-01"
author: "TruckerPro Team"
featured_image: "/static/blog/parking/safe-overnight.jpg"
cta_primary:
  text: "Try TruckerPro TMS Free"
  url: "https://www.truckerpro.ca/signup"
cta_secondary:
  text: "File eManifest Online"
  url: "https://border.truckerpro.ca"
related_slugs:
  - overnight-parking-regulations-ontario
  - truck-parking-near-border-crossings
---

# Article body in markdown...
```

### Categories

- **Parking domain:** guides, regulations, safety, industry, tips
- **Stops domain:** guides, fuel, routes, reviews, tips

## CTA Components (3 per post)

### 1. Hero CTA (top of post, below title)
Full-width banner with gradient background. Primary CTA button + secondary link. Appears before the article body.

### 2. Mid-Article Break
Injected at `<!-- cta -->` marker if present, otherwise auto-injected after 3rd `<h2>`. Inline card style.

### 3. Sticky Bottom Bar
Fixed to viewport bottom, appears after user scrolls past hero CTA. Dismissible. Compact single line.

All CTAs populated from frontmatter `cta_primary` and `cta_secondary` fields. Templates handle layout per domain.

## Content Plan — Parking Domain (20 posts)

### Pillar Guides (5)
1. Safe Overnight Truck Parking in Canada: Complete Guide
2. Truck Parking Regulations by Province: What Every Driver Needs to Know
3. The Ultimate Guide to Cross-Border Trucking Between US and Canada
4. Fleet Parking Management: Reducing Costs and Improving Driver Retention
5. LCV and Oversized Vehicle Parking: Where to Find Space in Canada

### How-To / Practical (10)
6. How to Book Truck Parking Online in Under 2 Minutes
7. Finding Truck Parking Near Major Canadian Border Crossings
8. How to File ACE and ACI eManifest for Your Cross-Border Loads
9. Truck Parking Near Toronto: Best Options for GTA Drivers
10. Winter Truck Parking Safety Tips for Canadian Highways
11. How to Choose the Right TMS for Your Small Carrier Fleet
12. Truck Parking Near Montreal and Quebec City
13. Overnight Parking Options Along the Trans-Canada Highway
14. How to Track Your Fleet in Real-Time with ELD Integration
15. Secure Truck Parking Near Vancouver and BC Ports

### Industry / SEO Magnets (5)
16. Why Truck Parking Shortages Are Getting Worse in Canada (2026)
17. Top 10 Busiest Truck Routes in Canada and Where to Park
18. The Real Cost of Unsafe Truck Parking: Theft, Fines, and Fatigue
19. How Owner-Operators Can Save Money on Parking and Fuel
20. FMCSA Compliance for Canadian Carriers Operating in the US

## Content Plan — Stops Domain (20 posts)

### Pillar Guides (5)
1. The Complete Guide to Truck Stops Across America
2. Best Truck Stops in Canada: Province-by-Province Directory
3. Cross-Border Trucking: Best Stops Near US-Canada Border Crossings
4. The Ultimate Fuel Savings Guide for Long-Haul Truckers
5. Truck Stop Amenities Ranked: What Drivers Actually Care About

### How-To / Practical (10)
6. Best Truck Stops on I-95: From Maine to Florida
7. Best Truck Stops on I-35: Texas to Minnesota
8. How to Find Diesel Prices in Real Time Before You Stop
9. How to Plan Your Route Around Truck Stop Locations
10. Best Truck Stops With Overnight Parking on I-40
11. Love's vs Pilot vs TA: Comparing America's Big Three Truck Stop Chains
12. How to File eManifest When Crossing into Canada
13. Best Truck Stops With Truck Repair and Service Bays
14. How to Use TMS Software to Optimize Your Fuel Stops
15. Best Truck Stops Near Los Angeles and California Ports

### Industry / SEO Magnets (5)
16. Why Fuel Prices Vary So Much Between Truck Stops (2026)
17. The Rise of EV Charging at Truck Stops: What Fleets Need to Know
18. How Fleet Managers Use TMS to Cut Fuel Costs by 15%
19. Driver Retention Starts at the Truck Stop: What Carriers Get Wrong
20. FMCSA Hours of Service Rules and How They Affect Your Stops

## SEO

### On-Page (per post)
- `<title>` — frontmatter title + " | Truck Parking Club" or " | Truck Stops Directory"
- `<meta name="description">` — frontmatter `meta_description` (max 160 chars)
- `<meta name="keywords">` — frontmatter `meta_keywords`
- `<link rel="canonical">` — full URL
- Open Graph + Twitter Card meta tags
- Schema.org `BlogPosting` JSON-LD (headline, author, datePublished, image, publisher)

### URL Structure
- `parking.truckerpro.ca/blog` — parking index
- `parking.truckerpro.ca/blog/<slug>` — parking post
- `stops.truckerpro.net/blog` — stops index
- `stops.truckerpro.net/blog/<slug>` — stops post

### Sitemap
- Blog posts added to each domain's existing `/sitemap.xml`
- `<lastmod>` from frontmatter `date`
- `<priority>0.7</priority>` for posts, `0.8` for index

### Internal Linking
- `related_slugs` renders "Related Articles" cards at post bottom
- Index page shows all posts grouped by category
- Category filter links on index (`/blog?category=guides`)

## GA4 Analytics (G-RREBK9SZZJ)

Base GA4 tag on all blog pages (both domains). Custom events:

| Event | Parameters |
|-------|-----------|
| `blog_view` | post slug, category, domain |
| `blog_cta_click` | CTA position (hero/mid/sticky), target URL, post slug |
| `blog_related_click` | clicked related article slug |
| `blog_scroll_depth` | 25%, 50%, 75%, 100% thresholds |
| `blog_time_on_page` | 30s, 60s, 120s, 300s marks |

All events use `data-action` attributes + event delegation (no inline onclick per CSP policy).

## Renderer

### `app/blog/renderer.py`
- On app startup, scans `content/parking/` and `content/stops/` directories
- Parses each `.md` file: YAML frontmatter → dict, markdown body → HTML
- Markdown extensions: `fenced_code`, `tables`
- Stores all posts in-memory dict keyed by `(domain, slug)`
- Mid-article CTA injection: splits HTML at `<!-- cta -->` or after 3rd `<h2>`
- Helper functions:
  - `get_post(domain, slug)` → single post dict or None
  - `get_all_posts(domain, category=None)` → list sorted by date descending
  - `get_related_posts(domain, slugs)` → list of related post dicts

### Caching
- All content loaded once at startup — no per-request file I/O
- Content only changes on deploy, no cache invalidation needed

## Templates

### Parking (`blog_parking/`)
- `index.html` — dark/green theme matching parking site. Hero section, category filter pills, post cards grid, CTA banners between rows
- `post.html` — breadcrumb (Home → Blog → Category → Title), hero CTA, article body with mid CTA, related articles, sticky bar, BlogPosting JSON-LD

### Stops (`blog_stops/`)
- `index.html` — blue/white theme matching stops site. Same layout structure, different visual identity
- `post.html` — same component structure, stops branding and canonical URLs

### Shared Patterns
- `data-action` attributes for all click tracking (CSP-safe)
- GA4 snippet in both templates
- Responsive mobile-first grid
- No shared base template; each stands alone

## Dependencies

- `markdown` — pip package for .md → HTML
- `pyyaml` — YAML frontmatter parsing (may already be installed)

## Funnel Strategy

Every post has two funnel targets:
- **Primary (always):** TMS signup at www.truckerpro.ca
- **Secondary (contextual):** varies by post topic
  - Border/cross-border posts → border.truckerpro.ca
  - Parking posts → parking.truckerpro.ca booking
  - FMCSA/compliance posts → truckerpro.net carrier lookup
  - Fleet management posts → tms.truckerpro.ca
