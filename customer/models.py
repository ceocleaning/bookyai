from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from business.models import Business


class Customer(models.Model):
    """
    Customer profile linked to Django User.
    One customer can be associated with multiple businesses.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Address fields
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='USA')
    
    # Preferences
    email_notifications = models.BooleanField(default=True, help_text="Receive email notifications for bookings")
    sms_notifications = models.BooleanField(default=True, help_text="Receive SMS notifications")
    marketing_emails = models.BooleanField(default=False, help_text="Receive marketing and promotional emails")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.email})"
    
    def get_full_name(self):
        """Return customer's full name"""
        return self.user.get_full_name() or self.user.email
    
    def get_linked_businesses(self):
        """Get all businesses this customer is linked to"""
        return Business.objects.filter(
            customer_links__customer=self,
            customer_links__is_active=True
        )
    
    def get_total_bookings(self):
        """Get total number of bookings across all businesses"""
        return self.bookings.count()
    
    def get_total_spent(self):
        """Calculate total amount spent across all businesses"""
        from invoices.models import Payment
        from decimal import Decimal
        
        total = Payment.objects.filter(
            invoice__booking__customer=self
        ).aggregate(total=models.Sum('amount'))['total']
        
        return total or Decimal('0.00')


class CustomerBusinessLink(models.Model):
    """
    Links customers to businesses they have interacted with.
    Tracks relationship status and metadata.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='business_links')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='customer_links')
    
    # Relationship metadata
    first_booking_date = models.DateTimeField(null=True, blank=True)
    last_booking_date = models.DateTimeField(null=True, blank=True)
    total_bookings = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text="Internal notes about this customer relationship")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Customer Business Link"
        verbose_name_plural = "Customer Business Links"
        unique_together = ('customer', 'business')
        ordering = ['-last_booking_date']
    
    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.business.name}"
    
    def update_stats(self):
        """Update booking statistics for this customer-business relationship"""
        from bookings.models import Booking
        from invoices.models import Payment
        from decimal import Decimal
        
        bookings = Booking.objects.filter(
            customer=self.customer,
            business=self.business
        )
        
        self.total_bookings = bookings.count()
        
        if bookings.exists():
            self.first_booking_date = bookings.order_by('created_at').first().created_at
            self.last_booking_date = bookings.order_by('-created_at').first().created_at
        
        # Calculate total spent
        total = Payment.objects.filter(
            invoice__booking__customer=self.customer,
            invoice__booking__business=self.business
        ).aggregate(total=models.Sum('amount'))['total']
        
        self.total_spent = total or Decimal('0.00')
        self.save()
