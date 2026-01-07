from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, 'core/index.html')


def about(request):
    """About Us page"""
    return render(request, 'core/about.html')


def pricing(request):
    """Pricing page"""
    context = {}
    if request.user.is_authenticated:
        context['user_email'] = request.user.email
    return render(request, 'core/pricing.html', context)


def contact(request):
    """Contact Us page"""
    return render(request, 'core/contact.html')


def usecases(request):
    """Use Cases page"""
    return render(request, 'core/usecases.html')


def features(request):
    """Features page"""
    return render(request, 'core/features.html')


def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'core/privacy_policy.html')


def terms_conditions(request):
    """Terms and Conditions page"""
    return render(request, 'core/terms_conditions.html')


def refund_policy(request):
    """Refund Policy page"""
    return render(request, 'core/refund_policy.html')


def system_status(request):
    """System Status page"""
    return render(request, 'core/system_status.html')



from .models import HelpCategory, HelpArticle
from django.db.models import Q
from django.shortcuts import get_object_or_404
from types import SimpleNamespace
from datetime import datetime

def faq(request):
    """FAQ page"""
    return render(request, 'core/faq.html')


def help_center(request):
    """Help Center landing page"""
    # Dummy Data for Visualization
    categories = [
        SimpleNamespace(
            name="Getting Started",
            slug="getting-started",
            icon="fas fa-rocket",
            description="Everything you need to know to get started with Booky AI.",
            articles=SimpleNamespace(count=5),
            first_article_slug="quick-start-guide"
        ),
        SimpleNamespace(
            name="Account Management",
            slug="account-management",
            icon="fas fa-user-cog",
            description="Manage your account settings, team members, and billing.",
            articles=SimpleNamespace(count=3),
            first_article_slug="account-setup"
        ),
        SimpleNamespace(
            name="Integrations",
            slug="integrations",
            icon="fas fa-plug",
            description="Connect Booky AI with your favorite tools and calendars.",
            articles=SimpleNamespace(count=8),
            first_article_slug="google-calendar-integration"
        ),
        SimpleNamespace(
            name="Troubleshooting",
            slug="troubleshooting",
            icon="fas fa-tools",
            description="Solutions to common issues and error messages.",
            articles=SimpleNamespace(count=4),
            first_article_slug="common-issues"
        ),
        SimpleNamespace(
            name="API Documentation",
            slug="api-docs",
            icon="fas fa-code",
            description="Developer guides and API reference.",
            articles=SimpleNamespace(count=12),
            first_article_slug="api-overview"
        ),
        SimpleNamespace(
            name="Security & Privacy",
            slug="security",
            icon="fas fa-shield-alt",
            description="Information about data security and privacy compliance.",
            articles=SimpleNamespace(count=6),
            first_article_slug="data-security"
        ),
    ]
    
    return render(request, 'core/help_center.html', {'categories': categories})


def help_category(request, category_slug):
    """View articles in a specific category"""
    # Dummy Data
    category = SimpleNamespace(
        name="Getting Started",
        slug="getting-started",
        icon="fas fa-rocket",
        description="Everything you need to know to get started with Booky AI."
    )
    
    articles = [
        SimpleNamespace(
            title="Quick Start Guide",
            slug="quick-start-guide",
            content="Learn the basics of setting up your account..."
        ),
        SimpleNamespace(
            title="Connecting Your Calendar",
            slug="connecting-calendar",
            content="How to sync Google, Outlook, or iCal..."
        ),
        SimpleNamespace(
            title="Customizing Your AI Assistant",
            slug="customizing-ai",
            content="Set up tone, voice, and hours..."
        ),
         SimpleNamespace(
            title="Inviting Team Members",
            slug="inviting-team",
            content="Add your colleagues to Booky AI..."
        ),
    ]
    
    return render(request, 'core/help_category.html', {'category': category, 'articles': articles})


def help_article(request, category_slug, article_slug):
    """View a specific article"""
    # Dummy Data
    category_articles = [
        SimpleNamespace(
            title="Quick Start Guide",
            slug="quick-start-guide",
        ),
        SimpleNamespace(
            title="Connecting Your Calendar",
            slug="connecting-calendar",
        ),
        SimpleNamespace(
            title="Customizing Your AI Assistant",
            slug="customizing-ai",
        ),
        SimpleNamespace(
            title="Inviting Team Members",
            slug="inviting-team",
        ),
        SimpleNamespace(
            title="Setting Up Notifications",
            slug="setup-notifications",
        ),
    ]
    
    article = SimpleNamespace(
        title="Quick Start Guide",
        slug="quick-start-guide",
        category=SimpleNamespace(name="Getting Started", slug="getting-started"),
        updated_at=datetime.now(),
        views=1245,
        content="""
        <p class="lead">Welcome to Booky AI! This guide will help you get your account set up and ready to accept bookings in less than 5 minutes.</p>
        
        <h2>Step 1: Sign up and create your profile</h2>
        <p>First things first, you'll need to create an account. Go to the sign-up page and enter your email and password. Once you're in, you'll be prompted to complete your profile.</p>
        
        <h2>Step 2: Connect your calendar</h2>
        <p>To avoid double bookings, it's crucial to connect your primary calendar. We support:</p>
        <ul>
            <li>Google Calendar</li>
            <li>Outlook / Office 365</li>
            <li>Apple iCloud Calendar</li>
        </ul>
        <p>Go to <strong>Settings > Integrations</strong> to connect your calendar.</p>
        
        <h2>Step 3: Define your services</h2>
        <p>What kind of appointments do you want to offer? You can set up different durations, prices, and descriptions for each service type.</p>
        
        <div class="alert alert-info">
            <i class="fas fa-info-circle me-2"></i> <strong>Pro Tip:</strong> You can create secret input fields for internal use only!
        </div>
        
        <h2>Step 4: Share your link</h2>
        <p>You're all set! Copy your booking link from the dashboard and share it with your clients, or embed it on your website.</p>
        """
    )
    
    return render(request, 'core/help_article.html', {
        'article': article,
        'category_articles': category_articles,
        'current_slug': article_slug
    })



