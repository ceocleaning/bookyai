from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    # Authentication
    path('register/', views.customer_register, name='register'),
    path('login/', views.customer_login, name='login'),
    path('logout/', views.customer_logout, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('set-password/<uidb64>/<token>/', views.set_password, name='set_password'),
    
    # Dashboard
    path('', views.customer_dashboard, name='dashboard'),
    
    # Bookings
    path('bookings/', views.bookings_list, name='bookings_list'),
    path('bookings/<str:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<str:booking_id>/reschedule/', views.booking_reschedule, name='booking_reschedule'),
    path('bookings/<str:booking_id>/cancel/', views.booking_cancel, name='booking_cancel'),
    
    # Invoices & Payments
    path('invoices/', views.invoices_list, name='invoices_list'),
    path('invoices/<str:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<str:invoice_id>/pay/', views.invoice_pay, name='invoice_pay'),
    path('payment-history/', views.payment_history, name='payment_history'),
    
    # Profile
    path('profile/', views.customer_profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/password/', views.change_password, name='change_password'),
    path('profile/notifications/', views.notification_preferences, name='notifications'),
    
    # Business Management
    path('businesses/', views.linked_businesses, name='businesses'),
    path('switch-business/<str:business_id>/', views.switch_business, name='switch_business'),
]