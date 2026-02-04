"""
Invoice Payment Completed Notification Handler
Sends notifications when an invoice payment is completed.
"""
from notifications.services.NotificationService import NotificationService


def notify_invoice_paid(invoice, payment=None):
    """
    Send notifications when an invoice is paid.
    
    Args:
        invoice: Invoice instance that was paid
        payment: Payment instance (optional)
    """
    booking = invoice.booking
    business = booking.business
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'invoice': invoice,
        'booking': booking,
        'payment': payment,
        'customer_name': booking.name,
        'invoice_number': invoice.invoice_number,
        'invoice_url': f"{email_context['site_url']}/invoices/{invoice.id}/",
        'amount_paid': payment.amount if payment else None,
    })
    
    # 1. Notify business users
    business_users = NotificationService.get_business_users(business)
    for user in business_users:
        NotificationService.send_notification(
            user=user,
            title=f"Payment Received: Invoice #{invoice.invoice_number}",
            message=f"Payment received for invoice #{invoice.invoice_number} - {booking.name}",
            notification_type='invoice_paid',
            business=business,
            related_object_id=invoice.id,
            related_object_type='invoice',
            send_email_flag=True,
            email_subject=f"Payment Received - Invoice #{invoice.invoice_number}",
            email_template='email/invoices/invoice_paid_business.html',
            email_context=email_context
        )
    
    # 2. Send payment confirmation to customer
    if booking.email:
        customer_context = email_context.copy()
        customer_context['customer_name'] = booking.name
        
        NotificationService.send_email_notification(
            to_email=booking.email,
            subject=f"Payment Confirmation - Invoice #{invoice.invoice_number}",
            template_name='email/invoices/invoice_paid_customer.html',
            context=customer_context
        )
    
    return True
