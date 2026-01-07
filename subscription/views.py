import stripe
import logging
import json
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
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
        subscription = Subscription.objects.get(business=business)
        
        if not subscription.stripe_customer_id:
            messages.warning(request, "No active billing account found.")
            return redirect('pricing')
            
        # Create billing portal session
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=request.build_absolute_uri(reverse('index'))
        )
        
        return redirect(session.url)
        
    except Subscription.DoesNotExist:
        messages.info(request, "You don't have an active subscription yet.")
        return redirect('pricing')
    except Exception as e:
        logger.error(f"Error creating billing portal session: {str(e)}")
        messages.error(request, "Unable to access billing portal. Please try again later.")
        return redirect('index')
