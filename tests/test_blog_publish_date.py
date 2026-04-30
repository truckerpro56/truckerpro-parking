"""Tests for blog publish-date filtering.

Round-3 #G: a draft committed with `date: 2099-01-01` must NOT appear in
listings, sitemap entries, or related-post links until its date arrives.
"""
from datetime import date, timedelta


def _post(slug, post_date, domain='stops', category='ops'):
    return {
        'domain': domain,
        'slug': slug,
        'title': slug,
        'category': category,
        'meta_description': '',
        'meta_keywords': '',
        'date': post_date,
        'author': '',
        'featured_image': '',
        'cta_primary': {},
        'cta_secondary': {},
        'related_slugs': [],
        'html': '',
        'html_before_cta': '',
        'html_after_cta': '',
    }


def _today():
    return date.today().isoformat()


def _future():
    return (date.today() + timedelta(days=30)).isoformat()


def _past():
    return (date.today() - timedelta(days=30)).isoformat()


def test_is_published_today_and_past_only():
    from app.blog.renderer import _is_published
    assert _is_published(_today()) is True
    assert _is_published(_past()) is True
    assert _is_published(_future()) is False


def test_is_published_handles_date_objects():
    from app.blog.renderer import _is_published
    assert _is_published(date.today()) is True
    assert _is_published(date.today() + timedelta(days=10)) is False


def test_is_published_handles_unparseable_string_as_published():
    """Legacy / malformed date strings shouldn't accidentally hide a post."""
    from app.blog.renderer import _is_published
    assert _is_published('') is True
    assert _is_published(None) is True
    assert _is_published('not-a-date') is True


def test_get_all_posts_excludes_future_dated_by_default():
    from app.blog.renderer import get_all_posts
    posts = [
        _post('past-1', _past()),
        _post('future-1', _future()),
        _post('today-1', _today()),
    ]
    result = get_all_posts(posts, 'stops')
    slugs = [p['slug'] for p in result]
    assert 'past-1' in slugs
    assert 'today-1' in slugs
    assert 'future-1' not in slugs


def test_get_all_posts_admin_can_include_unpublished():
    from app.blog.renderer import get_all_posts
    posts = [_post('past-1', _past()), _post('future-1', _future())]
    result = get_all_posts(posts, 'stops', include_unpublished=True)
    slugs = [p['slug'] for p in result]
    assert 'future-1' in slugs


def test_get_post_hides_future_dated_by_default():
    from app.blog.renderer import get_post
    posts = [_post('future-only', _future())]
    assert get_post(posts, 'stops', 'future-only') is None
    # Admin/preview path
    assert get_post(posts, 'stops', 'future-only', include_unpublished=True) is not None


def test_get_related_posts_filters_future():
    from app.blog.renderer import get_related_posts
    posts = [_post('rel-past', _past()), _post('rel-future', _future())]
    related = get_related_posts(posts, 'stops', ['rel-past', 'rel-future'])
    slugs = [p['slug'] for p in related]
    assert 'rel-past' in slugs
    assert 'rel-future' not in slugs
