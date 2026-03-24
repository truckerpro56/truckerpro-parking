#!/bin/bash
ROLE="${RAILWAY_SERVICE_ROLE:-web}"
if [ "$ROLE" = "worker" ]; then
    exec celery -A app.tasks worker --loglevel=info
elif [ "$ROLE" = "beat" ]; then
    exec celery -A app.tasks beat --loglevel=info
else
    exec gunicorn "app:create_app()" -c gunicorn.conf.py
fi
