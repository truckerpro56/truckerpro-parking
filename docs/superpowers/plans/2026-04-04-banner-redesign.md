# Banner Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace generic promo banners with 12 high-conversion variants (4 products × 3 styles) that rotate daily with layered CSS animations.

**Architecture:** Refactor `banner_service.py` to return variant-aware dicts (headline, hook, desc, cta, watermark). Templates use a single shared partial with Jinja conditionals per variant. truckerpro-web blog/insights pages get the same treatment with inline Jinja rotation logic.

**Tech Stack:** Flask/Jinja2, CSS animations, IntersectionObserver (vanilla JS)

**Spec:** `docs/superpowers/specs/2026-04-04-banner-redesign-design.md`

---

## File Structure

### truckerpro-parking (stops.truckerpro.net)

| File | Action | Responsibility |
|------|--------|----------------|
| `app/services/banner_service.py` | Modify | Add `_get_variant()`, expand each `_*_banner()` to return 3 copy sets |
| `tests/test_banner_service.py` | Modify | Add tests for variant rotation + new dict fields |
| `app/templates/stops/partials/banner_tms.html` | Rewrite | Variant-aware template with 3 styles |
| `app/templates/stops/partials/banner_border.html` | Rewrite | Same |
| `app/templates/stops/partials/banner_parking.html` | Rewrite | Same |
| `app/templates/stops/partials/banner_fmcsa.html` | Rewrite | Same |
| `app/templates/stops/base.html` | Modify (lines 706-761) | Replace `.native-promo-*` CSS with new animated banner CSS + add entrance JS |

### truckerpro-web (blog/insights)

| File | Action | Responsibility |
|------|--------|----------------|
| `app/templates/blog/post.html` | Modify (CSS lines 123-153, HTML lines 225-253) | Replace promo grid with variant-aware animated banners |
| `app/templates/blog/index.html` | Modify (CSS lines 75-100, HTML lines 166-194) | Same |
| `app/templates/insights/article.html` | Modify (CSS lines 119-144, HTML lines 254-282) | Same |
| `app/templates/insights/index.html` | Modify (CSS lines 98-123, HTML lines 218-246) | Same |

---

## Task 1: Add variant rotation to banner_service.py (test first)

**Files:**
- Modify: `tests/test_banner_service.py`
- Modify: `app/services/banner_service.py`

- [ ] **Step 1: Write failing tests for variant fields and rotation**

Add these tests to the end of `tests/test_banner_service.py`:

```python
from unittest.mock import patch
from app.services.banner_service import _get_variant


def test_get_variant_returns_a_b_or_c():
    result = _get_variant()
    assert result in ('a', 'b', 'c')


def test_get_variant_day_0_returns_a():
    """day_of_year=1 → 1%3=1 → 'b'; day_of_year=3 → 3%3=0 → 'a'"""
    import datetime
    with patch('app.services.banner_service.datetime') as mock_dt:
        mock_dt.now.return_value = datetime.datetime(2026, 1, 3)  # day 3, 3%3=0 → 'a'
        mock_dt.timezone = datetime.timezone
        assert _get_variant() == 'a'


def test_get_variant_day_1_returns_b():
    import datetime
    with patch('app.services.banner_service.datetime') as mock_dt:
        mock_dt.now.return_value = datetime.datetime(2026, 1, 1)  # day 1, 1%3=1 → 'b'
        mock_dt.timezone = datetime.timezone
        assert _get_variant() == 'b'


def test_get_variant_day_2_returns_c():
    import datetime
    with patch('app.services.banner_service.datetime') as mock_dt:
        mock_dt.now.return_value = datetime.datetime(2026, 1, 2)  # day 2, 2%3=2 → 'c'
        mock_dt.timezone = datetime.timezone
        assert _get_variant() == 'c'


def test_banner_has_variant_field():
    stop = _make_stop()
    banners = get_banners(stop)
    for b in banners:
        assert 'variant' in b
        assert b['variant'] in ('a', 'b', 'c')


def test_tms_banner_has_headline_and_cta():
    stop = _make_stop()
    banners = get_banners(stop)
    tms = [b for b in banners if b['type'] == 'tms'][0]
    assert 'headline' in tms
    assert 'desc' in tms
    assert 'cta' in tms
    assert 'eyebrow' in tms
    assert len(tms['headline']) > 0


def test_style_b_has_hook():
    import datetime
    with patch('app.services.banner_service.datetime') as mock_dt:
        mock_dt.now.return_value = datetime.datetime(2026, 1, 1)  # day 1 → 'b'
        mock_dt.timezone = datetime.timezone
        stop = _make_stop()
        banners = get_banners(stop)
        tms = [b for b in banners if b['type'] == 'tms'][0]
        assert tms['variant'] == 'b'
        assert 'hook' in tms
        assert '?' in tms['hook']


def test_style_c_has_watermark():
    import datetime
    with patch('app.services.banner_service.datetime') as mock_dt:
        mock_dt.now.return_value = datetime.datetime(2026, 1, 2)  # day 2 → 'c'
        mock_dt.timezone = datetime.timezone
        stop = _make_stop()
        banners = get_banners(stop)
        tms = [b for b in banners if b['type'] == 'tms'][0]
        assert tms['variant'] == 'c'
        assert 'watermark' in tms
        assert tms['watermark'] == 'TMS'


def test_border_banner_close_has_all_variants_fields():
    stop = _make_stop(
        nearest_border_crossing='Peace Bridge (Fort Erie/Buffalo)',
        border_distance_km=8.5, country='US',
    )
    banners = get_banners(stop)
    border = [b for b in banners if b['type'] == 'border'][0]
    assert 'headline' in border
    assert 'desc' in border
    assert 'cta' in border
    assert 'eyebrow' in border
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_banner_service.py -v`
Expected: Multiple FAILs — `_get_variant` not importable, no `variant`/`headline`/etc fields.

- [ ] **Step 3: Implement variant-aware banner_service.py**

Replace the entire contents of `app/services/banner_service.py` with:

```python
"""Smart contextual banner service for truck stop pages."""
from datetime import datetime, timezone
from ..constants import MAJOR_FREIGHT_CORRIDORS, MAJOR_METROS

_VARIANTS = ('a', 'b', 'c')


def _get_variant():
    """Return today's banner variant based on day of year."""
    day = datetime.now(timezone.utc).timetuple().tm_yday
    return _VARIANTS[day % 3]


def get_banners(truck_stop):
    """Return ordered list of variant-aware banner dicts for a truck stop."""
    variant = _get_variant()
    banners = []
    banners.append(_tms_banner(truck_stop, variant))
    border = _border_banner(truck_stop, variant)
    if border:
        banners.append(border)
    banners.append(_parking_banner(truck_stop, variant))
    banners.append(_fmcsa_banner(truck_stop, variant))
    return banners


def _tms_banner(stop, variant):
    # Contextual copy for legacy 'copy' field
    highway = getattr(stop, 'highway', None) or ''
    city = getattr(stop, 'city', '') or ''
    if highway.upper() in [c.upper() for c in MAJOR_FREIGHT_CORRIDORS]:
        copy = f"Dispatching loads on {highway}? Manage your fleet"
    elif city in MAJOR_METROS:
        copy = f"Running routes through {city}? Track every load"
    else:
        copy = "Trucking company? Manage your fleet with TruckerPro TMS"

    variants = {
        'a': {
            'headline': '527 carriers switched\nthis quarter.',
            'desc': 'Dispatch, ELD, compliance, invoicing \u2014 one platform.',
            'cta': 'Start Free Trial',
            'sub_cta': 'No credit card',
            'hook': None,
            'watermark': None,
        },
        'b': {
            'headline': 'Your fleet deserves better\nthan copy-paste logistics.',
            'desc': None,
            'cta': 'See How It Works',
            'sub_cta': '2 min demo',
            'hook': '\u201cStill dispatching from spreadsheets?\u201d',
            'watermark': None,
        },
        'c': {
            'headline': 'One app.\nWhole fleet.',
            'desc': 'Dispatch \u00b7 ELD \u00b7 IFTA \u00b7 Invoicing\n14 days free \u00b7 No card required',
            'cta': 'Get Started',
            'sub_cta': None,
            'hook': None,
            'watermark': 'TMS',
        },
    }
    v = variants[variant]
    return {
        'type': 'tms',
        'variant': variant,
        'copy': copy,
        'url': 'https://tms.truckerpro.ca',
        'eyebrow': 'TruckerPro TMS',
        **v,
    }


def _border_banner(stop, variant):
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

    variants = {
        'a': {
            'headline': '12,400 manifests filed\nthis month.',
            'desc': 'ACE & ACI eManifest in under 5 minutes. Zero penalties.',
            'cta': 'File Your First Manifest',
            'sub_cta': 'Free to start',
            'hook': None,
            'watermark': None,
        },
        'b': {
            'headline': 'Pre-clear customs before\nyou even hit the border.',
            'desc': None,
            'cta': 'See How It Works',
            'sub_cta': '5 min setup',
            'hook': '\u201cStuck at the crossing again?\u201d',
            'watermark': None,
        },
        'c': {
            'headline': 'File once.\nCross fast.',
            'desc': 'ACE \u00b7 ACI \u00b7 PAPS \u00b7 PARS\nFree to start \u00b7 CBSA & CBP compliant',
            'cta': 'Get Started',
            'sub_cta': None,
            'hook': None,
            'watermark': 'ACE',
        },
    }
    v = variants[variant]
    return {
        'type': 'border',
        'variant': variant,
        'copy': copy,
        'url': 'https://border.truckerpro.ca',
        'eyebrow': 'TruckerPro Border',
        **v,
    }


def _parking_banner(stop, variant):
    if getattr(stop, 'parking_location_id', None):
        copy = "Reserve parking at this stop"
    else:
        copy = "Find reservable parking nearby"

    variants = {
        'a': {
            'headline': '2,100 spots booked\nlast week.',
            'desc': '75+ verified lots across Canada. Reserve before you arrive.',
            'cta': 'Reserve a Spot',
            'sub_cta': None,
            'hook': None,
            'watermark': None,
        },
        'b': {
            'headline': 'Book your spot before\nyou leave the shipper.',
            'desc': None,
            'cta': 'Find Parking Now',
            'sub_cta': None,
            'hook': '\u201cCircled the lot three times?\u201d',
            'watermark': None,
        },
        'c': {
            'headline': 'Park safe.\nSleep easy.',
            'desc': '75+ Canadian locations \u00b7 Gated lots\nOnline booking \u00b7 Driver reviews',
            'cta': 'Find Parking',
            'sub_cta': None,
            'hook': None,
            'watermark': 'P',
        },
    }
    v = variants[variant]
    return {
        'type': 'parking',
        'variant': variant,
        'copy': copy,
        'url': 'https://parking.truckerpro.ca',
        'eyebrow': 'Truck Parking Club',
        **v,
    }


def _fmcsa_banner(stop, variant):
    variants = {
        'a': {
            'headline': '4.4 million carriers.\nOne search.',
            'desc': 'CSA scores, inspections, crash records, operating authority.',
            'cta': 'Look Up a Carrier',
            'sub_cta': None,
            'hook': None,
            'watermark': None,
        },
        'b': {
            'headline': "Check any carrier\u2019s safety\nrecord in 10 seconds.",
            'desc': None,
            'cta': 'Run a Free Check',
            'sub_cta': None,
            'hook': '\u201cWho\u2019s hauling your freight?\u201d',
            'watermark': None,
        },
        'c': {
            'headline': 'Know your\ncarrier.',
            'desc': 'CSA \u00b7 BASICs \u00b7 Inspections \u00b7 Crashes\n4.4M profiles \u00b7 Free instant lookup',
            'cta': 'Lookup Carrier',
            'sub_cta': None,
            'hook': None,
            'watermark': 'DOT',
        },
    }
    v = variants[variant]
    return {
        'type': 'fmcsa',
        'variant': variant,
        'copy': "Look up carriers at this stop",
        'url': 'https://fmcsa.truckerpro.net',
        'eyebrow': 'FMCSA Data',
        **v,
    }
```

- [ ] **Step 4: Fix existing tests that assert old `copy` content**

The existing `test_tms_banner_corridor_copy` and `test_tms_banner_metro_copy` assert against the `copy` field, which still exists and is still contextual. These should still pass. The `test_parking_banner_with_linked_location` asserts `'Reserve' in parking[0]['copy']` — still true. The `test_parking_banner_without_linked_location` asserts `'nearby' in parking[0]['copy'].lower()` — still true. No changes needed to existing tests.

- [ ] **Step 5: Run all banner tests**

Run: `python3 -m pytest tests/test_banner_service.py -v`
Expected: All tests PASS (existing + new).

- [ ] **Step 6: Run full test suite**

Run: `python3 -m pytest tests/ -v`
Expected: All 280+ tests PASS.

- [ ] **Step 7: Commit**

```bash
git add app/services/banner_service.py tests/test_banner_service.py
git commit -m "feat: add 3-variant day-rotation to banner service

Each banner now returns variant (a/b/c), headline, desc, hook, cta,
sub_cta, watermark, and eyebrow fields. Day-based rotation via
day_of_year % 3. Existing copy/url/cta fields preserved for
backwards compatibility."
```

---

## Task 2: Rewrite stops banner partials (variant-aware templates)

**Files:**
- Rewrite: `app/templates/stops/partials/banner_tms.html`
- Rewrite: `app/templates/stops/partials/banner_border.html`
- Rewrite: `app/templates/stops/partials/banner_parking.html`
- Rewrite: `app/templates/stops/partials/banner_fmcsa.html`

- [ ] **Step 1: Rewrite banner_tms.html**

Replace the entire file with:

```html
<a href="{{ banner.url }}" class="promo-banner promo-tms" data-ga-event="banner_click" data-ga-target="tms">
  {% if banner.variant == 'c' %}<div class="promo-watermark">{{ banner.watermark }}</div>{% endif %}
  <div>
    {% if banner.variant != 'c' %}
    <div class="promo-eyebrow"><span class="promo-dot"></span><span>{{ banner.eyebrow }}</span></div>
    {% endif %}
    {% if banner.variant == 'b' and banner.hook %}
    <div class="promo-hook">{{ banner.hook }}</div>
    {% endif %}
    <div class="promo-headline {% if banner.variant == 'c' %}promo-headline-lg{% endif %}">{{ banner.headline | replace('\n', '<br>') | safe }}</div>
    {% if banner.variant == 'c' %}<div class="promo-accent-bar"></div>{% endif %}
    {% if banner.desc %}<div class="promo-desc">{{ banner.desc | replace('\n', '<br>') | safe }}</div>{% endif %}
  </div>
  <div class="promo-cta-row">
    <span class="promo-btn {% if banner.variant == 'c' %}promo-btn-outline{% endif %}">{{ banner.cta }}{% if banner.variant == 'c' %} &rarr;{% endif %}</span>
    {% if banner.sub_cta %}<span class="promo-sub-cta">{{ banner.sub_cta }}</span>{% endif %}
  </div>
</a>
```

- [ ] **Step 2: Rewrite banner_border.html**

Replace the entire file with:

```html
<a href="{{ banner.url }}" class="promo-banner promo-border" target="_blank" rel="noopener" data-ga-event="banner_click" data-ga-target="border">
  {% if banner.variant == 'c' %}<div class="promo-watermark">{{ banner.watermark }}</div>{% endif %}
  <div>
    {% if banner.variant != 'c' %}
    <div class="promo-eyebrow"><span class="promo-dot"></span><span>{{ banner.eyebrow }}</span></div>
    {% endif %}
    {% if banner.variant == 'b' and banner.hook %}
    <div class="promo-hook">{{ banner.hook }}</div>
    {% endif %}
    <div class="promo-headline {% if banner.variant == 'c' %}promo-headline-lg{% endif %}">{{ banner.headline | replace('\n', '<br>') | safe }}</div>
    {% if banner.variant == 'c' %}<div class="promo-accent-bar"></div>{% endif %}
    {% if banner.desc %}<div class="promo-desc">{{ banner.desc | replace('\n', '<br>') | safe }}</div>{% endif %}
  </div>
  <div class="promo-cta-row">
    <span class="promo-btn {% if banner.variant == 'c' %}promo-btn-outline{% endif %}">{{ banner.cta }}{% if banner.variant == 'c' %} &rarr;{% endif %}</span>
    {% if banner.sub_cta %}<span class="promo-sub-cta">{{ banner.sub_cta }}</span>{% endif %}
  </div>
</a>
```

- [ ] **Step 3: Rewrite banner_parking.html**

Replace the entire file with:

```html
<a href="{{ banner.url }}" class="promo-banner promo-parking" target="_blank" rel="noopener" data-ga-event="banner_click" data-ga-target="parking">
  {% if banner.variant == 'c' %}<div class="promo-watermark">{{ banner.watermark }}</div>{% endif %}
  <div>
    {% if banner.variant != 'c' %}
    <div class="promo-eyebrow"><span class="promo-dot"></span><span>{{ banner.eyebrow }}</span></div>
    {% endif %}
    {% if banner.variant == 'b' and banner.hook %}
    <div class="promo-hook">{{ banner.hook }}</div>
    {% endif %}
    <div class="promo-headline {% if banner.variant == 'c' %}promo-headline-lg{% endif %}">{{ banner.headline | replace('\n', '<br>') | safe }}</div>
    {% if banner.variant == 'c' %}<div class="promo-accent-bar"></div>{% endif %}
    {% if banner.desc %}<div class="promo-desc">{{ banner.desc | replace('\n', '<br>') | safe }}</div>{% endif %}
  </div>
  <div class="promo-cta-row">
    <span class="promo-btn {% if banner.variant == 'c' %}promo-btn-outline{% endif %}">{{ banner.cta }}{% if banner.variant == 'c' %} &rarr;{% endif %}</span>
    {% if banner.sub_cta %}<span class="promo-sub-cta">{{ banner.sub_cta }}</span>{% endif %}
  </div>
</a>
```

- [ ] **Step 4: Rewrite banner_fmcsa.html**

Replace the entire file with:

```html
<a href="{{ banner.url }}" class="promo-banner promo-fmcsa" target="_blank" rel="noopener" data-ga-event="banner_click" data-ga-target="fmcsa">
  {% if banner.variant == 'c' %}<div class="promo-watermark">{{ banner.watermark }}</div>{% endif %}
  <div>
    {% if banner.variant != 'c' %}
    <div class="promo-eyebrow"><span class="promo-dot"></span><span>{{ banner.eyebrow }}</span></div>
    {% endif %}
    {% if banner.variant == 'b' and banner.hook %}
    <div class="promo-hook">{{ banner.hook }}</div>
    {% endif %}
    <div class="promo-headline {% if banner.variant == 'c' %}promo-headline-lg{% endif %}">{{ banner.headline | replace('\n', '<br>') | safe }}</div>
    {% if banner.variant == 'c' %}<div class="promo-accent-bar"></div>{% endif %}
    {% if banner.desc %}<div class="promo-desc">{{ banner.desc | replace('\n', '<br>') | safe }}</div>{% endif %}
  </div>
  <div class="promo-cta-row">
    <span class="promo-btn {% if banner.variant == 'c' %}promo-btn-outline{% endif %}">{{ banner.cta }}{% if banner.variant == 'c' %} &rarr;{% endif %}</span>
    {% if banner.sub_cta %}<span class="promo-sub-cta">{{ banner.sub_cta }}</span>{% endif %}
  </div>
</a>
```

- [ ] **Step 5: Run full test suite**

Run: `python3 -m pytest tests/ -v`
Expected: All tests PASS. Templates are only rendered in integration tests via route handlers.

- [ ] **Step 6: Commit**

```bash
git add app/templates/stops/partials/banner_tms.html \
       app/templates/stops/partials/banner_border.html \
       app/templates/stops/partials/banner_parking.html \
       app/templates/stops/partials/banner_fmcsa.html
git commit -m "feat: rewrite stop banner partials for 3-variant rotation

All 4 banner partials now use a shared structure with Jinja conditionals
for style A (social proof), B (pain point hook), C (bold typographic).
Replaces the old two-column native-promo layout with a simpler
single-column card format."
```

---

## Task 3: Replace stops base.html CSS with animated banner styles

**Files:**
- Modify: `app/templates/stops/base.html` (lines 706-761 CSS, add JS before `</body>`)

- [ ] **Step 1: Replace the native-promo CSS block (lines 706-761)**

Find in `app/templates/stops/base.html` the block starting with `/* ── Native Content Promos */` (line 706) through the closing `}` of the media query (line 761). Replace it with:

```css
      /* ── Promo Banners (animated, variant-aware) ─────── */
      .promo-banner { position:relative; overflow:hidden; border-radius:16px; padding:28px 24px; text-decoration:none; color:#fff; display:flex; flex-direction:column; justify-content:space-between; min-height:200px; transition:transform 0.3s ease, box-shadow 0.3s ease; margin:20px 0; opacity:0; transform:translateY(30px); }
      .promo-banner.visible { animation:promoEntrance 0.6s ease forwards; }
      .promo-banner:hover { transform:translateY(-4px); box-shadow:0 20px 60px rgba(0,0,0,0.5); color:#fff; }
      .promo-banner.visible:hover { transform:translateY(-4px); }
      .promo-banner::before { content:''; position:absolute; inset:0; z-index:0; background-size:300% 300%; animation:promoGradient 8s ease infinite; }
      .promo-banner > * { position:relative; z-index:1; }
      .promo-banner::after { content:''; position:absolute; inset:-1px; border-radius:17px; z-index:-1; }

      /* Product gradients */
      .promo-tms::before { background:linear-gradient(-45deg, #0b1020, #1a0c00, #2d1200, #ff6b35, #0b1020); }
      .promo-border::before { background:linear-gradient(-45deg, #051a14, #001a14, #002d24, #10b981, #051a14); }
      .promo-parking::before { background:linear-gradient(-45deg, #1a0035, #0d001a, #2d0050, #8b5cf6, #1a0035); }
      .promo-fmcsa::before { background:linear-gradient(-45deg, #111827, #0a0f1a, #1f2937, #4b5563, #111827); }

      /* Product glow pulses */
      .promo-tms::after { animation:glowTms 3s ease-in-out infinite; }
      .promo-border::after { animation:glowBorder 3s ease-in-out infinite; }
      .promo-parking::after { animation:glowParking 3s ease-in-out infinite; }
      .promo-fmcsa::after { animation:glowFmcsa 3s ease-in-out infinite; }

      @keyframes glowTms { 0%,100%{box-shadow:0 0 15px rgba(255,107,53,0), 0 0 30px rgba(255,107,53,0)} 50%{box-shadow:0 0 15px rgba(255,107,53,0.15), 0 0 40px rgba(255,107,53,0.05)} }
      @keyframes glowBorder { 0%,100%{box-shadow:0 0 15px rgba(16,185,129,0), 0 0 30px rgba(16,185,129,0)} 50%{box-shadow:0 0 15px rgba(16,185,129,0.15), 0 0 40px rgba(16,185,129,0.05)} }
      @keyframes glowParking { 0%,100%{box-shadow:0 0 15px rgba(139,92,246,0), 0 0 30px rgba(139,92,246,0)} 50%{box-shadow:0 0 15px rgba(139,92,246,0.15), 0 0 40px rgba(139,92,246,0.05)} }
      @keyframes glowFmcsa { 0%,100%{box-shadow:0 0 15px rgba(107,114,128,0), 0 0 30px rgba(107,114,128,0)} 50%{box-shadow:0 0 15px rgba(107,114,128,0.1), 0 0 40px rgba(107,114,128,0.03)} }

      @keyframes promoGradient { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
      @keyframes promoEntrance { from{opacity:0; transform:translateY(30px)} to{opacity:1; transform:translateY(0)} }

      /* Eyebrow */
      .promo-eyebrow { display:flex; align-items:center; gap:8px; margin-bottom:12px; }
      .promo-dot { width:8px; height:8px; border-radius:50%; animation:promoDotPulse 2s ease-in-out infinite; }
      .promo-tms .promo-dot { background:#ff6b35; }
      .promo-border .promo-dot { background:#10b981; }
      .promo-parking .promo-dot { background:#8b5cf6; }
      .promo-fmcsa .promo-dot { background:#6b7280; }
      .promo-eyebrow span:last-child { font-size:0.68rem; text-transform:uppercase; letter-spacing:1.5px; color:rgba(255,255,255,0.55); font-weight:600; }
      @keyframes promoDotPulse { 0%,100%{opacity:1; transform:scale(1)} 50%{opacity:0.5; transform:scale(0.85)} }

      /* Hook (style B) */
      .promo-hook { font-size:1rem; font-weight:400; color:rgba(255,255,255,0.4); font-style:italic; margin-bottom:4px; }

      /* Headline */
      .promo-headline { font-size:1.4rem; font-weight:900; line-height:1.15; letter-spacing:-0.5px; margin-bottom:5px; }
      .promo-headline-lg { font-size:2rem; letter-spacing:-1px; }

      /* Accent bar (style C) */
      .promo-accent-bar { width:36px; height:3px; border-radius:2px; margin-bottom:10px; }
      .promo-tms .promo-accent-bar { background:#ff6b35; }
      .promo-border .promo-accent-bar { background:#10b981; }
      .promo-parking .promo-accent-bar { background:#8b5cf6; }
      .promo-fmcsa .promo-accent-bar { background:#6b7280; }

      /* Description */
      .promo-desc { font-size:0.78rem; color:rgba(255,255,255,0.45); line-height:1.5; margin-bottom:16px; }

      /* Watermark (style C) */
      .promo-watermark { position:absolute; right:-15px; top:-20px; font-size:7rem; font-weight:900; line-height:1; z-index:0; opacity:0.04; pointer-events:none; }
      .promo-tms .promo-watermark { color:#ff6b35; }
      .promo-border .promo-watermark { color:#10b981; }
      .promo-parking .promo-watermark { color:#8b5cf6; }
      .promo-fmcsa .promo-watermark { color:#6b7280; }

      /* CTA */
      .promo-cta-row { display:flex; align-items:center; gap:14px; }
      .promo-btn { padding:10px 22px; border-radius:8px; font-size:0.8rem; font-weight:700; color:#fff; border:none; transition:all 0.2s; }
      .promo-tms .promo-btn { background:#ff6b35; }
      .promo-border .promo-btn { background:#10b981; }
      .promo-parking .promo-btn { background:#8b5cf6; }
      .promo-fmcsa .promo-btn { background:#6b7280; }
      .promo-btn-outline { background:transparent !important; }
      .promo-tms .promo-btn-outline { border:1.5px solid #ff6b35; color:#ff6b35; }
      .promo-border .promo-btn-outline { border:1.5px solid #10b981; color:#10b981; }
      .promo-parking .promo-btn-outline { border:1.5px solid #8b5cf6; color:#8b5cf6; }
      .promo-fmcsa .promo-btn-outline { border:1.5px solid #6b7280; color:#9ca3af; }
      .promo-sub-cta { font-size:0.72rem; color:rgba(255,255,255,0.35); }

      @media (max-width: 768px) {
        .promo-banner { min-height:180px; padding:24px 20px; }
        .promo-headline-lg { font-size:1.6rem; }
        .promo-watermark { font-size:5rem; }
      }
```

- [ ] **Step 2: Add IntersectionObserver JS before closing `</body>` tag**

Find the `{% block scripts %}{% endblock %}` line (line 871) in `app/templates/stops/base.html`. Add this script block immediately after it (before the PWA SW script):

```html
    <!-- Promo banner scroll entrance -->
    <script>
      (function(){
        var obs = new IntersectionObserver(function(entries) {
          entries.forEach(function(entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add('visible');
              obs.unobserve(entry.target);
            }
          });
        }, {threshold: 0.2});
        document.querySelectorAll('.promo-banner').forEach(function(el) { obs.observe(el); });
      })();
    </script>
```

- [ ] **Step 3: Run full test suite**

Run: `python3 -m pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add app/templates/stops/base.html
git commit -m "feat: replace stops banner CSS with animated 3-variant styles

Gradient shift (8s), glow pulse (3s), scroll entrance (0.6s) with
IntersectionObserver. Removes old native-promo two-column layout.
Supports all 3 variants: social proof, pain point, bold typographic."
```

---

## Task 4: Update truckerpro-web blog post.html banners

**Files:**
- Modify: `/Users/tps/Desktop/projects/truckerpro-web/app/templates/blog/post.html` (CSS lines 123-153, HTML lines 225-253)

- [ ] **Step 1: Replace CSS block (lines 123-153)**

In `blog/post.html`, find the block from `/* Promo Banners */` (line 123) through the end of the `@media(max-width:900px)` rule (line 153). Replace the promo-related CSS. Keep `footer` and everything before `/* Promo Banners */` unchanged. The new CSS replaces lines 123-153:

```css
        /* Promo Banners */
        .promo-banners { display:grid; grid-template-columns:repeat(3, 1fr); gap:20px; margin:48px 0 12px; }
        .promo-banner { position:relative; overflow:hidden; border-radius:16px; padding:32px 28px; text-decoration:none; color:#fff; display:flex; flex-direction:column; justify-content:space-between; min-height:200px; transition:transform 0.3s ease, box-shadow 0.3s ease; opacity:0; transform:translateY(30px); }
        .promo-banner.visible { animation:promoEntrance 0.6s ease forwards; }
        .promo-banner:hover { transform:translateY(-4px); box-shadow:0 20px 60px rgba(0,0,0,0.5); color:#fff; }
        .promo-banner.visible:hover { transform:translateY(-4px); }
        .promo-banner::before { content:''; position:absolute; inset:0; z-index:0; background-size:300% 300%; animation:promoGradient 8s ease infinite; }
        .promo-banner > * { position:relative; z-index:1; }
        .promo-banner::after { content:''; position:absolute; inset:-1px; border-radius:17px; z-index:-1; }
        .promo-tms::before { background:linear-gradient(-45deg,#0b1020,#1a0c00,#2d1200,#ff6b35,#0b1020); }
        .promo-border::before { background:linear-gradient(-45deg,#051a14,#001a14,#002d24,#10b981,#051a14); }
        .promo-parking::before { background:linear-gradient(-45deg,#1a0035,#0d001a,#2d0050,#8b5cf6,#1a0035); }
        .promo-tms::after { animation:glowTms 3s ease-in-out infinite; }
        .promo-border::after { animation:glowBorder 3s ease-in-out infinite; }
        .promo-parking::after { animation:glowParking 3s ease-in-out infinite; }
        @keyframes glowTms { 0%,100%{box-shadow:0 0 15px rgba(255,107,53,0),0 0 30px rgba(255,107,53,0)} 50%{box-shadow:0 0 15px rgba(255,107,53,0.15),0 0 40px rgba(255,107,53,0.05)} }
        @keyframes glowBorder { 0%,100%{box-shadow:0 0 15px rgba(16,185,129,0),0 0 30px rgba(16,185,129,0)} 50%{box-shadow:0 0 15px rgba(16,185,129,0.15),0 0 40px rgba(16,185,129,0.05)} }
        @keyframes glowParking { 0%,100%{box-shadow:0 0 15px rgba(139,92,246,0),0 0 30px rgba(139,92,246,0)} 50%{box-shadow:0 0 15px rgba(139,92,246,0.15),0 0 40px rgba(139,92,246,0.05)} }
        @keyframes promoGradient { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
        @keyframes promoEntrance { from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)} }
        .promo-eyebrow { display:flex; align-items:center; gap:8px; margin-bottom:12px; }
        .promo-dot { width:8px; height:8px; border-radius:50%; animation:promoDotPulse 2s ease-in-out infinite; }
        .promo-tms .promo-dot { background:#ff6b35; }
        .promo-border .promo-dot { background:#10b981; }
        .promo-parking .promo-dot { background:#8b5cf6; }
        .promo-eyebrow span:last-child { font-size:0.68rem; text-transform:uppercase; letter-spacing:1.5px; color:rgba(255,255,255,0.55); font-weight:600; }
        @keyframes promoDotPulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.85)} }
        .promo-hook { font-size:1rem; font-weight:400; color:rgba(255,255,255,0.4); font-style:italic; margin-bottom:4px; }
        .promo-headline { font-size:1.35rem; font-weight:900; line-height:1.15; letter-spacing:-0.5px; margin-bottom:5px; }
        .promo-headline-lg { font-size:2rem; letter-spacing:-1px; }
        .promo-accent-bar { width:36px; height:3px; border-radius:2px; margin-bottom:10px; }
        .promo-tms .promo-accent-bar { background:#ff6b35; }
        .promo-border .promo-accent-bar { background:#10b981; }
        .promo-parking .promo-accent-bar { background:#8b5cf6; }
        .promo-desc { font-size:0.78rem; color:rgba(255,255,255,0.45); line-height:1.5; margin-bottom:16px; }
        .promo-watermark { position:absolute; right:-15px; top:-20px; font-size:7rem; font-weight:900; line-height:1; z-index:0; opacity:0.04; pointer-events:none; }
        .promo-tms .promo-watermark { color:#ff6b35; }
        .promo-border .promo-watermark { color:#10b981; }
        .promo-parking .promo-watermark { color:#8b5cf6; }
        .promo-cta-row { display:flex; align-items:center; gap:14px; }
        .promo-btn { padding:10px 22px; border-radius:8px; font-size:0.8rem; font-weight:700; color:#fff; border:none; transition:all 0.2s; }
        .promo-tms .promo-btn { background:#ff6b35; }
        .promo-border .promo-btn { background:#10b981; }
        .promo-parking .promo-btn { background:#8b5cf6; }
        .promo-btn-outline { background:transparent !important; }
        .promo-tms .promo-btn-outline { border:1.5px solid #ff6b35; color:#ff6b35; }
        .promo-border .promo-btn-outline { border:1.5px solid #10b981; color:#10b981; }
        .promo-parking .promo-btn-outline { border:1.5px solid #8b5cf6; color:#8b5cf6; }
        .promo-sub-cta { font-size:0.72rem; color:rgba(255,255,255,0.35); }
        footer { border-top:1px solid var(--line); padding:24px 0 40px; color:var(--muted); font-size:0.88rem; text-align:center; }
        footer a { color:var(--brand); text-decoration:none; }
        @media(max-width:900px) { .post-layout { grid-template-columns:1fr; } .toc-sidebar { position:static; margin-bottom:24px; background:var(--card); padding:16px; border-radius:10px; border:1px solid var(--line); } .promo-banners { grid-template-columns:1fr; } .promo-banner { min-height:160px; } .promo-headline-lg { font-size:1.6rem; } .promo-watermark { font-size:5rem; } }
```

- [ ] **Step 2: Replace HTML banner block (lines 225-253)**

Find the `<div class="promo-banners">` block. Replace it with:

```html
        {% set variant = ['a','b','c'][now().timetuple().tm_yday % 3] %}
        <div class="promo-banners">
            {# ── TMS Banner ── #}
            <a href="/trucking-tms-software" class="promo-banner promo-tms">
                {% if variant == 'c' %}<div class="promo-watermark">TMS</div>{% endif %}
                <div>
                    {% if variant != 'c' %}<div class="promo-eyebrow"><span class="promo-dot"></span><span>TruckerPro TMS</span></div>{% endif %}
                    {% if variant == 'b' %}<div class="promo-hook">&ldquo;Still dispatching from spreadsheets?&rdquo;</div>{% endif %}
                    {% if variant == 'a' %}
                    <div class="promo-headline">527 carriers switched<br>this quarter.</div>
                    <div class="promo-desc">Dispatch, ELD, compliance, invoicing &mdash; one platform.</div>
                    {% elif variant == 'b' %}
                    <div class="promo-headline">Your fleet deserves better<br>than copy-paste logistics.</div>
                    {% else %}
                    <div class="promo-headline promo-headline-lg">One app.<br>Whole fleet.</div>
                    <div class="promo-accent-bar"></div>
                    <div class="promo-desc">Dispatch &middot; ELD &middot; IFTA &middot; Invoicing<br>14 days free &middot; No card required</div>
                    {% endif %}
                </div>
                <div class="promo-cta-row">
                    {% if variant == 'a' %}<span class="promo-btn">Start Free Trial</span><span class="promo-sub-cta">No credit card</span>
                    {% elif variant == 'b' %}<span class="promo-btn">See How It Works</span><span class="promo-sub-cta">2 min demo</span>
                    {% else %}<span class="promo-btn promo-btn-outline">Get Started &rarr;</span>{% endif %}
                </div>
            </a>
            {# ── Border Banner ── #}
            <a href="https://border.truckerpro.ca" class="promo-banner promo-border" target="_blank" rel="noopener">
                {% if variant == 'c' %}<div class="promo-watermark">ACE</div>{% endif %}
                <div>
                    {% if variant != 'c' %}<div class="promo-eyebrow"><span class="promo-dot"></span><span>TruckerPro Border</span></div>{% endif %}
                    {% if variant == 'b' %}<div class="promo-hook">&ldquo;Stuck at the crossing again?&rdquo;</div>{% endif %}
                    {% if variant == 'a' %}
                    <div class="promo-headline">12,400 manifests filed<br>this month.</div>
                    <div class="promo-desc">ACE &amp; ACI eManifest in under 5 minutes. Zero penalties.</div>
                    {% elif variant == 'b' %}
                    <div class="promo-headline">Pre-clear customs before<br>you even hit the border.</div>
                    {% else %}
                    <div class="promo-headline promo-headline-lg">File once.<br>Cross fast.</div>
                    <div class="promo-accent-bar"></div>
                    <div class="promo-desc">ACE &middot; ACI &middot; PAPS &middot; PARS<br>Free to start &middot; CBSA &amp; CBP compliant</div>
                    {% endif %}
                </div>
                <div class="promo-cta-row">
                    {% if variant == 'a' %}<span class="promo-btn">File Your First Manifest</span><span class="promo-sub-cta">Free to start</span>
                    {% elif variant == 'b' %}<span class="promo-btn">See How It Works</span><span class="promo-sub-cta">5 min setup</span>
                    {% else %}<span class="promo-btn promo-btn-outline">Get Started &rarr;</span>{% endif %}
                </div>
            </a>
            {# ── Parking Banner ── #}
            <a href="https://parking.truckerpro.ca" class="promo-banner promo-parking" target="_blank" rel="noopener">
                {% if variant == 'c' %}<div class="promo-watermark">P</div>{% endif %}
                <div>
                    {% if variant != 'c' %}<div class="promo-eyebrow"><span class="promo-dot"></span><span>Truck Parking Club</span></div>{% endif %}
                    {% if variant == 'b' %}<div class="promo-hook">&ldquo;Circled the lot three times?&rdquo;</div>{% endif %}
                    {% if variant == 'a' %}
                    <div class="promo-headline">2,100 spots booked<br>last week.</div>
                    <div class="promo-desc">75+ verified lots across Canada. Reserve before you arrive.</div>
                    {% elif variant == 'b' %}
                    <div class="promo-headline">Book your spot before<br>you leave the shipper.</div>
                    {% else %}
                    <div class="promo-headline promo-headline-lg">Park safe.<br>Sleep easy.</div>
                    <div class="promo-accent-bar"></div>
                    <div class="promo-desc">75+ Canadian locations &middot; Gated lots<br>Online booking &middot; Driver reviews</div>
                    {% endif %}
                </div>
                <div class="promo-cta-row">
                    {% if variant == 'a' %}<span class="promo-btn">Reserve a Spot</span>
                    {% elif variant == 'b' %}<span class="promo-btn">Find Parking Now</span>
                    {% else %}<span class="promo-btn promo-btn-outline">Find Parking &rarr;</span>{% endif %}
                </div>
            </a>
        </div>
```

- [ ] **Step 3: Add IntersectionObserver JS before closing `</body>`**

Find the closing `</body>` tag in `blog/post.html`. Add immediately before it:

```html
    <script>
    (function(){
      var obs = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            var banners = entry.target.parentElement.querySelectorAll('.promo-banner');
            banners.forEach(function(b, i) { setTimeout(function(){ b.classList.add('visible'); }, i * 150); });
            banners.forEach(function(b) { obs.unobserve(b); });
          }
        });
      }, {threshold: 0.2});
      document.querySelectorAll('.promo-banner').forEach(function(el) { obs.observe(el); });
    })();
    </script>
```

- [ ] **Step 4: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-web
git add app/templates/blog/post.html
git commit -m "feat: redesign blog post promo banners — 3 rotating variants with animations

Day-based rotation (day_of_year % 3): social proof, pain point, bold
typographic. Gradient shift, glow pulse, scroll entrance animations."
```

---

## Task 5: Update truckerpro-web blog index.html banners

**Files:**
- Modify: `/Users/tps/Desktop/projects/truckerpro-web/app/templates/blog/index.html` (CSS lines 75-100, HTML lines 166-194)

- [ ] **Step 1: Replace CSS block (lines 75-100)**

Same animated banner CSS as Task 4 Step 1, but with slightly smaller sizing for index pages. In `blog/index.html`, replace the block from `/* Promo Banners */` (line 75) through `.promo-banner .promo-icon` (line 100) with:

```css
        /* Promo Banners */
        .promo-banners { display:grid; grid-template-columns:repeat(3, 1fr); gap:20px; margin:12px 0 32px; }
        .promo-banner { position:relative; overflow:hidden; border-radius:16px; padding:28px 24px; text-decoration:none; color:#fff; display:flex; flex-direction:column; justify-content:space-between; min-height:180px; transition:transform 0.3s ease, box-shadow 0.3s ease; opacity:0; transform:translateY(30px); }
        .promo-banner.visible { animation:promoEntrance 0.6s ease forwards; }
        .promo-banner:hover { transform:translateY(-4px); box-shadow:0 20px 60px rgba(0,0,0,0.5); color:#fff; }
        .promo-banner.visible:hover { transform:translateY(-4px); }
        .promo-banner::before { content:''; position:absolute; inset:0; z-index:0; background-size:300% 300%; animation:promoGradient 8s ease infinite; }
        .promo-banner > * { position:relative; z-index:1; }
        .promo-banner::after { content:''; position:absolute; inset:-1px; border-radius:17px; z-index:-1; }
        .promo-tms::before { background:linear-gradient(-45deg,#0b1020,#1a0c00,#2d1200,#ff6b35,#0b1020); }
        .promo-border::before { background:linear-gradient(-45deg,#051a14,#001a14,#002d24,#10b981,#051a14); }
        .promo-parking::before { background:linear-gradient(-45deg,#1a0035,#0d001a,#2d0050,#8b5cf6,#1a0035); }
        .promo-tms::after { animation:glowTms 3s ease-in-out infinite; }
        .promo-border::after { animation:glowBorder 3s ease-in-out infinite; }
        .promo-parking::after { animation:glowParking 3s ease-in-out infinite; }
        @keyframes glowTms { 0%,100%{box-shadow:0 0 15px rgba(255,107,53,0),0 0 30px rgba(255,107,53,0)} 50%{box-shadow:0 0 15px rgba(255,107,53,0.15),0 0 40px rgba(255,107,53,0.05)} }
        @keyframes glowBorder { 0%,100%{box-shadow:0 0 15px rgba(16,185,129,0),0 0 30px rgba(16,185,129,0)} 50%{box-shadow:0 0 15px rgba(16,185,129,0.15),0 0 40px rgba(16,185,129,0.05)} }
        @keyframes glowParking { 0%,100%{box-shadow:0 0 15px rgba(139,92,246,0),0 0 30px rgba(139,92,246,0)} 50%{box-shadow:0 0 15px rgba(139,92,246,0.15),0 0 40px rgba(139,92,246,0.05)} }
        @keyframes promoGradient { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
        @keyframes promoEntrance { from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)} }
        .promo-eyebrow { display:flex; align-items:center; gap:8px; margin-bottom:10px; }
        .promo-dot { width:8px; height:8px; border-radius:50%; animation:promoDotPulse 2s ease-in-out infinite; }
        .promo-tms .promo-dot { background:#ff6b35; }
        .promo-border .promo-dot { background:#10b981; }
        .promo-parking .promo-dot { background:#8b5cf6; }
        .promo-eyebrow span:last-child { font-size:0.65rem; text-transform:uppercase; letter-spacing:1.5px; color:rgba(255,255,255,0.55); font-weight:600; }
        @keyframes promoDotPulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.85)} }
        .promo-hook { font-size:0.92rem; font-weight:400; color:rgba(255,255,255,0.4); font-style:italic; margin-bottom:4px; }
        .promo-headline { font-size:1.25rem; font-weight:900; line-height:1.15; letter-spacing:-0.5px; margin-bottom:5px; }
        .promo-headline-lg { font-size:1.8rem; letter-spacing:-1px; }
        .promo-accent-bar { width:32px; height:3px; border-radius:2px; margin-bottom:10px; }
        .promo-tms .promo-accent-bar { background:#ff6b35; }
        .promo-border .promo-accent-bar { background:#10b981; }
        .promo-parking .promo-accent-bar { background:#8b5cf6; }
        .promo-desc { font-size:0.75rem; color:rgba(255,255,255,0.45); line-height:1.5; margin-bottom:14px; }
        .promo-watermark { position:absolute; right:-15px; top:-15px; font-size:6rem; font-weight:900; line-height:1; z-index:0; opacity:0.04; pointer-events:none; }
        .promo-tms .promo-watermark { color:#ff6b35; }
        .promo-border .promo-watermark { color:#10b981; }
        .promo-parking .promo-watermark { color:#8b5cf6; }
        .promo-cta-row { display:flex; align-items:center; gap:12px; }
        .promo-btn { padding:8px 18px; border-radius:8px; font-size:0.75rem; font-weight:700; color:#fff; border:none; transition:all 0.2s; }
        .promo-tms .promo-btn { background:#ff6b35; }
        .promo-border .promo-btn { background:#10b981; }
        .promo-parking .promo-btn { background:#8b5cf6; }
        .promo-btn-outline { background:transparent !important; }
        .promo-tms .promo-btn-outline { border:1.5px solid #ff6b35; color:#ff6b35; }
        .promo-border .promo-btn-outline { border:1.5px solid #10b981; color:#10b981; }
        .promo-parking .promo-btn-outline { border:1.5px solid #8b5cf6; color:#8b5cf6; }
        .promo-sub-cta { font-size:0.7rem; color:rgba(255,255,255,0.35); }
```

Also find the responsive media query that references `.promo-banners` and update it to include:
```css
        .promo-headline-lg { font-size:1.5rem; } .promo-watermark { font-size:4rem; }
```

- [ ] **Step 2: Replace HTML banner block (lines 166-194)**

Same HTML as Task 4 Step 2 (the `{% set variant %}` + 3 banner `<a>` tags). Identical content.

- [ ] **Step 3: Add IntersectionObserver JS before `</body>`**

Same script as Task 4 Step 3.

- [ ] **Step 4: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-web
git add app/templates/blog/index.html
git commit -m "feat: redesign blog index promo banners — 3 rotating variants with animations"
```

---

## Task 6: Update truckerpro-web insights article.html banners

**Files:**
- Modify: `/Users/tps/Desktop/projects/truckerpro-web/app/templates/insights/article.html` (CSS lines 119-144, HTML lines 254-282)

- [ ] **Step 1: Replace CSS block (lines 119-144)**

Same CSS as Task 4 Step 1 (article pages use the larger sizing).

- [ ] **Step 2: Replace HTML banner block (lines 254-282)**

Same HTML as Task 4 Step 2.

- [ ] **Step 3: Add IntersectionObserver JS before `</body>`**

Same script as Task 4 Step 3.

- [ ] **Step 4: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-web
git add app/templates/insights/article.html
git commit -m "feat: redesign insights article promo banners — 3 rotating variants with animations"
```

---

## Task 7: Update truckerpro-web insights index.html banners

**Files:**
- Modify: `/Users/tps/Desktop/projects/truckerpro-web/app/templates/insights/index.html` (CSS lines 98-123, HTML lines 218-246)

- [ ] **Step 1: Replace CSS block (lines 98-123)**

Same CSS as Task 5 Step 1 (index pages use the smaller sizing).

- [ ] **Step 2: Replace HTML banner block (lines 218-246)**

Same HTML as Task 4 Step 2.

- [ ] **Step 3: Add IntersectionObserver JS before `</body>`**

Same script as Task 4 Step 3.

- [ ] **Step 4: Commit**

```bash
cd /Users/tps/Desktop/projects/truckerpro-web
git add app/templates/insights/index.html
git commit -m "feat: redesign insights index promo banners — 3 rotating variants with animations"
```

---

## Task 8: Final verification and push

**Files:** Both repos

- [ ] **Step 1: Run truckerpro-parking tests**

Run: `cd /Users/tps/Desktop/projects/truckerpro-parking && python3 -m pytest tests/ -v`
Expected: All 280+ tests PASS.

- [ ] **Step 2: Push truckerpro-parking**

```bash
cd /Users/tps/Desktop/projects/truckerpro-parking
git push
```

- [ ] **Step 3: Push truckerpro-web**

```bash
cd /Users/tps/Desktop/projects/truckerpro-web
git push
```

- [ ] **Step 4: Manual visual verification**

After deploy, check these URLs and cycle through all 3 variants (by waiting for different days, or temporarily hardcoding the variant):
- `stops.truckerpro.net` — any truck stop detail page
- Blog post page on truckerpro.ca
- Blog index page
- Insights article page
- Insights index page

Verify: gradient animation plays, glow pulses, banners fade in on scroll, all 3 variants render correctly, mobile responsive layout works.
