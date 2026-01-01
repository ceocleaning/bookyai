from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('pricing/', views.pricing, name='pricing'),
    path('contact/', views.contact, name='contact'),
    path('use-cases/', views.usecases, name='usecases'),
    path('features/', views.features, name='features'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('refund-policy/', views.refund_policy, name='refund_policy'),
    path('status/', views.system_status, name='system_status'),
    path('faq/', views.faq, name='faq'),
    path('help/', views.help_center, name='help_center'),
    path('help/<slug:category_slug>/', views.help_category, name='help_category'),
    path('help/<slug:category_slug>/<slug:article_slug>/', views.help_article, name='help_article'),
]