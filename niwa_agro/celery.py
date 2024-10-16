import os

from celery import Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niwa_agro.settings')
app = Celery('niwa_agro')
CELERY_CONFIG = {
    'broker_connection_retry_on_startup': True,  # or False, depending on your current configuration
    # ... other configurations ...
}

# Updating the Celery configuration with the new settings
app.conf.update(**CELERY_CONFIG)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')