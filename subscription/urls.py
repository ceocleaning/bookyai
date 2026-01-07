from django.urls import path
from . import views

app_name = 'subscription'

urlpatterns = [
    path('webhook/', views.stripe_webhook, name='webhook'),
    path('billing-portal/', views.billing_portal, name='billing_portal'),
]