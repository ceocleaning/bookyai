"""
Admin Dashboard URL Configuration
"""

from django.urls import path
from .views import index_views, users_views, business_views, help_articles_views

app_name = 'admin_dashboard'

urlpatterns = [
    # Dashboard Index
    path('', index_views.admin_dashboard_index, name='index'),
    
    # API Endpoints for Statistics
    path('api/users/', index_views.get_total_users, name='api_users'),
    path('api/businesses/', index_views.get_total_businesses, name='api_businesses'),
    path('api/bookings/', index_views.get_total_bookings, name='api_bookings'),
    path('api/leads/', index_views.get_total_leads, name='api_leads'),
    path('api/invoices/', index_views.get_total_invoices, name='api_invoices'),
    path('api/payments/', index_views.get_total_payments, name='api_payments'),
    path('api/client-revenue/', index_views.get_client_revenue, name='api_client_revenue'),
    path('api/saas-revenue/', index_views.get_saas_revenue, name='api_saas_revenue'),
    path('api/chart-data/', index_views.get_dashboard_chart_data, name='api_chart_data'),
    
    # User Management
    path('users/', users_views.users_list, name='users_list'),
    path('users/<int:user_id>/', users_views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', users_views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', users_views.user_delete, name='user_delete'),
    path('users/<int:user_id>/toggle-status/', users_views.user_toggle_status, name='user_toggle_status'),
    path('users/<int:user_id>/password-info/', users_views.get_user_password_info, name='user_password_info'),
    path('users/<int:user_id>/change-password/', users_views.change_user_password, name='user_change_password'),
    
    # Business Management
    path('businesses/', business_views.business_list, name='business_list'),
    path('businesses/add/', business_views.business_add, name='business_add'),
    path('businesses/<str:business_id>/', business_views.business_detail, name='business_detail'),
    path('businesses/<str:business_id>/edit/', business_views.business_edit, name='business_edit'),
    path('businesses/<str:business_id>/delete/', business_views.business_delete, name='business_delete'),
    path('businesses/<str:business_id>/toggle-status/', business_views.business_toggle_status, name='business_toggle_status'),
    path('businesses/<str:business_id>/bookings/', business_views.business_bookings, name='business_bookings'),
    path('businesses/<str:business_id>/bookings/<str:booking_id>/', business_views.booking_detail, name='booking_detail'),
    path('businesses/<str:business_id>/leads/', business_views.business_leads, name='business_leads'),
    path('businesses/<str:business_id>/leads/<str:lead_id>/', business_views.lead_detail, name='lead_detail'),
    
    # Help Articles Management
    path('help-articles/', help_articles_views.help_article_list, name='help_article_list'),
    path('help-articles/add/', help_articles_views.help_article_add, name='help_article_add'),
    path('help-articles/<int:article_id>/', help_articles_views.help_article_detail, name='help_article_detail'),
    path('help-articles/<int:article_id>/edit/', help_articles_views.help_article_edit, name='help_article_edit'),
    path('help-articles/<int:article_id>/delete/', help_articles_views.help_article_delete, name='help_article_delete'),
    path('help-articles/<int:article_id>/duplicate/', help_articles_views.help_article_duplicate, name='help_article_duplicate'),
    path('help-articles/bulk-delete/', help_articles_views.help_article_bulk_delete, name='help_article_bulk_delete'),
    path('help-articles/export/', help_articles_views.help_article_export, name='help_article_export'),
    
    # Help Categories Management
    path('help-categories/', help_articles_views.help_category_list, name='help_category_list'),
    path('help-categories/add/', help_articles_views.help_category_add, name='help_category_add'),
    path('help-categories/<int:category_id>/edit/', help_articles_views.help_category_edit, name='help_category_edit'),
    path('help-categories/<int:category_id>/delete/', help_articles_views.help_category_delete, name='help_category_delete'),
]

