"""Blog routes for parking.truckerpro.ca domain."""
from flask import render_template, request, abort, g

from . import blog_bp
from . import renderer as _renderer
from ..middleware import site_required
import sys


def _posts():
    """Return cached posts from the blog module (lazy reference to avoid import-time binding)."""
    mod = sys.modules.get('app.blog')
    return (mod._posts if mod is not None else None) or []


@blog_bp.route('/blog')
def blog_index():
    """Dispatch to parking or stops blog index based on g.site."""
    site = getattr(g, 'site', 'parking')
    category = request.args.get('category')
    if site == 'stops':
        posts = _renderer.get_all_posts(_posts(), 'stops', category=category)
        categories = ['guides', 'fuel', 'routes', 'reviews', 'tips']
        return render_template('blog_stops/index.html',
                               posts=posts,
                               categories=categories,
                               current_category=category)
    else:
        posts = _renderer.get_all_posts(_posts(), 'parking', category=category)
        categories = ['guides', 'regulations', 'safety', 'industry', 'tips']
        return render_template('blog_parking/index.html',
                               posts=posts,
                               categories=categories,
                               current_category=category)


@blog_bp.route('/blog/<slug>')
def blog_post(slug):
    """Dispatch to parking or stops blog post based on g.site."""
    site = getattr(g, 'site', 'parking')
    if site == 'stops':
        post = _renderer.get_post(_posts(), 'stops', slug)
        if not post:
            abort(404)
        related = _renderer.get_related_posts(_posts(), 'stops', post.get('related_slugs', []))
        return render_template('blog_stops/post.html', post=post, related=related)
    else:
        post = _renderer.get_post(_posts(), 'parking', slug)
        if not post:
            abort(404)
        related = _renderer.get_related_posts(_posts(), 'parking', post.get('related_slugs', []))
        return render_template('blog_parking/post.html', post=post, related=related)
