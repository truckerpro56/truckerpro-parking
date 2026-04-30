import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-me'
    ADMIN_SECRET_KEY = os.environ.get('ADMIN_SECRET_KEY', '')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///parking_dev.db').replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Pool options only apply to PostgreSQL; SQLite uses StaticPool
    SQLALCHEMY_ENGINE_OPTIONS = (
        {'pool_size': 5, 'max_overflow': 10, 'pool_pre_ping': True, 'pool_recycle': 300}
        if os.environ.get('DATABASE_URL', '').startswith('postgres')
        else {}
    )
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV', '').lower() != 'development'
    WTF_CSRF_ENABLED = True
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    STOPS_DOMAIN = os.environ.get('STOPS_DOMAIN', 'stops.truckerpro.net')
    PARKING_DOMAIN = os.environ.get('PARKING_DOMAIN', 'parking.truckerpro.ca')
    INDEXNOW_KEY = os.environ.get('INDEXNOW_KEY', '')
    # Comma-separated host allowlist for review/contribution photo URLs.
    # Empty (default) means "drop all external URLs"; drivers should use the
    # in-app photo upload endpoint instead.
    PHOTO_URL_ALLOWED_HOSTS = os.environ.get('PHOTO_URL_ALLOWED_HOSTS', '')
    GSC_VERIFICATION_STOPS = os.environ.get('GSC_VERIFICATION_STOPS', '')
    GSC_VERIFICATION_PARKING = os.environ.get('GSC_VERIFICATION_PARKING', '')


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    # SERVER_NAME intentionally NOT set: with it set to 'localhost',
    # Werkzeug's host-matching rejects any test request that sends
    # `Host: stops.localhost` (used by stops_client) with a 404 before
    # the URL map is even consulted. That broke ~89 tests across
    # stops_auth/stops_routes/blog_routes/weigh_stations. Tests that
    # need an external URL can use app.test_request_context with
    # base_url='http://stops.localhost/' as needed.
    RATELIMIT_STORAGE_URI = 'memory://'
    RATELIMIT_ENABLED = False
    STOPS_DOMAIN = 'stops.localhost'
    PARKING_DOMAIN = 'localhost'
