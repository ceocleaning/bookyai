"""
Signals for Lead notifications
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from leads.models import Lead
from notifications.services.leads.lead_created import notify_lead_created


@receiver(post_save, sender=Lead)
def lead_created_handler(sender, instance, created, **kwargs):
    """
    Send notification when a new lead is created.
    
    Args:
        sender: The model class (Lead)
        instance: The actual Lead instance
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    if created:
        # Only send notification for newly created leads
        notify_lead_created(instance)
