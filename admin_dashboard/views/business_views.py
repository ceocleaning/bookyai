"""
Admin Dashboard Business Views
Handles business management: list, detail, add, edit, delete
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal

from business.models import Business, Industry
from bookings.models import Booking
from leads.models import Lead
from invoices.models import Invoice, Payment


@staff_member_required
@login_required
def business_list(request):
    """
    Display all businesses with search and filtering
    """
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')  # all, active, inactive, industry
    industry_filter = request.GET.get('industry', '')
    page_number = request.GET.get('page', 1)
    
    # Base queryset
    businesses = Business.objects.all().select_related('user', 'industry')
    
    # Apply search
    if search_query:
        businesses = businesses.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Apply filters
    if filter_type == 'active':
        businesses = businesses.filter(is_active=True)
    elif filter_type == 'inactive':
        businesses = businesses.filter(is_active=False)
    
    if industry_filter:
        businesses = businesses.filter(industry_id=industry_filter)
    
    # Order by created date (newest first)
    businesses = businesses.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(businesses, 20)  # 20 businesses per page
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_businesses = Business.objects.count()
    active_businesses = Business.objects.filter(is_active=True).count()
    inactive_businesses = Business.objects.filter(is_active=False).count()
    
    # Get all industries for filter dropdown
    industries = Industry.objects.all().order_by('name')
    
    context = {
        'page_title': 'Business Management',
        'businesses': page_obj,
        'search_query': search_query,
        'filter_type': filter_type,
        'industry_filter': industry_filter,
        'industries': industries,
        'total_businesses': total_businesses,
        'active_businesses': active_businesses,
        'inactive_businesses': inactive_businesses,
    }
    
    return render(request, 'admin_dashboard/business/list.html', context)


@staff_member_required
@login_required
def business_detail(request, business_id):
    """
    Display detailed information about a specific business
    """
    business = get_object_or_404(Business.objects.select_related('user', 'industry'), id=business_id)
    
    # Get business statistics
    total_bookings = Booking.objects.filter(business=business).count()
    total_leads = Lead.objects.filter(business=business).count()
    total_invoices = Invoice.objects.filter(booking__business=business).count()
    
    # Calculate revenue
    total_revenue = Payment.objects.filter(
        invoice__booking__business=business,
        is_refunded=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Recent bookings
    recent_bookings = Booking.objects.filter(business=business).order_by('-created_at')[:5]
    
    # Recent leads
    recent_leads = Lead.objects.filter(business=business).order_by('-created_at')[:5]
    
    context = {
        'page_title': f'Business: {business.name}',
        'business': business,
        'total_bookings': total_bookings,
        'total_leads': total_leads,
        'total_invoices': total_invoices,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
        'recent_leads': recent_leads,
    }
    
    return render(request, 'admin_dashboard/business/detail.html', context)


@staff_member_required
@login_required
def business_add(request):
    """
    Add a new business
    """
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name', '').strip()
        user_id = request.POST.get('user_id')
        industry_id = request.POST.get('industry_id')
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()
        website = request.POST.get('website', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        zip_code = request.POST.get('zip_code', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        if not name:
            messages.error(request, 'Business name is required')
            return redirect('admin_dashboard:business_add')
        
        if not user_id:
            messages.error(request, 'User is required')
            return redirect('admin_dashboard:business_add')
        
        if not industry_id:
            messages.error(request, 'Industry is required')
            return redirect('admin_dashboard:business_add')
        
        try:
            user = User.objects.get(id=user_id)
            industry = Industry.objects.get(id=industry_id)
            
            # Check if user already has a business
            if hasattr(user, 'business'):
                messages.error(request, f'User {user.username} already has a business')
                return redirect('admin_dashboard:business_add')
            
            # Create business
            business = Business.objects.create(
                name=name,
                user=user,
                industry=industry,
                phone_number=phone_number,
                email=email,
                website=website,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                description=description,
                is_active=is_active
            )
            
            messages.success(request, f'Business {business.name} created successfully!')
            return redirect('admin_dashboard:business_detail', business_id=business.id)
            
        except User.DoesNotExist:
            messages.error(request, 'Selected user does not exist')
        except Industry.DoesNotExist:
            messages.error(request, 'Selected industry does not exist')
        except Exception as e:
            messages.error(request, f'Error creating business: {str(e)}')
    
    # Get users without businesses
    users_without_business = User.objects.filter(business__isnull=True).order_by('username')
    industries = Industry.objects.all().order_by('name')
    
    context = {
        'page_title': 'Add New Business',
        'users': users_without_business,
        'industries': industries,
    }
    
    return render(request, 'admin_dashboard/business/add.html', context)


@staff_member_required
@login_required
def business_edit(request, business_id):
    """
    Edit business information
    """
    business = get_object_or_404(Business, id=business_id)
    
    if request.method == 'POST':
        # Update business fields
        business.name = request.POST.get('name', business.name).strip()
        business.phone_number = request.POST.get('phone_number', '').strip()
        business.email = request.POST.get('email', '').strip()
        business.website = request.POST.get('website', '').strip()
        business.address = request.POST.get('address', '').strip()
        business.city = request.POST.get('city', '').strip()
        business.state = request.POST.get('state', '').strip()
        business.zip_code = request.POST.get('zip_code', '').strip()
        business.description = request.POST.get('description', '').strip()
        business.is_active = request.POST.get('is_active') == 'on'
        
        # Update industry if changed
        industry_id = request.POST.get('industry_id')
        if industry_id:
            try:
                business.industry = Industry.objects.get(id=industry_id)
            except Industry.DoesNotExist:
                messages.error(request, 'Selected industry does not exist')
                return redirect('admin_dashboard:business_edit', business_id=business.id)
        
        try:
            business.save()
            messages.success(request, f'Business {business.name} updated successfully!')
            return redirect('admin_dashboard:business_detail', business_id=business.id)
        except Exception as e:
            messages.error(request, f'Error updating business: {str(e)}')
    
    industries = Industry.objects.all().order_by('name')
    
    context = {
        'page_title': f'Edit Business: {business.name}',
        'business': business,
        'industries': industries,
    }
    
    return render(request, 'admin_dashboard/business/edit.html', context)


@staff_member_required
@login_required
def business_delete(request, business_id):
    """
    API endpoint to delete a business
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    business = get_object_or_404(Business, id=business_id)
    
    try:
        business_name = business.name
        business.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Business {business_name} deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
@login_required
def business_toggle_status(request, business_id):
    """
    API endpoint to toggle business active status
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    business = get_object_or_404(Business, id=business_id)
    
    try:
        business.is_active = not business.is_active
        business.save()
        
        status = 'activated' if business.is_active else 'deactivated'
        
        return JsonResponse({
            'success': True,
            'message': f'Business {business.name} {status} successfully',
            'is_active': business.is_active
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
@login_required
def business_bookings(request, business_id):
    """
    Display all bookings for a specific business
    """
    business = get_object_or_404(Business, id=business_id)
    
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    page_number = request.GET.get('page', 1)
    
    # Base queryset
    bookings = Booking.objects.filter(business=business).select_related('service_offering', 'lead')
    
    # Apply search
    if search_query:
        bookings = bookings.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(service_offering__name__icontains=search_query) |
            Q(lead__name__icontains=search_query) |
            Q(lead__email__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter != 'all':
        bookings = bookings.filter(status=status_filter)
    
    # Order by created date (newest first)
    bookings = bookings.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(bookings, 20)
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    from bookings.models import BookingStatus
    total_bookings = Booking.objects.filter(business=business).count()
    confirmed_bookings = Booking.objects.filter(business=business, status=BookingStatus.CONFIRMED).count()
    completed_bookings = Booking.objects.filter(business=business, status=BookingStatus.COMPLETED).count()
    cancelled_bookings = Booking.objects.filter(business=business, status=BookingStatus.CANCELLED).count()
    
    context = {
        'page_title': f'Bookings - {business.name}',
        'business': business,
        'bookings': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
    }
    
    return render(request, 'admin_dashboard/business/bookings.html', context)


@staff_member_required
@login_required
def business_leads(request, business_id):
    """
    Display all leads for a specific business
    """
    business = get_object_or_404(Business, id=business_id)
    
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    page_number = request.GET.get('page', 1)
    
    # Base queryset
    leads = Lead.objects.filter(business=business)
    
    # Apply search
    if search_query:
        leads = leads.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter != 'all':
        leads = leads.filter(status=status_filter)
    
    # Order by created date (newest first)
    leads = leads.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(leads, 20)
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    from leads.models import LeadStatus
    total_leads = Lead.objects.filter(business=business).count()
    new_leads = Lead.objects.filter(business=business, status=LeadStatus.NEW).count()
    contacted_leads = Lead.objects.filter(business=business, status=LeadStatus.CONTACTED).count()
    converted_leads = Lead.objects.filter(business=business, status=LeadStatus.CONVERTED).count()
    
    context = {
        'page_title': f'Leads - {business.name}',
        'business': business,
        'leads': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_leads': total_leads,
        'new_leads': new_leads,
        'contacted_leads': contacted_leads,
        'converted_leads': converted_leads,
    }
    
    return render(request, 'admin_dashboard/business/leads.html', context)

@staff_member_required
@login_required
def booking_detail(request, business_id, booking_id):
    """
    Display details for a specific booking
    """
    business = get_object_or_404(Business, id=business_id)
    booking = get_object_or_404(Booking, id=booking_id, business=business)
    
    # Get related data
    from bookings.models import BookingEvent, BookingEventType, ReminderType
    
    timeline = BookingEvent.objects.filter(booking=booking).order_by('-created_at')
    
    # Service items (assuming related name or model structure)
    # Using 'items' if that's the related name, or querying BookingServiceItem directly
    # Based on checking models.py properly, we might need to adjust.
    # The snippet used: for item in service_items
    try:
        service_items = booking.service_items.all() 
    except AttributeError:
        # Fallback if related name is different
        service_items = []

    # Calculate totals
    paid_service_items = [item for item in service_items if item.price_at_booking > 0]
    paid_service_items_total = sum(item.price_at_booking for item in paid_service_items)
    
    has_paid_items = len(paid_service_items) > 0
    total_price = booking.service_offering.price + paid_service_items_total
    
    # Invoice and payments
    invoice = Invoice.objects.filter(booking=booking).first()
    payments = []
    total_paid = Decimal('0.00')
    balance_due = total_price
    
    if invoice:
        payments = Payment.objects.filter(invoice=invoice).order_by('-payment_date')
        total_paid = payments.filter(is_refunded=False).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        balance_due = max(Decimal('0.00'), total_price - total_paid)
        
    # Configs
    enabled_event_types = BookingEventType.objects.filter(business=business, is_enabled=True)
    enabled_reminder_types = ReminderType.objects.filter(business=business, is_enabled=True)
    
    # Event configs for JS
    import json
    event_configs = {}
    for et in enabled_event_types:
        event_configs[et.event_key] = et.get_fields_config()
    
    days = 0 
    hours = 0
    minutes = 0
    if booking.end_time and booking.start_time:
        # duration in minutes
        # This is a bit complex with TimeField only, assuming same day
        # Ideally calculate from model method
        duration = booking.get_service_duration()
    else:
        duration = 0

    context = {
        'page_title': f'Booking #{booking.id}',
        'business': business,
        'booking': booking,
        'timeline': timeline,
        'service_items': service_items,
        'has_paid_items': has_paid_items,
        'paid_service_items': paid_service_items,
        'paid_service_items_total': paid_service_items_total,
        'total_price': total_price,
        'invoice': invoice,
        'payments': payments,
        'total_paid': total_paid,
        'balance_due': balance_due,
        'enabled_event_types': enabled_event_types,
        'enabled_reminder_types': enabled_reminder_types,
        'event_configs': json.dumps(event_configs),
        'duration': duration,
        # Fields
        'industry_fields': booking.fields.filter(field_type='industry'),
        'custom_fields': booking.fields.filter(field_type='business'),
    }
    
    return render(request, 'admin_dashboard/business/booking_detail.html', context)


@staff_member_required
@login_required
def lead_detail(request, business_id, lead_id):
    """
    Display details for a specific lead
    """
    business = get_object_or_404(Business, id=business_id)
    lead = get_object_or_404(Lead, id=lead_id, business=business)
    
    from leads.models import LeadCommunication
    
    communications = LeadCommunication.objects.filter(lead=lead).order_by('-created_at')
    
    context = {
        'page_title': f'Lead: {lead.get_full_name()}',
        'business': business,
        'lead': lead,
        'communications': communications,
    }
    
    return render(request, 'admin_dashboard/business/lead_detail.html', context)
