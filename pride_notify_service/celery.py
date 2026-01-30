from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab


# Set default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pride_notify_service.settings')

app = Celery('pride_notify_service')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.

# Disable UTC default timezone
app.conf.enable_utc = False

# Set the timezone to Uganda
app.conf.timezone = 'Africa/Kampala'

app.config_from_object(settings, namespace='CELERY')

# Celery Beat schedule (for periodic tasks)
app.conf.beat_schedule = {
    'send-sms-every-day-at-10': {
        'task': 'pride_notify_notice.tasks.retrieve_data',
        'schedule': crontab(hour=6, minute=50), # Run everyday at 6:50 am
        # 'schedule': crontab(minute='*/1'),  # Every 1 minutes
    },
    'send-birthday-messages-every-day-at-8': {  
        'task': 'pride_notify_notice.tasks.retrieve_birthday_data',
        'schedule': crontab(hour=7, minute=20),  # Run everyday at 7:20 am
    },
    'send-ura-report-every-day-at-8': {
        'task': 'pride_notify_notice.tasks.retrieve_ura_report',
        'schedule': crontab(hour=6, minute=10),  # Run everyday at 6:10 am
    },
    'send-group-loans-report': {
        'task': 'pride_notify_notice.tasks.retrieve_group_loans',
        'schedule': crontab(hour=8, minute=17),  # Run everyday at 8:17 am
    },
    'send-escrow-notifications': {
        'task': 'pride_notify_notice.tasks.retrieve_escrow_notifications',
        'schedule': crontab(hour=6, minute=30),  # Run everyday at 6:30 am
    },
    # This should run once in a month on the 15th day at 9:00 am
    'send-atm-expiry-notifications': {
        'task': 'pride_notify_notice.tasks.retrieve_atm_expiry_notifications',
        # 'schedule': crontab(hour=9, minute=10),  # Run everyday at 9:10 am
        # 'schedule': crontab(hour=9, minute=0, day_of_month='15'),  # Run on the 15th of every month at 9:00 am
        'schedule': crontab(hour=8, minute=0, day_of_month='2'),  # Run on the 2nd of every month at 8:00 am
    },
}
    
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Debug task (useful for testing if Celery is working) - Only for Development Environment!!
@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
