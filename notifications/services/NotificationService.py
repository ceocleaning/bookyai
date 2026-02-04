from services_ai.utils import send_email
from notifications.models import Notification
from django.template.loader import render_to_string
from django.conf import settings
from typing import Optional, Dict, Any, List


class NotificationService:
    """
    Centralized service for handling all notifications in BookyAI.
    Supports both in-app notifications and email notifications.
    """
    
    @staticmethod
    def get_business_users(business):
        """
        Get active users for a business.
        Since Business has OneToOneField with User, returns a list with the business owner.
        
        Args:
            business: Business instance
            
        Returns:
            List of active User instances
        """
        if business.user and business.user.is_active:
            return [business.user]
        return []
    
    @staticmethod
    def create_in_app_notification(
        user,
        title: str,
        message: str,
        notification_type: str,
        business=None,
        related_object_id: Optional[str] = None,
        related_object_type: Optional[str] = None
    ) -> Notification:
        """
        Create an in-app notification for a user.
        
        Args:
            user: User instance to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification (e.g., 'lead_created', 'booking_confirmed')
            business: Business instance (optional)
            related_object_id: ID of related object (optional)
            related_object_type: Type of related object (optional, e.g., 'lead', 'booking', 'invoice')
        
        Returns:
            Notification instance
        """
        notification = Notification.objects.create(
            user=user,
            business=business,
            notification_type=notification_type,
            title=title,
            message=message,
            related_object_id=related_object_id,
            related_object_type=related_object_type
        )
        return notification
    
    @staticmethod
    def send_email_notification(
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Send an email notification using a template.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Path to email template (e.g., 'email/bookings/booking_created.html')
            context: Context dictionary for template rendering
            from_email: Sender email (optional, defaults to settings)
            reply_to: Reply-to email (optional)
            attachments: List of attachment dictionaries (optional)
        
        Returns:
            Dictionary with success status and response
        """
        # Render HTML content from template
        html_content = render_to_string(template_name, context)
        
        # Set default from_email if not provided
        if not from_email:
            from_email = f"BookyAI <noreply@cleaningbizai.com>"
        
        # Send email using the send_email utility
        result = send_email(
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            reply_to=reply_to,
            html_content=html_content,
            attachments=attachments
        )
        
        return result
    
    @staticmethod
    def send_notification(
        user,
        title: str,
        message: str,
        notification_type: str,
        business=None,
        related_object_id: Optional[str] = None,
        related_object_type: Optional[str] = None,
        send_email_flag: bool = True,
        email_subject: Optional[str] = None,
        email_template: Optional[str] = None,
        email_context: Optional[Dict[str, Any]] = None,
        to_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send both in-app and email notifications.
        
        Args:
            user: User instance to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            business: Business instance (optional)
            related_object_id: ID of related object (optional)
            related_object_type: Type of related object (optional)
            send_email_flag: Whether to send email notification (default: True)
            email_subject: Email subject (required if send_email_flag is True)
            email_template: Email template path (required if send_email_flag is True)
            email_context: Email template context (required if send_email_flag is True)
            to_email: Recipient email (optional, defaults to user.email)
        
        Returns:
            Dictionary with notification and email results
        """
        result = {
            'in_app_notification': None,
            'email_result': None
        }
        
        # Create in-app notification
        notification = NotificationService.create_in_app_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            business=business,
            related_object_id=related_object_id,
            related_object_type=related_object_type
        )
        result['in_app_notification'] = notification
        
        # Send email notification if enabled
        if send_email_flag and email_subject and email_template and email_context:
            recipient_email = to_email or user.email
            email_result = NotificationService.send_email_notification(
                to_email=recipient_email,
                subject=email_subject,
                template_name=email_template,
                context=email_context
            )
            result['email_result'] = email_result
        
        return result
    
    @staticmethod
    def get_base_email_context(business=None, user=None) -> Dict[str, Any]:
        """
        Get base context for email templates.
        
        Args:
            business: Business instance (optional)
            user: User instance (optional)
        
        Returns:
            Dictionary with base context
        """
        context = {
            'site_name': 'BookyAI',
            'site_url': settings.BASE_URL,
            'current_year': 2026,
        }
        
        if business:
            context['business'] = business
            context['business_name'] = business.name
        
        if user:
            context['user'] = user
            context['user_name'] = user.get_full_name() if hasattr(user, 'get_full_name') else user.username
        
        return context
