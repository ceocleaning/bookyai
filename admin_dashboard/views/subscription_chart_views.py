"""
Additional API endpoints for subscription analytics charts
"""

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.db.models import Count

from subscription.models import Subscription, SubscriptionPlan


@staff_member_required
@login_required
def get_mrr_chart_data(request):
    """
    API endpoint to get Monthly Recurring Revenue chart data for the last 12 months
    """
    now = timezone.now()
    labels = []
    revenue_data = []
    
    # Get data for last 12 months
    for i in range(11, -1, -1):
        month_start = (now - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + relativedelta(months=1))
        
        labels.append(month_start.strftime('%b %Y'))
        
        # Get active subscriptions for this month
        subs = Subscription.objects.filter(
            status__in=['active', 'trialing'],
            created_at__lt=month_end
        ).exclude(
            canceled_at__lt=month_start,
            canceled_at__isnull=False
        )
        
        # Calculate MRR for this month
        mrr = Decimal('0.00')
        for sub in subs:
            if sub.plan:
                if sub.plan.billing_period == 'month':
                    mrr += sub.plan.price
                elif sub.plan.billing_period == 'year':
                    mrr += sub.plan.price / 12
        
        revenue_data.append(float(mrr))
    
    return JsonResponse({
        'labels': labels,
        'revenue': revenue_data
    })


@staff_member_required
@login_required
def get_plan_distribution(request):
    """
    API endpoint to get subscription plan distribution for pie chart
    """
    # Get count of active subscriptions per plan
    plan_data = Subscription.objects.filter(
        status__in=['active', 'trialing']
    ).values(
        'plan__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    labels = []
    counts = []
    
    for item in plan_data:
        plan_name = item['plan__name'] or 'No Plan'
        labels.append(plan_name)
        counts.append(item['count'])
    
    # If no data, return empty state
    if not labels:
        labels = ['No Active Subscriptions']
        counts = [1]
    
    return JsonResponse({
        'labels': labels,
        'counts': counts
    })
