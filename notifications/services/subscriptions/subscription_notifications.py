"""
Subscription Notification Handlers
Handles all subscription-related notifications.
"""
from notifications.services.NotificationService import NotificationService
from django.utils import timezone


def notify_subscription_created(subscription):
    """
    Send notification when a new subscription is created.
    
    Args:
        subscription: Subscription instance
    """
    business = subscription.business
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'subscription': subscription,
        'plan_name': subscription.plan.name if subscription.plan else 'N/A',
        'plan_price': subscription.plan.price if subscription.plan else 'N/A',
        'billing_period': subscription.plan.billing_period if subscription.plan else 'N/A',
        'trial_end': subscription.trial_end,
        'is_trial': subscription.is_trial(),
    })
    
    # Notify business users
    business_users = NotificationService.get_business_users(business)
    for user in business_users:
        NotificationService.send_notification(
            user=user,
            title="Subscription Activated",
            message=f"Your {subscription.plan.name if subscription.plan else 'subscription'} plan is now active",
            notification_type='subscription_created',
            business=business,
            send_email_flag=True,
            email_subject=f"Welcome to {subscription.plan.name if subscription.plan else 'BookyAI'}!",
            email_template='email/subscriptions/subscription_created.html',
            email_context=email_context
        )
    
    return True


def notify_subscription_trial_ending(subscription, days_remaining=3):
    """
    Send notification when trial is ending soon.
    
    Args:
        subscription: Subscription instance
        days_remaining: Number of days remaining in trial
    """
    business = subscription.business
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'subscription': subscription,
        'plan_name': subscription.plan.name if subscription.plan else 'N/A',
        'trial_end': subscription.trial_end,
        'days_remaining': days_remaining,
    })
    
    # Notify business users
    business_users = NotificationService.get_business_users(business)
    for user in business_users:
        NotificationService.send_notification(
            user=user,
            title="Trial Ending Soon",
            message=f"Your trial ends in {days_remaining} days",
            notification_type='subscription_trial_ending',
            business=business,
            send_email_flag=True,
            email_subject=f"Your trial ends in {days_remaining} days",
            email_template='email/subscriptions/subscription_trial_ending.html',
            email_context=email_context
        )
    
    return True


def notify_subscription_renewed(subscription):
    """
    Send notification when subscription is renewed.
    
    Args:
        subscription: Subscription instance
    """
    business = subscription.business
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'subscription': subscription,
        'plan_name': subscription.plan.name if subscription.plan else 'N/A',
        'plan_price': subscription.plan.price if subscription.plan else 'N/A',
        'next_billing_date': subscription.current_period_end,
    })
    
    # Notify business users
    business_users = NotificationService.get_business_users(business)
    for user in business_users:
        NotificationService.send_notification(
            user=user,
            title="Subscription Renewed",
            message=f"Your subscription has been renewed successfully",
            notification_type='subscription_renewed',
            business=business,
            send_email_flag=True,
            email_subject="Subscription Renewed Successfully",
            email_template='email/subscriptions/subscription_renewed.html',
            email_context=email_context
        )
    
    return True


def notify_subscription_cancelled(subscription):
    """
    Send notification when subscription is cancelled.
    
    Args:
        subscription: Subscription instance
    """
    business = subscription.business
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'subscription': subscription,
        'plan_name': subscription.plan.name if subscription.plan else 'N/A',
        'end_date': subscription.current_period_end,
        'cancel_at_period_end': subscription.cancel_at_period_end,
    })
    
    # Notify business users
    business_users = NotificationService.get_business_users(business)
    for user in business_users:
        NotificationService.send_notification(
            user=user,
            title="Subscription Cancelled",
            message=f"Your subscription has been cancelled",
            notification_type='subscription_cancelled',
            business=business,
            send_email_flag=True,
            email_subject="Subscription Cancellation Confirmation",
            email_template='email/subscriptions/subscription_cancelled.html',
            email_context=email_context
        )
    
    return True


def notify_subscription_payment_failed(subscription):
    """
    Send notification when subscription payment fails.
    
    Args:
        subscription: Subscription instance
    """
    business = subscription.business
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'subscription': subscription,
        'plan_name': subscription.plan.name if subscription.plan else 'N/A',
        'retry_date': subscription.current_period_end,
    })
    
    # Notify business users
    business_users = NotificationService.get_business_users(business)
    for user in business_users:
        NotificationService.send_notification(
            user=user,
            title="Payment Failed",
            message=f"Your subscription payment failed. Please update your payment method.",
            notification_type='subscription_payment_failed',
            business=business,
            send_email_flag=True,
            email_subject="Action Required: Subscription Payment Failed",
            email_template='email/subscriptions/subscription_payment_failed.html',
            email_context=email_context
        )
    
    return True


def send_subscription_renewal_reminders():
    """
    Send renewal reminders for subscriptions expiring soon.
    This function should be called by a scheduled task.
    """
    from subscription.models import Subscription
    from datetime import timedelta
    
    # Get subscriptions expiring in 7 days
    seven_days_from_now = timezone.now() + timedelta(days=7)
    
    subscriptions = Subscription.objects.filter(
        status='active',
        cancel_at_period_end=False,
        current_period_end__date=seven_days_from_now.date()
    ).select_related('business', 'plan')
    
    for subscription in subscriptions:
        notify_subscription_renewal_reminder(subscription)
    
    return len(subscriptions)


def notify_subscription_renewal_reminder(subscription):
    """
    Send renewal reminder notification.
    
    Args:
        subscription: Subscription instance
    """
    business = subscription.business
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'subscription': subscription,
        'plan_name': subscription.plan.name if subscription.plan else 'N/A',
        'plan_price': subscription.plan.price if subscription.plan else 'N/A',
        'renewal_date': subscription.current_period_end,
        'days_until_renewal': subscription.days_until_renewal(),
    })
    
    # Notify business users
    business_users = NotificationService.get_business_users(business)
    for user in business_users:
        NotificationService.send_notification(
            user=user,
            title="Subscription Renewal Reminder",
            message=f"Your subscription will renew in {subscription.days_until_renewal()} days",
            notification_type='subscription_renewal_reminder',
            business=business,
            send_email_flag=True,
            email_subject="Subscription Renewal Reminder",
            email_template='email/subscriptions/subscription_renewal_reminder.html',
            email_context=email_context
        )
    
    return True
