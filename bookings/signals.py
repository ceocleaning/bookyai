"""
Signals for Booking notifications
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from bookings.models import Booking, BookingStatus
from notifications.services.bookings.booking_created import notify_booking_created
from notifications.services.bookings.booking_rescheduled import notify_booking_rescheduled
from notifications.services.bookings.booking_cancelled import notify_booking_cancelled
from notifications.services.bookings.booking_completion_reminder import notify_booking_completed
from notifications.services.bookings.booking_hour_before_reminder import notify_request_review


# Store previous booking state for comparison
_booking_previous_state = {}


@receiver(pre_save, sender=Booking)
def booking_pre_save_handler(sender, instance, **kwargs):
    """
    Store previous booking state before save for comparison.
    This allows us to detect changes in status, date, or time.
    
    Args:
        sender: The model class (Booking)
        instance: The actual Booking instance being saved
        **kwargs: Additional keyword arguments
    """
    if instance.pk:
        try:
            old_booking = Booking.objects.get(pk=instance.pk)
            _booking_previous_state[instance.pk] = {
                'status': old_booking.status,
                'booking_date': old_booking.booking_date,
                'start_time': old_booking.start_time,
            }
        except Booking.DoesNotExist:
            pass


@receiver(post_save, sender=Booking)
def booking_post_save_handler(sender, instance, created, **kwargs):
    """
    Handle booking notifications based on creation or status changes.
    
    This signal handler:
    - Sends creation notification for new bookings
    - Detects rescheduling (date/time changes)
    - Detects cancellations
    - Detects completions and triggers review requests
    
    Args:
        sender: The model class (Booking)
        instance: The actual Booking instance
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    
    if created:
        # New booking created - notify all parties
        notify_booking_created(instance)
    
    else:
        # Booking updated - check for status or schedule changes
        previous_state = _booking_previous_state.get(instance.pk, {})
        old_status = previous_state.get('status')
        old_date = previous_state.get('booking_date')
        old_time = previous_state.get('start_time')
        
        # Check if booking was rescheduled (date or time changed)
        if (old_date and old_time and 
            (old_date != instance.booking_date or old_time != instance.start_time)):
            notify_booking_rescheduled(instance, old_date=old_date, old_time=old_time)
        
        # Check if booking was cancelled
        if old_status and old_status != BookingStatus.CANCELLED and instance.status == BookingStatus.CANCELLED:
            notify_booking_cancelled(instance)
        
        # Check if booking was completed
        if old_status and old_status != BookingStatus.COMPLETED and instance.status == BookingStatus.COMPLETED:
            notify_booking_completed(instance)
            # Also send review request after completion
            notify_request_review(instance)
        
        # Clean up previous state to avoid memory leaks
        if instance.pk in _booking_previous_state:
            del _booking_previous_state[instance.pk]
