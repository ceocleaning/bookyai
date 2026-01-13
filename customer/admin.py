from django.contrib import admin
from .models import Customer, CustomerBusinessLink


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'email_notifications', 'sms_notifications', 'created_at')
    list_filter = ('email_notifications', 'sms_notifications', 'marketing_emails', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone_number', 'date_of_birth')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'zip_code', 'country')
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'sms_notifications', 'marketing_emails')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomerBusinessLink)
class CustomerBusinessLinkAdmin(admin.ModelAdmin):
    list_display = ('customer', 'business', 'total_bookings', 'total_spent', 'is_active', 'last_booking_date')
    list_filter = ('is_active', 'created_at', 'business')
    search_fields = ('customer__user__email', 'customer__user__first_name', 'customer__user__last_name', 'business__name')
    readonly_fields = ('first_booking_date', 'last_booking_date', 'total_bookings', 'total_spent', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Relationship', {
            'fields': ('customer', 'business', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_bookings', 'total_spent', 'first_booking_date', 'last_booking_date')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['update_statistics']
    
    def update_statistics(self, request, queryset):
        """Update statistics for selected customer-business links"""
        for link in queryset:
            link.update_stats()
        self.message_user(request, f"Updated statistics for {queryset.count()} customer-business links.")
    update_statistics.short_description = "Update statistics for selected links"
