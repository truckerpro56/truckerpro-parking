/**
 * blog-analytics.js — GA4 event tracking for blog pages.
 * Uses event delegation on data-action attributes (no inline onclick).
 */
(function () {
    'use strict';

    function track(eventName, params) {
        if (typeof gtag === 'function') {
            gtag('event', eventName, params);
        }
    }

    // CTA click tracking via event delegation
    document.addEventListener('click', function (e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;

        var action = el.dataset.action;
        var position = el.dataset.position || '';
        var target = el.dataset.target || '';
        var slug = el.dataset.slug || '';

        if (action === 'blog-cta-click') {
            track('blog_cta_click', {
                position: position,
                target: target,
                slug: slug
            });
        } else if (action === 'blog-category-filter') {
            track('blog_category_filter', {
                category: el.dataset.category || ''
            });
        } else if (action === 'blog-related-click') {
            track('blog_related_click', {
                slug: slug
            });
        } else if (action === 'sticky-bar-dismiss') {
            track('blog_sticky_bar_dismiss', { slug: slug });
        }
    });

    // Scroll depth tracking
    var scrollMilestones = [25, 50, 75, 90];
    var fired = {};

    function getScrollPercent() {
        var scrollTop = window.scrollY || document.documentElement.scrollTop;
        var docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        return docHeight > 0 ? Math.round((scrollTop / docHeight) * 100) : 0;
    }

    window.addEventListener('scroll', function () {
        var pct = getScrollPercent();
        scrollMilestones.forEach(function (milestone) {
            if (!fired[milestone] && pct >= milestone) {
                fired[milestone] = true;
                track('blog_scroll_depth', { percent: milestone });
            }
        });
    }, { passive: true });

    // Time on page
    var startTime = Date.now();
    window.addEventListener('beforeunload', function () {
        var seconds = Math.round((Date.now() - startTime) / 1000);
        track('blog_time_on_page', { seconds: seconds });
    });
})();
