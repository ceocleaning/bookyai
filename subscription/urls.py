from django.urls import path
from . import views

app_name = 'subscription'

urlpatterns = [
    path('webhook/', views.stripe_webhook, name='webhook'),
    path('billing-portal/', views.billing_portal, name='billing_portal'),
    path('manage/', views.subscription_management, name='manage'),
    path('cancel/', views.cancel_subscription, name='cancel'),
    path('checkout/<int:plan_id>/', views.create_checkout_session, name='checkout'),
]