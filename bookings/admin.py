from django.contrib import admin
from .models import (
    Booking, BookingServiceItem, StaffServiceAssignment, StaffAvailability, 
    StaffRole, StaffMember, BookingEvent, BookingEventType, ReminderType, BookingReminder,
    StaffPayout
)

@admin.register(BookingEventType)
class BookingEventTypeAdmin(admin.ModelAdmin):
    list_display = ['business', 'name', 'event_key', 'icon', 'color', 'is_enabled', 'requires_reason', 'display_order']
    list_filter = ['business', 'is_enabled', 'show_in_timeline']
    search_fields = ['name', 'event_key']
    ordering = ['business', 'display_order']

@admin.register(ReminderType)
class ReminderTypeAdmin(admin.ModelAdmin):
    list_display = ['business', 'name', 'reminder_key', 'icon', 'is_enabled', 'default_hours_before', 'display_order']
    list_filter = ['business', 'is_enabled']
    search_fields = ['name', 'reminder_key']
    ordering = ['business', 'display_order']

@admin.register(StaffPayout)
class StaffPayoutAdmin(admin.ModelAdmin):
    list_display = ['staff_member', 'business', 'status', 'paid_date', 'created_at']
    list_filter = ['business', 'status', 'created_at']
    search_fields = ['staff_member__first_name', 'staff_member__last_name', 'staff_member__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['bookings']  # Makes the M2M field easier to manage


admin.site.register(Booking)
admin.site.register(BookingServiceItem)
admin.site.register(StaffServiceAssignment)
admin.site.register(StaffAvailability)
admin.site.register(StaffRole)
admin.site.register(StaffMember)
admin.site.register(BookingEvent)
admin.site.register(BookingReminder)

