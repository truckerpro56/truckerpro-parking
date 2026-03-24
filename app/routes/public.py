from flask import render_template, jsonify
from . import pages_bp


@pages_bp.route('/')
def landing():
    """Main landing page — public, SEO-optimized."""
    return render_template('public/landing.html')


@pages_bp.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200


@pages_bp.route('/ready')
def ready():
    return jsonify({'status': 'ready'}), 200
