"""
crm/celery.py
Celery configuration for CRM application
"""

import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

# Create Celery app
app = Celery('crm')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Optional: Configure task routes
app.conf.task_routes = {
    'crm.tasks.*': {'queue': 'crm_tasks'},
    'crm.tasks.generate_crm_report': {'queue': 'reports'},
}

# Optional: Task time limits
app.conf.task_time_limit = 300  # 5 minutes
app.conf.task_soft_time_limit = 240  # 4 minutes

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery setup"""
    print(f'Request: {self.request!r}')
    