from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path('', views.index, name='index'),
    
    # Customer Management
    path('customers/', views.customers_list, name='customers_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:customer_id>/delete/', views.customer_delete, name='customer_delete'),
    
    # API Endpoints
    path('api/customers/', views.get_customers_api, name='get_customers_api'),
]