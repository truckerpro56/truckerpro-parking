import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get('WEB_CONCURRENCY', 1))
worker_class = 'eventlet'
timeout = 120

# Recycle workers to prevent memory leaks
max_requests = 500
max_requests_jitter = 50
