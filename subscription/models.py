from django.db import models
from django.utils import timezone
from business.models import Business


class SubscriptionPlan(models.Model):
    """
    Stores metadata about available subscription plans.
    This mirrors plan information from Stripe for display and feature mapping.
    """
    BILLING_PERIOD_CHOICES = (
        ('month', 'Monthly'),
        ('year', 'Yearly'),
    )
    
    stripe_price_id = models.CharField(max_length=255, unique=True, help_text="Stripe Price ID (e.g., price_xxx)")
    name = models.CharField(max_length=100, help_text="Plan name (e.g., Starter, Professional, Enterprise)")
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in USD")
    billing_period = models.CharField(max_length=20, choices=BILLING_PERIOD_CHOICES, default='month')
    features = models.JSONField(default=list, help_text="List of features included in this plan")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - ${self.price}/{self.billing_period}"


class Subscription(models.Model):
    """
    Tracks subscription history for each business.
    Each subscription period (renewal, plan change, etc.) creates a new record.
    Stripe is the single source of truth; this model is updated via webhooks only.
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('trialing', 'Trialing'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('ended', 'Ended'),  # Added for when a subscription period ends naturally
    )
    
    # Changed from OneToOneField to ForeignKey to allow multiple subscriptions per business
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='plan_subscriptions')
    
    # Stripe identifiers
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, help_text="Stripe Customer ID", db_index=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True, help_text="Stripe Subscription ID", db_index=True)
    
    # Subscription state
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='incomplete')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True, help_text="When this subscription period ended (for history tracking)")
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business', 'status', '-created_at']),
            models.Index(fields=['stripe_subscription_id']),
        ]
    
    def __str__(self):
        return f"{self.business.name} - {self.get_status_display()} ({self.created_at.strftime('%Y-%m-%d')})"
    
    @classmethod
    def get_active_subscription(cls, business):
        """
        Get the currently active subscription for a business.
        Returns the most recent subscription with active or trialing status.
        
        Args:
            business: Business model instance
            
        Returns:
            Subscription instance or None
        """
        return cls.objects.filter(
            business=business,
            status__in=['active', 'trialing'],
            ended_at__isnull=True
        ).order_by('-created_at').first()
    
    def is_active(self):
        """
        Returns True if the subscription is active or in trial period and not ended.
        This is the primary method for feature gating.
        """
        return self.status in ['active', 'trialing'] and self.ended_at is None
    
    def is_trial(self):
        """Returns True if subscription is currently in trial period."""
        if self.status == 'trialing' and self.trial_end and self.ended_at is None:
            return timezone.now() < self.trial_end
        return False
    
    def days_until_renewal(self):
        """Returns number of days until next billing period."""
        if self.current_period_end and self.ended_at is None:
            delta = self.current_period_end - timezone.now()
            return max(0, delta.days)
        return None
    
    def end_subscription(self):
        """
        Mark this subscription as ended.
        Called when a new subscription starts or when subscription is cancelled.
        """
        if self.ended_at is None:
            self.ended_at = timezone.now()
            if self.status in ['active', 'trialing']:
                self.status = 'ended'
            self.save()


class WebhookEvent(models.Model):
    """
    Stores processed webhook events to ensure idempotent processing.
    Prevents duplicate processing of the same Stripe event.
    """
    stripe_event_id = models.CharField(max_length=255, unique=True, db_index=True, help_text="Stripe Event ID (evt_xxx)")
    event_type = models.CharField(max_length=100, help_text="Event type (e.g., customer.subscription.updated)")
    payload = models.JSONField(help_text="Full event payload from Stripe")
    processed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Webhook Event"
        verbose_name_plural = "Webhook Events"
        ordering = ['-processed_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.stripe_event_id}"
