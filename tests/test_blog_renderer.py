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
