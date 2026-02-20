from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.contrib import messages
from django.http import JsonResponse


class SubscriptionRequiredMiddleware:
    """
    Middleware to restrict access to specific URLs for users without active subscriptions.
    Staff and superusers are exempt from this restriction.
    """
    
    # URL patterns that require an active subscription
    RESTRICTED_URL_PATTERNS = [
        'admin_dashboard',  # admin-dashboard/
        'ai_agent',         # ai-agent/
        # 'bookings',         # bookings/
        'leads',            # leads/
        'retell_agent',     # voice-agent/
        'business',         # business/
        'integration',      # integration/
        # 'staff',          # staff/ - REMOVED: Staff users should have access
        'ai_website',       # ai-website/
    ]
    
    # URL patterns that should always be accessible (whitelist)
    EXEMPT_URL_PATTERNS = [
        'admin',            # Django admin
        'subscription',     # Subscription management pages
        'login',
        'logout',
        'register',
        'password_reset',
        'bookings',
        'staff',            # Staff portal - always accessible for staff users
    ]
    
    # Specific URL names that should always be accessible
    EXEMPT_URL_NAMES = [
        'api_industries',           # Business registration - load industries
        'api_register_business',    # Business registration - submit form
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process the request before the view
        if not self._should_check_subscription(request):
            # Skip subscription check for exempt URLs or users
            return self.get_response(request)
        
        # Check if user has an active subscription
        if not self._has_active_subscription(request.user):
            # User doesn't have an active subscription
            return self._handle_no_subscription(request)
        
        # User has active subscription, proceed normally
        response = self.get_response(request)
        return response
    
    def _should_check_subscription(self, request):
        """
        Determine if subscription check should be performed for this request.
        Returns False if the request should be exempt from subscription checks.
        """
        # Skip check if user is not authenticated
        if not request.user.is_authenticated:
            return False
        
        # Skip check for Django staff and superusers
        if request.user.is_staff or request.user.is_superuser:
            return False
        
        # Skip check for staff group users (cleaners/staff members)
        if request.user.groups.filter(name='staff').exists():
            return False
        
        # Skip check for users with staff_profile (alternative check)
        if hasattr(request.user, 'staff_profile') and request.user.staff_profile:
            return False
        
        # Get the URL pattern name
        try:
            resolved = resolve(request.path)
            url_name = resolved.url_name
            app_name = resolved.app_name
        except:
            # If URL cannot be resolved, don't check subscription
            return False
        
        # Check if URL is in exempt patterns
        for exempt_pattern in self.EXEMPT_URL_PATTERNS:
            if app_name and app_name.startswith(exempt_pattern):
                return False
            if url_name and exempt_pattern in url_name:
                return False
            if request.path.startswith(f'/{exempt_pattern}/'):
                return False
        
        # Check if URL name is in the specific exempt URL names
        if url_name and url_name in self.EXEMPT_URL_NAMES:
            return False
        
        # Check if URL is in restricted patterns
        for restricted_pattern in self.RESTRICTED_URL_PATTERNS:
            if app_name and app_name == restricted_pattern:
                return True
            if request.path.startswith(f'/{restricted_pattern}/'):
                return True
        
        # Default: don't check subscription
        return False
    
    def _has_active_subscription(self, user):
        """
        Check if the user has an active subscription.
        Returns True if user has an active or trialing subscription.
        """
        try:
            # Get the business associated with the user
            if not hasattr(user, 'business'):
                return False
            
            business = user.business
            
            # Import here to avoid circular imports
            from .models import Subscription
            
            # Get the active subscription for this business
            subscription = Subscription.get_active_subscription(business)
            
            if not subscription:
                return False
            
            # Use the is_active method from the Subscription model
            return subscription.is_active()
        
        except Exception as e:
            # If any error occurs, deny access for safety
            print(f"Error checking subscription: {e}")
            return False
    
    def _handle_no_subscription(self, request):
        """
        Handle requests from users without active subscriptions.
        Returns appropriate response based on request type.
        """
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Active subscription required',
                'message': 'You need an active subscription to access this feature.',
                'redirect_url': reverse('pricing')
            }, status=403)
        
        # For regular requests, redirect to subscription page with message
        messages.warning(
            request,
            'You need an active subscription to access this feature. Please subscribe to continue.'
        )
        
        # Try to get the pricing page URL
        try:
            subscription_url = reverse('pricing')
        except:
            # Fallback to billing portal if pricing doesn't exist
            try:
                subscription_url = reverse('subscription:billing_portal')
            except:
                # Last resort fallback
                subscription_url = '/'
        
        return redirect(subscription_url)
