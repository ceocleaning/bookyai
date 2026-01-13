from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from .models import Customer, CustomerBusinessLink
from decimal import Decimal


def customer_required(view_func):
    """
    Decorator to ensure user is a customer.
    Redirects to login if not authenticated or to home if not a customer.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access the customer portal.')
            return redirect('customer:login')
        
        if not hasattr(request.user, 'customer_profile'):
            messages.error(request, 'Access denied. Customer account required.')
            return redirect('core:index')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def get_or_create_customer(email, name, phone, business):
    """
    Get existing customer or create new one.
    Returns (customer, created) tuple.
    Sends welcome email if newly created.
    """
    # Check if user exists
    user = User.objects.filter(email=email).first()
    
    if user and hasattr(user, 'customer_profile'):
        # Existing customer - link to business if not already linked
        customer = user.customer_profile
        link, link_created = CustomerBusinessLink.objects.get_or_create(
            customer=customer,
            business=business
        )
        return customer, False
    
    # Create new customer
    # Split name into first and last
    name_parts = name.split()
    first_name = name_parts[0] if name_parts else ''
    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
    
    # Create user if doesn't exist
    if not user:
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_unusable_password()  # Will be set via email link
        user.save()
    
    # Add to customer group
    customer_group, _ = Group.objects.get_or_create(name='customer')
    user.groups.add(customer_group)
    
    # Create customer profile
    customer = Customer.objects.create(
        user=user,
        phone_number=phone
    )
    
    # Link to business
    CustomerBusinessLink.objects.create(
        customer=customer,
        business=business
    )
    
    # Send welcome email
    send_customer_welcome_email(user, business)
    
    return customer, True


def send_customer_welcome_email(user, business):
    """
    Send welcome email to new customer with password setup link.
    """
    # Generate password reset token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build password setup URL
    # Note: This assumes the request object is available in context
    # For async tasks, you'll need to build the absolute URL differently
    password_setup_path = reverse('customer:set_password', kwargs={'uidb64': uid, 'token': token})
    password_setup_url = f"{settings.SITE_URL}{password_setup_path}"
    
    # Email subject and message
    subject = f'Welcome to {business.name} - Set Up Your Account'
    
    # Plain text message
    message = f'''
Hello {user.first_name},

A booking has been created for you at {business.name}.

To manage your bookings and view your account, please set up your password by clicking the link below:
{password_setup_url}

Once set up, you can:
- View and manage your bookings
- Reschedule or cancel appointments
- View invoices and payment history
- Update your profile information

If you did not request this, please ignore this email.

Best regards,
{business.name}
    '''
    
    # Send email
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        # Log error but don't fail the customer creation
        print(f"Error sending welcome email to {user.email}: {str(e)}")


def get_active_business(request, customer):
    """
    Get the active business for the customer from session.
    Returns the first linked business if none is set in session.
    """
    business_id = request.session.get('active_business_id')
    
    if business_id:
        link = customer.business_links.filter(
            business_id=business_id,
            is_active=True
        ).select_related('business').first()
        
        if link:
            return link.business
    
    # Default to first linked business
    first_link = customer.business_links.filter(
        is_active=True
    ).select_related('business').first()
    
    if first_link:
        request.session['active_business_id'] = first_link.business.id
        return first_link.business
    
    return None


def set_active_business(request, business_id):
    """
    Set the active business in the session.
    """
    request.session['active_business_id'] = business_id


def send_booking_notification_email(booking, event_type):
    """
    Send email notification to customer about booking event.
    
    Args:
        booking: Booking instance
        event_type: Type of event (created, rescheduled, cancelled, reminder)
    """
    if not booking.customer or not booking.customer.email_notifications:
        return
    
    user = booking.customer.user
    business = booking.business
    
    # Email subjects and templates based on event type
    email_config = {
        'created': {
            'subject': f'Booking Confirmation - {business.name}',
            'template': 'customer/emails/booking_created.txt'
        },
        'rescheduled': {
            'subject': f'Booking Rescheduled - {business.name}',
            'template': 'customer/emails/booking_rescheduled.txt'
        },
        'cancelled': {
            'subject': f'Booking Cancelled - {business.name}',
            'template': 'customer/emails/booking_cancelled.txt'
        },
        'reminder': {
            'subject': f'Booking Reminder - {business.name}',
            'template': 'customer/emails/booking_reminder.txt'
        },
    }
    
    config = email_config.get(event_type)
    if not config:
        return
    
    # Context for email template
    context = {
        'user': user,
        'booking': booking,
        'business': business,
    }
    
    # Render email message
    try:
        message = render_to_string(config['template'], context)
        
        send_mail(
            config['subject'],
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending {event_type} email to {user.email}: {str(e)}")
