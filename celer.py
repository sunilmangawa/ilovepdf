import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ilovepdf.settings')  # Update with your project name

app = Celery('celer')  # Use your project name here as well
app.conf.enable_utc = False

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")