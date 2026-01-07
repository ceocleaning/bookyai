from django.contrib import admin
from .models import SubscriptionPlan, Subscription, WebhookEvent


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'billing_period', 'is_active', 'stripe_price_id')
    list_filter = ('billing_period', 'is_active')
    search_fields = ('name', 'stripe_price_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'description', 'stripe_price_id')
        }),
        ('Pricing', {
            'fields': ('price', 'billing_period')
        }),
        ('Features', {
            'fields': ('features', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('business', 'plan', 'status', 'current_period_end', 'cancel_at_period_end', 'is_active')
    list_filter = ('status', 'cancel_at_period_end', 'plan')
    search_fields = ('business__name', 'stripe_customer_id', 'stripe_subscription_id')
    readonly_fields = ('created_at', 'updated_at', 'stripe_customer_id', 'stripe_subscription_id')
    raw_id_fields = ('business',)
    
    fieldsets = (
        ('Business & Plan', {
            'fields': ('business', 'plan')
        }),
        ('Stripe Identifiers', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id')
        }),
        ('Subscription Status', {
            'fields': ('status', 'cancel_at_period_end', 'canceled_at')
        }),
        ('Billing Period', {
            'fields': ('current_period_start', 'current_period_end')
        }),
        ('Trial Period', {
            'fields': ('trial_start', 'trial_end'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active(self, obj):
        return obj.is_active()
    is_active.boolean = True
    is_active.short_description = 'Active'


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('stripe_event_id', 'event_type', 'processed_at')
    list_filter = ('event_type', 'processed_at')
    search_fields = ('stripe_event_id', 'event_type')
    readonly_fields = ('stripe_event_id', 'event_type', 'payload', 'processed_at')
    
    def has_add_permission(self, request):
        # Webhook events should only be created by the system
        return False
    
    def has_change_permission(self, request, obj=None):
        # Webhook events should be read-only
        return False
