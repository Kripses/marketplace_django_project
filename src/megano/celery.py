import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'megano.settings')
app = Celery(
    'megano',
    broker='amqp://{user}:{passwd}@{host}:{port}'.format(
        user=settings.RABBITMQ_USER,
        passwd=settings.RABBITMQ_PASS,
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
    ),
    backend='redis://{host}:{port}/{db}'.format(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
    ),
)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
