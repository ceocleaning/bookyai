from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField

from bookings.models import Booking, BookingServiceItem
from leads.models import Lead
from invoices.models import Invoice


@login_required
def index(request):
    """
    Render the dashboard index page
    Requires user to be logged in and have a business
    """
    # Check if user has a business
    if not hasattr(request.user, 'business'):
        messages.warning(request, 'Please register your business first.')
        return redirect('business:register')
    
    # Get business data
    business = request.user.business
    
    # Get today's date and date ranges
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_start - timedelta(days=1)
    
    # Get upcoming appointments (today and future)
    upcoming_appointments = Booking.objects.filter(
        business=business,
        booking_date__gte=today
    ).order_by('booking_date', 'start_time')[:5]
    
    # Get today's appointments count
    todays_appointments_count = Booking.objects.filter(
        business=business,
        created_at__date=today
    ).count()

    
    # Get yesterday's appointments count for comparison
    yesterday = today - timedelta(days=1)
    yesterdays_appointments_count = Booking.objects.filter(
        business=business,
        created_at__date=yesterday
    ).count()
    
    # Calculate appointment change percentage
    if yesterdays_appointments_count > 0:
        appointment_change_percent = int((todays_appointments_count - yesterdays_appointments_count) / yesterdays_appointments_count * 100)
    else:
        appointment_change_percent = 100 if todays_appointments_count > 0 else 0
    
    # Get new leads (last 7 days)
    new_leads = Lead.objects.filter(
        business=business,
        created_at__gte=today - timedelta(days=7)
    ).order_by('-created_at')[:5]
    
    # Get new leads count this week
    new_leads_count = Lead.objects.filter(
        business=business,
        created_at__date__range=[week_start, week_end]
    ).count()
    
    # Get new leads count last week for comparison
    last_week_leads_count = Lead.objects.filter(
        business=business,
        created_at__date__range=[last_week_start, last_week_end]
    ).count()
    
    # Calculate lead change percentage
    if last_week_leads_count > 0:
        lead_change_percent = int((new_leads_count - last_week_leads_count) / last_week_leads_count * 100)
    else:
        lead_change_percent = 100 if new_leads_count > 0 else 0
    
    # Get AI calls count (placeholder - would be replaced with actual data)
    ai_calls_count = 24
    ai_calls_change_percent = 15
    
    # Get revenue this week from booking service items
    revenue_this_week = BookingServiceItem.objects.filter(
        booking__business=business,
        booking__created_at__date__range=[week_start, week_end]
    ).annotate(
        item_total=ExpressionWrapper(
            F('price_at_booking') * F('quantity'),
            output_field=DecimalField()
        )
    ).aggregate(total=Sum('item_total'))['total'] or 0
    
    # Get revenue last week for comparison
    revenue_last_week = BookingServiceItem.objects.filter(
        booking__business=business,
        booking__created_at__date__range=[last_week_start, last_week_end]
    ).annotate(
        item_total=ExpressionWrapper(
            F('price_at_booking') * F('quantity'),
            output_field=DecimalField()
        )
    ).aggregate(total=Sum('item_total'))['total'] or 0
    
    # Calculate revenue change percentage
    if revenue_last_week > 0:
        revenue_change_percent = int((revenue_this_week - revenue_last_week) / revenue_last_week * 100)
    else:
        revenue_change_percent = 100 if revenue_this_week > 0 else 0
    
    context = {
        'business': business,
        'upcoming_appointments': upcoming_appointments,
        'todays_appointments_count': todays_appointments_count,
        'appointment_change_percent': appointment_change_percent,
        'new_leads': new_leads,
        'new_leads_count': new_leads_count,
        'lead_change_percent': lead_change_percent,
        'ai_calls_count': ai_calls_count,
        'ai_calls_change_percent': ai_calls_change_percent,
        'revenue_this_week': revenue_this_week,
        'revenue_change_percent': revenue_change_percent,
        'today': today,
    }
    

    return render(request, 'dashboard/index.html', context)


# ============================================================================
# CUSTOMER MANAGEMENT VIEWS
# ============================================================================

@login_required
def customers_list(request):
    """List all customers for the business"""
    from customer.models import Customer, CustomerBusinessLink
    
    if not hasattr(request.user, 'business'):
        messages.warning(request, 'Please register your business first.')
        return redirect('business:register')
    
    business = request.user.business
    
    # Get all customers linked to this business
    customer_links = CustomerBusinessLink.objects.filter(
        business=business,
        is_active=True
    ).select_related('customer__user').order_by('-last_booking_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        from django.db.models import Q
        customer_links = customer_links.filter(
            Q(customer__user__first_name__icontains=search_query) |
            Q(customer__user__last_name__icontains=search_query) |
            Q(customer__user__email__icontains=search_query) |
            Q(customer__phone_number__icontains=search_query)
        )
    
    context = {
        'business': business,
        'customer_links': customer_links,
        'search_query': search_query,
        'total_customers': customer_links.count()
    }
    
    return render(request, 'dashboard/customers_list.html', context)


@login_required
def customer_detail(request, customer_id):
    """View customer details"""
    from customer.models import Customer, CustomerBusinessLink
    from django.shortcuts import get_object_or_404
    
    if not hasattr(request.user, 'business'):
        messages.warning(request, 'Please register your business first.')
        return redirect('business:register')
    
    business = request.user.business
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Verify customer is linked to this business
    link = CustomerBusinessLink.objects.filter(
        customer=customer,
        business=business
    ).first()
    
    if not link:
        messages.error(request, 'Customer not found.')
        return redirect('dashboard:customers_list')
    
    # Get customer's bookings with this business
    bookings = Booking.objects.filter(
        customer=customer,
        business=business
    ).select_related('service_offering').order_by('-booking_date', '-start_time')
    
    context = {
        'business': business,
        'customer': customer,
        'link': link,
        'bookings': bookings
    }
    
    return render(request, 'dashboard/customer_detail.html', context)


@login_required
def customer_add(request):
    """Add a new customer"""
    from customer.models import Customer, CustomerBusinessLink
    from django.contrib.auth.models import User, Group
    
    if not hasattr(request.user, 'business'):
        messages.warning(request, 'Please register your business first.')
        return redirect('business:register')
    
    business = request.user.business
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        
        # Check if user already exists
        user = User.objects.filter(email=email).first()
        
        if user and hasattr(user, 'customer_profile'):
            # Existing customer - just link to business
            customer = user.customer_profile
            link, created = CustomerBusinessLink.objects.get_or_create(
                customer=customer,
                business=business
            )
            
            if created:
                messages.success(request, f'Customer {customer.user.get_full_name()} linked to your business.')
            else:
                messages.info(request, 'Customer is already linked to your business.')
            
            return redirect('dashboard:customer_detail', customer_id=customer.id)
        
        # Create new customer
        if not user:
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            user.set_unusable_password()
            user.save()
        
        # Add to customer group
        customer_group, _ = Group.objects.get_or_create(name='customer')
        user.groups.add(customer_group)
        
        # Create customer profile
        customer = Customer.objects.create(
            user=user,
            phone_number=phone_number
        )
        
        # Link to business
        CustomerBusinessLink.objects.create(
            customer=customer,
            business=business
        )
        
        # Send welcome email
        from customer.utils import send_customer_welcome_email
        send_customer_welcome_email(user, business)
        
        messages.success(request, f'Customer {user.get_full_name()} added successfully. Welcome email sent.')
        return redirect('dashboard:customer_detail', customer_id=customer.id)
    
    context = {
        'business': business
    }
    
    return render(request, 'dashboard/customer_add.html', context)


@login_required
def customer_delete(request, customer_id):
    """Delete/unlink a customer from the business"""
    from customer.models import Customer, CustomerBusinessLink
    from django.shortcuts import get_object_or_404
    
    if not hasattr(request.user, 'business'):
        messages.warning(request, 'Please register your business first.')
        return redirect('business:register')
    
    business = request.user.business
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Get the link
    link = CustomerBusinessLink.objects.filter(
        customer=customer,
        business=business
    ).first()
    
    if not link:
        messages.error(request, 'Customer not found.')
        return redirect('dashboard:customers_list')
    
    if request.method == 'POST':
        # Soft delete - just deactivate the link
        link.is_active = False
        link.save()
        
        messages.success(request, f'Customer {customer.user.get_full_name()} removed from your business.')
        return redirect('dashboard:customers_list')
    
    context = {
        'business': business,
        'customer': customer,
        'link': link
    }
    
    return render(request, 'dashboard/customer_delete.html', context)


@login_required
def get_customers_api(request):
    from django.http import JsonResponse
    from customer.models import Customer, CustomerBusinessLink
    
    if not hasattr(request.user, 'business'):
        return JsonResponse({'customers': []})
    
    business = request.user.business
    customer_links = CustomerBusinessLink.objects.filter(business=business).select_related('customer')
    
    customers_data = []
    for link in customer_links:
        customer = link.customer
        customers_data.append({
            'id': customer.id,
            'name': customer.get_full_name(),
            'email': customer.user.email,
            'phone_number': customer.phone_number or '',
        })
    
    return JsonResponse({'customers': customers_data})
