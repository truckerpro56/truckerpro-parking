from celery import Celery
import os

celery_app = Celery(
    'parking',
    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
)
celery_app.autodiscover_tasks(['app.tasks'])
