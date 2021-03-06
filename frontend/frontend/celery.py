from __future__ import absolute_import
from celery import Celery
from datetime import timedelta
from django.conf import settings

app = Celery('scapl')

# Using a string here means the worker will not have to pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

CELERYBEAT_SCHEDULE = {
    'run-expiration': {
        'task': 'remove_expirables',
        'schedule': timedelta(seconds=10),
    },
}


# TODO: make the remove_expirables a periodic task
@app.task(bind=True)
def remove_expirables(self):
    pass
