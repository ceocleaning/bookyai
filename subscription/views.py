import stripe
import logging
import json
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import WebhookEvent, Subscription
from . import webhook_handlers

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Stripe webhook endpoint.
    Verifies signature and dispatches events to handlers.
    Idempotent: prevents processing the same event twice.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None
    
    # Check if webhook secret is configured
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET is not configured in settings")
        return JsonResponse({
            'error': 'Webhook secret not configured. Please add STRIPE_WEBHOOK_SECRET to your .env file.'
        }, status=500)
    
    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid webhook payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid webhook signature: {str(e)}")
        return HttpResponse(status=400)
    
    # Idempotency check
    event_id = event['id']
    event_type = event['type']
    
    if WebhookEvent.objects.filter(stripe_event_id=event_id).exists():
        logger.info(f"Duplicate webhook event ignored: {event_id} ({event_type})")
        return HttpResponse(status=200)
    
    # Log event
    logger.info(f"Processing webhook event: {event_id} ({event_type})")
    
    try:
        # Dispatch to handler based on event type
        if event_type == 'checkout.session.completed':
            webhook_handlers.handle_checkout_session_completed(event)
        
        elif event_type == 'customer.subscription.created':
            webhook_handlers.handle_subscription_created(event)
        
        elif event_type == 'customer.subscription.updated':
            webhook_handlers.handle_subscription_updated(event)
            
        elif event_type == 'customer.subscription.deleted':
            webhook_handlers.handle_subscription_deleted(event)
            
        elif event_type == 'invoice.payment_failed':
            webhook_handlers.handle_invoice_payment_failed(event)
            
        elif event_type == 'invoice.payment_succeeded':
            webhook_handlers.handle_invoice_payment_succeeded(event)
            
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        # Record processed event
        WebhookEvent.objects.create(
            stripe_event_id=event_id,
            event_type=event_type,
            payload=event
        )
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error processing webhook {event_id}: {str(e)}")
        # Return 500 to prompt Stripe to retry later if it was a transient error
        # Or return 200 to acknowledge receipt if the error is permanent/application logic
        # For now returning 200 to prevent Stripe retries loop on buggy code, but logging error
        return HttpResponse(status=200)


@login_required
def billing_portal(request):
    """
    Redirects user to Stripe Customer Portal to manage subscription.
    """
    user = request.user
    
    try:
        business = user.business
    except AttributeError:
        messages.error(request, "No business account found.")
        return redirect('index')
        
    try:
        # Get the active subscription for this business
        subscription = Subscription.get_active_subscription(business)
        
        if not subscription or not subscription.stripe_customer_id:
            messages.warning(request, "No active billing account found.")
            return redirect('pricing')
            
        # Create billing portal session
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=request.build_absolute_uri(reverse('index'))
        )
        
        return redirect(session.url)
        
    except Exception as e:
        logger.error(f"Error creating billing portal session: {str(e)}")
        messages.error(request, "Unable to access billing portal. Please try again later.")
        return redirect('index')


@login_required
def subscription_management(request):
    """
    Subscription management page for users.
    Shows current subscription, history, and available plans.
    """
    user = request.user
    
    try:
        business = user.business
    except AttributeError:
        messages.error(request, "No business account found.")
        return redirect('index')
    
    # Get active subscription
    active_subscription = Subscription.get_active_subscription(business)
    
    # Get subscription history (all subscriptions for this business)
    subscription_history = Subscription.objects.filter(
        business=business
    ).order_by('-created_at')
    
    # Get available plans
    from .models import SubscriptionPlan
    available_plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    
    # Get upcoming invoice if there's an active subscription
    upcoming_invoice = None
    invoices = []
    
    if active_subscription and active_subscription.stripe_subscription_id:
        try:
            # Get upcoming invoice
            upcoming_invoice = stripe.Invoice.create_preview(
                customer=active_subscription.stripe_customer_id,
                subscription=active_subscription.stripe_subscription_id,
            )
            
            # Get invoice history
            invoices_response = stripe.Invoice.list(
                customer=active_subscription.stripe_customer_id,
                subscription=active_subscription.stripe_subscription_id,
                limit=10
            )
            
            # Convert invoice timestamps to datetime objects
            from datetime import datetime, timezone as dt_timezone
            invoices = []
            for invoice in invoices_response.data:
                # Convert Unix timestamp to datetime
                invoice_dict = invoice.to_dict()
                if invoice_dict.get('created'):
                    invoice_dict['created_datetime'] = datetime.fromtimestamp(
                        invoice_dict['created'], tz=dt_timezone.utc
                    )
                invoices.append(invoice_dict)
            
        except stripe.error.StripeError as e:
            logger.error(f"Error fetching Stripe data: {str(e)}")
    
    context = {
        'active_subscription': active_subscription,
        'subscription_history': subscription_history,
        'available_plans': available_plans,
        'upcoming_invoice': upcoming_invoice,
        'invoices': invoices,
    }
    
    return render(request, 'subscription/manage.html', context)


@login_required
def cancel_subscription(request):
    """
    Cancel user's subscription at the end of the current billing period.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('subscription:manage')
    
    user = request.user
    
    try:
        business = user.business
    except AttributeError:
        messages.error(request, "No business account found.")
        return redirect('index')
    
    # Get active subscription
    active_subscription = Subscription.get_active_subscription(business)
    
    if not active_subscription or not active_subscription.stripe_subscription_id:
        messages.warning(request, "No active subscription found to cancel.")
        return redirect('subscription:manage')
    
    try:
        # Cancel subscription at period end via Stripe
        stripe.Subscription.modify(
            active_subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        # Update local record
        active_subscription.cancel_at_period_end = True
        active_subscription.save()
        
        messages.success(
            request, 
            f"Your subscription has been scheduled for cancellation at the end of the current billing period ({active_subscription.current_period_end.strftime('%B %d, %Y')})."
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        messages.error(request, "Unable to cancel subscription. Please try again or contact support.")
    except Exception as e:
        logger.error(f"Unexpected error canceling subscription: {str(e)}")
        messages.error(request, "An unexpected error occurred. Please try again.")
    
    return redirect('subscription:manage')


@login_required
def create_checkout_session(request, plan_id):
    """
    Create a Stripe Checkout session for subscribing to a plan.
    """
    user = request.user
    
    try:
        business = user.business
    except AttributeError:
        messages.error(request, "No business account found.")
        return redirect('index')
    
    # Get the plan
    from .models import SubscriptionPlan
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        messages.error(request, "Invalid plan selected.")
        return redirect('subscription:manage')
    
    # Get active subscription
    active_subscription = Subscription.get_active_subscription(business)
    
    try:
        # Prepare checkout session parameters
        checkout_params = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price': plan.stripe_price_id,
                'quantity': 1,
            }],
            'mode': 'subscription',
            'success_url': request.build_absolute_uri(reverse('subscription:manage')) + '?session_id={CHECKOUT_SESSION_ID}',
            'cancel_url': request.build_absolute_uri(reverse('subscription:manage')),
            'client_reference_id': str(business.id),
        }
        
        # If user already has a Stripe customer ID, use it
        # Otherwise, use customer_email (Stripe will create a new customer)
        if active_subscription and active_subscription.stripe_customer_id:
            checkout_params['customer'] = active_subscription.stripe_customer_id
            
            # If they have an active subscription, this will be an upgrade/downgrade
            # Cancel the old subscription in Stripe immediately
            if active_subscription.stripe_subscription_id:
                try:
                    # Cancel the old subscription immediately (not at period end)
                    stripe.Subscription.delete(active_subscription.stripe_subscription_id)
                    logger.info(f"Canceled old subscription {active_subscription.stripe_subscription_id} for upgrade")
                    
                    # Mark it as ended in our database
                    active_subscription.end_subscription()
                    active_subscription.status = 'canceled'
                    active_subscription.save()
                    
                except stripe.error.StripeError as e:
                    logger.error(f"Error canceling old subscription: {str(e)}")
                    # Continue anyway - the webhook will handle cleanup
                
        else:
            # New customer - use email
            checkout_params['customer_email'] = user.email
        
        # Create Stripe Checkout Session
        session = stripe.checkout.Session.create(**checkout_params)
        
        # Redirect to Stripe Checkout
        return redirect(session.url)
        
    except stripe.error.StripeError as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        messages.error(request, "Unable to create checkout session. Please try again or contact support.")
        return redirect('subscription:manage')
    except Exception as e:
        logger.error(f"Unexpected error creating checkout session: {str(e)}")
        messages.error(request, "An unexpected error occurred. Please try again.")
        return redirect('subscription:manage')
