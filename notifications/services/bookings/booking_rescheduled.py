"""
Booking Rescheduled Notification Handler
Sends notifications when a booking is rescheduled.
"""
from notifications.services.NotificationService import NotificationService


def notify_booking_rescheduled(booking, old_date=None, old_time=None):
    """
    Send notifications when a booking is rescheduled.
    Notifies business users, customers (in-app + email), and staff (email only).
    
    Args:
        booking: Booking instance that was rescheduled
        old_date: Previous booking date (optional)
        old_time: Previous booking time (optional)
    """
    business = booking.business
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'booking': booking,
        'customer_name': booking.name,
        'service_name': booking.service_offering.name if booking.service_offering else 'N/A',
        'old_date': old_date,
        'old_time': old_time,
        'new_date': booking.booking_date,
        'new_time': booking.start_time,
        'booking_url': f"{email_context['site_url']}/bookings/{booking.id}/",
    })
    
    # 1. Notify business users (in-app + email)
    business_users = NotificationService.get_business_users(business)
    for user in business_users:
        NotificationService.send_notification(
            user=user,
            title=f"Booking Rescheduled: {booking.name}",
            message=f"Booking has been rescheduled to {booking.booking_date} at {booking.start_time}",
            notification_type='booking_rescheduled',
            business=business,
            related_object_id=booking.id,
            related_object_type='booking',
            send_email_flag=True,
            email_subject=f"Booking Rescheduled - {booking.name}",
            email_template='email/bookings/booking_rescheduled_business.html',
            email_context=email_context
        )
    
    # 2. Notify customer (in-app + email if they have an account, email only otherwise)
    if booking.customer and booking.customer.user:
        # Customer has a user account - send both in-app and email notification
        customer_context = email_context.copy()
        customer_context['customer_name'] = booking.customer.get_full_name()
        
        NotificationService.send_notification(
            user=booking.customer.user,
            title=f"Booking Rescheduled - {business.name}",
            message=f"Your booking has been rescheduled to {booking.booking_date} at {booking.start_time}",
            notification_type='booking_rescheduled',
            business=business,
            related_object_id=booking.id,
            related_object_type='booking',
            send_email_flag=True,
            email_subject=f"Booking Rescheduled - {business.name}",
            email_template='email/bookings/booking_rescheduled_customer.html',
            email_context=customer_context
        )
    elif booking.email:
        # Customer doesn't have an account - send email only
        customer_context = email_context.copy()
        customer_context['customer_name'] = booking.name
        
        NotificationService.send_email_notification(
            to_email=booking.email,
            subject=f"Booking Rescheduled - {business.name}",
            template_name='email/bookings/booking_rescheduled_customer.html',
            context=customer_context
        )
    
    # 3. Notify assigned staff members (email only - staff don't have user accounts)
    for staff_assignment in booking.staff_assignments.all():
        staff_member = staff_assignment.staff_member
        if staff_member.email:
            staff_context = email_context.copy()
            staff_context['staff_name'] = staff_member.get_full_name()
            
            NotificationService.send_email_notification(
                to_email=staff_member.email,
                subject=f"Booking Rescheduled - {booking.booking_date}",
                template_name='email/bookings/booking_rescheduled_staff.html',
                context=staff_context
            )
    
    return True
