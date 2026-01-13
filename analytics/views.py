from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, F, Q, Avg, ExpressionWrapper, DecimalField
from datetime import timedelta, datetime
from decimal import Decimal
import csv

from bookings.models import Booking, BookingServiceItem, BookingStatus, StaffMember
from leads.models import Lead, LeadStatus, LeadSource
from invoices.models import Invoice, Payment
from business.models import ServiceOffering


@login_required
def analytics_dashboard(request):
    """
    Main analytics dashboard view with comprehensive business metrics
    """
    # Get business
    if not hasattr(request.user, 'business'):
        return render(request, 'analytics/no_business.html')
    
    business = request.user.business
    
    # Date range filtering
    # Get date range from GET parameters or default to current month
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    today = timezone.now().date()
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            # If invalid dates, default to current month
            start_date = today.replace(day=1)
            end_date = today
    else:
        # Default to current month
        start_date = today.replace(day=1)
        end_date = today
    
    # Calculate comparison period (same length as selected period)
    period_length = (end_date - start_date).days
    comparison_end = start_date - timedelta(days=1)
    comparison_start = comparison_end - timedelta(days=period_length)
    
    # For monthly comparisons
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = current_month_start - timedelta(days=1)
    
    # === REVENUE METRICS ===
    # Total revenue (all time)
    total_revenue = BookingServiceItem.objects.filter(
        booking__business=business,
        booking__created_at__gte=start_date,
        booking__created_at__lte=end_date
    ).annotate(
        item_total=ExpressionWrapper(
            F('price_at_booking') * F('quantity'),
            output_field=DecimalField()
        )
    ).aggregate(total=Sum('item_total'))['total'] or Decimal('0.00')
    
    # Selected period revenue
    this_month_revenue = BookingServiceItem.objects.filter(
        booking__business=business,
        booking__created_at__date__gte=start_date,
        booking__created_at__date__lte=end_date
    ).annotate(
        item_total=ExpressionWrapper(
            F('price_at_booking') * F('quantity'),
            output_field=DecimalField()
        )
    ).aggregate(total=Sum('item_total'))['total'] or Decimal('0.00')
    
    # Comparison period revenue
    last_month_revenue = BookingServiceItem.objects.filter(
        booking__business=business,
        booking__created_at__date__gte=comparison_start,
        booking__created_at__date__lte=comparison_end
    ).annotate(
        item_total=ExpressionWrapper(
            F('price_at_booking') * F('quantity'),
            output_field=DecimalField()
        )
    ).aggregate(total=Sum('item_total'))['total'] or Decimal('0.00')
    
    # Revenue growth percentage
    if last_month_revenue > 0:
        revenue_growth = float((this_month_revenue - last_month_revenue) / last_month_revenue * 100)
    else:
        revenue_growth = 100.0 if this_month_revenue > 0 else 0.0
    
    # === BOOKING METRICS ===
    total_bookings = Booking.objects.filter(business=business, created_at__gte=start_date, created_at__lte=end_date).count()
    
    this_month_bookings = Booking.objects.filter(
        business=business,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    last_month_bookings = Booking.objects.filter(
        business=business,
        created_at__date__gte=comparison_start,
        created_at__date__lte=comparison_end
    ).count()
    
    # Booking growth percentage
    if last_month_bookings > 0:
        bookings_growth = int((this_month_bookings - last_month_bookings) / last_month_bookings * 100)
    else:
        bookings_growth = 100 if this_month_bookings > 0 else 0
    
    # Booking status breakdown
    confirmed_bookings = Booking.objects.filter(
        business=business,
        status=BookingStatus.CONFIRMED
    ).count()
    
    cancelled_bookings = Booking.objects.filter(
        business=business,
        status=BookingStatus.CANCELLED
    ).count()
    
    completed_bookings = Booking.objects.filter(
        business=business,
        status=BookingStatus.COMPLETED
    ).count()
    
    # === LEAD METRICS ===
    total_leads = Lead.objects.filter(business=business, created_at__gte=start_date, created_at__lte=end_date).count()
    
    converted_leads = Lead.objects.filter(
        business=business,
        status=LeadStatus.CONVERTED,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).count()
    
    # Conversion rate
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    # Selected period leads
    this_month_leads = Lead.objects.filter(
        business=business,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    last_month_leads = Lead.objects.filter(
        business=business,
        created_at__date__gte=comparison_start,
        created_at__date__lte=comparison_end
    ).count()
    
    # Lead growth percentage
    if last_month_leads > 0:
        leads_growth = int((this_month_leads - last_month_leads) / last_month_leads * 100)
    else:
        leads_growth = 100 if this_month_leads > 0 else 0
    
    # === AVERAGE BOOKING VALUE ===
    if total_bookings > 0:
        avg_booking_value = total_revenue / total_bookings
    else:
        avg_booking_value = Decimal('0.00')
    
    # === TOP SERVICES ===
    top_services = ServiceOffering.objects.filter(
        business=business,
        bookings__created_at__gte=start_date,
        bookings__created_at__lte=end_date
    ).annotate(
        total_bookings=Count('bookings'),
        total_revenue=Sum(
            ExpressionWrapper(
                F('bookings__service_items__price_at_booking') * 
                F('bookings__service_items__quantity'),
                output_field=DecimalField()
            )
        )
    ).filter(total_bookings__gt=0).order_by('-total_revenue')[:5]
    
    # === STAFF PERFORMANCE ===
    staff_performance = StaffMember.objects.filter(
        business=business,
        is_active=True,
        assigned_bookings__created_at__gte=start_date,
        assigned_bookings__created_at__lte=end_date
    ).annotate(
        total_bookings=Count('assigned_bookings'),
        completed_bookings=Count(
            'assigned_bookings',
            filter=Q(assigned_bookings__status=BookingStatus.COMPLETED)
        )
    ).filter(total_bookings__gt=0).order_by('-total_bookings')[:5]
    
    # === LEAD SOURCES ===
    lead_sources = Lead.objects.filter(
        business=business,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('source').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # === LEAD STATUS BREAKDOWN ===
    # All-time lead status counts
    lead_status_new = Lead.objects.filter(
        business=business,
        status=LeadStatus.NEW,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).count()
    
    lead_status_contacted = Lead.objects.filter(
        business=business,
        status__in=[LeadStatus.CONTACTED_BY_PHONE, LeadStatus.CONTACTED_BY_SMS],
        created_at__gte=start_date,
        created_at__lte=end_date
    ).count()
    
    lead_status_qualified = Lead.objects.filter(
        business=business,
        status=LeadStatus.QUALIFIED,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).count()
    
    lead_status_converted = Lead.objects.filter(
        business=business,
        status=LeadStatus.CONVERTED,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).count()
    
    lead_status_lost = Lead.objects.filter(
        business=business,
        status=LeadStatus.LOST,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).count()
    
    # Selected period lead status counts
    lead_status_new_month = Lead.objects.filter(
        business=business,
        status=LeadStatus.NEW,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    lead_status_contacted_month = Lead.objects.filter(
        business=business,
        status__in=[LeadStatus.CONTACTED_BY_PHONE, LeadStatus.CONTACTED_BY_SMS],
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    lead_status_qualified_month = Lead.objects.filter(
        business=business,
        status=LeadStatus.QUALIFIED,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    lead_status_converted_month = Lead.objects.filter(
        business=business,
        status=LeadStatus.CONVERTED,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    lead_status_lost_month = Lead.objects.filter(
        business=business,
        status=LeadStatus.LOST,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    context = {
        'business': business,
        'today': today,
        'start_date': start_date,
        'end_date': end_date,
        
        # Revenue metrics
        'total_revenue': total_revenue,
        'this_month_revenue': this_month_revenue,
        'revenue_growth': revenue_growth,
        
        # Booking metrics
        'total_bookings': total_bookings,
        'this_month_bookings': this_month_bookings,
        'bookings_growth': bookings_growth,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'completed_bookings': completed_bookings,
        
        # Lead metrics
        'total_leads': total_leads,
        'conversion_rate': conversion_rate,
        'this_month_leads': this_month_leads,
        'leads_growth': leads_growth,
        
        # Lead status breakdown
        'lead_status_new': lead_status_new,
        'lead_status_contacted': lead_status_contacted,
        'lead_status_qualified': lead_status_qualified,
        'lead_status_converted': lead_status_converted,
        'lead_status_lost': lead_status_lost,
        'lead_status_new_month': lead_status_new_month,
        'lead_status_contacted_month': lead_status_contacted_month,
        'lead_status_qualified_month': lead_status_qualified_month,
        'lead_status_converted_month': lead_status_converted_month,
        'lead_status_lost_month': lead_status_lost_month,
        
        # Other metrics
        'avg_booking_value': avg_booking_value,
        
        # Performance data
        'top_services': top_services,
        'staff_performance': staff_performance,
        'lead_sources': lead_sources,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def revenue_chart_data(request):
    """
    API endpoint for revenue chart data (last 12 months)
    """
    if not hasattr(request.user, 'business'):
        return JsonResponse({'error': 'No business found'}, status=400)
    
    business = request.user.business
    today = timezone.now().date()
    
    # Get last 12 months
    months_data = []
    labels = []
    
    for i in range(11, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        
        if i == 0:
            month_end = today
        else:
            next_month = month_start + timedelta(days=32)
            month_end = next_month.replace(day=1) - timedelta(days=1)
        
        revenue = BookingServiceItem.objects.filter(
            booking__business=business,
            booking__created_at__gte=month_start,
            booking__created_at__lte=month_end
        ).annotate(
            item_total=ExpressionWrapper(
                F('price_at_booking') * F('quantity'),
                output_field=DecimalField()
            )
        ).aggregate(total=Sum('item_total'))['total'] or Decimal('0.00')
        
        months_data.append(float(revenue))
        labels.append(month_start.strftime('%b %Y'))
    
    return JsonResponse({
        'labels': labels,
        'data': months_data
    })


@login_required
def bookings_chart_data(request):
    """
    API endpoint for bookings chart data (last 30 days)
    """
    if not hasattr(request.user, 'business'):
        return JsonResponse({'error': 'No business found'}, status=400)
    
    business = request.user.business
    today = timezone.now().date()
    
    # Get last 30 days
    days_data = []
    labels = []
    
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        
        bookings_count = Booking.objects.filter(
            business=business,
            created_at__date=day
        ).count()
        
        days_data.append(bookings_count)
        labels.append(day.strftime('%b %d'))
    
    return JsonResponse({
        'labels': labels,
        'data': days_data
    })


@login_required
def lead_source_chart_data(request):
    """
    API endpoint for lead source distribution
    """
    if not hasattr(request.user, 'business'):
        return JsonResponse({'error': 'No business found'}, status=400)
    
    business = request.user.business
    
    lead_sources = Lead.objects.filter(
        business=business
    ).values('source').annotate(
        count=Count('id')
    ).order_by('-count')
    
    labels = [item['source'].replace('_', ' ').title() for item in lead_sources]
    data = [item['count'] for item in lead_sources]
    
    return JsonResponse({
        'labels': labels,
        'data': data
    })


@login_required
def service_popularity_chart_data(request):
    """
    API endpoint for service popularity by revenue
    """
    if not hasattr(request.user, 'business'):
        return JsonResponse({'error': 'No business found'}, status=400)
    
    business = request.user.business
    
    top_services = ServiceOffering.objects.filter(
        business=business
    ).annotate(
        total_revenue=Sum(
            ExpressionWrapper(
                F('bookings__service_items__price_at_booking') * 
                F('bookings__service_items__quantity'),
                output_field=DecimalField()
            )
        )
    ).filter(total_revenue__isnull=False).order_by('-total_revenue')[:5]
    
    labels = [service.name for service in top_services]
    data = [float(service.total_revenue or 0) for service in top_services]
    
    return JsonResponse({
        'labels': labels,
        'data': data
    })


@login_required
def export_analytics(request):
    """
    Export analytics data as CSV
    """
    if not hasattr(request.user, 'business'):
        return HttpResponse('No business found', status=400)
    
    business = request.user.business
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="analytics_{business.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow(['Analytics Report', business.name, timezone.now().strftime('%Y-%m-%d')])
    writer.writerow([])
    
    # Revenue metrics
    writer.writerow(['Revenue Metrics'])
    writer.writerow(['Metric', 'Value'])
    
    total_revenue = BookingServiceItem.objects.filter(
        booking__business=business
    ).annotate(
        item_total=ExpressionWrapper(
            F('price_at_booking') * F('quantity'),
            output_field=DecimalField()
        )
    ).aggregate(total=Sum('item_total'))['total'] or Decimal('0.00')
    
    writer.writerow(['Total Revenue', f'${total_revenue}'])
    writer.writerow([])
    
    # Booking metrics
    writer.writerow(['Booking Metrics'])
    writer.writerow(['Status', 'Count'])
    
    for status in BookingStatus:
        count = Booking.objects.filter(business=business, status=status).count()
        writer.writerow([status.label, count])
    
    writer.writerow([])
    
    # Lead metrics
    writer.writerow(['Lead Metrics'])
    writer.writerow(['Status', 'Count'])
    
    for status in LeadStatus:
        count = Lead.objects.filter(business=business, status=status).count()
        writer.writerow([status.label, count])
    
    return response

