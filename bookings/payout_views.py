from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import models
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from business.models import Business
from business.utils import get_user_business
from .models import (
    StaffMember, StaffPayout, Booking, 
    BookingStatus, PayoutStatus, BookingStaffAssignment
)


@login_required
def payout_list(request):
    """List all staff payouts with filtering options"""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, 'Please register your business first.')
        return redirect('business:register')
    
    # Get all payouts for this business
    payouts = StaffPayout.objects.filter(business=business).select_related(
        'staff_member'
    ).prefetch_related('bookings')
    
    # Apply filters
    status_filter = request.GET.get('status', '')
    if status_filter and status_filter in dict(PayoutStatus.choices):
        payouts = payouts.filter(status=status_filter)
    
    staff_filter = request.GET.get('staff', '')
    if staff_filter:
        payouts = payouts.filter(staff_member_id=staff_filter)
    
    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        try:
            payouts = payouts.filter(created_at__gte=date_from)
        except ValueError:
            pass
    if date_to:
        try:
            payouts = payouts.filter(created_at__lte=date_to)
        except ValueError:
            pass
    
    # Get all staff members for the filter dropdown
    staff_members = StaffMember.objects.filter(business=business, is_active=True).order_by('first_name', 'last_name')
    
    # Calculate summary statistics
    paid_payouts = payouts.filter(status=PayoutStatus.PAID)
    total_paid = sum(p.get_payout_amount() for p in paid_payouts)
    
    pending_payouts = payouts.filter(status=PayoutStatus.PENDING)
    total_pending = sum(p.get_payout_amount() for p in pending_payouts)
    
    context = {
        'title': 'Staff Payouts',
        'business': business,
        'payouts': payouts,
        'staff_members': staff_members,
        'payout_statuses': PayoutStatus.choices,
        'current_status': status_filter,
        'current_staff': staff_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_paid': total_paid,
        'total_pending': total_pending,
    }
    
    return render(request, 'bookings/payouts/payout_list.html', context)


@login_required
def payout_detail(request, payout_id):
    """View detailed information about a specific payout"""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, 'Please register your business first.')
        return redirect('business:register')
    
    payout = get_object_or_404(
        StaffPayout.objects.select_related('staff_member', 'business')
        .prefetch_related('bookings'),
        id=payout_id,
        business=business
    )
    
    context = {
        'title': f'Payout Details - {payout.staff_member.get_full_name()}',
        'business': business,
        'payout': payout,
    }
    
    return render(request, 'bookings/payouts/payout_detail.html', context)


@login_required
def create_payout(request):
    """Create a new payout for a staff member"""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, 'Please register your business first.')
        return redirect('business:register')
    
    staff_members = StaffMember.objects.filter(business=business, is_active=True).order_by('first_name', 'last_name')
    
    # Get default payout percentage from business configuration
    default_percentage = Decimal('0.00')
    if hasattr(business, 'configuration') and business.configuration.staff_pay_percentage:
        default_percentage = business.configuration.staff_pay_percentage
    
    if request.method == 'POST':
        staff_member_id = request.POST.get('staff_member')
        period_start = request.POST.get('period_start')
        period_end = request.POST.get('period_end')
        notes = request.POST.get('notes', '')
        
        # Validation
        errors = []
        if not staff_member_id:
            errors.append('Staff member is required.')
        if not period_start:
            errors.append('Period start date is required.')
        if not period_end:
            errors.append('Period end date is required.')
        
        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'bookings/payouts/create_payout.html', {
                'title': 'Create Payout',
                'business': business,
                'staff_members': staff_members,
                'default_percentage': default_percentage,
            })
        
        try:
            staff_member = StaffMember.objects.get(id=staff_member_id, business=business)
        except StaffMember.DoesNotExist:
            messages.error(request, 'Invalid staff member selected.')
            return render(request, 'bookings/payouts/create_payout.html', {
                'title': 'Create Payout',
                'business': business,
                'staff_members': staff_members,
                'default_percentage': default_percentage,
            })
        
        # Get all completed bookings for this staff member in the period
        completed_bookings = Booking.objects.filter(
            business=business,
            status=BookingStatus.COMPLETED,
            booking_date__gte=period_start,
            booking_date__lte=period_end,
            staff_assignments__staff_member=staff_member
        ).distinct()
        
        # Create the payout
        payout = StaffPayout.objects.create(
            business=business,
            staff_member=staff_member,
            notes=notes,
            status=PayoutStatus.PENDING
        )
        
        # Link bookings to this payout using M2M
        payout.bookings.set(completed_bookings)
        
        messages.success(request, f'Payout created successfully for {staff_member.get_full_name()} with {completed_bookings.count()} bookings!')
        return redirect('bookings:payout_detail', payout_id=payout.id)
    
    # GET request
    context = {
        'title': 'Create Payout',
        'business': business,
        'staff_members': staff_members,
        'default_percentage': default_percentage,
    }
    
    return render(request, 'bookings/payouts/create_payout.html', context)


@login_required
@require_http_methods(["POST"])
def mark_payout_paid(request, payout_id):
    """Mark a payout as paid"""
    business = get_user_business(request.user)
    if not business:
        return JsonResponse({'success': False, 'error': 'Business not found'}, status=400)
    
    payout = get_object_or_404(StaffPayout, id=payout_id, business=business)
    
    payment_method = request.POST.get('payment_method', '')
    payment_reference = request.POST.get('payment_reference', '')
    paid_date = request.POST.get('paid_date', timezone.now().date())
    
    payout.mark_as_paid(
        payment_method=payment_method,
        payment_reference=payment_reference,
        paid_date=paid_date,
        user=request.user
    )
    
    messages.success(request, f'Payout marked as paid for {payout.staff_member.get_full_name()}!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('bookings:payout_detail', payout_id=payout_id)


@login_required
@require_http_methods(["POST"])
def mark_payout_pending(request, payout_id):
    """Mark a payout as pending"""
    business = get_user_business(request.user)
    if not business:
        return JsonResponse({'success': False, 'error': 'Business not found'}, status=400)
    
    payout = get_object_or_404(StaffPayout, id=payout_id, business=business)
    
    payout.mark_as_pending()
    
    messages.success(request, f'Payout marked as pending for {payout.staff_member.get_full_name()}!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('bookings:payout_detail', payout_id=payout_id)


@login_required
def staff_payout_summary(request):
    """View summary of payouts for all staff members"""
    business = get_user_business(request.user)
    if not business:
        messages.error(request, 'Please register your business first.')
        return redirect('business:register')
    
    # Get all active staff members
    staff_members = StaffMember.objects.filter(business=business, is_active=True).order_by('first_name', 'last_name')
    
    # Calculate summary for each staff member
    staff_summaries = []
    for staff in staff_members:
        # Get all payouts for this staff member
        payouts = StaffPayout.objects.filter(staff_member=staff)
        
        paid_payouts = payouts.filter(status=PayoutStatus.PAID)
        total_paid = sum(p.get_payout_amount() for p in paid_payouts)
        
        pending_payouts = payouts.filter(status=PayoutStatus.PENDING)
        total_pending = sum(p.get_payout_amount() for p in pending_payouts)
        
        total_bookings = sum(p.get_total_bookings() for p in payouts)
        
        # Get completed bookings not yet in any payout
        completed_bookings_count = Booking.objects.filter(
            business=business,
            status=BookingStatus.COMPLETED,
            staff_assignments__staff_member=staff
        ).exclude(
            staff_payouts__isnull=False
        ).distinct().count()
        
        staff_summaries.append({
            'staff': staff,
            'total_paid': total_paid,
            'total_pending': total_pending,
            'total_bookings': total_bookings,
            'unpaid_bookings': completed_bookings_count,
        })
    
    context = {
        'title': 'Staff Payout Summary',
        'business': business,
        'staff_summaries': staff_summaries,
    }
    
    return render(request, 'bookings/payouts/staff_summary.html', context)


@login_required
def get_staff_bookings(request):
    """AJAX endpoint to get completed bookings for a staff member in a date range"""
    business = get_user_business(request.user)
    if not business:
        return JsonResponse({'success': False, 'error': 'Business not found'}, status=400)
    
    staff_member_id = request.GET.get('staff_member')
    period_start = request.GET.get('period_start')
    period_end = request.GET.get('period_end')
    
    if not all([staff_member_id, period_start, period_end]):
        return JsonResponse({'success': False, 'error': 'Missing required parameters'}, status=400)
    
    try:
        staff_member = StaffMember.objects.get(id=staff_member_id, business=business)
    except StaffMember.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Staff member not found'}, status=404)
    
    # Get completed bookings for this staff member in the period
    bookings = Booking.objects.filter(
        business=business,
        status=BookingStatus.COMPLETED,
        booking_date__gte=period_start,
        booking_date__lte=period_end,
        staff_assignments__staff_member=staff_member
    ).distinct().select_related('service_offering')
    
    # Calculate totals
    total_bookings = bookings.count()
    total_revenue = sum(booking.get_total() for booking in bookings)
    
    # Prepare booking data
    booking_data = []
    for booking in bookings:
        booking_data.append({
            'id': booking.id,
            'date': booking.booking_date.strftime('%Y-%m-%d'),
            'service': booking.service_offering.name if booking.service_offering else 'N/A',
            'customer': booking.name,
            'revenue': str(booking.get_total()),
        })
    
    return JsonResponse({
        'success': True,
        'total_bookings': total_bookings,
        'total_revenue': str(total_revenue),
        'bookings': booking_data,
    })
