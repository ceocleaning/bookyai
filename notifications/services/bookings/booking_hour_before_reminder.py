"""
Booking Review Request Handler
Sends review request after a booking is completed.
"""
from notifications.services.NotificationService import NotificationService


def notify_request_review(booking):
    """
    Send review request notification after a booking is completed.
    This should be called after a booking is marked as completed.
    Sends in-app notification to customers with accounts, email to all.
    
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
        'review_url': f"{email_context['site_url']}/review/{booking.id}/",
        'business_name': business.name,
    })
    
    # Send review request (in-app + email if they have an account, email only otherwise)
    if booking.customer and booking.customer.user:
        # Customer has a user account - send both in-app and email notification
        customer_context = email_context.copy()
        customer_context['customer_name'] = booking.customer.get_full_name()
        
        NotificationService.send_notification(
            user=booking.customer.user,
            title=f"How was your experience with {business.name}?",
            message=f"We'd love to hear about your experience! Please take a moment to leave a review.",
            notification_type='review_request',
            business=business,
            related_object_id=booking.id,
            related_object_type='booking',
            send_email_flag=True,
            email_subject=f"How was your experience with {business.name}?",
            email_template='email/bookings/booking_review_request.html',
            email_context=customer_context
        )
    elif booking.email:
        # Customer doesn't have an account - send email only
        customer_context = email_context.copy()
        customer_context['customer_name'] = booking.name
        
        NotificationService.send_email_notification(
            to_email=booking.email,
            subject=f"How was your experience with {business.name}?",
            template_name='email/bookings/booking_review_request.html',
            context=customer_context
        )
    
    return True
