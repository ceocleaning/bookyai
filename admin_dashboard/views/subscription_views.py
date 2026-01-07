"""
Subscription Plan Management Views for Admin Dashboard
"""
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from subscription.models import SubscriptionPlan, Subscription
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


@staff_member_required
def subscription_plan_list(request):
    """List all subscription plans"""
    plans = SubscriptionPlan.objects.all().annotate(
        subscriber_count=Count('subscriptions')
    ).order_by('price')
    
    context = {
        'plans': plans,
        'total_plans': plans.count(),
        'active_plans': plans.filter(is_active=True).count(),
    }
    return render(request, 'admin_dashboard/subscription/plan_list.html', context)


@staff_member_required
def subscription_plan_add(request):
    """Add a new subscription plan"""
    if request.method == 'POST':
        try:
            # Parse features from JSON
            features_json = request.POST.get('features', '[]')
            features = json.loads(features_json) if features_json else []
            
            plan = SubscriptionPlan.objects.create(
                stripe_price_id=request.POST.get('stripe_price_id'),
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                price=Decimal(request.POST.get('price', '0')),
                billing_period=request.POST.get('billing_period', 'month'),
                features=features,
                is_active=request.POST.get('is_active') == 'on'
            )
            
            messages.success(request, f'Subscription plan "{plan.name}" created successfully!')
            return redirect('admin_dashboard:subscription_plan_detail', plan_id=plan.id)
            
        except Exception as e:
            messages.error(request, f'Error creating plan: {str(e)}')
    
    context = {
        'billing_periods': SubscriptionPlan.BILLING_PERIOD_CHOICES,
    }
    return render(request, 'admin_dashboard/subscription/plan_add.html', context)


@staff_member_required
def subscription_plan_detail(request, plan_id):
    """View subscription plan details"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    # Get subscribers for this plan
    subscribers = Subscription.objects.filter(plan=plan).select_related('business', 'business__user')
    
    # Calculate statistics
    active_subscribers = subscribers.filter(status__in=['active', 'trialing']).count()
    total_subscribers = subscribers.count()
    
    context = {
        'plan': plan,
        'subscribers': subscribers[:10],  # Show first 10
        'total_subscribers': total_subscribers,
        'active_subscribers': active_subscribers,
        'monthly_revenue': plan.price * active_subscribers if plan.billing_period == 'month' else 0,
        'yearly_revenue': plan.price * active_subscribers if plan.billing_period == 'year' else 0,
    }
    return render(request, 'admin_dashboard/subscription/plan_detail.html', context)


@staff_member_required
def subscription_plan_edit(request, plan_id):
    """Edit subscription plan"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    if request.method == 'POST':
        try:
            # Parse features from JSON
            features_json = request.POST.get('features', '[]')
            features = json.loads(features_json) if features_json else []
            
            plan.stripe_price_id = request.POST.get('stripe_price_id')
            plan.name = request.POST.get('name')
            plan.description = request.POST.get('description', '')
            plan.price = Decimal(request.POST.get('price', '0'))
            plan.billing_period = request.POST.get('billing_period', 'month')
            plan.features = features
            plan.is_active = request.POST.get('is_active') == 'on'
            plan.save()
            
            messages.success(request, f'Plan "{plan.name}" updated successfully!')
            return redirect('admin_dashboard:subscription_plan_detail', plan_id=plan.id)
            
        except Exception as e:
            messages.error(request, f'Error updating plan: {str(e)}')
    
    context = {
        'plan': plan,
        'billing_periods': SubscriptionPlan.BILLING_PERIOD_CHOICES,
        'features_json': json.dumps(plan.features),
    }
    return render(request, 'admin_dashboard/subscription/plan_edit.html', context)


@staff_member_required
def subscription_plan_delete(request, plan_id):
    """Delete subscription plan"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    # Check if plan has active subscribers
    active_subscribers = Subscription.objects.filter(
        plan=plan,
        status__in=['active', 'trialing']
    ).count()
    
    if active_subscribers > 0:
        messages.error(
            request,
            f'Cannot delete plan "{plan.name}" - it has {active_subscribers} active subscribers.'
        )
        return redirect('admin_dashboard:subscription_plan_detail', plan_id=plan.id)
    
    if request.method == 'POST':
        plan_name = plan.name
        plan.delete()
        messages.success(request, f'Plan "{plan_name}" deleted successfully!')
        return redirect('admin_dashboard:subscription_plan_list')
    
    context = {
        'plan': plan,
    }
    return render(request, 'admin_dashboard/subscription/plan_delete.html', context)


@staff_member_required
def subscription_plan_toggle_status(request, plan_id):
    """Toggle plan active status"""
    if request.method == 'POST':
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)
        plan.is_active = not plan.is_active
        plan.save()
        
        status = 'activated' if plan.is_active else 'deactivated'
        messages.success(request, f'Plan "{plan.name}" {status} successfully!')
        
        return JsonResponse({
            'success': True,
            'is_active': plan.is_active,
            'message': f'Plan {status}'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


@staff_member_required
def subscription_list(request):
    """List all subscriptions"""
    subscriptions = Subscription.objects.select_related(
        'business', 'business__user', 'plan'
    ).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        subscriptions = subscriptions.filter(status=status_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        subscriptions = subscriptions.filter(
            Q(business__name__icontains=search_query) |
            Q(business__user__email__icontains=search_query) |
            Q(stripe_customer_id__icontains=search_query)
        )
    
    # Statistics
    total_subscriptions = Subscription.objects.count()
    active_subscriptions = Subscription.objects.filter(status__in=['active', 'trialing']).count()
    
    context = {
        'subscriptions': subscriptions[:50],  # Paginate in production
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'status_choices': Subscription.STATUS_CHOICES,
        'current_status': status_filter,
        'search_query': search_query,
    }
    return render(request, 'admin_dashboard/subscription/subscription_list.html', context)


@staff_member_required
def subscription_detail(request, subscription_id):
    """View detailed subscription information including invoices"""
    subscription = get_object_or_404(
        Subscription.objects.select_related('business', 'business__user', 'plan'),
        id=subscription_id
    )
    
    # Fetch invoices from Stripe
    invoices = []
    if subscription.stripe_customer_id:
        try:
            stripe_invoices = stripe.Invoice.list(
                customer=subscription.stripe_customer_id,
                limit=10
            )
            invoices = stripe_invoices.data
        except Exception as e:
            logger.error(f"Error fetching invoices: {str(e)}")
            messages.warning(request, "Unable to fetch invoice history from Stripe.")
    
    # Fetch upcoming invoice
    upcoming_invoice = None
    if subscription.stripe_subscription_id and subscription.status in ['active', 'trialing']:
        try:
            upcoming_invoice = stripe.Invoice.upcoming(
                subscription=subscription.stripe_subscription_id
            )
        except Exception as e:
            logger.debug(f"No upcoming invoice: {str(e)}")
    
    context = {
        'subscription': subscription,
        'invoices': invoices,
        'upcoming_invoice': upcoming_invoice,
    }
    return render(request, 'admin_dashboard/subscription/subscription_detail.html', context)


@staff_member_required
def subscription_cancel(request, subscription_id):
    """Cancel a subscription in Stripe"""
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        cancel_immediately = request.POST.get('cancel_immediately') == 'on'
        
        try:
            if subscription.stripe_subscription_id:
                # Cancel in Stripe
                if cancel_immediately:
                    stripe.Subscription.delete(subscription.stripe_subscription_id)
                    messages.success(request, f'Subscription for {subscription.business.name} canceled immediately.')
                else:
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                    messages.success(request, f'Subscription for {subscription.business.name} will cancel at period end.')
                
                return redirect('admin_dashboard:subscription_detail', subscription_id=subscription.id)
            else:
                messages.error(request, 'No Stripe subscription ID found.')
                return redirect('admin_dashboard:subscription_detail', subscription_id=subscription.id)
                
        except Exception as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            messages.error(request, f'Error canceling subscription: {str(e)}')
            return redirect('admin_dashboard:subscription_detail', subscription_id=subscription.id)
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'admin_dashboard/subscription/subscription_cancel.html', context)


@staff_member_required
def subscription_delete(request, subscription_id):
    """Delete a local subscription record (does NOT cancel in Stripe)"""
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        business_name = subscription.business.name
        subscription.delete()
        messages.success(request, f'Subscription record for {business_name} deleted from local database.')
        return redirect('admin_dashboard:subscription_list')
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'admin_dashboard/subscription/subscription_delete.html', context)
