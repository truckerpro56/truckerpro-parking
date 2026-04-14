"""Celery task for async IndexNow URL submission on content mutation."""
import logging
from . import celery_app, get_flask_app

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.submit_indexnow_urls', ignore_result=True,
                 autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 2})
def submit_indexnow_urls(host, urls):
    if not urls:
        return
    flask_app = get_flask_app()
    with flask_app.app_context():
        from ..services.indexnow import submit_urls
        submit_urls(host, urls)


def enqueue_indexnow(host, urls):
    """Fire-and-forget dispatch. Safe when broker/Celery unavailable."""
    if not urls:
        return
    try:
        submit_indexnow_urls.delay(host, urls)
    except Exception as e:
        logger.warning("IndexNow enqueue failed, skipping: %s", str(e)[:200])
