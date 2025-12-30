from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, 'core/index.html')


def about(request):
    """About Us page"""
    return render(request, 'core/about.html')


def pricing(request):
    """Pricing page"""
    return render(request, 'core/pricing.html')


def contact(request):
    """Contact Us page"""
    return render(request, 'core/contact.html')


def usecases(request):
    """Use Cases page"""
    return render(request, 'core/usecases.html')


def features(request):
    """Features page"""
    return render(request, 'core/features.html')