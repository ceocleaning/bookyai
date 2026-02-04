"""
Scheduled Tasks for Automated Notifications
This file contains scheduled tasks that should be run periodically using Django-Q or Celery.

Setup Instructions:
1. Make sure Django-Q is installed and configured
2. Add these tasks to your Django-Q schedule or Celery beat schedule
3. Tasks will run automatically at specified intervals
"""

from notifications.services.bookings.booking_day_before_reminder import send_day_before_reminders
from notifications.services.invoices.invoice_pending_reminder import send_pending_invoice_reminders
from notifications.services.subscriptions.subscription_notifications import send_subscription_renewal_reminders


def run_daily_booking_reminders():
    """
    Send booking reminders for appointments happening tomorrow.
    Schedule: Run daily at 9:00 AM
    """
    count = send_day_before_reminders()
    print(f"Sent {count} booking reminders")
    return count


def run_daily_invoice_reminders():
    """
    Send reminders for pending and overdue invoices.
    Schedule: Run daily at 10:00 AM
    """
    count = send_pending_invoice_reminders()
    print(f"Processed {count} invoice reminders")
    return count


def run_weekly_subscription_reminders():
    """
    Send subscription renewal reminders.
    Schedule: Run weekly on Monday at 9:00 AM
    """
    count = send_subscription_renewal_reminders()
    print(f"Sent {count} subscription renewal reminders")
    return count


# Django-Q Schedule Configuration
# Add this to your Django admin or programmatically:
"""
from django_q.models import Schedule

# Booking reminders - daily at 9:00 AM
Schedule.objects.create(
    func='notifications.tasks.run_daily_booking_reminders',
    schedule_type=Schedule.DAILY,
    repeats=-1,  # Repeat indefinitely
    name='Daily Booking Reminders'
)

# Invoice reminders - daily at 10:00 AM
Schedule.objects.create(
    func='notifications.tasks.run_daily_invoice_reminders',
    schedule_type=Schedule.DAILY,
    repeats=-1,
    name='Daily Invoice Reminders'
)

# Subscription reminders - weekly on Monday
Schedule.objects.create(
    func='notifications.tasks.run_weekly_subscription_reminders',
    schedule_type=Schedule.WEEKLY,
    repeats=-1,
    name='Weekly Subscription Reminders'
)
"""

# Celery Beat Schedule Configuration (Alternative)
# Add this to your settings.py if using Celery:
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'daily-booking-reminders': {
        'task': 'notifications.tasks.run_daily_booking_reminders',
        'schedule': crontab(hour=9, minute=0),  # 9:00 AM daily
    },
    'daily-invoice-reminders': {
        'task': 'notifications.tasks.run_daily_invoice_reminders',
        'schedule': crontab(hour=10, minute=0),  # 10:00 AM daily
    },
    'weekly-subscription-reminders': {
        'task': 'notifications.tasks.run_weekly_subscription_reminders',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Monday 9:00 AM
    },
}
"""
