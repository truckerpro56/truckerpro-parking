"""Blog module — static markdown-based SEO blog for parking and stops domains."""
import os
from flask import Blueprint

blog_bp = Blueprint('blog', __name__)

_posts = None


def get_blog_posts(app):
    """Load and cache blog posts. Called once during app creation."""
    global _posts
    if _posts is None:
        from .renderer import load_posts
        content_dir = os.path.join(os.path.dirname(__file__), 'content')
        _posts = load_posts(content_dir)
    return _posts


from . import routes_parking, routes_stops  # noqa: E402, F401
