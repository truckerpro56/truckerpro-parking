from celery import Celery
from celery.schedules import crontab
import os

celery_app = Celery(
    'parking',
    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
)
celery_app.autodiscover_tasks(['app.tasks'])

# Run Celery Beat in Eastern time so the digest schedule below tracks DST
# automatically. Without this, hour=13 UTC was "8am EST" in winter but
# "9am EDT" in summer — drivers got the digest an hour late for ~8 months.
# Override via CELERY_TIMEZONE if a deploy needs different local semantics.
celery_app.conf.timezone = os.environ.get('CELERY_TIMEZONE', 'America/Toronto')
celery_app.conf.enable_utc = False

# Periodic tasks (Celery Beat). Schedules below are now in CELERY_TIMEZONE.
celery_app.conf.beat_schedule = {
    'weekly-fuel-digest': {
        'task': 'app.tasks.send_weekly_fuel_digests',
        # Monday 8 AM Eastern, year-round — DST handled by celery_app.conf.timezone
        'schedule': crontab(hour=8, minute=0, day_of_week=1),
    },
    'purge-old-webhook-events': {
        'task': 'app.tasks.purge_old_webhook_events',
        # Daily at 3 AM Eastern (low-traffic window)
        'schedule': crontab(hour=3, minute=0),
    },
}

# Shared Flask app for tasks — created once, not per-task
_flask_app = None


def get_flask_app():
    global _flask_app
    if _flask_app is None:
        from app import create_app
        _flask_app = create_app()
    return _flask_app
