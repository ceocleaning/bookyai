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
        
        # End any existing active subscriptions for this business
        active_subscriptions = Subscription.objects.filter(
            business=business,
            status__in=['active', 'trialing'],
            ended_at__isnull=True
        )
        for sub in active_subscriptions:
            sub.end_subscription()
            logger.info(f"Ended previous subscription for business: {business.name}")
        
        # Check if we already have a subscription with this stripe_subscription_id
        if stripe_subscription_id:
            existing_sub = Subscription.objects.filter(
                stripe_subscription_id=stripe_subscription_id
            ).first()
            
            if existing_sub:
                # Update existing subscription
                existing_sub.stripe_customer_id = stripe_customer_id
                existing_sub.save()
                logger.info(f"Updated existing subscription for business: {business.name}")
                return
        
        # Create new subscription record
        subscription = Subscription.objects.create(
            business=business,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            status='incomplete'
        )
        
        logger.info(f"Created new subscription record for business: {business.name}")
        
    except User.DoesNotExist:
        logger.error(f"User not found for email: {customer_email}")
    except Business.DoesNotExist:
        logger.error(f"Business not found for user email: {customer_email}")
    except Exception as e:
        logger.error(f"Error handling checkout.session.completed: {str(e)}")


def handle_subscription_created(event):
    """
    Handle customer.subscription.created event.
    Creates a new subscription record for this subscription period.
    Ends any other active subscriptions for the same business.
    """
    subscription_data = event['data']['object']
    stripe_subscription_id = subscription_data['id']
    stripe_customer_id = subscription_data['customer']
    status = subscription_data['status']
    
    logger.info(f"Subscription created: {stripe_subscription_id}")
    
    try:
        # Check if we already have this subscription
        existing_sub = Subscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id
        ).first()
        
        if existing_sub:
            # Update existing subscription
            _update_subscription_from_stripe(existing_sub, subscription_data)
            logger.info(f"Updated existing subscription for business: {existing_sub.business.name}")
            return
        
        # Find the business by stripe_customer_id
        business_subscription = Subscription.objects.filter(
            stripe_customer_id=stripe_customer_id
        ).first()
        
        if not business_subscription:
            logger.warning(f"No business found for customer: {stripe_customer_id}")
            return
        
        business = business_subscription.business
        
        # End any other active subscriptions for this business
        # This handles upgrades/downgrades where a new subscription is created
        other_active_subs = Subscription.objects.filter(
            business=business,
            status__in=['active', 'trialing'],
            ended_at__isnull=True
        ).exclude(stripe_subscription_id=stripe_subscription_id)
        
        for old_sub in other_active_subs:
            old_sub.end_subscription()
            logger.info(f"Ended previous subscription {old_sub.stripe_subscription_id} for business: {business.name}")
        
        # Create new subscription record
        subscription = Subscription.objects.create(
            business=business,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            status='incomplete'
        )
        
        # Update with full details
        _update_subscription_from_stripe(subscription, subscription_data)
        
        logger.info(f"New subscription created for business: {business.name}")
        
    except Exception as e:
        logger.error(f"Error handling customer.subscription.created: {str(e)}")


def handle_subscription_updated(event):
    """
    Handle customer.subscription.updated event.
    Updates the local subscription status, plan, and billing period.
    If this is a renewal (new billing period), creates a new subscription record.
    """
    subscription_data = event['data']['object']
    stripe_subscription_id = subscription_data['id']
    
    logger.info(f"Subscription updated: {stripe_subscription_id}")
    
    try:
        # Get the current subscription with this stripe_subscription_id
        current_subscription = Subscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id,
            ended_at__isnull=True
        ).order_by('-created_at').first()
        
        if not current_subscription:
            logger.error(f"Active subscription not found: {stripe_subscription_id}")
            return
        
        # Check if this is a renewal (billing period changed)
        new_period_start = None
        if subscription_data.get('current_period_start'):
            from datetime import datetime, timezone as dt_timezone
            new_period_start = datetime.fromtimestamp(
                subscription_data['current_period_start'], tz=dt_timezone.utc
            )
        
        is_renewal = False
        if new_period_start and current_subscription.current_period_start:
            # If the period start has changed, this is a renewal
            if new_period_start > current_subscription.current_period_start:
                is_renewal = True
                logger.info(f"Detected renewal for subscription: {stripe_subscription_id}")
        
        if is_renewal:
            # End the current subscription period
            current_subscription.end_subscription()
            logger.info(f"Ended previous subscription period for business: {current_subscription.business.name}")
            
            # Create a new subscription record for the new period
            new_subscription = Subscription.objects.create(
                business=current_subscription.business,
                stripe_customer_id=current_subscription.stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
                plan=current_subscription.plan,
                status='incomplete'
            )
            
            # Update the new subscription with Stripe data
            _update_subscription_from_stripe(new_subscription, subscription_data)
            logger.info(f"Created new subscription period for business: {new_subscription.business.name}")
        else:
            # Just update the existing subscription
            _update_subscription_from_stripe(current_subscription, subscription_data)
            logger.info(f"Updated subscription for business: {current_subscription.business.name}, status: {current_subscription.status}")
        
    except Exception as e:
        logger.error(f"Error handling customer.subscription.updated: {str(e)}")


def handle_subscription_deleted(event):
    """
    Handle customer.subscription.deleted event.
    Marks the subscription as canceled and ended.
    """
    subscription_data = event['data']['object']
    stripe_subscription_id = subscription_data['id']
    
    logger.info(f"Subscription deleted: {stripe_subscription_id}")
    
    try:
        # Find the active subscription with this ID
        subscription = Subscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id,
            ended_at__isnull=True
        ).order_by('-created_at').first()
        
        if not subscription:
            logger.warning(f"Active subscription not found: {stripe_subscription_id}")
            return
        
        subscription.status = 'canceled'
        subscription.canceled_at = timezone.now()
        subscription.end_subscription()
        
        logger.info(f"Subscription canceled and ended for business: {subscription.business.name}")
        
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
        subscription = Subscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id,
            ended_at__isnull=True
        ).order_by('-created_at').first()
        
        if not subscription:
            logger.error(f"Active subscription not found: {stripe_subscription_id}")
            return
        
        subscription.status = 'past_due'
        subscription.save()
        
        logger.warning(f"Subscription marked as past_due for business: {subscription.business.name}")
        
        # TODO: Send notification to business owner about payment failure
        
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
        subscription = Subscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id,
            ended_at__isnull=True
        ).order_by('-created_at').first()
        
        if not subscription:
            logger.error(f"Active subscription not found: {stripe_subscription_id}")
            return
        
        # Only update if currently past_due or unpaid
        if subscription.status in ['past_due', 'unpaid']:
            subscription.status = 'active'
            subscription.save()
            logger.info(f"Subscription reactivated for business: {subscription.business.name}")
        
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
