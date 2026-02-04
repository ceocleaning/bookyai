"""
Lead Created Notification Handler
Sends notifications when a new lead is created.
"""
from notifications.services.NotificationService import NotificationService


def notify_lead_created(lead):
    """
    Send notifications when a new lead is created.
    
    Args:
        lead: Lead instance that was created
    """
    business = lead.business
    
    # Get business owner (Business has OneToOneField with User)
    user = business.user
    if not user or not user.is_active:
        return False
    
    # Prepare notification content
    title = f"New Lead: {lead.get_full_name()}"
    message = f"A new lead has been created from {lead.get_source_display()}. Contact: {lead.email}, {lead.phone}"
    
    # Prepare email context
    email_context = NotificationService.get_base_email_context(business=business)
    email_context.update({
        'lead': lead,
        'lead_name': lead.get_full_name(),
        'lead_email': lead.email,
        'lead_phone': lead.phone,
        'lead_source': lead.get_source_display(),
        'lead_url': f"{email_context['site_url']}/leads/{lead.id}/",
    })
    
    # Send notification to business owner
    NotificationService.send_notification(
        user=user,
        title=title,
        message=message,
        notification_type='lead_created',
        business=business,
        related_object_id=lead.id,
        related_object_type='lead',
        send_email_flag=True,
        email_subject=f"New Lead: {lead.get_full_name()}",
        email_template='email/leads/lead_created.html',
        email_context=email_context
    )
    
    return True
