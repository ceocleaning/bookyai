from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q, Count
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from decimal import Decimal

from .models import Customer, CustomerBusinessLink
from .forms import CustomerRegistrationForm, CustomerLoginForm, CustomerProfileForm, NotificationPreferencesForm
from .utils import customer_required, get_active_business, set_active_business
from bookings.models import Booking, BookingStatus, BookingEventType
from invoices.models import Invoice, InvoiceStatus, Payment
from business.utils import get_user_business
import json


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

def customer_register(request):
    """Customer self-registration"""
    if request.user.is_authenticated:
        return redirect('customer:dashboard')
    
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            # Create user
            user = form.save()
            
            # Add to customer group
            customer_group, _ = Group.objects.get_or_create(name='customer')
            user.groups.add(customer_group)
            
            # Create customer profile
            Customer.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number']
            )
            
            # Log in user
            login(request, user)
            
            messages.success(request, 'Welcome! Your account has been created successfully.')
            return redirect('customer:dashboard')
    else:
        form = CustomerRegistrationForm()
    
    return render(request, 'customer/register.html', {'form': form})


def customer_login(request):
    """Customer login"""
    if request.user.is_authenticated:
        return redirect('customer:dashboard')
    
    if request.method == 'POST':
        form = CustomerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Check if user is a customer
            if not hasattr(user, 'customer_profile'):
                messages.error(request, 'Invalid credentials. Please use the business login.')
                return redirect('customer:login')
            
            login(request, user)
            
            # Update last login
            customer = user.customer_profile
            customer.last_login = timezone.now()
            customer.save(update_fields=['last_login'])
            
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            # Redirect to next or dashboard
            next_url = request.GET.get('next', 'customer:dashboard')
            return redirect(next_url)
    else:
        form = CustomerLoginForm()
    
    return render(request, 'customer/login.html', {'form': form})


@login_required
def customer_logout(request):
    """Customer logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('customer:login')


def password_reset_request(request):
    """Password reset request - to be implemented"""
    messages.info(request, 'Password reset functionality coming soon.')
    return redirect('customer:login')


def password_reset_confirm(request, uidb64, token):
    """Password reset confirmation - to be implemented"""
    messages.info(request, 'Password reset functionality coming soon.')
    return redirect('customer:login')


def set_password(request, uidb64, token):
    """Set password for new customers"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if password1 and password1 == password2:
                user.set_password(password1)
                user.save()
                
                messages.success(request, 'Your password has been set successfully. You can now log in.')
                return redirect('customer:login')
            else:
                messages.error(request, 'Passwords do not match.')
        
        return render(request, 'customer/set_password.html', {'validlink': True})
    else:
        messages.error(request, 'Invalid or expired password reset link.')
        return render(request, 'customer/set_password.html', {'validlink': False})


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
@customer_required
def customer_dashboard(request):
    """Customer dashboard with overview"""
    customer = request.user.customer_profile
    
    # Get active business
    business = get_active_business(request, customer)
    
    if not business:
        return render(request, 'customer/no_businesses.html', {'customer': customer})
    
    # Upcoming bookings
    upcoming_bookings = Booking.objects.filter(
        customer=customer,
        business=business,
        booking_date__gte=timezone.now().date(),
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
    ).select_related('service_offering').order_by('booking_date', 'start_time')[:5]
    
    # Recent bookings
    recent_bookings = Booking.objects.filter(
        customer=customer,
        business=business
    ).select_related('service_offering').order_by('-created_at')[:5]
    
    # Recent invoices
    recent_invoices = Invoice.objects.filter(
        booking__customer=customer,
        booking__business=business
    ).select_related('booking').order_by('-created_at')[:5]
    
    # Outstanding balance - calculate from booking service prices
    outstanding_invoices = Invoice.objects.filter(
        booking__customer=customer,
        booking__business=business,
        status__in=[InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]
    ).select_related('booking__service_offering')
    
    outstanding_balance = Decimal('0.00')
    for invoice in outstanding_invoices:
        if invoice.booking and invoice.booking.service_offering:
            outstanding_balance += invoice.booking.service_offering.price
    
    # Statistics
    total_bookings = Booking.objects.filter(
        customer=customer,
        business=business
    ).count()
    
    completed_bookings = Booking.objects.filter(
        customer=customer,
        business=business,
        status=BookingStatus.COMPLETED
    ).count()
    
    context = {
        'customer': customer,
        'business': business,
        'upcoming_bookings': upcoming_bookings,
        'recent_bookings': recent_bookings,
        'recent_invoices': recent_invoices,
        'outstanding_balance': outstanding_balance,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'linked_businesses': customer.business_links.filter(is_active=True).select_related('business')
    }
    
    return render(request, 'customer/dashboard.html', context)


# ============================================================================
# BOOKING MANAGEMENT
# ============================================================================

@login_required
@customer_required
def bookings_list(request):
    """List all bookings for customer"""
    customer = request.user.customer_profile
    business = get_active_business(request, customer)
    
    if not business:
        return redirect('customer:dashboard')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    
    bookings = Booking.objects.filter(
        customer=customer,
        business=business
    ).select_related('service_offering')
    
    if status_filter != 'all':
        bookings = bookings.filter(status=status_filter)
    
    bookings = bookings.order_by('-booking_date', '-start_time')
    
    context = {
        'customer': customer,
        'business': business,
        'bookings': bookings,
        'status_filter': status_filter,
        'booking_statuses': BookingStatus.choices
    }
    
    return render(request, 'customer/bookings_list.html', context)


@login_required
@customer_required
def booking_detail(request, booking_id):
    """Booking detail view"""
    customer = request.user.customer_profile
    
    booking = get_object_or_404(
        Booking.objects.select_related('service_offering', 'business'),
        id=booking_id,
        customer=customer
    )
    
    # Get invoice if exists
    invoice = Invoice.objects.filter(booking=booking).first()
    
    # Get enabled event types for customer
    business = booking.business
    all_enabled_event_types = BookingEventType.objects.filter(
        business=business,
        is_enabled=True
    ).order_by('display_order')
    
    enabled_event_types = [et for et in all_enabled_event_types if et.is_accessible_by_user(request.user)]
    
    # Build event configs for JavaScript
    event_configs_dict = {}
    for event_type in enabled_event_types:
        field_config = event_type.get_fields_config()
        event_configs_dict[event_type.event_key] = {
            'id': event_type.id,
            'title': event_type.name,
            'icon': event_type.icon,
            'color': event_type.color,
            'requires_reason': event_type.requires_reason,
            'fields': field_config["fields"],
            'submitText': field_config["submitText"],
            'successMessage': field_config["successMessage"],
        }
    event_configs = json.dumps(event_configs_dict)
    
    context = {
        'customer': customer,
        'booking': booking,
        'invoice': invoice,
        'duration': booking.get_service_duration(),
        'event_configs': event_configs,
        'business': business,
    }
    
    return render(request, 'customer/booking_detail.html', context)


@login_required
@customer_required
def booking_reschedule(request, booking_id):
    """Reschedule booking - placeholder"""
    messages.info(request, 'Booking rescheduling functionality coming soon.')
    return redirect('customer:booking_detail', booking_id=booking_id)


@login_required
@customer_required
def booking_cancel(request, booking_id):
    """Cancel booking"""
    customer = request.user.customer_profile
    
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        customer=customer
    )
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        booking.cancel(reason=reason)
        
        messages.success(request, 'Your booking has been cancelled successfully.')
        return redirect('customer:bookings_list')
    
    return render(request, 'customer/booking_cancel.html', {'booking': booking})


# ============================================================================
# INVOICES & PAYMENTS
# ============================================================================

@login_required
@customer_required
def invoices_list(request):
    """List all invoices"""
    customer = request.user.customer_profile
    business = get_active_business(request, customer)
    
    if not business:
        return redirect('customer:dashboard')
    
    invoices = Invoice.objects.filter(
        booking__customer=customer,
        booking__business=business
    ).select_related('booking').order_by('-created_at')
    
    context = {
        'customer': customer,
        'business': business,
        'invoices': invoices
    }
    
    return render(request, 'customer/invoices_list.html', context)


@login_required
@customer_required
def invoice_detail(request, invoice_id):
    """Invoice detail - placeholder"""
    messages.info(request, 'Invoice detail functionality coming soon.')
    return redirect('customer:invoices_list')


@login_required
@customer_required
def invoice_pay(request, invoice_id):
    """Pay invoice - placeholder"""
    messages.info(request, 'Payment functionality coming soon.')
    return redirect('customer:invoices_list')


@login_required
@customer_required
def payment_history(request):
    """Payment history - placeholder"""
    messages.info(request, 'Payment history functionality coming soon.')
    return redirect('customer:dashboard')


# ============================================================================
# PROFILE MANAGEMENT
# ============================================================================

@login_required
@customer_required
def customer_profile(request):
    """View customer profile"""
    customer = request.user.customer_profile
    
    context = {
        'customer': customer
    }
    
    return render(request, 'customer/profile.html', context)


@login_required
@customer_required
def profile_edit(request):
    """Edit customer profile"""
    customer = request.user.customer_profile
    
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=customer)
        if form.is_valid():
            # Update user fields
            user = customer.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            
            # Save customer profile
            form.save()
            
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('customer:profile')
    else:
        form = CustomerProfileForm(instance=customer)
    
    context = {
        'customer': customer,
        'form': form
    }
    
    return render(request, 'customer/profile_edit.html', context)


@login_required
@customer_required
def change_password(request):
    """Change password - placeholder"""
    messages.info(request, 'Password change functionality coming soon.')
    return redirect('customer:profile')


@login_required
@customer_required
def notification_preferences(request):
    """Manage notification preferences"""
    customer = request.user.customer_profile
    
    if request.method == 'POST':
        form = NotificationPreferencesForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your notification preferences have been updated.')
            return redirect('customer:profile')
    else:
        form = NotificationPreferencesForm(instance=customer)
    
    context = {
        'customer': customer,
        'form': form
    }
    
    return render(request, 'customer/notification_preferences.html', context)


# ============================================================================
# BUSINESS MANAGEMENT
# ============================================================================

@login_required
@customer_required
def linked_businesses(request):
    """View all linked businesses"""
    customer = request.user.customer_profile
    
    businesses = customer.business_links.filter(
        is_active=True
    ).select_related('business').order_by('-last_booking_date')
    
    context = {
        'customer': customer,
        'businesses': businesses
    }
    
    return render(request, 'customer/linked_businesses.html', context)


@login_required
@customer_required
def switch_business(request, business_id):
    """Switch active business"""
    customer = request.user.customer_profile
    
    # Verify customer is linked to this business
    link = customer.business_links.filter(
        business_id=business_id,
        is_active=True
    ).first()
    
    if link:
        set_active_business(request, business_id)
        messages.success(request, f'Switched to {link.business.name}')
    else:
        messages.error(request, 'You do not have access to this business.')
    
    return redirect('customer:dashboard')
