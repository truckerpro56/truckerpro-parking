# Banner Redesign — Design Spec

**Date:** 2026-04-04
**Scope:** TMS, Border, Parking, FMCSA banners across stops.truckerpro.net and truckerpro-web blog/insights pages
**Goal:** Replace generic, low-conversion banners with 3 distinct copy/style variants that rotate daily, with layered animations.

## Problem

Current banners are bland and generic — they read like typical AI-generated promotional blocks. CTAs are weak, value props are unclear, and the static presentation causes banner blindness on repeat visits.

## Solution

12 banner variants (4 products × 3 styles) with day-based rotation and 3-layer animation.

## Banner Variants

### Style A — Social Proof Lead

Lead with a compelling number. The stat does the selling.

| Product | Headline | Description | CTA |
|---|---|---|---|
| TMS | "527 carriers switched this quarter." | Dispatch, ELD, compliance, invoicing — one platform. | Start Free Trial |
| Border | "12,400 manifests filed this month." | ACE & ACI eManifest in under 5 minutes. Zero penalties. | File Your First Manifest |
| Parking | "2,100 spots booked last week." | 75+ verified lots across Canada. Reserve before you arrive. | Reserve a Spot |
| FMCSA | "4.4 million carriers. One search." | CSA scores, inspections, crash records, operating authority. | Look Up a Carrier |

Sub-CTA text: "No credit card" (TMS), "Free to start" (Border), none (Parking/FMCSA).

### Style B — Pain Point Hook

Open with a relatable pain question, then reframe with a solution.

| Product | Hook | Headline | CTA |
|---|---|---|---|
| TMS | "Still dispatching from spreadsheets?" | Your fleet deserves better than copy-paste logistics. | See How It Works |
| Border | "Stuck at the crossing again?" | Pre-clear customs before you even hit the border. | See How It Works |
| Parking | "Circled the lot three times?" | Book your spot before you leave the shipper. | Find Parking Now |
| FMCSA | "Who's hauling your freight?" | Check any carrier's safety record in 10 seconds. | Run a Free Check |

Sub-CTA text: "2 min demo" (TMS), "5 min setup" (Border), none (Parking/FMCSA).

### Style C — Bold Typographic

Minimal. Big type, ghost watermark, outline CTA. Highest design quality, lowest word count.

| Product | Watermark | Headline | Features line | CTA |
|---|---|---|---|---|
| TMS | TMS | "One app. Whole fleet." | Dispatch · ELD · IFTA · Invoicing / 14 days free · No card required | Get Started → |
| Border | ACE | "File once. Cross fast." | ACE · ACI · PAPS · PARS / Free to start · CBSA & CBP compliant | Get Started → |
| Parking | P | "Park safe. Sleep easy." | 75+ Canadian locations · Gated lots / Online booking · Driver reviews | Find Parking → |
| FMCSA | DOT | "Know your carrier." | CSA · BASICs · Inspections · Crashes / 4.4M profiles · Free instant lookup | Lookup Carrier → |

Watermark is positioned top-right at ~7rem, opacity 0.04.

## Rotation Logic

Day-based: `day_of_year % 3` determines the active style (0=A, 1=B, 2=C). All banners on all pages show the same style for a given day. Changes at midnight UTC.

Implemented in `banner_service.py` — each banner dict gets a `variant` field (`'a'`, `'b'`, or `'c'`) and the corresponding `copy`, `headline`, `hook` (style B only), `cta`, and `sub_cta` fields.

## Animation

Three layered animations, all CSS-only except the scroll entrance:

### 1. Gradient Shift (background)

```css
.banner::before {
  background-size: 300% 300%;
  animation: gradientShift 8s ease infinite;
}
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

Gradient colors per product:
- TMS: `linear-gradient(-45deg, #0b1020, #1a0c00, #2d1200, #ff6b35, #0b1020)`
- Border: `linear-gradient(-45deg, #051a14, #001a14, #002d24, #10b981, #051a14)`
- Parking: `linear-gradient(-45deg, #1a0035, #0d001a, #2d0050, #8b5cf6, #1a0035)`
- FMCSA: `linear-gradient(-45deg, #111827, #0a0f1a, #1f2937, #4b5563, #111827)`

### 2. Glow Pulse (border glow)

```css
.banner::after {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 17px;
  z-index: -1;
  animation: glowPulse 3s ease-in-out infinite;
}
```

Glow colors per product (at peak):
- TMS: `box-shadow: 0 0 15px rgba(255,107,53,0.15), 0 0 40px rgba(255,107,53,0.05)`
- Border: `box-shadow: 0 0 15px rgba(16,185,129,0.15), 0 0 40px rgba(16,185,129,0.05)`
- Parking: `box-shadow: 0 0 15px rgba(139,92,246,0.15), 0 0 40px rgba(139,92,246,0.05)`
- FMCSA: `box-shadow: 0 0 15px rgba(107,114,128,0.1), 0 0 40px rgba(107,114,128,0.03)`

### 3. Scroll Entrance (IntersectionObserver)

Banners start with `opacity:0; transform:translateY(30px)`. When they enter the viewport (threshold 0.2), they animate to full opacity over 0.6s with a 150ms stagger between siblings.

```css
@keyframes entrance {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
```

### Eyebrow Dot Pulse

Small accent dot next to the product label pulses subtly (2s loop).

## Color Scheme

Unchanged from current design — one accent color per product:

| Product | Accent | Filled CTA bg | Outline CTA border |
|---|---|---|---|
| TMS | `#ff6b35` | `#ff6b35` | `#ff6b35` |
| Border | `#10b981` | `#10b981` | `#10b981` |
| Parking | `#8b5cf6` | `#8b5cf6` | `#8b5cf6` |
| FMCSA | `#6b7280` | `#6b7280` | `#6b7280` / text `#9ca3af` |

## HTML Structure

All 3 styles share a common wrapper. The variant determines inner content.

```html
<a href="{{ banner.url }}" class="promo-banner promo-{{ banner.type }}"
   {% if banner.url.startswith('http') %}target="_blank" rel="noopener"{% endif %}>
  <!-- Style C watermark (only if variant == 'c') -->
  {% if banner.variant == 'c' %}
    <div class="promo-watermark">{{ banner.watermark }}</div>
  {% endif %}

  <div>
    {% if banner.variant != 'c' %}
      <div class="promo-eyebrow">
        <span class="promo-dot"></span>
        <span>{{ banner.eyebrow }}</span>
      </div>
    {% endif %}
    {% if banner.variant == 'b' %}
      <div class="promo-hook">{{ banner.hook }}</div>
    {% endif %}
    <div class="promo-headline">{{ banner.headline }}</div>
    {% if banner.variant == 'c' %}
      <div class="promo-accent-bar"></div>
    {% endif %}
    <div class="promo-desc">{{ banner.desc }}</div>
  </div>

  <div class="promo-cta-row">
    <span class="promo-btn {% if banner.variant == 'c' %}promo-btn-outline{% endif %}">
      {{ banner.cta }}{% if banner.variant == 'c' %} →{% endif %}
    </span>
    {% if banner.sub_cta %}
      <span class="promo-sub-cta">{{ banner.sub_cta }}</span>
    {% endif %}
  </div>
</a>
```

## File Changes

### truckerpro-parking (stops.truckerpro.net)

1. **`app/services/banner_service.py`** — Refactor to return variant-aware banner dicts. Add `_get_variant()` function using `day_of_year % 3`. Each `_*_banner()` function returns all 3 copy sets, with the active variant selected. New fields: `variant`, `headline`, `hook`, `desc`, `cta`, `sub_cta`, `watermark`, `eyebrow`.

2. **`app/templates/stops/partials/banner_tms.html`** — Replace current single-style template with variant-aware template using the shared HTML structure above.

3. **`app/templates/stops/partials/banner_border.html`** — Same treatment.

4. **`app/templates/stops/partials/banner_parking.html`** — Same treatment.

5. **`app/templates/stops/partials/banner_fmcsa.html`** — Same treatment.

6. **`app/templates/stops/base.html`** — Replace current `.native-promo-*` CSS with new animated banner CSS. Add entrance JS (IntersectionObserver) in a `<script>` block.

### truckerpro-web (blog/insights)

7. **`app/templates/blog/post.html`** — Replace static `.promo-banners` grid with new variant-aware templates. Add rotation logic via Jinja (`now().timetuple().tm_yday % 3`). Update inline CSS to match new animation system.

8. **`app/templates/blog/index.html`** — Same treatment.

9. **`app/templates/insights/article.html`** — Same treatment.

10. **`app/templates/insights/index.html`** — Same treatment.

Note: truckerpro-web doesn't import `banner_service.py` — the blog/insights pages use hardcoded banner markup. The variant rotation is computed inline with Jinja: `{% set variant = ['a','b','c'][now().timetuple().tm_yday % 3] %}`.

## Testing

- Existing test suite (280 tests) must continue to pass
- Manual verification: change system date to confirm rotation works across all 3 variants
- Visual check on both stops.truckerpro.net and blog/insights pages
- Responsive check: banners stack properly on mobile (<768px)
- Animation performance: no jank on low-end devices (gradient animation uses GPU-composited properties)

## Mockups

Live animated preview saved at:
`.superpowers/brainstorm/96497-1775287477/content/animated-banners.html`
