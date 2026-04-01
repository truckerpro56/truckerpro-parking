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
