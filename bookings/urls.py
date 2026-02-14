from django.urls import path
from . import views, widget_views, payout_views
from .views_widget_example import widget_showcase

app_name = 'bookings'

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_booking, name='create_booking'),
    path('<str:booking_id>/edit/', views.edit_booking, name='edit_booking'),
    path('<str:booking_id>/detail/', views.booking_detail, name='booking_detail'),
    
    # API endpoints
    path('api/service-items/<str:service_id>/', views.get_service_items, name='get_service_items'),
    path('api/leads/', views.get_leads, name='get_leads'),
    path('api/check-availability/', views.check_availability, name='check_availability'),
    
    # Widget API endpoints (public, no auth required)
    path('widget/<str:business_id>/config/', widget_views.get_widget_config, name='widget_config'),
    path('widget/<str:business_id>/service-items/<str:service_id>/', widget_views.get_widget_service_items, name='widget_service_items'),
    path('widget/<str:business_id>/check-availability/', widget_views.check_widget_availability, name='widget_check_availability'),
    path('widget/<str:business_id>/create/', widget_views.create_widget_booking, name='widget_create_booking'),
    
    # Widget pages
    path('widget-showcase/', widget_showcase, name='widget_showcase'),
    
    # Booking actions
    path('<str:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('<str:booking_id>/reschedule/', views.reschedule_booking, name='reschedule_booking'),
    path('<str:booking_id>/available-timeslots/', views.get_available_timeslots, name='get_available_timeslots'),
    path('<str:booking_id>/trigger-event/', views.trigger_booking_event, name='trigger_booking_event'),
    path('bulk-delete/', views.bulk_delete_bookings, name='bulk_delete_bookings'),
    
    # Staff Payout URLs
    path('payouts/', payout_views.payout_list, name='payout_list'),
    path('payouts/create/', payout_views.create_payout, name='create_payout'),
    path('payouts/<str:payout_id>/', payout_views.payout_detail, name='payout_detail'),
    path('payouts/<str:payout_id>/mark-paid/', payout_views.mark_payout_paid, name='mark_payout_paid'),
    path('payouts/<str:payout_id>/mark-pending/', payout_views.mark_payout_pending, name='mark_payout_pending'),
    path('payouts/summary/staff/', payout_views.staff_payout_summary, name='staff_payout_summary'),
    path('payouts/api/staff-bookings/', payout_views.get_staff_bookings, name='get_staff_bookings'),
]

