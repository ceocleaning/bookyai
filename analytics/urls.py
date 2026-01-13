from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('api/revenue-chart/', views.revenue_chart_data, name='revenue_chart'),
    path('api/bookings-chart/', views.bookings_chart_data, name='bookings_chart'),
    path('api/lead-source-chart/', views.lead_source_chart_data, name='lead_source_chart'),
    path('api/service-popularity-chart/', views.service_popularity_chart_data, name='service_popularity_chart'),
    path('export/', views.export_analytics, name='export'),
]