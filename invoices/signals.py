"""
Signals for Invoice and Payment notifications
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from invoices.models import Invoice, Payment, InvoiceStatus
from bookings.models import BookingStatus
from notifications.services.invoices.payment_completed import notify_invoice_paid

import logging

logger = logging.getLogger(__name__)

# Store previous invoice state
_invoice_previous_state = {}


@receiver(post_save, sender=Payment)
def payment_created_handler(sender, instance, created, **kwargs):
    """
    Send notification when a payment is received.
    
    Args:
        sender: The model class (Payment)
        instance: The actual Payment instance
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    if created:
        invoice = instance.invoice
        notify_invoice_paid(invoice, payment=instance)


@receiver(pre_save, sender=Invoice)
def invoice_pre_save_handler(sender, instance, **kwargs):
    """
    Store previous invoice state before save for comparison.
    
    Args:
        sender: The model class (Invoice)
        instance: The actual Invoice instance being saved
        **kwargs: Additional keyword arguments
    """
    if instance.pk:
        try:
            old_invoice = Invoice.objects.get(pk=instance.pk)
            _invoice_previous_state[instance.pk] = {
                'status': old_invoice.status,
            }
        except Invoice.DoesNotExist:
            pass


@receiver(post_save, sender=Invoice)
def invoice_post_save_handler(sender, instance, created, **kwargs):
    """
    Handle invoice status changes:
    - Send notification when invoice is marked as paid.
    - Confirm the linked booking when invoice is paid or authorized.
    
    Args:
        sender: The model class (Invoice)
        instance: The actual Invoice instance
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    
    if not created:
        previous_state = _invoice_previous_state.get(instance.pk, {})
        old_status = previous_state.get('status')
        
        # Invoice marked as paid
        if old_status and old_status != InvoiceStatus.PAID and instance.status == InvoiceStatus.PAID:
            # Get the most recent payment for this invoice
            payment = instance.payments.order_by('-created_at').first()
            notify_invoice_paid(instance, payment=payment)
        
        # Confirm booking when invoice is paid or authorized
        if old_status and old_status not in (InvoiceStatus.PAID, InvoiceStatus.AUTHORIZED):
            if instance.status in (InvoiceStatus.PAID, InvoiceStatus.AUTHORIZED):
                booking = instance.booking
                if booking and booking.status != BookingStatus.CONFIRMED:
                    booking.status = BookingStatus.CONFIRMED
                    booking.save(update_fields=['status', 'updated_at'])
                    logger.info(
                        f"Booking {booking.pk} confirmed after invoice {instance.invoice_number} "
                        f"status changed to {instance.status}."
                    )
        
        # Clean up previous state to avoid memory leaks
        if instance.pk in _invoice_previous_state:
            del _invoice_previous_state[instance.pk]
