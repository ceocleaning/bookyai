"""
Pending Invoice Reminder Handler
Sends reminder notifications for unpaid invoices.
"""
from notifications.services.NotificationService import NotificationService
from django.utils import timezone
from datetime import timedelta


def send_pending_invoice_reminders():
    """
    Send reminder notifications for pending/overdue invoices.
    This function should be called by a scheduled task.
    """
    from invoices.models import Invoice, InvoiceStatus
    
    # Get all pending and overdue invoices
    invoices = Invoice.objects.filter(
        status__in=[InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]
    ).select_related('booking', 'booking__business')
    
    for invoice in invoices:
        # Check if invoice is overdue
        if invoice.due_date < timezone.now().date():
            notify_invoice_overdue(invoice)
        else:
            # Send reminder 3 days before due date
            days_until_due = (invoice.due_date - timezone.now().date()).days
            if days_until_due == 3:
                notify_invoice_pending(invoice)
    
    return len(invoices)


def notify_invoice_pending(invoice):
    """
    Send reminder notification for pending invoice.
    
    Args:
        invoice: Invoice instance
    """
    booking = invoice.booking
    business = booking.business
    
    if not booking.email:
        return False
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'invoice': invoice,
        'booking': booking,
        'customer_name': booking.name,
        'invoice_number': invoice.invoice_number,
        'due_date': invoice.due_date,
        'invoice_url': invoice.get_preview_url(),
        'total_amount': booking.get_total(),
    })
    
    # Send reminder to customer
    NotificationService.send_email_notification(
        to_email=booking.email,
        subject=f"Payment Reminder - Invoice #{invoice.invoice_number}",
        template_name='email/invoices/invoice_pending_reminder.html',
        context=email_context
    )
    
    return True


def notify_invoice_overdue(invoice):
    """
    Send overdue notification for unpaid invoice.
    
    Args:
        invoice: Invoice instance
    """
    booking = invoice.booking
    business = booking.business
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'invoice': invoice,
        'booking': booking,
        'customer_name': booking.name,
        'invoice_number': invoice.invoice_number,
        'due_date': invoice.due_date,
        'invoice_url': invoice.get_preview_url(),
        'total_amount': booking.get_total(),
        'days_overdue': (timezone.now().date() - invoice.due_date).days,
    })
    
    # 1. Notify business users
    business_users = NotificationService.get_business_users(business)
    for user in business_users:
        NotificationService.send_notification(
            user=user,
            title=f"Overdue Invoice: #{invoice.invoice_number}",
            message=f"Invoice #{invoice.invoice_number} for {booking.name} is overdue",
            notification_type='invoice_overdue',
            business=business,
            related_object_id=invoice.id,
            related_object_type='invoice',
            send_email_flag=True,
            email_subject=f"Overdue Invoice Alert - #{invoice.invoice_number}",
            email_template='email/invoices/invoice_overdue_business.html',
            email_context=email_context
        )
    
    # 2. Send overdue notice to customer
    if booking.email:
        customer_context = email_context.copy()
        customer_context['customer_name'] = booking.name
        
        NotificationService.send_email_notification(
            to_email=booking.email,
            subject=f"Overdue Payment Notice - Invoice #{invoice.invoice_number}",
            template_name='email/invoices/invoice_overdue_customer.html',
            context=customer_context
        )
    
    return True
