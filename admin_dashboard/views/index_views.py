"""
Admin Dashboard Index Views
Handles the main dashboard index page and overview statistics with real data
Supports daily, monthly, and yearly range comparisons
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User
from datetime import timedelta, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta

# Import models
from business.models import Business
from bookings.models import Booking, BookingStatus
from leads.models import Lead
from invoices.models import Invoice, Payment, InvoiceStatus


def calculate_trend_periods(range_type='monthly'):
    """
    Calculate current and previous period based on range type
    Returns: (current_start, current_end, previous_start, previous_end)
    """
    now = timezone.now()
    
    if range_type == 'daily':
        # Today vs Yesterday
        current_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        current_end = now
        previous_start = current_start - timedelta(days=1)
        previous_end = current_start
        
    elif range_type == 'monthly':
        # This month vs Last month
        current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_end = now
        previous_start = (current_start - relativedelta(months=1))
        previous_end = current_start
        
    elif range_type == 'yearly':
        # This year vs Last year
        current_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        current_end = now
        previous_start = (current_start - relativedelta(years=1))
        previous_end = current_start
        
    else:  # default to monthly
        current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_end = now
        previous_start = (current_start - relativedelta(months=1))
        previous_end = current_start
    
    return current_start, current_end, previous_start, previous_end


@staff_member_required
@login_required
def admin_dashboard_index(request):
    """
    Main admin dashboard index page
    Shows overview statistics and key metrics
    """
    
    context = {
        'page_title': 'Admin Dashboard',
    }
    
    return render(request, 'admin_dashboard/index.html', context)


@staff_member_required
@login_required
def get_total_users(request):
    """
    API endpoint to get total users count with date range filtering and trend calculation
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    range_type = request.GET.get('range', 'monthly')  # daily, monthly, yearly
    
    queryset = User.objects.all()
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end + timedelta(days=1)
            queryset = queryset.filter(date_joined__gte=start, date_joined__lt=end)
        except ValueError:
            pass
    
    total = queryset.count()
    
    # Calculate growth based on range type
    current_start, current_end, previous_start, previous_end = calculate_trend_periods(range_type)
    
    current_period = User.objects.filter(
        date_joined__gte=current_start,
        date_joined__lt=current_end
    ).count()
    
    previous_period = User.objects.filter(
        date_joined__gte=previous_start,
        date_joined__lt=previous_end
    ).count()
    
    growth = 0
    if previous_period > 0:
        growth = ((current_period - previous_period) / previous_period) * 100
    elif current_period > 0:
        growth = 100
    
    trend_labels = {
        'daily': 'vs yesterday',
        'monthly': 'vs last month',
        'yearly': 'vs last year'
    }
    
    return JsonResponse({
        'total': total,
        'current_period': current_period,
        'previous_period': previous_period,
        'growth': round(growth, 1),
        'trend': 'up' if growth > 0 else ('down' if growth < 0 else 'neutral'),
        'trend_label': trend_labels.get(range_type, 'vs last month')
    })


@staff_member_required
@login_required
def get_total_businesses(request):
    """
    API endpoint to get total active businesses count with date range filtering and trend calculation
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    range_type = request.GET.get('range', 'monthly')
    
    queryset = Business.objects.filter(is_active=True)
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end + timedelta(days=1)
            queryset = queryset.filter(created_at__gte=start, created_at__lt=end)
        except ValueError:
            pass
    
    total = queryset.count()
    
    current_start, current_end, previous_start, previous_end = calculate_trend_periods(range_type)
    
    current_period = Business.objects.filter(
        is_active=True,
        created_at__gte=current_start,
        created_at__lt=current_end
    ).count()
    
    previous_period = Business.objects.filter(
        is_active=True,
        created_at__gte=previous_start,
        created_at__lt=previous_end
    ).count()
    
    growth = 0
    if previous_period > 0:
        growth = ((current_period - previous_period) / previous_period) * 100
    elif current_period > 0:
        growth = 100
    
    trend_labels = {
        'daily': 'vs yesterday',
        'monthly': 'vs last month',
        'yearly': 'vs last year'
    }
    
    return JsonResponse({
        'total': total,
        'current_period': current_period,
        'previous_period': previous_period,
        'growth': round(growth, 1),
        'trend': 'up' if growth > 0 else ('down' if growth < 0 else 'neutral'),
        'trend_label': trend_labels.get(range_type, 'vs last month')
    })


@staff_member_required
@login_required
def get_total_bookings(request):
    """
    API endpoint to get total bookings count with date range filtering and trend calculation
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    range_type = request.GET.get('range', 'monthly')
    
    queryset = Booking.objects.all()
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end + timedelta(days=1)
            queryset = queryset.filter(created_at__gte=start, created_at__lt=end)
        except ValueError:
            pass
    
    total = queryset.count()
    confirmed = queryset.filter(status=BookingStatus.CONFIRMED).count()
    completed = queryset.filter(status=BookingStatus.COMPLETED).count()
    cancelled = queryset.filter(status=BookingStatus.CANCELLED).count()
    
    current_start, current_end, previous_start, previous_end = calculate_trend_periods(range_type)
    
    current_period = Booking.objects.filter(
        created_at__gte=current_start,
        created_at__lt=current_end
    ).count()
    
    previous_period = Booking.objects.filter(
        created_at__gte=previous_start,
        created_at__lt=previous_end
    ).count()
    
    growth = 0
    if previous_period > 0:
        growth = ((current_period - previous_period) / previous_period) * 100
    elif current_period > 0:
        growth = 100
    
    trend_labels = {
        'daily': 'vs yesterday',
        'monthly': 'vs last month',
        'yearly': 'vs last year'
    }
    
    return JsonResponse({
        'total': total,
        'confirmed': confirmed,
        'completed': completed,
        'cancelled': cancelled,
        'current_period': current_period,
        'previous_period': previous_period,
        'growth': round(growth, 1),
        'trend': 'up' if growth > 0 else ('down' if growth < 0 else 'neutral'),
        'trend_label': trend_labels.get(range_type, 'vs last month')
    })


@staff_member_required
@login_required
def get_total_leads(request):
    """
    API endpoint to get total leads count with date range filtering and trend calculation
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    range_type = request.GET.get('range', 'monthly')
    
    queryset = Lead.objects.all()
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end + timedelta(days=1)
            queryset = queryset.filter(created_at__gte=start, created_at__lt=end)
        except ValueError:
            pass
    
    total = queryset.count()
    
    current_start, current_end, previous_start, previous_end = calculate_trend_periods(range_type)
    
    current_period = Lead.objects.filter(
        created_at__gte=current_start,
        created_at__lt=current_end
    ).count()
    
    previous_period = Lead.objects.filter(
        created_at__gte=previous_start,
        created_at__lt=previous_end
    ).count()
    
    growth = 0
    if previous_period > 0:
        growth = ((current_period - previous_period) / previous_period) * 100
    elif current_period > 0:
        growth = 100
    
    trend_labels = {
        'daily': 'vs yesterday',
        'monthly': 'vs last month',
        'yearly': 'vs last year'
    }
    
    return JsonResponse({
        'total': total,
        'current_period': current_period,
        'previous_period': previous_period,
        'growth': round(growth, 1),
        'trend': 'up' if growth > 0 else ('down' if growth < 0 else 'neutral'),
        'trend_label': trend_labels.get(range_type, 'vs last month')
    })


@staff_member_required
@login_required
def get_total_invoices(request):
    """
    API endpoint to get total invoices count with date range filtering and trend calculation
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    range_type = request.GET.get('range', 'monthly')
    
    queryset = Invoice.objects.all()
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end + timedelta(days=1)
            queryset = queryset.filter(created_at__gte=start, created_at__lt=end)
        except ValueError:
            pass
    
    total = queryset.count()
    paid = queryset.filter(status=InvoiceStatus.PAID).count()
    pending = queryset.filter(status=InvoiceStatus.PENDING).count()
    overdue = queryset.filter(status=InvoiceStatus.OVERDUE).count()
    
    current_start, current_end, previous_start, previous_end = calculate_trend_periods(range_type)
    
    current_period = Invoice.objects.filter(
        created_at__gte=current_start,
        created_at__lt=current_end
    ).count()
    
    previous_period = Invoice.objects.filter(
        created_at__gte=previous_start,
        created_at__lt=previous_end
    ).count()
    
    growth = 0
    if previous_period > 0:
        growth = ((current_period - previous_period) / previous_period) * 100
    elif current_period > 0:
        growth = 100
    
    trend_labels = {
        'daily': 'vs yesterday',
        'monthly': 'vs last month',
        'yearly': 'vs last year'
    }
    
    return JsonResponse({
        'total': total,
        'paid': paid,
        'pending': pending,
        'overdue': overdue,
        'current_period': current_period,
        'previous_period': previous_period,
        'growth': round(growth, 1),
        'trend': 'up' if growth > 0 else ('down' if growth < 0 else 'neutral'),
        'trend_label': trend_labels.get(range_type, 'vs last month')
    })


@staff_member_required
@login_required
def get_total_payments(request):
    """
    API endpoint to get total payments count and amount with date range filtering and trend calculation
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    range_type = request.GET.get('range', 'monthly')
    
    queryset = Payment.objects.filter(is_refunded=False)
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end + timedelta(days=1)
            queryset = queryset.filter(payment_date__gte=start, payment_date__lt=end)
        except ValueError:
            pass
    
    total_count = queryset.count()
    total_amount = queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    current_start, current_end, previous_start, previous_end = calculate_trend_periods(range_type)
    
    current_period = Payment.objects.filter(
        is_refunded=False,
        payment_date__gte=current_start,
        payment_date__lt=current_end
    ).count()
    
    previous_period = Payment.objects.filter(
        is_refunded=False,
        payment_date__gte=previous_start,
        payment_date__lt=previous_end
    ).count()
    
    growth = 0
    if previous_period > 0:
        growth = ((current_period - previous_period) / previous_period) * 100
    elif current_period > 0:
        growth = 100
    
    trend_labels = {
        'daily': 'vs yesterday',
        'monthly': 'vs last month',
        'yearly': 'vs last year'
    }
    
    return JsonResponse({
        'total_count': total_count,
        'total_amount': float(total_amount),
        'current_period': current_period,
        'previous_period': previous_period,
        'growth': round(float(growth), 1),
        'trend': 'up' if growth > 0 else ('down' if growth < 0 else 'neutral'),
        'trend_label': trend_labels.get(range_type, 'vs last month')
    })


@staff_member_required
@login_required
def get_client_revenue(request):
    """
    API endpoint to get total revenue from client payments with trend calculation
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    range_type = request.GET.get('range', 'monthly')
    
    queryset = Payment.objects.filter(is_refunded=False)
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end + timedelta(days=1)
            queryset = queryset.filter(payment_date__gte=start, payment_date__lt=end)
        except ValueError:
            pass
    
    total_revenue = queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    current_start, current_end, previous_start, previous_end = calculate_trend_periods(range_type)
    
    current_period = Payment.objects.filter(
        is_refunded=False,
        payment_date__gte=current_start,
        payment_date__lt=current_end
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    previous_period = Payment.objects.filter(
        is_refunded=False,
        payment_date__gte=previous_start,
        payment_date__lt=previous_end
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    growth = 0
    if previous_period > 0:
        growth = ((current_period - previous_period) / previous_period) * 100
    elif current_period > 0:
        growth = 100
    
    trend_labels = {
        'daily': 'vs yesterday',
        'monthly': 'vs last month',
        'yearly': 'vs last year'
    }
    
    return JsonResponse({
        'total_revenue': float(total_revenue),
        'current_period': float(current_period),
        'previous_period': float(previous_period),
        'growth': round(float(growth), 1),
        'trend': 'up' if growth > 0 else ('down' if growth < 0 else 'neutral'),
        'trend_label': trend_labels.get(range_type, 'vs last month')
    })


@staff_member_required
@login_required
def get_saas_revenue(request):
    """
    API endpoint to get SaaS subscription revenue
    Calculates MRR (Monthly Recurring Revenue) from active subscriptions
    """
    from subscription.models import Subscription
    
    range_type = request.GET.get('range', 'monthly')
    
    # Get all active subscriptions
    active_subs = Subscription.objects.filter(status__in=['active', 'trialing'])
    
    # Calculate total MRR
    total_mrr = Decimal('0.00')
    for sub in active_subs:
        if sub.plan:
            if sub.plan.billing_period == 'month':
                total_mrr += sub.plan.price
            elif sub.plan.billing_period == 'year':
                # Convert yearly to monthly
                total_mrr += sub.plan.price / 12
    
    # Calculate growth
    current_start, current_end, previous_start, previous_end = calculate_trend_periods(range_type)
    
    # Current period subscriptions
    current_subs = Subscription.objects.filter(
        status__in=['active', 'trialing'],
        created_at__gte=current_start,
        created_at__lt=current_end
    )
    
    current_revenue = Decimal('0.00')
    for sub in current_subs:
        if sub.plan:
            if sub.plan.billing_period == 'month':
                current_revenue += sub.plan.price
            elif sub.plan.billing_period == 'year':
                current_revenue += sub.plan.price / 12
    
    # Previous period subscriptions
    previous_subs = Subscription.objects.filter(
        status__in=['active', 'trialing'],
        created_at__gte=previous_start,
        created_at__lt=previous_end
    )
    
    previous_revenue = Decimal('0.00')
    for sub in previous_subs:
        if sub.plan:
            if sub.plan.billing_period == 'month':
                previous_revenue += sub.plan.price
            elif sub.plan.billing_period == 'year':
                previous_revenue += sub.plan.price / 12
    
    growth = 0
    if previous_revenue > 0:
        growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
    elif current_revenue > 0:
        growth = 100
    
    trend_labels = {
        'daily': 'vs yesterday',
        'monthly': 'vs last month',
        'yearly': 'vs last year'
    }
    
    return JsonResponse({
        'total_revenue': float(total_mrr),
        'active_subscriptions': active_subs.count(),
        'current_period': float(current_revenue),
        'previous_period': float(previous_revenue),
        'growth': round(float(growth), 1),
        'trend': 'up' if growth > 0 else ('down' if growth < 0 else 'neutral'),
        'trend_label': trend_labels.get(range_type, 'vs last month')
    })


@staff_member_required
@login_required
def get_total_subscriptions(request):
    """
    API endpoint to get total subscriptions count with trend calculation
    """
    from subscription.models import Subscription
    
    range_type = request.GET.get('range', 'monthly')
    
    total = Subscription.objects.count()
    
    current_start, current_end, previous_start, previous_end = calculate_trend_periods(range_type)
    
    current_period = Subscription.objects.filter(
        created_at__gte=current_start,
        created_at__lt=current_end
    ).count()
    
    previous_period = Subscription.objects.filter(
        created_at__gte=previous_start,
        created_at__lt=previous_end
    ).count()
    
    growth = 0
    if previous_period > 0:
        growth = ((current_period - previous_period) / previous_period) * 100
    elif current_period > 0:
        growth = 100
    
    trend_labels = {
        'daily': 'vs yesterday',
        'monthly': 'vs last month',
        'yearly': 'vs last year'
    }
    
    return JsonResponse({
        'total': total,
        'current_period': current_period,
        'previous_period': previous_period,
        'growth': round(growth, 1),
        'trend': 'up' if growth > 0 else ('down' if growth < 0 else 'neutral'),
        'trend_label': trend_labels.get(range_type, 'vs last month')
    })


@staff_member_required
@login_required
def get_active_subscriptions(request):
    """
    API endpoint to get active subscriptions count with trend calculation
    """
    from subscription.models import Subscription
    
    range_type = request.GET.get('range', 'monthly')
    
    total = Subscription.objects.filter(status__in=['active', 'trialing']).count()
    
    current_start, current_end, previous_start, previous_end = calculate_trend_periods(range_type)
    
    current_period = Subscription.objects.filter(
        status__in=['active', 'trialing'],
        created_at__gte=current_start,
        created_at__lt=current_end
    ).count()
    
    previous_period = Subscription.objects.filter(
        status__in=['active', 'trialing'],
        created_at__gte=previous_start,
        created_at__lt=previous_end
    ).count()
    
    growth = 0
    if previous_period > 0:
        growth = ((current_period - previous_period) / previous_period) * 100
    elif current_period > 0:
        growth = 100
    
    trend_labels = {
        'daily': 'vs yesterday',
        'monthly': 'vs last month',
        'yearly': 'vs last year'
    }
    
    return JsonResponse({
        'total': total,
        'current_period': current_period,
        'previous_period': previous_period,
        'growth': round(growth, 1),
        'trend': 'up' if growth > 0 else ('down' if growth < 0 else 'neutral'),
        'trend_label': trend_labels.get(range_type, 'vs last month')
    })


@staff_member_required
@login_required
def get_dashboard_chart_data(request):
    """
    API endpoint to get chart data for revenue and bookings over time
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 30 days if no date range provided
    if not start_date or not end_date:
        end = timezone.now()
        start = end - timedelta(days=30)
    else:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            end = timezone.now()
            start = end - timedelta(days=30)
    
    # Generate daily data points
    days = (end.date() - start.date()).days + 1
    labels = []
    revenue_data = []
    bookings_data = []
    
    for i in range(days):
        current_date = start.date() + timedelta(days=i)
        next_date = current_date + timedelta(days=1)
        
        labels.append(current_date.strftime('%b %d'))
        
        # Get revenue for this day
        daily_revenue = Payment.objects.filter(
            is_refunded=False,
            payment_date__gte=current_date,
            payment_date__lt=next_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        revenue_data.append(float(daily_revenue))
        
        # Get bookings for this day
        daily_bookings = Booking.objects.filter(
            created_at__gte=current_date,
            created_at__lt=next_date
        ).count()
        bookings_data.append(daily_bookings)
    
    return JsonResponse({
        'labels': labels,
        'revenue': revenue_data,
        'bookings': bookings_data
    })
