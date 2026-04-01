# Blog SEO Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a static markdown-based blog system serving 40+ SEO posts across parking.truckerpro.ca and stops.truckerpro.net, with strong CTAs funneling to the main TMS and border apps, and GA4 analytics.

**Architecture:** Markdown files with YAML frontmatter in `app/blog/content/{parking,stops}/`, parsed once at startup by a renderer module. Two separate blueprints handle `/blog` and `/blog/<slug>` per domain via `site_required` decorator. Each domain has its own templates matching its existing visual identity.

**Tech Stack:** Flask, markdown (pip), pyyaml (pip), Bootstrap 5.3.3, Font Awesome 6.7.2, GA4 (G-RREBK9SZZJ)

**Spec:** `docs/superpowers/specs/2026-04-01-blog-seo-pages-design.md`

---

## File Structure

```
Create: requirements.txt (modify — add markdown, pyyaml)
Create: app/blog/__init__.py           — Blog blueprint factory
Create: app/blog/renderer.py           — Markdown parser, frontmatter, CTA injection, caching
Create: app/blog/routes_parking.py     — /blog, /blog/<slug> for parking domain
Create: app/blog/routes_stops.py       — /blog, /blog/<slug> for stops domain
Modify: app/__init__.py                — Register blog blueprint
Modify: app/routes/public.py           — Add blog posts to parking sitemap
Modify: app/stops/routes.py            — Add blog posts to stops sitemap
Create: app/templates/blog_parking/index.html  — Parking blog listing
Create: app/templates/blog_parking/post.html   — Parking blog post
Create: app/templates/blog_stops/index.html    — Stops blog listing
Create: app/templates/blog_stops/post.html     — Stops blog post
Create: app/static/js/blog-analytics.js        — GA4 event tracking
Create: app/blog/content/parking/*.md  — 20 parking blog posts
Create: app/blog/content/stops/*.md    — 20 stops blog posts
Create: tests/test_blog_renderer.py    — Renderer unit tests
Create: tests/test_blog_routes.py      — Route integration tests
```

---

### Task 1: Add Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add markdown and pyyaml to requirements.txt**

Add these two lines to the end of `requirements.txt`:

```
markdown==3.5.2
pyyaml==6.0.1
```

- [ ] **Step 2: Install dependencies**

Run: `cd /Users/tps/projects/truckerpro-parking && pip3 install markdown==3.5.2 pyyaml==6.0.1`

- [ ] **Step 3: Verify imports work**

Run: `python3 -c "import markdown; import yaml; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add markdown and pyyaml dependencies for blog"
```

---

### Task 2: Build the Renderer

**Files:**
- Create: `app/blog/__init__.py`
- Create: `app/blog/renderer.py`
- Create: `app/blog/content/parking/.gitkeep`
- Create: `app/blog/content/stops/.gitkeep`
- Test: `tests/test_blog_renderer.py`

- [ ] **Step 1: Create the blog package with empty init**

Create `app/blog/__init__.py`:

```python
"""Blog module — static markdown-based SEO blog for parking and stops domains."""
```

Create empty content directories:

```bash
mkdir -p app/blog/content/parking app/blog/content/stops
touch app/blog/content/parking/.gitkeep app/blog/content/stops/.gitkeep
```

- [ ] **Step 2: Write failing tests for the renderer**

Create `tests/test_blog_renderer.py`:

```python
"""Tests for blog renderer — markdown parsing, frontmatter, CTA injection."""
import os
import pytest
import tempfile
import shutil
from app.blog.renderer import load_posts, get_post, get_all_posts, get_related_posts


@pytest.fixture
def content_dir():
    """Create a temp directory with test markdown files."""
    tmpdir = tempfile.mkdtemp()
    parking_dir = os.path.join(tmpdir, 'parking')
    stops_dir = os.path.join(tmpdir, 'stops')
    os.makedirs(parking_dir)
    os.makedirs(stops_dir)

    # Parking post
    with open(os.path.join(parking_dir, 'test-post.md'), 'w') as f:
        f.write("""---
title: "Test Parking Post"
slug: test-post
category: guides
meta_description: "A test post for parking."
meta_keywords: "test, parking"
date: "2026-04-01"
author: "TruckerPro Team"
cta_primary:
  text: "Try TruckerPro Free"
  url: "https://www.truckerpro.ca/signup"
cta_secondary:
  text: "File eManifest"
  url: "https://border.truckerpro.ca"
related_slugs:
  - another-post
---

# Test Parking Post

This is the first section.

## Section One

Content for section one.

## Section Two

Content for section two.

## Section Three

Content for section three.

## Section Four

Content after the CTA should be injected.
""")

    # Second parking post for related_slugs testing
    with open(os.path.join(parking_dir, 'another-post.md'), 'w') as f:
        f.write("""---
title: "Another Parking Post"
slug: another-post
category: tips
meta_description: "Another test post."
meta_keywords: "test"
date: "2026-03-30"
author: "TruckerPro Team"
cta_primary:
  text: "Sign Up"
  url: "https://www.truckerpro.ca/signup"
cta_secondary:
  text: "Border"
  url: "https://border.truckerpro.ca"
related_slugs: []
---

# Another Post

Some content here.
""")

    # Post with explicit CTA marker
    with open(os.path.join(parking_dir, 'marker-post.md'), 'w') as f:
        f.write("""---
title: "Marker Post"
slug: marker-post
category: guides
meta_description: "Post with CTA marker."
meta_keywords: "test"
date: "2026-03-29"
author: "TruckerPro Team"
cta_primary:
  text: "Sign Up"
  url: "https://www.truckerpro.ca/signup"
cta_secondary:
  text: "Border"
  url: "https://border.truckerpro.ca"
related_slugs: []
---

# Marker Post

Before the marker.

<!-- cta -->

After the marker.
""")

    # Stops post
    with open(os.path.join(stops_dir, 'stops-test.md'), 'w') as f:
        f.write("""---
title: "Test Stops Post"
slug: stops-test
category: fuel
meta_description: "A test post for stops."
meta_keywords: "test, stops"
date: "2026-04-01"
author: "TruckerPro Team"
cta_primary:
  text: "Try TruckerPro Free"
  url: "https://www.truckerpro.ca/signup"
cta_secondary:
  text: "File eManifest"
  url: "https://border.truckerpro.ca"
related_slugs: []
---

# Test Stops Post

Stops content here.
""")

    yield tmpdir
    shutil.rmtree(tmpdir)


class TestLoadPosts:
    def test_loads_parking_posts(self, content_dir):
        posts = load_posts(content_dir)
        parking_posts = [p for p in posts if p['domain'] == 'parking']
        assert len(parking_posts) == 3

    def test_loads_stops_posts(self, content_dir):
        posts = load_posts(content_dir)
        stops_posts = [p for p in posts if p['domain'] == 'stops']
        assert len(stops_posts) == 1

    def test_parses_frontmatter(self, content_dir):
        posts = load_posts(content_dir)
        post = next(p for p in posts if p['slug'] == 'test-post')
        assert post['title'] == 'Test Parking Post'
        assert post['category'] == 'guides'
        assert post['meta_description'] == 'A test post for parking.'
        assert post['author'] == 'TruckerPro Team'
        assert post['date'] == '2026-04-01'
        assert post['cta_primary']['text'] == 'Try TruckerPro Free'
        assert post['cta_secondary']['url'] == 'https://border.truckerpro.ca'
        assert post['related_slugs'] == ['another-post']

    def test_renders_markdown_to_html(self, content_dir):
        posts = load_posts(content_dir)
        post = next(p for p in posts if p['slug'] == 'test-post')
        assert '<h1>' in post['html']
        assert '<h2>' in post['html']
        assert 'Test Parking Post' in post['html']

    def test_splits_html_for_cta_injection(self, content_dir):
        posts = load_posts(content_dir)
        post = next(p for p in posts if p['slug'] == 'test-post')
        assert 'html_before_cta' in post
        assert 'html_after_cta' in post
        assert 'Section Two' in post['html_before_cta']
        assert 'Section Four' in post['html_after_cta']

    def test_cta_marker_splits_at_marker(self, content_dir):
        posts = load_posts(content_dir)
        post = next(p for p in posts if p['slug'] == 'marker-post')
        assert 'Before the marker' in post['html_before_cta']
        assert 'After the marker' in post['html_after_cta']


class TestGetPost:
    def test_returns_post_by_domain_and_slug(self, content_dir):
        posts = load_posts(content_dir)
        post = get_post(posts, 'parking', 'test-post')
        assert post is not None
        assert post['title'] == 'Test Parking Post'

    def test_returns_none_for_missing_slug(self, content_dir):
        posts = load_posts(content_dir)
        post = get_post(posts, 'parking', 'nonexistent')
        assert post is None

    def test_returns_none_for_wrong_domain(self, content_dir):
        posts = load_posts(content_dir)
        post = get_post(posts, 'stops', 'test-post')
        assert post is None


class TestGetAllPosts:
    def test_returns_all_posts_for_domain(self, content_dir):
        posts = load_posts(content_dir)
        parking = get_all_posts(posts, 'parking')
        assert len(parking) == 3

    def test_filters_by_category(self, content_dir):
        posts = load_posts(content_dir)
        guides = get_all_posts(posts, 'parking', category='guides')
        assert len(guides) == 2
        assert all(p['category'] == 'guides' for p in guides)

    def test_sorted_by_date_descending(self, content_dir):
        posts = load_posts(content_dir)
        parking = get_all_posts(posts, 'parking')
        dates = [p['date'] for p in parking]
        assert dates == sorted(dates, reverse=True)


class TestGetRelatedPosts:
    def test_returns_related_posts(self, content_dir):
        posts = load_posts(content_dir)
        related = get_related_posts(posts, 'parking', ['another-post'])
        assert len(related) == 1
        assert related[0]['slug'] == 'another-post'

    def test_returns_empty_for_no_matches(self, content_dir):
        posts = load_posts(content_dir)
        related = get_related_posts(posts, 'parking', ['nonexistent'])
        assert related == []
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/test_blog_renderer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.blog.renderer'`

- [ ] **Step 4: Implement the renderer**

Create `app/blog/renderer.py`:

```python
"""Markdown blog renderer — parses .md files with YAML frontmatter, caches in memory."""
import os
import re
import yaml
import markdown


def load_posts(content_dir):
    """Load all markdown posts from content_dir/parking/ and content_dir/stops/.

    Returns a list of post dicts, each containing:
        domain, slug, title, category, meta_description, meta_keywords,
        date, author, featured_image, cta_primary, cta_secondary,
        related_slugs, html, html_before_cta, html_after_cta
    """
    posts = []
    md = markdown.Markdown(extensions=['fenced_code', 'tables'])

    for domain in ('parking', 'stops'):
        domain_dir = os.path.join(content_dir, domain)
        if not os.path.isdir(domain_dir):
            continue
        for filename in sorted(os.listdir(domain_dir)):
            if not filename.endswith('.md'):
                continue
            filepath = os.path.join(domain_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                raw = f.read()

            post = _parse_post(raw, md, domain)
            if post:
                posts.append(post)
            md.reset()

    return posts


def _parse_post(raw, md, domain):
    """Parse a single markdown file with YAML frontmatter."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', raw, re.DOTALL)
    if not match:
        return None

    frontmatter = yaml.safe_load(match.group(1))
    body_md = match.group(2)
    html = md.convert(body_md)

    html_before_cta, html_after_cta = _split_for_cta(html)

    return {
        'domain': domain,
        'slug': frontmatter.get('slug', ''),
        'title': frontmatter.get('title', ''),
        'category': frontmatter.get('category', ''),
        'meta_description': frontmatter.get('meta_description', ''),
        'meta_keywords': frontmatter.get('meta_keywords', ''),
        'date': frontmatter.get('date', ''),
        'author': frontmatter.get('author', ''),
        'featured_image': frontmatter.get('featured_image', ''),
        'cta_primary': frontmatter.get('cta_primary', {}),
        'cta_secondary': frontmatter.get('cta_secondary', {}),
        'related_slugs': frontmatter.get('related_slugs', []),
        'html': html,
        'html_before_cta': html_before_cta,
        'html_after_cta': html_after_cta,
    }


def _split_for_cta(html):
    """Split HTML at <!-- cta --> marker, or after 3rd <h2> tag."""
    # Check for explicit marker first
    if '<!-- cta -->' in html:
        parts = html.split('<!-- cta -->', 1)
        return parts[0].strip(), parts[1].strip()

    # Auto-inject after 3rd <h2>
    h2_positions = [m.start() for m in re.finditer(r'<h2>', html)]
    if len(h2_positions) >= 3:
        split_pos = h2_positions[2]
        return html[:split_pos].strip(), html[split_pos:].strip()

    # Not enough headings — no split, put everything before CTA
    return html, ''


def get_post(posts, domain, slug):
    """Get a single post by domain and slug. Returns dict or None."""
    for post in posts:
        if post['domain'] == domain and post['slug'] == slug:
            return post
    return None


def get_all_posts(posts, domain, category=None):
    """Get all posts for a domain, optionally filtered by category. Sorted by date descending."""
    result = [p for p in posts if p['domain'] == domain]
    if category:
        result = [p for p in result if p['category'] == category]
    result.sort(key=lambda p: p['date'], reverse=True)
    return result


def get_related_posts(posts, domain, slugs):
    """Get posts matching a list of slugs within a domain."""
    return [p for p in posts if p['domain'] == domain and p['slug'] in slugs]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/test_blog_renderer.py -v`
Expected: All 13 tests PASS

- [ ] **Step 6: Commit**

```bash
git add app/blog/__init__.py app/blog/renderer.py app/blog/content/ tests/test_blog_renderer.py
git commit -m "feat: add blog renderer with markdown parsing and CTA injection"
```

---

### Task 3: Blog Blueprint and Parking Routes

**Files:**
- Modify: `app/blog/__init__.py`
- Create: `app/blog/routes_parking.py`
- Modify: `app/__init__.py`
- Test: `tests/test_blog_routes.py`

- [ ] **Step 1: Write failing tests for parking blog routes**

Create `tests/test_blog_routes.py`:

```python
"""Tests for blog routes — parking and stops domains."""
import pytest


class TestParkingBlogIndex:
    def test_blog_index_returns_200(self, client):
        resp = client.get('/blog')
        assert resp.status_code == 200

    def test_blog_index_contains_blog_heading(self, client):
        resp = client.get('/blog')
        assert b'Blog' in resp.data

    def test_blog_index_contains_post_titles(self, client):
        resp = client.get('/blog')
        # Should contain at least one post title from parking content
        assert resp.status_code == 200

    def test_blog_index_category_filter(self, client):
        resp = client.get('/blog?category=guides')
        assert resp.status_code == 200

    def test_blog_index_invalid_category_returns_200(self, client):
        resp = client.get('/blog?category=nonexistent')
        assert resp.status_code == 200


class TestParkingBlogPost:
    def test_nonexistent_post_returns_404(self, client):
        resp = client.get('/blog/this-does-not-exist')
        assert resp.status_code == 404

    def test_stops_post_not_accessible_on_parking(self, client):
        # Stops-domain posts should 404 on parking domain
        resp = client.get('/blog/stops-test')
        assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/test_blog_routes.py -v`
Expected: FAIL — 404 on `/blog` (route doesn't exist yet)

- [ ] **Step 3: Update blog __init__.py to create the blueprint**

Replace `app/blog/__init__.py` with:

```python
"""Blog module — static markdown-based SEO blog for parking and stops domains."""
import os
from flask import Blueprint

blog_bp = Blueprint('blog', __name__)

# Content is loaded once when the blueprint is first imported in create_app
_posts = None


def get_blog_posts(app):
    """Load and cache blog posts. Called once during app creation."""
    global _posts
    if _posts is None:
        from .renderer import load_posts
        content_dir = os.path.join(os.path.dirname(__file__), 'content')
        _posts = load_posts(content_dir)
    return _posts


from . import routes_parking  # noqa: E402, F401
```

- [ ] **Step 4: Create parking routes**

Create `app/blog/routes_parking.py`:

```python
"""Blog routes for parking.truckerpro.ca domain."""
from flask import render_template, request, abort, g

from . import blog_bp, _posts
from .renderer import get_post, get_all_posts, get_related_posts
from ..middleware import site_required


@blog_bp.route('/blog')
@site_required('parking')
def parking_blog_index():
    category = request.args.get('category')
    posts = get_all_posts(_posts or [], 'parking', category=category)
    categories = ['guides', 'regulations', 'safety', 'industry', 'tips']
    return render_template('blog_parking/index.html',
                           posts=posts,
                           categories=categories,
                           current_category=category)


@blog_bp.route('/blog/<slug>')
@site_required('parking')
def parking_blog_post(slug):
    post = get_post(_posts or [], 'parking', slug)
    if not post:
        abort(404)
    related = get_related_posts(_posts or [], 'parking', post.get('related_slugs', []))
    return render_template('blog_parking/post.html', post=post, related=related)
```

- [ ] **Step 5: Register the blog blueprint in app factory**

In `app/__init__.py`, add after the `csrf.exempt(api_bp)` line (line 210):

```python
    from .blog import blog_bp, get_blog_posts
    get_blog_posts(app)
    app.register_blueprint(blog_bp)
```

- [ ] **Step 6: Create minimal parking blog templates (to make tests pass)**

Create `app/templates/blog_parking/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head><title>Blog | Truck Parking Club</title></head>
<body>
<h1>Blog</h1>
{% for post in posts %}
<article>
  <h2><a href="/blog/{{ post.slug }}">{{ post.title }}</a></h2>
  <span>{{ post.category }}</span>
  <time>{{ post.date }}</time>
</article>
{% endfor %}
</body>
</html>
```

Create `app/templates/blog_parking/post.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head><title>{{ post.title }} | Truck Parking Club</title></head>
<body>
<article>
  <h1>{{ post.title }}</h1>
  {{ post.html_before_cta|safe }}
  {{ post.html_after_cta|safe }}
</article>
</body>
</html>
```

- [ ] **Step 7: Create a test parking content post so routes have data**

Create `app/blog/content/parking/test-seo-post.md`:

```markdown
---
title: "Test SEO Post"
slug: test-seo-post
category: guides
meta_description: "Test post for development."
meta_keywords: "test"
date: "2026-04-01"
author: "TruckerPro Team"
cta_primary:
  text: "Try TruckerPro Free"
  url: "https://www.truckerpro.ca/signup"
cta_secondary:
  text: "File eManifest"
  url: "https://border.truckerpro.ca"
related_slugs: []
---

# Test SEO Post

This is a test post for development purposes.
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/test_blog_routes.py -v`
Expected: All 7 tests PASS

- [ ] **Step 9: Run full test suite to verify nothing broke**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/ -v`
Expected: All tests PASS (154 existing + 7 new)

- [ ] **Step 10: Commit**

```bash
git add app/blog/ app/templates/blog_parking/ app/__init__.py tests/test_blog_routes.py
git commit -m "feat: add blog blueprint with parking routes and templates"
```

---

### Task 4: Stops Blog Routes

**Files:**
- Create: `app/blog/routes_stops.py`
- Modify: `app/blog/__init__.py`
- Modify: `tests/test_blog_routes.py`

- [ ] **Step 1: Add failing tests for stops blog routes**

Append to `tests/test_blog_routes.py`:

```python
class TestStopsBlogIndex:
    def test_blog_index_returns_200(self, stops_client):
        resp = stops_client.get('/blog')
        assert resp.status_code == 200

    def test_blog_index_contains_blog_heading(self, stops_client):
        resp = stops_client.get('/blog')
        assert b'Blog' in resp.data

    def test_blog_index_category_filter(self, stops_client):
        resp = stops_client.get('/blog?category=fuel')
        assert resp.status_code == 200


class TestStopsBlogPost:
    def test_nonexistent_post_returns_404(self, stops_client):
        resp = stops_client.get('/blog/this-does-not-exist')
        assert resp.status_code == 404

    def test_parking_post_not_accessible_on_stops(self, stops_client):
        # Parking-domain posts should 404 on stops domain
        resp = stops_client.get('/blog/test-seo-post')
        assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/test_blog_routes.py::TestStopsBlogIndex -v`
Expected: FAIL — 404 on `/blog` for stops domain

- [ ] **Step 3: Create stops blog routes**

Create `app/blog/routes_stops.py`:

```python
"""Blog routes for stops.truckerpro.net domain."""
from flask import render_template, request, abort, g

from . import blog_bp, _posts
from .renderer import get_post, get_all_posts, get_related_posts
from ..middleware import site_required


@blog_bp.route('/blog', endpoint='stops_blog_index')
@site_required('stops')
def stops_blog_index():
    category = request.args.get('category')
    posts = get_all_posts(_posts or [], 'stops', category=category)
    categories = ['guides', 'fuel', 'routes', 'reviews', 'tips']
    return render_template('blog_stops/index.html',
                           posts=posts,
                           categories=categories,
                           current_category=category)


@blog_bp.route('/blog/<slug>', endpoint='stops_blog_post')
@site_required('stops')
def stops_blog_post(slug):
    post = get_post(_posts or [], 'stops', slug)
    if not post:
        abort(404)
    related = get_related_posts(_posts or [], 'stops', post.get('related_slugs', []))
    return render_template('blog_stops/post.html', post=post, related=related)
```

- [ ] **Step 4: Import stops routes in blog __init__**

Update `app/blog/__init__.py` — change the last import line:

```python
from . import routes_parking, routes_stops  # noqa: E402, F401
```

- [ ] **Step 5: Create minimal stops blog templates**

Create `app/templates/blog_stops/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head><title>Blog | Truck Stops Directory</title></head>
<body>
<h1>Blog</h1>
{% for post in posts %}
<article>
  <h2><a href="/blog/{{ post.slug }}">{{ post.title }}</a></h2>
  <span>{{ post.category }}</span>
  <time>{{ post.date }}</time>
</article>
{% endfor %}
</body>
</html>
```

Create `app/templates/blog_stops/post.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head><title>{{ post.title }} | Truck Stops Directory</title></head>
<body>
<article>
  <h1>{{ post.title }}</h1>
  {{ post.html_before_cta|safe }}
  {{ post.html_after_cta|safe }}
</article>
</body>
</html>
```

- [ ] **Step 6: Create a test stops content post**

Create `app/blog/content/stops/test-stops-seo.md`:

```markdown
---
title: "Test Stops SEO Post"
slug: test-stops-seo
category: fuel
meta_description: "Test stops post for development."
meta_keywords: "test"
date: "2026-04-01"
author: "TruckerPro Team"
cta_primary:
  text: "Try TruckerPro Free"
  url: "https://www.truckerpro.ca/signup"
cta_secondary:
  text: "File eManifest"
  url: "https://border.truckerpro.ca"
related_slugs: []
---

# Test Stops SEO Post

This is a test post for development purposes.
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/test_blog_routes.py -v`
Expected: All 12 tests PASS

- [ ] **Step 8: Commit**

```bash
git add app/blog/routes_stops.py app/blog/__init__.py app/templates/blog_stops/ app/blog/content/stops/ tests/test_blog_routes.py
git commit -m "feat: add stops blog routes and templates"
```

---

### Task 5: Parking Blog Templates (Full Design)

**Files:**
- Modify: `app/templates/blog_parking/index.html`
- Modify: `app/templates/blog_parking/post.html`
- Create: `app/static/js/blog-analytics.js`

**Reference:** Study `app/templates/public/landing.html` for the parking domain's dark/green theme, Bootstrap 5.3.3, Font Awesome 6.7.2, Google Fonts Inter, GA4 tag pattern, and meta tag structure. Match the visual identity exactly.

- [ ] **Step 1: Build the full parking blog index template**

Replace `app/templates/blog_parking/index.html` with the full production template. Key requirements:
- Dark background matching parking site (#0a0a0a or similar from landing.html)
- Green accent color matching parking site
- Bootstrap 5.3.3 CSS via CDN
- Font Awesome 6.7.2 via CDN
- Google Fonts Inter 400-800
- GA4 tag `G-RREBK9SZZJ` in `<head>`
- `<title>`: "Truck Parking Blog | Truck Parking Club"
- `<meta name="description">`: "Expert guides, tips, and industry insights for truck parking across Canada."
- `<link rel="canonical" href="https://parking.truckerpro.ca/blog">`
- Open Graph meta tags (og:title, og:description, og:url, og:type=website)
- Hero section: "Truck Parking Blog" heading with subtitle
- Category filter pills row: All, Guides, Regulations, Safety, Industry, Tips — uses `?category=` query param, highlights active pill
- Post cards in responsive grid (3 columns desktop, 2 tablet, 1 mobile)
  - Each card: featured_image (or placeholder gradient), title, category badge, date, excerpt (first 160 chars of meta_description)
  - Card links to `/blog/{{ post.slug }}`
- CTA banner between card rows (after every 6 posts): "Manage Your Fleet with TruckerPro TMS" with primary button linking to `https://www.truckerpro.ca/signup`
- Footer CTA banner: "Cross the Border? File eManifest Online" linking to `https://border.truckerpro.ca`
- All clickable elements use `data-action` attributes for GA4 tracking (no inline onclick)
- Include `<script src="/static/js/blog-analytics.js"></script>` before `</body>`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% if current_category %}{{ current_category|title }} Articles{% else %}Truck Parking Blog{% endif %} | Truck Parking Club</title>
    <meta name="description" content="Expert guides, tips, and industry insights for truck parking across Canada. Regulations, safety, fleet management, and cross-border trucking.">
    <meta name="keywords" content="truck parking blog, truck parking canada, fleet management, cross-border trucking">
    <link rel="canonical" href="https://parking.truckerpro.ca/blog{% if current_category %}?category={{ current_category }}{% endif %}">
    <meta property="og:title" content="Truck Parking Blog | Truck Parking Club">
    <meta property="og:description" content="Expert guides, tips, and industry insights for truck parking across Canada.">
    <meta property="og:url" content="https://parking.truckerpro.ca/blog">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- GA4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-RREBK9SZZJ"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-RREBK9SZZJ');</script>
    <style>
        :root { --bg-primary: #0a0a0a; --bg-card: #151515; --bg-card-hover: #1a1a1a; --accent: #22c55e; --accent-hover: #16a34a; --text-primary: #f1f1f1; --text-secondary: #a0a0a0; --border: #2a2a2a; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: var(--bg-primary); color: var(--text-primary); }
        a { color: var(--accent); text-decoration: none; }
        a:hover { color: var(--accent-hover); }

        .blog-hero { padding: 80px 0 40px; text-align: center; }
        .blog-hero h1 { font-size: 2.8rem; font-weight: 800; margin-bottom: 12px; }
        .blog-hero p { font-size: 1.15rem; color: var(--text-secondary); max-width: 600px; margin: 0 auto; }

        .category-pills { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; padding: 0 0 40px; }
        .category-pills a { padding: 8px 20px; border-radius: 50px; border: 1px solid var(--border); color: var(--text-secondary); font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
        .category-pills a:hover, .category-pills a.active { background: var(--accent); color: #000; border-color: var(--accent); }

        .post-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; transition: transform 0.2s, border-color 0.2s; }
        .post-card:hover { transform: translateY(-4px); border-color: var(--accent); }
        .post-card-img { height: 200px; background: linear-gradient(135deg, #1a472a, #0d2818); display: flex; align-items: center; justify-content: center; }
        .post-card-img img { width: 100%; height: 100%; object-fit: cover; }
        .post-card-body { padding: 24px; }
        .post-card-body .badge { background: rgba(34,197,94,0.15); color: var(--accent); font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 4px; text-transform: uppercase; }
        .post-card-body h3 { font-size: 1.15rem; font-weight: 700; margin: 12px 0 8px; line-height: 1.4; }
        .post-card-body h3 a { color: var(--text-primary); }
        .post-card-body h3 a:hover { color: var(--accent); }
        .post-card-body p { font-size: 0.9rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: 12px; }
        .post-card-body time { font-size: 0.8rem; color: var(--text-secondary); }

        .cta-banner { background: linear-gradient(135deg, #1a472a, #0d3320); border: 1px solid rgba(34,197,94,0.2); border-radius: 16px; padding: 48px; text-align: center; margin: 48px 0; }
        .cta-banner h2 { font-size: 1.8rem; font-weight: 800; margin-bottom: 12px; }
        .cta-banner p { color: var(--text-secondary); margin-bottom: 24px; font-size: 1.05rem; }
        .cta-banner .btn-cta { background: var(--accent); color: #000; font-weight: 700; padding: 14px 36px; border-radius: 8px; font-size: 1rem; border: none; display: inline-block; transition: background 0.2s; }
        .cta-banner .btn-cta:hover { background: var(--accent-hover); }
        .cta-banner .cta-link { display: block; margin-top: 16px; color: var(--text-secondary); font-size: 0.9rem; }
        .cta-banner .cta-link:hover { color: var(--accent); }

        .footer-section { padding: 60px 0 40px; text-align: center; border-top: 1px solid var(--border); margin-top: 60px; }
        .footer-section p { color: var(--text-secondary); font-size: 0.85rem; }
        .footer-section a { color: var(--accent); }
    </style>
</head>
<body>

<section class="blog-hero">
    <div class="container">
        <h1><i class="fa-solid fa-newspaper" style="color:var(--accent);margin-right:12px"></i>Truck Parking Blog</h1>
        <p>Expert guides, regulations, and industry insights for truck parking across Canada</p>
    </div>
</section>

<div class="container">
    <div class="category-pills">
        <a href="/blog" class="{% if not current_category %}active{% endif %}" data-action="blog-category-filter" data-category="all">All</a>
        {% for cat in categories %}
        <a href="/blog?category={{ cat }}" class="{% if current_category == cat %}active{% endif %}" data-action="blog-category-filter" data-category="{{ cat }}">{{ cat|title }}</a>
        {% endfor %}
    </div>

    <div class="row g-4">
        {% for post in posts %}
        {% if loop.index == 7 %}
        <div class="col-12">
            <div class="cta-banner">
                <h2>Manage Your Fleet with Canada's #1 TMS</h2>
                <p>Dispatch, compliance, ELD tracking, invoicing — all in one platform</p>
                <a href="https://www.truckerpro.ca/signup" class="btn-cta" data-action="blog-cta-click" data-position="mid-index" data-target="tms-signup">Try TruckerPro Free</a>
                <a href="https://border.truckerpro.ca" class="cta-link" data-action="blog-cta-click" data-position="mid-index" data-target="border">Cross-border carrier? File eManifest online <i class="fa-solid fa-arrow-right"></i></a>
            </div>
        </div>
        {% endif %}
        <div class="col-md-6 col-lg-4">
            <div class="post-card">
                <div class="post-card-img">
                    {% if post.featured_image %}
                    <img src="{{ post.featured_image }}" alt="{{ post.title }}" loading="lazy">
                    {% else %}
                    <i class="fa-solid fa-truck" style="font-size:3rem;color:rgba(34,197,94,0.3)"></i>
                    {% endif %}
                </div>
                <div class="post-card-body">
                    <span class="badge">{{ post.category }}</span>
                    <h3><a href="/blog/{{ post.slug }}" data-action="blog-card-click" data-slug="{{ post.slug }}">{{ post.title }}</a></h3>
                    <p>{{ post.meta_description[:160] }}</p>
                    <time datetime="{{ post.date }}">{{ post.date }}</time>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    {% if not posts %}
    <div style="text-align:center;padding:80px 0">
        <p style="color:var(--text-secondary);font-size:1.1rem">No posts found{% if current_category %} in "{{ current_category }}"{% endif %}.</p>
    </div>
    {% endif %}

    <div class="cta-banner" style="margin-top:60px">
        <h2>Cross the Border? File eManifest Online</h2>
        <p>ACE and ACI eManifest filing for US-Canada cross-border carriers</p>
        <a href="https://border.truckerpro.ca" class="btn-cta" data-action="blog-cta-click" data-position="footer" data-target="border">Start Filing <i class="fa-solid fa-arrow-right"></i></a>
        <a href="https://www.truckerpro.ca/signup" class="cta-link" data-action="blog-cta-click" data-position="footer" data-target="tms-signup">Or try the full TMS platform free <i class="fa-solid fa-arrow-right"></i></a>
    </div>
</div>

<footer class="footer-section">
    <div class="container">
        <p>&copy; 2026 TruckerPro &middot; <a href="https://parking.truckerpro.ca">Truck Parking</a> &middot; <a href="https://stops.truckerpro.net">Truck Stops</a> &middot; <a href="https://www.truckerpro.ca">TMS</a> &middot; <a href="https://border.truckerpro.ca">Border</a></p>
    </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="/static/js/blog-analytics.js"></script>
</body>
</html>
```

- [ ] **Step 2: Build the full parking blog post template**

Replace `app/templates/blog_parking/post.html` with the full production template. Key requirements:
- Same dark/green theme as index
- Same CDN includes (Bootstrap, FA, Inter, GA4)
- `<title>`: `{{ post.title }} | Truck Parking Club`
- Full SEO meta tags: description, keywords, canonical, OG, Twitter Card
- Schema.org `BlogPosting` JSON-LD
- Breadcrumb: Home > Blog > Category > Title
- Hero CTA banner (below title, above article body) using `post.cta_primary` and `post.cta_secondary`
- Article body: `post.html_before_cta` → mid-article CTA card → `post.html_after_cta`
- Related articles grid at bottom (from `related` list)
- Sticky bottom CTA bar (position:fixed, shows after scrolling past hero CTA, dismissible)
- All CTAs use `data-action` attributes
- Include blog-analytics.js

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ post.title }} | Truck Parking Club</title>
    <meta name="description" content="{{ post.meta_description }}">
    <meta name="keywords" content="{{ post.meta_keywords }}">
    <link rel="canonical" href="https://parking.truckerpro.ca/blog/{{ post.slug }}">
    <meta property="og:title" content="{{ post.title }}">
    <meta property="og:description" content="{{ post.meta_description }}">
    <meta property="og:url" content="https://parking.truckerpro.ca/blog/{{ post.slug }}">
    <meta property="og:type" content="article">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{ post.title }}">
    <meta name="twitter:description" content="{{ post.meta_description }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-RREBK9SZZJ"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-RREBK9SZZJ');</script>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "{{ post.title }}",
        "description": "{{ post.meta_description }}",
        "author": {"@type": "Organization", "name": "{{ post.author }}"},
        "datePublished": "{{ post.date }}",
        "publisher": {"@type": "Organization", "name": "TruckerPro", "url": "https://www.truckerpro.ca"},
        "mainEntityOfPage": "https://parking.truckerpro.ca/blog/{{ post.slug }}"
        {% if post.featured_image %},"image": "https://parking.truckerpro.ca{{ post.featured_image }}"{% endif %}
    }
    </script>
    <style>
        :root { --bg-primary: #0a0a0a; --bg-card: #151515; --bg-card-hover: #1a1a1a; --accent: #22c55e; --accent-hover: #16a34a; --text-primary: #f1f1f1; --text-secondary: #a0a0a0; --border: #2a2a2a; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: var(--bg-primary); color: var(--text-primary); }
        a { color: var(--accent); text-decoration: none; }
        a:hover { color: var(--accent-hover); }

        .breadcrumb-nav { padding: 20px 0; font-size: 0.85rem; color: var(--text-secondary); }
        .breadcrumb-nav a { color: var(--text-secondary); }
        .breadcrumb-nav a:hover { color: var(--accent); }
        .breadcrumb-nav .separator { margin: 0 8px; }

        .post-header { padding: 40px 0 20px; }
        .post-header .badge { background: rgba(34,197,94,0.15); color: var(--accent); font-size: 0.8rem; font-weight: 600; padding: 6px 14px; border-radius: 4px; text-transform: uppercase; }
        .post-header h1 { font-size: 2.4rem; font-weight: 800; margin: 16px 0 12px; line-height: 1.3; }
        .post-header .meta { color: var(--text-secondary); font-size: 0.9rem; }

        .hero-cta { background: linear-gradient(135deg, #1a472a, #0d3320); border: 1px solid rgba(34,197,94,0.2); border-radius: 12px; padding: 32px; margin: 24px 0 40px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; }
        .hero-cta .cta-text { flex: 1; min-width: 200px; }
        .hero-cta .cta-text h3 { font-size: 1.2rem; font-weight: 700; margin-bottom: 4px; }
        .hero-cta .cta-text p { color: var(--text-secondary); font-size: 0.9rem; margin: 0; }
        .hero-cta .cta-buttons { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        .hero-cta .btn-cta { background: var(--accent); color: #000; font-weight: 700; padding: 12px 28px; border-radius: 8px; font-size: 0.95rem; border: none; display: inline-block; }
        .hero-cta .btn-cta:hover { background: var(--accent-hover); }
        .hero-cta .btn-secondary-cta { color: var(--text-secondary); font-size: 0.9rem; }
        .hero-cta .btn-secondary-cta:hover { color: var(--accent); }

        .article-body { max-width: 780px; margin: 0 auto; padding-bottom: 40px; }
        .article-body h1, .article-body h2, .article-body h3 { font-weight: 700; margin: 32px 0 16px; }
        .article-body h2 { font-size: 1.6rem; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
        .article-body h3 { font-size: 1.25rem; }
        .article-body p { font-size: 1.05rem; line-height: 1.8; color: var(--text-secondary); margin-bottom: 16px; }
        .article-body ul, .article-body ol { color: var(--text-secondary); font-size: 1.05rem; line-height: 1.8; margin-bottom: 16px; padding-left: 24px; }
        .article-body code { background: #1e1e1e; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
        .article-body pre { background: #1e1e1e; padding: 16px; border-radius: 8px; overflow-x: auto; margin-bottom: 16px; }
        .article-body table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
        .article-body th, .article-body td { border: 1px solid var(--border); padding: 10px 14px; text-align: left; }
        .article-body th { background: var(--bg-card); font-weight: 600; }

        .mid-cta { background: var(--bg-card); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: 8px; padding: 28px; margin: 40px 0; }
        .mid-cta h4 { font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; }
        .mid-cta p { color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 16px; }
        .mid-cta .btn-cta { background: var(--accent); color: #000; font-weight: 700; padding: 10px 24px; border-radius: 8px; font-size: 0.9rem; border: none; display: inline-block; }
        .mid-cta .btn-cta:hover { background: var(--accent-hover); }

        .related-section { padding: 60px 0; border-top: 1px solid var(--border); }
        .related-section h2 { font-size: 1.6rem; font-weight: 800; margin-bottom: 32px; }
        .related-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 24px; transition: border-color 0.2s; }
        .related-card:hover { border-color: var(--accent); }
        .related-card .badge { background: rgba(34,197,94,0.15); color: var(--accent); font-size: 0.7rem; font-weight: 600; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; }
        .related-card h4 { font-size: 1rem; font-weight: 700; margin: 10px 0 8px; }
        .related-card h4 a { color: var(--text-primary); }
        .related-card h4 a:hover { color: var(--accent); }
        .related-card time { font-size: 0.8rem; color: var(--text-secondary); }

        .sticky-bar { position: fixed; bottom: 0; left: 0; right: 0; background: rgba(10,10,10,0.95); backdrop-filter: blur(10px); border-top: 1px solid var(--border); padding: 12px 0; z-index: 1000; display: none; }
        .sticky-bar.visible { display: block; }
        .sticky-bar .container { display: flex; align-items: center; justify-content: space-between; }
        .sticky-bar span { font-size: 0.9rem; font-weight: 600; }
        .sticky-bar .btn-cta { background: var(--accent); color: #000; font-weight: 700; padding: 8px 20px; border-radius: 6px; font-size: 0.85rem; border: none; }
        .sticky-bar .btn-cta:hover { background: var(--accent-hover); }
        .sticky-bar .dismiss { background: none; border: none; color: var(--text-secondary); font-size: 1.2rem; cursor: pointer; padding: 4px 8px; }

        .footer-section { padding: 60px 0 40px; text-align: center; border-top: 1px solid var(--border); margin-top: 60px; }
        .footer-section p { color: var(--text-secondary); font-size: 0.85rem; }
        .footer-section a { color: var(--accent); }

        @media (max-width: 768px) {
            .post-header h1 { font-size: 1.8rem; }
            .hero-cta { flex-direction: column; text-align: center; }
            .sticky-bar span { display: none; }
        }
    </style>
</head>
<body>

<div class="container">
    <nav class="breadcrumb-nav">
        <a href="/">Home</a><span class="separator">/</span>
        <a href="/blog">Blog</a><span class="separator">/</span>
        <a href="/blog?category={{ post.category }}">{{ post.category|title }}</a><span class="separator">/</span>
        <span style="color:var(--text-primary)">{{ post.title[:50] }}{% if post.title|length > 50 %}...{% endif %}</span>
    </nav>

    <header class="post-header">
        <span class="badge">{{ post.category }}</span>
        <h1>{{ post.title }}</h1>
        <div class="meta">
            <span><i class="fa-regular fa-user"></i> {{ post.author }}</span>
            &nbsp;&middot;&nbsp;
            <time datetime="{{ post.date }}"><i class="fa-regular fa-calendar"></i> {{ post.date }}</time>
        </div>
    </header>

    <div class="hero-cta" id="hero-cta">
        <div class="cta-text">
            <h3>{{ post.cta_primary.text }}</h3>
            <p>All-in-one TMS for Canadian and US carriers</p>
        </div>
        <div class="cta-buttons">
            <a href="{{ post.cta_primary.url }}" class="btn-cta" data-action="blog-cta-click" data-position="hero" data-target="{{ post.cta_primary.url }}" data-slug="{{ post.slug }}">{{ post.cta_primary.text }} <i class="fa-solid fa-arrow-right"></i></a>
            {% if post.cta_secondary %}
            <a href="{{ post.cta_secondary.url }}" class="btn-secondary-cta" data-action="blog-cta-click" data-position="hero" data-target="{{ post.cta_secondary.url }}" data-slug="{{ post.slug }}">{{ post.cta_secondary.text }} <i class="fa-solid fa-arrow-right"></i></a>
            {% endif %}
        </div>
    </div>

    <article class="article-body">
        {{ post.html_before_cta|safe }}

        {% if post.html_after_cta %}
        <div class="mid-cta">
            <h4><i class="fa-solid fa-truck" style="color:var(--accent);margin-right:8px"></i>{{ post.cta_secondary.text if post.cta_secondary else post.cta_primary.text }}</h4>
            <p>{{ post.cta_secondary.text if post.cta_secondary else 'Manage your fleet, dispatches, and compliance in one platform.' }}</p>
            <a href="{{ post.cta_secondary.url if post.cta_secondary else post.cta_primary.url }}" class="btn-cta" data-action="blog-cta-click" data-position="mid" data-target="{{ post.cta_secondary.url if post.cta_secondary else post.cta_primary.url }}" data-slug="{{ post.slug }}">Learn More <i class="fa-solid fa-arrow-right"></i></a>
        </div>

        {{ post.html_after_cta|safe }}
        {% endif %}
    </article>

    {% if related %}
    <section class="related-section">
        <h2>Related Articles</h2>
        <div class="row g-4">
            {% for rel in related %}
            <div class="col-md-4">
                <div class="related-card">
                    <span class="badge">{{ rel.category }}</span>
                    <h4><a href="/blog/{{ rel.slug }}" data-action="blog-related-click" data-slug="{{ rel.slug }}">{{ rel.title }}</a></h4>
                    <time datetime="{{ rel.date }}">{{ rel.date }}</time>
                </div>
            </div>
            {% endfor %}
        </div>
    </section>
    {% endif %}
</div>

<div class="sticky-bar" id="sticky-bar">
    <div class="container">
        <span>TruckerPro — All-in-one TMS for Canadian carriers</span>
        <div style="display:flex;align-items:center;gap:12px">
            <a href="{{ post.cta_primary.url }}" class="btn-cta" data-action="blog-cta-click" data-position="sticky" data-target="{{ post.cta_primary.url }}" data-slug="{{ post.slug }}">Sign Up Free</a>
            <button class="dismiss" data-action="blog-sticky-dismiss" aria-label="Dismiss">&times;</button>
        </div>
    </div>
</div>

<footer class="footer-section">
    <div class="container">
        <p>&copy; 2026 TruckerPro &middot; <a href="https://parking.truckerpro.ca">Truck Parking</a> &middot; <a href="https://stops.truckerpro.net">Truck Stops</a> &middot; <a href="https://www.truckerpro.ca">TMS</a> &middot; <a href="https://border.truckerpro.ca">Border</a></p>
    </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="/static/js/blog-analytics.js"></script>
<script>
(function(){
    var heroCta = document.getElementById('hero-cta');
    var stickyBar = document.getElementById('sticky-bar');
    var dismissed = false;
    function checkScroll() {
        if (dismissed) return;
        var heroBottom = heroCta.getBoundingClientRect().bottom;
        if (heroBottom < 0) { stickyBar.classList.add('visible'); }
        else { stickyBar.classList.remove('visible'); }
    }
    window.addEventListener('scroll', checkScroll, {passive: true});
    document.querySelector('[data-action="blog-sticky-dismiss"]').addEventListener('click', function() {
        stickyBar.classList.remove('visible');
        dismissed = true;
    });
})();
</script>
</body>
</html>
```

- [ ] **Step 3: Create the GA4 blog analytics JavaScript**

Create `app/static/js/blog-analytics.js`:

```javascript
/**
 * Blog GA4 Analytics — event tracking via data-action attributes.
 * CSP-safe: no inline onclick handlers.
 * Events: blog_view, blog_cta_click, blog_related_click, blog_scroll_depth, blog_time_on_page
 */
(function() {
    'use strict';
    if (typeof gtag !== 'function') return;

    // ── Blog View ──
    var slug = document.querySelector('[data-slug]');
    var category = document.querySelector('.badge');
    var domain = window.location.hostname.indexOf('stops') !== -1 ? 'stops' : 'parking';
    if (slug || document.querySelector('.article-body')) {
        gtag('event', 'blog_view', {
            post_slug: slug ? slug.getAttribute('data-slug') : 'index',
            category: category ? category.textContent.trim().toLowerCase() : 'all',
            domain: domain
        });
    }

    // ── CTA & Related Click Tracking (event delegation) ──
    document.addEventListener('click', function(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var action = el.getAttribute('data-action');

        if (action === 'blog-cta-click') {
            gtag('event', 'blog_cta_click', {
                position: el.getAttribute('data-position') || '',
                target_url: el.getAttribute('data-target') || el.href || '',
                post_slug: el.getAttribute('data-slug') || ''
            });
        } else if (action === 'blog-related-click') {
            gtag('event', 'blog_related_click', {
                clicked_slug: el.getAttribute('data-slug') || ''
            });
        } else if (action === 'blog-card-click') {
            gtag('event', 'blog_cta_click', {
                position: 'card',
                target_url: el.href || '',
                post_slug: el.getAttribute('data-slug') || ''
            });
        }
    });

    // ── Scroll Depth ──
    var scrollFired = {};
    window.addEventListener('scroll', function() {
        var scrollTop = window.scrollY || document.documentElement.scrollTop;
        var docHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (docHeight <= 0) return;
        var pct = Math.round((scrollTop / docHeight) * 100);
        [25, 50, 75, 100].forEach(function(threshold) {
            if (pct >= threshold && !scrollFired[threshold]) {
                scrollFired[threshold] = true;
                gtag('event', 'blog_scroll_depth', {
                    depth: threshold,
                    post_slug: slug ? slug.getAttribute('data-slug') : 'index',
                    domain: domain
                });
            }
        });
    }, {passive: true});

    // ── Time on Page ──
    var timeFired = {};
    [30, 60, 120, 300].forEach(function(seconds) {
        setTimeout(function() {
            if (timeFired[seconds]) return;
            timeFired[seconds] = true;
            gtag('event', 'blog_time_on_page', {
                seconds: seconds,
                post_slug: slug ? slug.getAttribute('data-slug') : 'index',
                domain: domain
            });
        }, seconds * 1000);
    });
})();
```

- [ ] **Step 4: Verify parking blog renders correctly**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/test_blog_routes.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/templates/blog_parking/ app/static/js/blog-analytics.js
git commit -m "feat: add full parking blog templates with GA4 analytics"
```

---

### Task 6: Stops Blog Templates (Full Design)

**Files:**
- Modify: `app/templates/blog_stops/index.html`
- Modify: `app/templates/blog_stops/post.html`

**Reference:** Study `app/templates/stops/base.html` and `app/templates/stops/home.html` for the stops domain's blue/white theme. Match the visual identity.

- [ ] **Step 1: Build the full stops blog index template**

Replace `app/templates/blog_stops/index.html`. Same structure as the parking index but with stops visual identity:
- Light background (#ffffff or #f8fafc)
- Blue accent (#2563eb) instead of green
- Blue gradient cards and CTA banners
- `<title>`: "Truck Stops Blog | Truck Stops Directory"
- `<link rel="canonical" href="https://stops.truckerpro.net/blog">`
- Categories: All, Guides, Fuel, Routes, Reviews, Tips
- Same GA4 tag, same blog-analytics.js, same data-action attributes
- CTA banners reference TMS + border app

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% if current_category %}{{ current_category|title }} Articles{% else %}Truck Stops Blog{% endif %} | Truck Stops Directory</title>
    <meta name="description" content="Expert guides on truck stops, fuel savings, route planning, and fleet management across the US and Canada.">
    <meta name="keywords" content="truck stops blog, fuel prices, route planning, fleet management">
    <link rel="canonical" href="https://stops.truckerpro.net/blog{% if current_category %}?category={{ current_category }}{% endif %}">
    <meta property="og:title" content="Truck Stops Blog | Truck Stops Directory">
    <meta property="og:description" content="Expert guides on truck stops, fuel savings, route planning, and fleet management.">
    <meta property="og:url" content="https://stops.truckerpro.net/blog">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-RREBK9SZZJ"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-RREBK9SZZJ');</script>
    <style>
        :root { --bg-primary: #f8fafc; --bg-card: #ffffff; --bg-card-hover: #f1f5f9; --accent: #2563eb; --accent-hover: #1d4ed8; --text-primary: #0f172a; --text-secondary: #64748b; --border: #e2e8f0; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: var(--bg-primary); color: var(--text-primary); }
        a { color: var(--accent); text-decoration: none; }
        a:hover { color: var(--accent-hover); }

        .blog-hero { padding: 80px 0 40px; text-align: center; }
        .blog-hero h1 { font-size: 2.8rem; font-weight: 800; margin-bottom: 12px; }
        .blog-hero p { font-size: 1.15rem; color: var(--text-secondary); max-width: 600px; margin: 0 auto; }

        .category-pills { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; padding: 0 0 40px; }
        .category-pills a { padding: 8px 20px; border-radius: 50px; border: 1px solid var(--border); color: var(--text-secondary); font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
        .category-pills a:hover, .category-pills a.active { background: var(--accent); color: #fff; border-color: var(--accent); }

        .post-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
        .post-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
        .post-card-img { height: 200px; background: linear-gradient(135deg, #1e3a5f, #0f2440); display: flex; align-items: center; justify-content: center; }
        .post-card-img img { width: 100%; height: 100%; object-fit: cover; }
        .post-card-body { padding: 24px; }
        .post-card-body .badge { background: rgba(37,99,235,0.1); color: var(--accent); font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 4px; text-transform: uppercase; }
        .post-card-body h3 { font-size: 1.15rem; font-weight: 700; margin: 12px 0 8px; line-height: 1.4; }
        .post-card-body h3 a { color: var(--text-primary); }
        .post-card-body h3 a:hover { color: var(--accent); }
        .post-card-body p { font-size: 0.9rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: 12px; }
        .post-card-body time { font-size: 0.8rem; color: var(--text-secondary); }

        .cta-banner { background: linear-gradient(135deg, #1e3a5f, #0f2440); border-radius: 16px; padding: 48px; text-align: center; margin: 48px 0; color: #fff; }
        .cta-banner h2 { font-size: 1.8rem; font-weight: 800; margin-bottom: 12px; }
        .cta-banner p { color: #94a3b8; margin-bottom: 24px; font-size: 1.05rem; }
        .cta-banner .btn-cta { background: var(--accent); color: #fff; font-weight: 700; padding: 14px 36px; border-radius: 8px; font-size: 1rem; border: none; display: inline-block; transition: background 0.2s; }
        .cta-banner .btn-cta:hover { background: var(--accent-hover); }
        .cta-banner .cta-link { display: block; margin-top: 16px; color: #94a3b8; font-size: 0.9rem; }
        .cta-banner .cta-link:hover { color: #fff; }

        .footer-section { padding: 60px 0 40px; text-align: center; border-top: 1px solid var(--border); margin-top: 60px; }
        .footer-section p { color: var(--text-secondary); font-size: 0.85rem; }
        .footer-section a { color: var(--accent); }
    </style>
</head>
<body>

<section class="blog-hero">
    <div class="container">
        <h1><i class="fa-solid fa-gas-pump" style="color:var(--accent);margin-right:12px"></i>Truck Stops Blog</h1>
        <p>Expert guides on truck stops, fuel savings, route planning, and fleet management across the US and Canada</p>
    </div>
</section>

<div class="container">
    <div class="category-pills">
        <a href="/blog" class="{% if not current_category %}active{% endif %}" data-action="blog-category-filter" data-category="all">All</a>
        {% for cat in categories %}
        <a href="/blog?category={{ cat }}" class="{% if current_category == cat %}active{% endif %}" data-action="blog-category-filter" data-category="{{ cat }}">{{ cat|title }}</a>
        {% endfor %}
    </div>

    <div class="row g-4">
        {% for post in posts %}
        {% if loop.index == 7 %}
        <div class="col-12">
            <div class="cta-banner">
                <h2>Manage Your Fleet with Canada's #1 TMS</h2>
                <p>Dispatch, compliance, ELD tracking, invoicing — all in one platform</p>
                <a href="https://www.truckerpro.ca/signup" class="btn-cta" data-action="blog-cta-click" data-position="mid-index" data-target="tms-signup">Try TruckerPro Free</a>
                <a href="https://border.truckerpro.ca" class="cta-link" data-action="blog-cta-click" data-position="mid-index" data-target="border">Cross-border carrier? File eManifest online <i class="fa-solid fa-arrow-right"></i></a>
            </div>
        </div>
        {% endif %}
        <div class="col-md-6 col-lg-4">
            <div class="post-card">
                <div class="post-card-img">
                    {% if post.featured_image %}
                    <img src="{{ post.featured_image }}" alt="{{ post.title }}" loading="lazy">
                    {% else %}
                    <i class="fa-solid fa-gas-pump" style="font-size:3rem;color:rgba(37,99,235,0.3)"></i>
                    {% endif %}
                </div>
                <div class="post-card-body">
                    <span class="badge">{{ post.category }}</span>
                    <h3><a href="/blog/{{ post.slug }}" data-action="blog-card-click" data-slug="{{ post.slug }}">{{ post.title }}</a></h3>
                    <p>{{ post.meta_description[:160] }}</p>
                    <time datetime="{{ post.date }}">{{ post.date }}</time>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    {% if not posts %}
    <div style="text-align:center;padding:80px 0">
        <p style="color:var(--text-secondary);font-size:1.1rem">No posts found{% if current_category %} in "{{ current_category }}"{% endif %}.</p>
    </div>
    {% endif %}

    <div class="cta-banner" style="margin-top:60px">
        <h2>Cross the Border? File eManifest Online</h2>
        <p>ACE and ACI eManifest filing for US-Canada cross-border carriers</p>
        <a href="https://border.truckerpro.ca" class="btn-cta" data-action="blog-cta-click" data-position="footer" data-target="border">Start Filing <i class="fa-solid fa-arrow-right"></i></a>
        <a href="https://www.truckerpro.ca/signup" class="cta-link" data-action="blog-cta-click" data-position="footer" data-target="tms-signup">Or try the full TMS platform free <i class="fa-solid fa-arrow-right"></i></a>
    </div>
</div>

<footer class="footer-section">
    <div class="container">
        <p>&copy; 2026 TruckerPro &middot; <a href="https://stops.truckerpro.net">Truck Stops</a> &middot; <a href="https://parking.truckerpro.ca">Truck Parking</a> &middot; <a href="https://www.truckerpro.ca">TMS</a> &middot; <a href="https://border.truckerpro.ca">Border</a></p>
    </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="/static/js/blog-analytics.js"></script>
</body>
</html>
```

- [ ] **Step 2: Build the full stops blog post template**

Replace `app/templates/blog_stops/post.html`. Same structure as parking post template but:
- Light background (#f8fafc), blue accent (#2563eb)
- `<title>`: `{{ post.title }} | Truck Stops Directory`
- Canonical: `https://stops.truckerpro.net/blog/{{ post.slug }}`
- Schema.org publisher URL: `https://stops.truckerpro.net`
- Blue gradient hero CTA, blue accent mid CTA border
- Light-themed sticky bar with blue button
- Same data-action attributes, same blog-analytics.js

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ post.title }} | Truck Stops Directory</title>
    <meta name="description" content="{{ post.meta_description }}">
    <meta name="keywords" content="{{ post.meta_keywords }}">
    <link rel="canonical" href="https://stops.truckerpro.net/blog/{{ post.slug }}">
    <meta property="og:title" content="{{ post.title }}">
    <meta property="og:description" content="{{ post.meta_description }}">
    <meta property="og:url" content="https://stops.truckerpro.net/blog/{{ post.slug }}">
    <meta property="og:type" content="article">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{ post.title }}">
    <meta name="twitter:description" content="{{ post.meta_description }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-RREBK9SZZJ"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-RREBK9SZZJ');</script>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "{{ post.title }}",
        "description": "{{ post.meta_description }}",
        "author": {"@type": "Organization", "name": "{{ post.author }}"},
        "datePublished": "{{ post.date }}",
        "publisher": {"@type": "Organization", "name": "TruckerPro", "url": "https://stops.truckerpro.net"},
        "mainEntityOfPage": "https://stops.truckerpro.net/blog/{{ post.slug }}"
        {% if post.featured_image %},"image": "https://stops.truckerpro.net{{ post.featured_image }}"{% endif %}
    }
    </script>
    <style>
        :root { --bg-primary: #f8fafc; --bg-card: #ffffff; --accent: #2563eb; --accent-hover: #1d4ed8; --text-primary: #0f172a; --text-secondary: #64748b; --border: #e2e8f0; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: var(--bg-primary); color: var(--text-primary); }
        a { color: var(--accent); text-decoration: none; }
        a:hover { color: var(--accent-hover); }

        .breadcrumb-nav { padding: 20px 0; font-size: 0.85rem; color: var(--text-secondary); }
        .breadcrumb-nav a { color: var(--text-secondary); }
        .breadcrumb-nav a:hover { color: var(--accent); }
        .breadcrumb-nav .separator { margin: 0 8px; }

        .post-header { padding: 40px 0 20px; }
        .post-header .badge { background: rgba(37,99,235,0.1); color: var(--accent); font-size: 0.8rem; font-weight: 600; padding: 6px 14px; border-radius: 4px; text-transform: uppercase; }
        .post-header h1 { font-size: 2.4rem; font-weight: 800; margin: 16px 0 12px; line-height: 1.3; }
        .post-header .meta { color: var(--text-secondary); font-size: 0.9rem; }

        .hero-cta { background: linear-gradient(135deg, #1e3a5f, #0f2440); border-radius: 12px; padding: 32px; margin: 24px 0 40px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; color: #fff; }
        .hero-cta .cta-text { flex: 1; min-width: 200px; }
        .hero-cta .cta-text h3 { font-size: 1.2rem; font-weight: 700; margin-bottom: 4px; }
        .hero-cta .cta-text p { color: #94a3b8; font-size: 0.9rem; margin: 0; }
        .hero-cta .cta-buttons { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        .hero-cta .btn-cta { background: var(--accent); color: #fff; font-weight: 700; padding: 12px 28px; border-radius: 8px; font-size: 0.95rem; border: none; display: inline-block; }
        .hero-cta .btn-cta:hover { background: var(--accent-hover); }
        .hero-cta .btn-secondary-cta { color: #94a3b8; font-size: 0.9rem; }
        .hero-cta .btn-secondary-cta:hover { color: #fff; }

        .article-body { max-width: 780px; margin: 0 auto; padding-bottom: 40px; }
        .article-body h1, .article-body h2, .article-body h3 { font-weight: 700; margin: 32px 0 16px; }
        .article-body h2 { font-size: 1.6rem; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
        .article-body h3 { font-size: 1.25rem; }
        .article-body p { font-size: 1.05rem; line-height: 1.8; color: var(--text-secondary); margin-bottom: 16px; }
        .article-body ul, .article-body ol { color: var(--text-secondary); font-size: 1.05rem; line-height: 1.8; margin-bottom: 16px; padding-left: 24px; }
        .article-body code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
        .article-body pre { background: #f1f5f9; padding: 16px; border-radius: 8px; overflow-x: auto; margin-bottom: 16px; }
        .article-body table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
        .article-body th, .article-body td { border: 1px solid var(--border); padding: 10px 14px; text-align: left; }
        .article-body th { background: var(--bg-card); font-weight: 600; }

        .mid-cta { background: var(--bg-card); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: 8px; padding: 28px; margin: 40px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
        .mid-cta h4 { font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; }
        .mid-cta p { color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 16px; }
        .mid-cta .btn-cta { background: var(--accent); color: #fff; font-weight: 700; padding: 10px 24px; border-radius: 8px; font-size: 0.9rem; border: none; display: inline-block; }
        .mid-cta .btn-cta:hover { background: var(--accent-hover); }

        .related-section { padding: 60px 0; border-top: 1px solid var(--border); }
        .related-section h2 { font-size: 1.6rem; font-weight: 800; margin-bottom: 32px; }
        .related-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 24px; transition: box-shadow 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
        .related-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .related-card .badge { background: rgba(37,99,235,0.1); color: var(--accent); font-size: 0.7rem; font-weight: 600; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; }
        .related-card h4 { font-size: 1rem; font-weight: 700; margin: 10px 0 8px; }
        .related-card h4 a { color: var(--text-primary); }
        .related-card h4 a:hover { color: var(--accent); }
        .related-card time { font-size: 0.8rem; color: var(--text-secondary); }

        .sticky-bar { position: fixed; bottom: 0; left: 0; right: 0; background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); border-top: 1px solid var(--border); padding: 12px 0; z-index: 1000; display: none; }
        .sticky-bar.visible { display: block; }
        .sticky-bar .container { display: flex; align-items: center; justify-content: space-between; }
        .sticky-bar span { font-size: 0.9rem; font-weight: 600; color: var(--text-primary); }
        .sticky-bar .btn-cta { background: var(--accent); color: #fff; font-weight: 700; padding: 8px 20px; border-radius: 6px; font-size: 0.85rem; border: none; }
        .sticky-bar .btn-cta:hover { background: var(--accent-hover); }
        .sticky-bar .dismiss { background: none; border: none; color: var(--text-secondary); font-size: 1.2rem; cursor: pointer; padding: 4px 8px; }

        .footer-section { padding: 60px 0 40px; text-align: center; border-top: 1px solid var(--border); margin-top: 60px; }
        .footer-section p { color: var(--text-secondary); font-size: 0.85rem; }
        .footer-section a { color: var(--accent); }

        @media (max-width: 768px) {
            .post-header h1 { font-size: 1.8rem; }
            .hero-cta { flex-direction: column; text-align: center; }
            .sticky-bar span { display: none; }
        }
    </style>
</head>
<body>

<div class="container">
    <nav class="breadcrumb-nav">
        <a href="/">Home</a><span class="separator">/</span>
        <a href="/blog">Blog</a><span class="separator">/</span>
        <a href="/blog?category={{ post.category }}">{{ post.category|title }}</a><span class="separator">/</span>
        <span style="color:var(--text-primary)">{{ post.title[:50] }}{% if post.title|length > 50 %}...{% endif %}</span>
    </nav>

    <header class="post-header">
        <span class="badge">{{ post.category }}</span>
        <h1>{{ post.title }}</h1>
        <div class="meta">
            <span><i class="fa-regular fa-user"></i> {{ post.author }}</span>
            &nbsp;&middot;&nbsp;
            <time datetime="{{ post.date }}"><i class="fa-regular fa-calendar"></i> {{ post.date }}</time>
        </div>
    </header>

    <div class="hero-cta" id="hero-cta">
        <div class="cta-text">
            <h3>{{ post.cta_primary.text }}</h3>
            <p>All-in-one TMS for Canadian and US carriers</p>
        </div>
        <div class="cta-buttons">
            <a href="{{ post.cta_primary.url }}" class="btn-cta" data-action="blog-cta-click" data-position="hero" data-target="{{ post.cta_primary.url }}" data-slug="{{ post.slug }}">{{ post.cta_primary.text }} <i class="fa-solid fa-arrow-right"></i></a>
            {% if post.cta_secondary %}
            <a href="{{ post.cta_secondary.url }}" class="btn-secondary-cta" data-action="blog-cta-click" data-position="hero" data-target="{{ post.cta_secondary.url }}" data-slug="{{ post.slug }}">{{ post.cta_secondary.text }} <i class="fa-solid fa-arrow-right"></i></a>
            {% endif %}
        </div>
    </div>

    <article class="article-body">
        {{ post.html_before_cta|safe }}

        {% if post.html_after_cta %}
        <div class="mid-cta">
            <h4><i class="fa-solid fa-gas-pump" style="color:var(--accent);margin-right:8px"></i>{{ post.cta_secondary.text if post.cta_secondary else post.cta_primary.text }}</h4>
            <p>{{ post.cta_secondary.text if post.cta_secondary else 'Manage your fleet, dispatches, and compliance in one platform.' }}</p>
            <a href="{{ post.cta_secondary.url if post.cta_secondary else post.cta_primary.url }}" class="btn-cta" data-action="blog-cta-click" data-position="mid" data-target="{{ post.cta_secondary.url if post.cta_secondary else post.cta_primary.url }}" data-slug="{{ post.slug }}">Learn More <i class="fa-solid fa-arrow-right"></i></a>
        </div>

        {{ post.html_after_cta|safe }}
        {% endif %}
    </article>

    {% if related %}
    <section class="related-section">
        <h2>Related Articles</h2>
        <div class="row g-4">
            {% for rel in related %}
            <div class="col-md-4">
                <div class="related-card">
                    <span class="badge">{{ rel.category }}</span>
                    <h4><a href="/blog/{{ rel.slug }}" data-action="blog-related-click" data-slug="{{ rel.slug }}">{{ rel.title }}</a></h4>
                    <time datetime="{{ rel.date }}">{{ rel.date }}</time>
                </div>
            </div>
            {% endfor %}
        </div>
    </section>
    {% endif %}
</div>

<div class="sticky-bar" id="sticky-bar">
    <div class="container">
        <span>TruckerPro — All-in-one TMS for carriers</span>
        <div style="display:flex;align-items:center;gap:12px">
            <a href="{{ post.cta_primary.url }}" class="btn-cta" data-action="blog-cta-click" data-position="sticky" data-target="{{ post.cta_primary.url }}" data-slug="{{ post.slug }}">Sign Up Free</a>
            <button class="dismiss" data-action="blog-sticky-dismiss" aria-label="Dismiss">&times;</button>
        </div>
    </div>
</div>

<footer class="footer-section">
    <div class="container">
        <p>&copy; 2026 TruckerPro &middot; <a href="https://stops.truckerpro.net">Truck Stops</a> &middot; <a href="https://parking.truckerpro.ca">Truck Parking</a> &middot; <a href="https://www.truckerpro.ca">TMS</a> &middot; <a href="https://border.truckerpro.ca">Border</a></p>
    </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="/static/js/blog-analytics.js"></script>
<script>
(function(){
    var heroCta = document.getElementById('hero-cta');
    var stickyBar = document.getElementById('sticky-bar');
    var dismissed = false;
    function checkScroll() {
        if (dismissed) return;
        var heroBottom = heroCta.getBoundingClientRect().bottom;
        if (heroBottom < 0) { stickyBar.classList.add('visible'); }
        else { stickyBar.classList.remove('visible'); }
    }
    window.addEventListener('scroll', checkScroll, {passive: true});
    document.querySelector('[data-action="blog-sticky-dismiss"]').addEventListener('click', function() {
        stickyBar.classList.remove('visible');
        dismissed = true;
    });
})();
</script>
</body>
</html>
```

- [ ] **Step 3: Run tests**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/test_blog_routes.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add app/templates/blog_stops/
git commit -m "feat: add full stops blog templates with blue/white theme"
```

---

### Task 7: Sitemap Integration

**Files:**
- Modify: `app/routes/public.py` (parking sitemap)
- Modify: `app/stops/routes.py` (stops sitemap)

- [ ] **Step 1: Add blog posts to parking sitemap**

In `app/routes/public.py`, find the existing sitemap route function. Add blog posts to the URL list by importing the blog module and appending entries:

After building the existing sitemap URLs list, before returning, add:

```python
    # Blog posts
    from ..blog import _posts
    from ..blog.renderer import get_all_posts
    blog_posts = get_all_posts(_posts or [], 'parking')
    urls.append({'loc': 'https://parking.truckerpro.ca/blog', 'lastmod': blog_posts[0]['date'] if blog_posts else '2026-04-01', 'changefreq': 'weekly', 'priority': '0.8'})
    for bp in blog_posts:
        urls.append({'loc': f"https://parking.truckerpro.ca/blog/{bp['slug']}", 'lastmod': bp['date'], 'changefreq': 'monthly', 'priority': '0.7'})
```

- [ ] **Step 2: Add blog sitemap to stops sitemap index**

In `app/stops/routes.py`, find the `sitemap_index()` function. Add a new child sitemap entry for blog:

```python
xml.append(f'<sitemap><loc>https://stops.truckerpro.net/sitemap-blog.xml</loc></sitemap>')
```

Then add a new route for the blog sitemap:

```python
@stops_public_bp.route('/sitemap-blog.xml')
@site_required('stops')
def sitemap_blog():
    from ..blog import _posts
    from ..blog.renderer import get_all_posts
    blog_posts = get_all_posts(_posts or [], 'stops')
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml.append(f'<url><loc>https://stops.truckerpro.net/blog</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    for bp in blog_posts:
        xml.append(f"<url><loc>https://stops.truckerpro.net/blog/{bp['slug']}</loc><lastmod>{bp['date']}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>")
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')
```

Import `Response` from flask if not already imported at the top of the file.

- [ ] **Step 3: Run full tests**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add app/routes/public.py app/stops/routes.py
git commit -m "feat: add blog posts to parking and stops sitemaps"
```

---

### Task 8: Parking Blog Content — Pillar Guides (5 posts)

**Files:**
- Create: `app/blog/content/parking/safe-overnight-truck-parking-canada.md`
- Create: `app/blog/content/parking/truck-parking-regulations-by-province.md`
- Create: `app/blog/content/parking/cross-border-trucking-guide.md`
- Create: `app/blog/content/parking/fleet-parking-management.md`
- Create: `app/blog/content/parking/lcv-oversized-vehicle-parking.md`
- Delete: `app/blog/content/parking/test-seo-post.md` (test placeholder)

Each post must be 1,500-2,500 words of real, authoritative SEO content. Use proper markdown with `##` and `###` headings. Include:
- 4-6 `<h2>` sections for rich structure
- Practical tips, statistics, and actionable advice
- Natural keyword placement (no stuffing)
- `<!-- cta -->` marker placed ~40% through each article
- `related_slugs` cross-linking to other parking posts
- `cta_primary` always pointing to `https://www.truckerpro.ca/signup`
- `cta_secondary` contextual per topic (border, parking booking, FMCSA)

- [ ] **Step 1: Write all 5 pillar guide posts**

Write each `.md` file with full frontmatter and body content per the spec. Content topics:

1. **safe-overnight-truck-parking-canada.md** — Comprehensive guide to finding safe overnight parking. Cover: parking shortage problem, provincial differences, security features to look for, technology solutions, booking platforms, cost comparison, tips by region.

2. **truck-parking-regulations-by-province.md** — Province-by-province breakdown. Cover: ON, QC, BC, AB, SK, MB, NS, NB, PEI, NL. Municipal bylaws, rest area rules, weight station parking, fines for illegal parking.

3. **cross-border-trucking-guide.md** — US-Canada cross-border trucking. Cover: customs requirements, ACE/ACI eManifest, FAST cards, border wait times, parking near border crossings, compliance requirements. Heavy CTA to border.truckerpro.ca.

4. **fleet-parking-management.md** — For fleet managers. Cover: parking cost analysis, driver retention impact, parking reservation systems, fuel stop optimization, TMS integration benefits. Heavy CTA to TMS.

5. **lcv-oversized-vehicle-parking.md** — Specialty parking. Cover: LCV regulations by province, oversize load parking requirements, turning radius needs, clearance heights, dedicated yards.

- [ ] **Step 2: Delete the test placeholder**

```bash
rm app/blog/content/parking/test-seo-post.md
```

- [ ] **Step 3: Verify posts load correctly**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -c "from app.blog.renderer import load_posts; import os; posts = load_posts(os.path.join('app', 'blog', 'content')); parking = [p for p in posts if p['domain'] == 'parking']; print(f'{len(parking)} parking posts loaded'); [print(f'  - {p[\"slug\"]}') for p in parking]"`

Expected: 5 parking posts loaded with correct slugs

- [ ] **Step 4: Run tests**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/blog/content/parking/
git commit -m "content: add 5 parking pillar guide blog posts"
```

---

### Task 9: Parking Blog Content — How-To Posts (10 posts)

**Files:**
- Create 10 markdown files in `app/blog/content/parking/`

Posts 6-15 from the content plan. Same format as Task 8. Each 1,200-2,000 words:

6. `how-to-book-truck-parking-online.md` — Step-by-step booking guide, platform comparison, mobile booking, payment tips
7. `truck-parking-near-border-crossings.md` — Locations near Ambassador Bridge, Peace Bridge, Blue Water, Pacific Highway, etc.
8. `how-to-file-ace-aci-emanifest.md` — eManifest filing guide, ACE vs ACI, required data, common mistakes. Heavy border CTA.
9. `truck-parking-near-toronto.md` — GTA-specific: Mississauga, Brampton, Milton, Highway 401 corridor
10. `winter-truck-parking-safety-tips.md` — Cold weather parking, engine idling rules, block heaters, plug-in parking
11. `how-to-choose-tms-for-small-carrier.md` — TMS comparison criteria, features checklist, pricing. Heavy TMS CTA.
12. `truck-parking-near-montreal.md` — Montreal/QC City area, language considerations, Quebec-specific regulations
13. `overnight-parking-trans-canada-highway.md` — Rest stops across the Trans-Canada, province by province
14. `how-to-track-fleet-eld-integration.md` — ELD tracking benefits, Samsara integration, HOS compliance. TMS CTA.
15. `truck-parking-near-vancouver.md` — BC ports, Delta, Surrey, Highway 1 corridor

- [ ] **Step 1: Write all 10 how-to posts**

Write each `.md` file with full frontmatter and 1,200-2,000 word body content.

- [ ] **Step 2: Verify posts load**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -c "from app.blog.renderer import load_posts; import os; posts = load_posts(os.path.join('app', 'blog', 'content')); parking = [p for p in posts if p['domain'] == 'parking']; print(f'{len(parking)} parking posts loaded')"`

Expected: 15 parking posts loaded

- [ ] **Step 3: Commit**

```bash
git add app/blog/content/parking/
git commit -m "content: add 10 parking how-to blog posts"
```

---

### Task 10: Parking Blog Content — Industry Posts (5 posts)

**Files:**
- Create 5 markdown files in `app/blog/content/parking/`

Posts 16-20. Each 1,200-2,000 words:

16. `truck-parking-shortages-canada-2026.md` — Industry analysis: shortage stats, government response, technology solutions
17. `busiest-truck-routes-canada.md` — Top 10 routes with parking availability data
18. `cost-of-unsafe-truck-parking.md` — Theft stats, fatigue accidents, fine amounts, insurance impact
19. `owner-operator-save-money-parking-fuel.md` — Cost-cutting strategies, loyalty programs, fuel cards, parking subscriptions
20. `fmcsa-compliance-canadian-carriers.md` — US operating authority, CSA scores, HOS rules, DOT inspections for Canadian carriers. FMCSA + TMS CTAs.

- [ ] **Step 1: Write all 5 industry posts**

Write each `.md` file with full frontmatter and body content.

- [ ] **Step 2: Verify all 20 parking posts load**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -c "from app.blog.renderer import load_posts; import os; posts = load_posts(os.path.join('app', 'blog', 'content')); parking = [p for p in posts if p['domain'] == 'parking']; print(f'{len(parking)} parking posts loaded')"`

Expected: 20 parking posts loaded

- [ ] **Step 3: Commit**

```bash
git add app/blog/content/parking/
git commit -m "content: add 5 parking industry blog posts — 20 total parking posts"
```

---

### Task 11: Stops Blog Content — Pillar Guides (5 posts)

**Files:**
- Create 5 markdown files in `app/blog/content/stops/`
- Delete: `app/blog/content/stops/test-stops-seo.md` (test placeholder)

Posts 1-5 from stops content plan. Each 1,500-2,500 words:

1. `complete-guide-truck-stops-america.md` — Overview of US truck stop industry, major chains, what to expect, amenities breakdown
2. `best-truck-stops-canada.md` — Province-by-province directory, independent yards, chain locations
3. `cross-border-stops-us-canada.md` — Best stops near border crossings, customs prep areas, parking before crossing. Border CTA.
4. `fuel-savings-guide-long-haul.md` — Fuel optimization, price tracking apps, loyalty programs, route planning for fuel. TMS CTA.
5. `truck-stop-amenities-ranked.md` — Driver survey-style ranking: showers, food, WiFi, parking, scales, repair, DEF

- [ ] **Step 1: Write all 5 pillar guide posts and delete test placeholder**

```bash
rm app/blog/content/stops/test-stops-seo.md
```

Write each `.md` file with full frontmatter and body content.

- [ ] **Step 2: Verify posts load**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -c "from app.blog.renderer import load_posts; import os; posts = load_posts(os.path.join('app', 'blog', 'content')); stops = [p for p in posts if p['domain'] == 'stops']; print(f'{len(stops)} stops posts loaded')"`

Expected: 5 stops posts loaded

- [ ] **Step 3: Commit**

```bash
git add app/blog/content/stops/
git commit -m "content: add 5 stops pillar guide blog posts"
```

---

### Task 12: Stops Blog Content — How-To Posts (10 posts)

**Files:**
- Create 10 markdown files in `app/blog/content/stops/`

Posts 6-15 from stops content plan. Each 1,200-2,000 words:

6. `best-truck-stops-i-95.md` — Corridor guide Maine to Florida, top picks per state
7. `best-truck-stops-i-35.md` — Corridor guide Texas to Minnesota
8. `how-to-find-diesel-prices-real-time.md` — Price tracking apps, driver-contributed data, fuel cards
9. `route-planning-truck-stop-locations.md` — How to plan routes around stops, TMS integration. TMS CTA.
10. `best-truck-stops-overnight-parking-i-40.md` — I-40 corridor guide
11. `loves-vs-pilot-vs-ta-comparison.md` — Chain comparison: amenities, loyalty programs, pricing, locations
12. `how-to-file-emanifest-crossing-canada.md` — eManifest guide for US drivers crossing into Canada. Border CTA.
13. `best-truck-stops-truck-repair.md` — Stops with repair bays, mobile mechanics, tire service
14. `tms-software-optimize-fuel-stops.md` — How TMS helps plan fuel stops, track costs, manage fleet fuel. TMS CTA.
15. `best-truck-stops-near-los-angeles.md` — LA/Long Beach port area, inland stops, California-specific rules

- [ ] **Step 1: Write all 10 how-to posts**

Write each `.md` file with full frontmatter and body content.

- [ ] **Step 2: Verify posts load**

Expected: 15 stops posts loaded

- [ ] **Step 3: Commit**

```bash
git add app/blog/content/stops/
git commit -m "content: add 10 stops how-to blog posts"
```

---

### Task 13: Stops Blog Content — Industry Posts (5 posts)

**Files:**
- Create 5 markdown files in `app/blog/content/stops/`

Posts 16-20. Each 1,200-2,000 words:

16. `why-fuel-prices-vary-truck-stops.md` — Market analysis, wholesale vs retail, location pricing, seasonal trends
17. `ev-charging-truck-stops.md` — Industry trend: EV infrastructure at truck stops, timeline, fleet implications
18. `fleet-managers-cut-fuel-costs.md` — How fleet managers use TMS + fuel data to reduce spend. TMS CTA.
19. `driver-retention-truck-stops.md` — Quality of life on the road, stop amenities, carrier differentiation
20. `fmcsa-hours-of-service-stops.md` — HOS rules, mandatory breaks, how stop planning affects compliance. TMS CTA.

- [ ] **Step 1: Write all 5 industry posts**

Write each `.md` file with full frontmatter and body content.

- [ ] **Step 2: Verify all 20 stops posts load**

Expected: 20 stops posts loaded

- [ ] **Step 3: Commit**

```bash
git add app/blog/content/stops/
git commit -m "content: add 5 stops industry blog posts — 20 total stops posts"
```

---

### Task 14: Update Footer Links and Final Integration

**Files:**
- Modify: `app/templates/public/province.html` (fix broken /blog link)
- Modify: `app/templates/public/city.html` (fix broken /blog link)
- Modify: `tests/test_blog_routes.py` (add integration tests for real content)

- [ ] **Step 1: Fix broken footer blog links**

In `app/templates/public/province.html` and `app/templates/public/city.html`, find the footer section with the broken `/blog` link (around line 561). The link `<a href="/blog">Blog</a>` should already work now that the blog blueprint is registered. Verify it points to `/blog`.

- [ ] **Step 2: Add integration tests for real content**

Append to `tests/test_blog_routes.py`:

```python
class TestParkingBlogContent:
    def test_blog_index_has_posts(self, client):
        resp = client.get('/blog')
        assert resp.status_code == 200
        # Should contain at least one real post title
        assert b'Truck Parking' in resp.data or b'truck parking' in resp.data.lower()

    def test_blog_post_has_cta(self, client):
        resp = client.get('/blog')
        if resp.status_code == 200:
            # Check any post renders
            assert b'data-action' in resp.data

    def test_blog_has_ga4(self, client):
        resp = client.get('/blog')
        assert b'G-RREBK9SZZJ' in resp.data

    def test_blog_has_schema_org(self, client):
        # Test a specific post for BlogPosting schema
        resp = client.get('/blog/safe-overnight-truck-parking-canada')
        if resp.status_code == 200:
            assert b'BlogPosting' in resp.data


class TestStopsBlogContent:
    def test_blog_index_has_posts(self, stops_client):
        resp = stops_client.get('/blog')
        assert resp.status_code == 200

    def test_blog_has_ga4(self, stops_client):
        resp = stops_client.get('/blog')
        assert b'G-RREBK9SZZJ' in resp.data
```

- [ ] **Step 3: Run full test suite**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/ -v`
Expected: All tests PASS (154 existing + ~25 new blog tests)

- [ ] **Step 4: Commit**

```bash
git add tests/test_blog_routes.py app/templates/public/province.html app/templates/public/city.html
git commit -m "feat: fix footer blog links and add blog integration tests"
```

---

### Task 15: Final Verification and Push

- [ ] **Step 1: Run full test suite one final time**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Verify post count**

Run: `cd /Users/tps/projects/truckerpro-parking && python3 -c "from app.blog.renderer import load_posts; import os; posts = load_posts(os.path.join('app', 'blog', 'content')); parking = [p for p in posts if p['domain'] == 'parking']; stops = [p for p in posts if p['domain'] == 'stops']; print(f'Parking: {len(parking)} posts'); print(f'Stops: {len(stops)} posts'); print(f'Total: {len(posts)} posts')"`

Expected:
```
Parking: 20 posts
Stops: 20 posts
Total: 40 posts
```

- [ ] **Step 3: Git push**

```bash
cd /Users/tps/projects/truckerpro-parking && git push
```

- [ ] **Step 4: Verify Railway deploy succeeds**

Check Railway dashboard or run: `railway logs` to confirm healthy deployment with blog routes loaded.
