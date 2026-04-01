from celery import Celery
import os

celery_app = Celery(
    'parking',
    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
)
celery_app.autodiscover_tasks(['app.tasks'])

# Shared Flask app for tasks — created once, not per-task
_flask_app = None


def get_flask_app():
    global _flask_app
    if _flask_app is None:
        from app import create_app
        _flask_app = create_app()
    return _flask_app
