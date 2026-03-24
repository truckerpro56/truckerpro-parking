import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///parking_dev.db').replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_size': 5, 'max_overflow': 10}
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    WTF_CSRF_ENABLED = True
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'
    RATELIMIT_STORAGE_URI = 'memory://'
