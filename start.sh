#!/bin/bash

# Start the Celery worker in the background
# (The '&' at the end is crucial—it means "run in background")
celery -A app.core.celery_app worker --loglevel=info &

# Start the FastAPI web server in the foreground
uvicorn main:app --host 0.0.0.0 --port $PORT