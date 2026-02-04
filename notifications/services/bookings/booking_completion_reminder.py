"""
Booking Completed Notification Handler
Sends notifications when a booking is completed.
"""
from notifications.services.NotificationService import NotificationService


def notify_booking_completed(booking):
    """
    Send notifications when a booking is completed.
    Notifies business users and customers (in-app + email).
    
    Args:
        booking: Booking instance that was completed
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
        'booking_url': f"{email_context['site_url']}/bookings/{booking.id}/",
    })
    
    # 1. Notify business users (in-app + email)
    business_users = NotificationService.get_business_users(business)
    for user in business_users:
        NotificationService.send_notification(
            user=user,
            title=f"Booking Completed: {booking.name}",
            message=f"Booking for {booking.booking_date} has been marked as completed",
            notification_type='booking_completed',
            business=business,
            related_object_id=booking.id,
            related_object_type='booking',
            send_email_flag=True,
            email_subject=f"Booking Completed - {booking.name}",
            email_template='email/bookings/booking_completed_business.html',
            email_context=email_context
        )
    
    # 2. Send thank you notification to customer (in-app + email if they have an account, email only otherwise)
    if booking.customer and booking.customer.user:
        # Customer has a user account - send both in-app and email notification
        customer_context = email_context.copy()
        customer_context['customer_name'] = booking.customer.get_full_name()
        
        NotificationService.send_notification(
            user=booking.customer.user,
            title=f"Thank You - {business.name}",
            message=f"Thank you for choosing {business.name}! We hope you enjoyed your service.",
            notification_type='booking_completed',
            business=business,
            related_object_id=booking.id,
            related_object_type='booking',
            send_email_flag=True,
            email_subject=f"Thank You - {business.name}",
            email_template='email/bookings/booking_completed_customer.html',
            email_context=customer_context
        )
    elif booking.email:
        # Customer doesn't have an account - send email only
        customer_context = email_context.copy()
        customer_context['customer_name'] = booking.name
        
        NotificationService.send_email_notification(
            to_email=booking.email,
            subject=f"Thank You - {business.name}",
            template_name='email/bookings/booking_completed_customer.html',
            context=customer_context
        )
    
    return True
