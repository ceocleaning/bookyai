from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.shortcuts import get_object_or_404


User = get_user_model()

class Notification(models.Model):
    '''
    This model is used to store in-App notifications only for users.
    '''
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    business = models.ForeignKey('business.Business', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=200, null=True, blank=True)

    title = models.CharField(max_length=255)
    message = models.TextField()
    related_object_id = models.CharField(max_length=50, null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()
    
    def get_time_since(self):
        """Return a human-readable string representing time since notification was created"""
        now = timezone.now()
        diff = now - self.created_at
        
        seconds = diff.total_seconds()
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return self.created_at.strftime("%b %d, %Y")
    
    def get_related_object_url(self):
        """Return the URL for the related object if it exists"""
        if not self.related_object_id or not self.related_object_type:
            return None
        
        try:
            if self.related_object_type == 'lead':
                return reverse('leads:lead_detail', kwargs={'lead_id': self.related_object_id})
            elif self.related_object_type == 'booking':
                return reverse('bookings:booking_detail', kwargs={'booking_id': self.related_object_id})
            elif self.related_object_type == 'invoice':
                return reverse('invoices:invoice_detail', kwargs={'invoice_id': self.related_object_id})
            elif self.related_object_type == 'staff':
                return reverse('business:staff_detail', kwargs={'staff_id': self.related_object_id})
            elif self.related_object_type == 'staff_availability':
                # For staff availability, we'll link to the staff detail page
                from bookings.models import StaffAvailability
                availability = StaffAvailability.objects.get(id=self.related_object_id)
                return reverse('business:staff_detail', kwargs={'staff_id': availability.staff_member.id})
            else:
                return None
        except Exception:
            # If there's any error (like the object was deleted), return None
            return None
