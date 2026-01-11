"""
Subscription utility functions for feature gating and subscription management.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import Subscription


def get_business_subscription(business):
    """
    Get the active subscription for a business.
    
    Args:
        business: Business model instance
        
    Returns:
        Subscription instance or None if no active subscription exists
    """
    return Subscription.get_active_subscription(business)


def has_active_subscription(business):
    """
    Check if a business has an active subscription.
    
    Args:
        business: Business model instance
        
    Returns:
        bool: True if subscription is active or trialing, False otherwise
    """
    subscription = get_business_subscription(business)
    if subscription:
        return subscription.is_active()
    return False


def get_subscription_features(business):
    """
    Get the list of features for a business's current subscription plan.
    
    Args:
        business: Business model instance
        
    Returns:
        list: List of feature strings, or empty list if no subscription
    """
    subscription = get_business_subscription(business)
    if subscription and subscription.plan:
        return subscription.plan.features
    return []


def subscription_required(view_func):
    """
    Decorator to protect views that require an active subscription.
    Redirects to pricing page if no active subscription exists.
    
    Usage:
        @subscription_required
        def my_protected_view(request):
            # This view requires an active subscription
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this feature.")
            return redirect('accounts:login')
        
        # Check if user has a business
        try:
            business = request.user.business
        except AttributeError:
            messages.error(request, "No business account found. Please complete your registration.")
            return redirect('dashboard:home')
        
        # Check if business has an active subscription
        if not has_active_subscription(business):
            messages.warning(
                request, 
                "This feature requires an active subscription. Please choose a plan to continue."
            )
            return redirect('core:pricing')
        
        # All checks passed, proceed to view
        return view_func(request, *args, **kwargs)
    
    return wrapper


def get_subscription_status_display(business):
    """
    Get a human-readable subscription status for display.
    
    Args:
        business: Business model instance
        
    Returns:
        dict: Dictionary with 'status', 'label', and 'css_class' keys
    """
    subscription = get_business_subscription(business)
    
    if not subscription:
        return {
            'status': 'none',
            'label': 'No Subscription',
            'css_class': 'badge-secondary'
        }
    
    status_map = {
        'active': {'label': 'Active', 'css_class': 'badge-success'},
        'trialing': {'label': 'Trial', 'css_class': 'badge-info'},
        'past_due': {'label': 'Past Due', 'css_class': 'badge-warning'},
        'canceled': {'label': 'Canceled', 'css_class': 'badge-danger'},
        'unpaid': {'label': 'Unpaid', 'css_class': 'badge-danger'},
        'incomplete': {'label': 'Incomplete', 'css_class': 'badge-secondary'},
        'incomplete_expired': {'label': 'Expired', 'css_class': 'badge-secondary'},
    }
    
    status_info = status_map.get(subscription.status, {
        'label': subscription.get_status_display(),
        'css_class': 'badge-secondary'
    })
    
    return {
        'status': subscription.status,
        **status_info
    }
