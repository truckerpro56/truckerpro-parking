import os
import eventlet
eventlet.monkey_patch()

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get('WEB_CONCURRENCY', 1))
worker_class = 'eventlet'
timeout = 120
preload_app = False
graceful_timeout = 30

# Recycle workers to prevent memory leaks
max_requests = 500
max_requests_jitter = 50


def on_starting(server):
    server.log.info("Gunicorn master starting")


def when_ready(server):
    server.log.info("Gunicorn ready — accepting connections")
