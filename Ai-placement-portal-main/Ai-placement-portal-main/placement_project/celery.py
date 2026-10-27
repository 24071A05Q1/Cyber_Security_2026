import os
from celery import Celery

# Default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'placement_project.settings')

app = Celery('placement_project')

# Use Redis as broker & result backend
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'

# Optional — speed and reliability tweaks
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
)

# Load task modules from all registered Django apps
app.autodiscover_tasks()
