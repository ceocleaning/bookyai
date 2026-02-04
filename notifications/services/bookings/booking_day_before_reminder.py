"""
Booking Day Before Reminder Handler
Sends reminder notifications 1 day before a booking.
"""
from notifications.services.NotificationService import NotificationService
from django.utils import timezone
from datetime import timedelta


def send_day_before_reminders():
    """
    Send reminder notifications for bookings happening tomorrow.
    This function should be called by a scheduled task (e.g., Django-Q, Celery).
    """
    from bookings.models import Booking, BookingStatus
    
    # Get tomorrow's date
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    # Get all confirmed bookings for tomorrow
    bookings = Booking.objects.filter(
        booking_date=tomorrow,
        status__in=[BookingStatus.CONFIRMED, BookingStatus.PENDING]
    ).select_related('business', 'service_offering', 'customer__user')
    
    for booking in bookings:
        notify_booking_day_before(booking)
    
    return len(bookings)


def notify_booking_day_before(booking):
    """
    Send reminder notification 1 day before a booking.
    Sends in-app notifications to customers and staff with accounts, email to all.
    
    Args:
        booking: Booking instance
    """
    business = booking.business
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'booking': booking,
        'customer_name': booking.name,
        'service_name': booking.service_offering.name if booking.service_offering else 'N/A',
        'booking_date': booking.booking_date,
        'booking_time': booking.start_time,
        'location_details': booking.location_details,
        'booking_url': f"{email_context['site_url']}/bookings/{booking.id}/",
    })
    
    # 1. Notify customer (in-app + email if they have an account, email only otherwise)
    if booking.customer and booking.customer.user:
        # Customer has a user account - send both in-app and email notification
        customer_context = email_context.copy()
        customer_context['customer_name'] = booking.customer.get_full_name()
        
        NotificationService.send_notification(
            user=booking.customer.user,
            title=f"Reminder: Appointment Tomorrow",
            message=f"Your appointment with {business.name} is tomorrow at {booking.start_time}",
            notification_type='booking_reminder',
            business=business,
            related_object_id=booking.id,
            related_object_type='booking',
            send_email_flag=True,
            email_subject=f"Reminder: Your appointment tomorrow with {business.name}",
            email_template='email/bookings/booking_day_before_reminder.html',
            email_context=customer_context
        )
    elif booking.email:
        # Customer doesn't have an account - send email only
        customer_context = email_context.copy()
        customer_context['customer_name'] = booking.name
        
        NotificationService.send_email_notification(
            to_email=booking.email,
            subject=f"Reminder: Your appointment tomorrow with {business.name}",
            template_name='email/bookings/booking_day_before_reminder.html',
            context=customer_context
        )
    
    # 2. Notify assigned staff members (in-app + email if they have user account, email only otherwise)
    for staff_assignment in booking.staff_assignments.all():
        staff_member = staff_assignment.staff_member
        staff_context = email_context.copy()
        staff_context['staff_name'] = staff_member.get_full_name()
        
        # Check if staff member has a user account (via StaffProfile)
        if hasattr(staff_member, 'profile') and staff_member.profile and staff_member.profile.user:
            # Staff has user account - send both in-app and email notification
            NotificationService.send_notification(
                user=staff_member.profile.user,
                title=f"Reminder: Appointment Tomorrow",
                message=f"You have an appointment tomorrow at {booking.start_time} with {booking.name}",
                notification_type='booking_reminder',
                business=business,
                related_object_id=booking.id,
                related_object_type='booking',
                send_email_flag=True,
                email_subject=f"Reminder: Appointment tomorrow - {booking.name}",
                email_template='email/bookings/booking_day_before_reminder_staff.html',
                email_context=staff_context
            )
        elif staff_member.email:
            # Staff doesn't have user account - send email only
            NotificationService.send_email_notification(
                to_email=staff_member.email,
                subject=f"Reminder: Appointment tomorrow - {booking.name}",
                template_name='email/bookings/booking_day_before_reminder_staff.html',
                context=staff_context
            )
    
    # Mark reminder as sent
    booking.reminder_sent = True
    booking.save(update_fields=['reminder_sent'])
    
    return True
