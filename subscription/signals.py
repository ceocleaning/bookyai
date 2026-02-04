"""
Signals for Subscription notifications
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from subscription.models import Subscription
from notifications.services.subscriptions.subscription_notifications import (
    notify_subscription_created,
    notify_subscription_renewed,
    notify_subscription_cancelled,
    notify_subscription_payment_failed
)


# Store previous subscription state
_subscription_previous_state = {}


@receiver(pre_save, sender=Subscription)
def subscription_pre_save_handler(sender, instance, **kwargs):
    """
    Store previous subscription state before save for comparison.
    
    Args:
        sender: The model class (Subscription)
        instance: The actual Subscription instance being saved
        **kwargs: Additional keyword arguments
    """
    if instance.pk:
        try:
            old_subscription = Subscription.objects.get(pk=instance.pk)
            _subscription_previous_state[instance.pk] = {
                'status': old_subscription.status,
            }
        except Subscription.DoesNotExist:
            pass


@receiver(post_save, sender=Subscription)
def subscription_post_save_handler(sender, instance, created, **kwargs):
    """
    Handle subscription notifications based on creation or status changes.
    
    This signal handler:
    - Sends creation notification for new subscriptions
    - Detects renewals (status changes to active)
    - Detects cancellations
    - Detects payment failures
    
    Args:
        sender: The model class (Subscription)
        instance: The actual Subscription instance
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    
    if created:
        # New subscription created
        notify_subscription_created(instance)
    
    else:
        # Subscription updated - check for status changes
        previous_state = _subscription_previous_state.get(instance.pk, {})
        old_status = previous_state.get('status')
        
        if old_status:
            # Subscription renewed (status changed to active from another state)
            # This typically happens after trial ends or after successful payment
            if old_status != 'active' and instance.status == 'active':
                notify_subscription_renewed(instance)
            
            # Subscription cancelled
            if old_status != 'canceled' and instance.status == 'canceled':
                notify_subscription_cancelled(instance)
            
            # Payment failed (past_due or unpaid status)
            if old_status not in ['past_due', 'unpaid'] and instance.status in ['past_due', 'unpaid']:
                notify_subscription_payment_failed(instance)
        
        # Clean up previous state to avoid memory leaks
        if instance.pk in _subscription_previous_state:
            del _subscription_previous_state[instance.pk]
