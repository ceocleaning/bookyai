"""
Email verification utilities for business registration.
This module provides functions to handle OTP generation, verification, and email sending.
"""

from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction

from .models import EmailVerification
from services_ai.utils import send_email
from business.models import Business

def create_verification(user, email):
    """
    Create a new email verification record or refresh an existing one.
    
    Args:
        user: User object
        email: Email address to verify
        
    Returns:
        EmailVerification object with new OTP
    """
    # Check if a verification already exists for this user and email
    try:
        verification = EmailVerification.objects.get(user=user, email=email)
        # If it exists, refresh the OTP
        otp = verification.refresh_otp()
    except EmailVerification.DoesNotExist:
        # Create a new verification record
        otp = EmailVerification.generate_otp()
        verification = EmailVerification.objects.create(
            user=user,
            email=email,
            otp=otp,
            otp_expiry=timezone.now() + timezone.timedelta(minutes=30)
        )
    
    return verification

def verify_otp(user, email, otp):
    """
    Verify the OTP for a user's email.
    
    Args:
        user: User object
        email: Email address to verify
        otp: OTP to verify
        
    Returns:
        tuple: (is_verified, message)
    """
    try:
        verification = EmailVerification.objects.get(user=user, email=email)
        
        # Check if already verified
        if verification.is_verified:
            return True, "Email already verified"
        
        # Check if OTP is expired
        if verification.is_expired:
            return False, "OTP has expired. Please request a new one."
        
        # Check if max attempts reached
        if verification.max_attempts_reached:
            return False, "Maximum verification attempts reached. Please request a new OTP."
        
        # Increment attempts
        verification.attempts += 1
        verification.save()
        
        # Check if OTP matches
        if verification.otp == otp:
            verification.is_verified = True
            verification.save()
            return True, "Email verified successfully"
        else:
            remaining = verification.max_attempts - verification.attempts
            return False, f"Invalid OTP. {remaining} attempts remaining."
            
    except EmailVerification.DoesNotExist:
        return False, "No verification found for this email. Please request a new OTP."

def resend_otp(user, email):
    """
    Resend OTP for a user's email if allowed.
    
    Args:
        user: User object
        email: Email address
        
    Returns:
        tuple: (success, message)
    """
    try:
        verification = EmailVerification.objects.get(user=user, email=email)
        
        # Check if already verified
        if verification.is_verified:
            return False, "Email already verified"
        
        # Check if can resend
        if not verification.can_resend:
            time_diff = (verification.otp_created_at + timezone.timedelta(minutes=1)) - timezone.now()
            seconds = max(1, int(time_diff.total_seconds()))
            return False, f"Please wait {seconds} seconds before requesting a new OTP."
        
        # Refresh OTP
        verification.refresh_otp()
        
        # Send OTP email
        send_verification_email(user, email, verification.otp)
        
        return True, "New OTP sent successfully"
        
    except EmailVerification.DoesNotExist:
        # Create new verification
        verification = create_verification(user, email)
        
        # Send OTP email
        send_verification_email(user, email, verification.otp)
        
        return True, "OTP sent successfully"

def send_verification_email(user, email, otp):
    """
    Send verification email with OTP.
    
    Args:
        user: User object
        email: Email address to send to
        otp: OTP to include in the email
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Get business if it exists
    business = None
    try:
        business = Business.objects.get(user=user)
    except Business.DoesNotExist:
        pass
    
    # Prepare context for email template
    context = {
        'user': user,
        'otp': otp,
        'business_name': business.name if business else "Your Business",
        'expiry_minutes': 30,
    }
    
    # Render email template
    html_content = render_to_string('emails/otp_verification.html', context)
    
    # Send email using custom send_email function
    subject = "Verify Your Email Address"
    from_email = f"{business.name if business else 'Booky AI'} <noreply@trackifye.com>"
    
    try:
        result = send_email(
            from_email=from_email,
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=f"Your OTP is: {otp}. It will expire in 30 minutes."
        )
        return result.get('success', False) if result else False
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

