from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.contrib.auth.models import Group
from django.contrib import messages


class StaffAccessMiddleware:
    """
    Middleware to restrict staff users to ONLY staff portal and core auth URLs.
    Staff users can ONLY access:
    - /staff/ - Staff portal (dashboard, bookings)
    - /login/, /logout/, /password_reset/ - Authentication
    - /static/, /media/ - Static files
    
    Staff users are BLOCKED from:
    - /dashboard/ - Business dashboard
    - /bookings/ - Booking management
    - /leads/ - Lead management
    - /business/ - Business settings
    - Everything else
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # ONLY these URL patterns are allowed for staff users
        self.allowed_url_patterns = [
            'staff',           # /staff/ - Staff portal
            'accounts',        # /accounts/ - Login, logout, profile
            'login',
            'logout',
            'password_reset',
            'password_change',
            'booking_detail',  # Allow viewing booking details
        ]
        
        # ONLY these URL path prefixes are allowed
        self.allowed_path_prefixes = [
            '/staff/',              # Staff portal
            '/accounts/login/',     # Login
            '/accounts/logout/',    # Logout
            '/accounts/password',   # Password reset/change
            '/bookings/booking/',   # Booking detail pages
            '/static/',             # Static files
            '/media/',              # Media files
            '/admin/jsi18n/',       # Django admin JS (if needed)
        ]
    
    def __call__(self, request):
        # Skip middleware for non-authenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Skip middleware for superusers
        if request.user.is_superuser:
            return self.get_response(request)
        
        # Check if user is in staff group
        try:
            is_staff_user = request.user.groups.filter(name='staff').exists()
        except Exception:
            is_staff_user = False
        
        # Also check for staff_profile
        if not is_staff_user and hasattr(request.user, 'staff_profile'):
            is_staff_user = True
        
        # If not a staff user, allow all access (normal business user)
        if not is_staff_user:
            return self.get_response(request)
        
        # ============================================
        # STAFF USER - RESTRICT ACCESS
        # ============================================
        
        current_path = request.path
        
        # Check if path starts with allowed prefixes
        for prefix in self.allowed_path_prefixes:
            if current_path.startswith(prefix):
                return self.get_response(request)
        
        # Resolve the current URL
        try:
            resolved = resolve(current_path)
            url_name = resolved.url_name
            namespace = resolved.namespace
            
            # Check if namespace is in allowed patterns
            if namespace in self.allowed_url_patterns:
                return self.get_response(request)
            
            # Check if URL name contains allowed patterns
            for pattern in self.allowed_url_patterns:
                if url_name and pattern in url_name:
                    return self.get_response(request)
            
        except Exception:
            # If URL resolution fails, block access
            pass
        
        # ============================================
        # BLOCKED - Redirect to staff portal
        # ============================================
        
        messages.warning(
            request,
            'You do not have permission to access this page. Staff users can only access the staff portal.'
        )
        
        # Redirect to staff dashboard
        return redirect('staff:dashboard')
    
    def process_exception(self, request, exception):
        """Handle exceptions during request processing"""
        return None
