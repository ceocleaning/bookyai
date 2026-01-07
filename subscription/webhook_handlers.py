"""
Webhook event handlers for Stripe subscription lifecycle events.
Each handler processes a specific Stripe event type and updates local database state.
"""
import logging
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone
from .models import Subscription, SubscriptionPlan, WebhookEvent
from business.models import Business

logger = logging.getLogger(__name__)


def handle_checkout_session_completed(event):
    """
    Handle checkout.session.completed event.
    Creates or updates the Stripe customer ID for the business.
    """
    session = event['data']['object']
    customer_email = session.get('customer_email')
    stripe_customer_id = session.get('customer')
    stripe_subscription_id = session.get('subscription')
    
    logger.info(f"Checkout completed for customer: {customer_email}")
    
    try:
        # Find business by user email
        from django.contrib.auth.models import User
        user = User.objects.get(email=customer_email)
        business = user.business
        
        # Get or create subscription record
        subscription, created = Subscription.objects.get_or_create(
            business=business,
            defaults={
                'stripe_customer_id': stripe_customer_id,
                'stripe_subscription_id': stripe_subscription_id,
                'status': 'incomplete'
            }
        )
        
        # Update if already exists
        if not created:
            subscription.stripe_customer_id = stripe_customer_id
            if stripe_subscription_id:
                subscription.stripe_subscription_id = stripe_subscription_id
            subscription.save()
        
        logger.info(f"Subscription record {'created' if created else 'updated'} for business: {business.name}")
        
    except User.DoesNotExist:
        logger.error(f"User not found for email: {customer_email}")
    except Business.DoesNotExist:
        logger.error(f"Business not found for user email: {customer_email}")
    except Exception as e:
        logger.error(f"Error handling checkout.session.completed: {str(e)}")


def handle_subscription_created(event):
    """
    Handle customer.subscription.created event.
    Creates or updates the local subscription record.
    """
    subscription_data = event['data']['object']
    stripe_subscription_id = subscription_data['id']
    stripe_customer_id = subscription_data['customer']
    status = subscription_data['status']
    
    logger.info(f"Subscription created: {stripe_subscription_id}")
    
    try:
        # Find subscription by stripe_customer_id or stripe_subscription_id
        subscription = Subscription.objects.filter(
            stripe_customer_id=stripe_customer_id
        ).first() or Subscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id
        ).first()
        
        if not subscription:
            logger.warning(f"Subscription record not found for customer: {stripe_customer_id}")
            return
        
        # Update subscription details
        _update_subscription_from_stripe(subscription, subscription_data)
        
        logger.info(f"Subscription updated for business: {subscription.business.name}")
        
    except Exception as e:
        logger.error(f"Error handling customer.subscription.created: {str(e)}")


def handle_subscription_updated(event):
    """
    Handle customer.subscription.updated event.
    Updates the local subscription status, plan, and billing period.
    """
    subscription_data = event['data']['object']
    stripe_subscription_id = subscription_data['id']
    
    logger.info(f"Subscription updated: {stripe_subscription_id}")
    
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
        _update_subscription_from_stripe(subscription, subscription_data)
        
        logger.info(f"Subscription updated for business: {subscription.business.name}, status: {subscription.status}")
        
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found: {stripe_subscription_id}")
    except Exception as e:
        logger.error(f"Error handling customer.subscription.updated: {str(e)}")


def handle_subscription_deleted(event):
    """
    Handle customer.subscription.deleted event.
    Marks the subscription as canceled.
    """
    subscription_data = event['data']['object']
    stripe_subscription_id = subscription_data['id']
    
    logger.info(f"Subscription deleted: {stripe_subscription_id}")
    
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
        subscription.status = 'canceled'
        subscription.canceled_at = timezone.now()
        subscription.save()
        
        logger.info(f"Subscription canceled for business: {subscription.business.name}")
        
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found: {stripe_subscription_id}")
    except Exception as e:
        logger.error(f"Error handling customer.subscription.deleted: {str(e)}")


def handle_invoice_payment_failed(event):
    """
    Handle invoice.payment_failed event.
    Updates subscription status to past_due.
    """
    invoice_data = event['data']['object']
    stripe_subscription_id = invoice_data.get('subscription')
    
    if not stripe_subscription_id:
        logger.warning("Invoice payment failed but no subscription ID found")
        return
    
    logger.info(f"Payment failed for subscription: {stripe_subscription_id}")
    
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
        subscription.status = 'past_due'
        subscription.save()
        
        logger.warning(f"Subscription marked as past_due for business: {subscription.business.name}")
        
        # TODO: Send notification to business owner about payment failure
        
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found: {stripe_subscription_id}")
    except Exception as e:
        logger.error(f"Error handling invoice.payment_failed: {str(e)}")


def handle_invoice_payment_succeeded(event):
    """
    Handle invoice.payment_succeeded event.
    Ensures subscription is marked as active.
    """
    invoice_data = event['data']['object']
    stripe_subscription_id = invoice_data.get('subscription')
    
    if not stripe_subscription_id:
        logger.info("Invoice payment succeeded but no subscription ID (likely one-time payment)")
        return
    
    logger.info(f"Payment succeeded for subscription: {stripe_subscription_id}")
    
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
        
        # Only update if currently past_due or unpaid
        if subscription.status in ['past_due', 'unpaid']:
            subscription.status = 'active'
            subscription.save()
            logger.info(f"Subscription reactivated for business: {subscription.business.name}")
        
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found: {stripe_subscription_id}")
    except Exception as e:
        logger.error(f"Error handling invoice.payment_succeeded: {str(e)}")


def _update_subscription_from_stripe(subscription, stripe_data):
    """
    Helper function to update local subscription from Stripe data.
    Extracts relevant fields and updates the subscription model.
    """
    # Update basic fields
    subscription.status = stripe_data['status']
    subscription.cancel_at_period_end = stripe_data.get('cancel_at_period_end', False)
    
    # Update billing period
    if stripe_data.get('current_period_start'):
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_data['current_period_start'], tz=dt_timezone.utc
        )
    
    if stripe_data.get('current_period_end'):
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_data['current_period_end'], tz=dt_timezone.utc
        )
    
    # Update trial period
    if stripe_data.get('trial_start'):
        subscription.trial_start = datetime.fromtimestamp(
            stripe_data['trial_start'], tz=dt_timezone.utc
        )
    
    if stripe_data.get('trial_end'):
        subscription.trial_end = datetime.fromtimestamp(
            stripe_data['trial_end'], tz=dt_timezone.utc
        )
    
    # Update canceled_at
    if stripe_data.get('canceled_at'):
        subscription.canceled_at = datetime.fromtimestamp(
            stripe_data['canceled_at'], tz=dt_timezone.utc
        )
    
    # Try to match plan by Stripe price ID
    items = stripe_data.get('items', {}).get('data', [])
    if items:
        stripe_price_id = items[0]['price']['id']
        try:
            plan = SubscriptionPlan.objects.get(stripe_price_id=stripe_price_id)
            subscription.plan = plan
        except SubscriptionPlan.DoesNotExist:
            logger.warning(f"SubscriptionPlan not found for Stripe price ID: {stripe_price_id}")
    
    subscription.save()
