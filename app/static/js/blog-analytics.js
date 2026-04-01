/**
 * blog-analytics.js — GA4 event tracking for Truck Parking Club and Truck Stops blog.
 * CSP-safe: no inline onclick/onchange handlers. Uses event delegation on data-action attributes.
 */
(function() {
    'use strict';
    if (typeof gtag !== 'function') return;

    var slug = document.querySelector('[data-slug]');
    var category = document.querySelector('.badge');
    var domain = window.location.hostname.indexOf('stops') !== -1 ? 'stops' : 'parking';

    // ── blog_view ──────────────────────────────────────────────────────────────
    if (slug || document.querySelector('.article-body')) {
        gtag('event', 'blog_view', {
            post_slug: slug ? slug.getAttribute('data-slug') : 'index',
            category: category ? category.textContent.trim().toLowerCase() : 'all',
            domain: domain
        });
    }

    // ── Click event delegation ─────────────────────────────────────────────────
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

    // ── blog_scroll_depth ──────────────────────────────────────────────────────
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

    // ── blog_time_on_page ──────────────────────────────────────────────────────
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
