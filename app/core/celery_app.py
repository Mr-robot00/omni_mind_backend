# app/core/celery_app.py
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL")

if not redis_url:
    print("🚨 WARNING: REDIS_URL is missing! Celery will not be able to connect to the queue.")

# Initialize the Celery application
# 'worker' is the name of our task app
# broker handles the queue, backend stores the result
celery = Celery(
    "worker",
    broker=redis_url,
    backend=redis_url 
)

# Optional configuration to make it robust
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],  
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # This ensures a worker doesn't hog a task forever if it crashes
    task_time_limit=600, # 10 minutes max per task
)