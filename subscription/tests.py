from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Subscription, SubscriptionPlan, WebhookEvent
from business.models import Business, Industry
from .utils import has_active_subscription
import json
from unittest.mock import patch, MagicMock

class WebhookSignatureTests(TestCase):
    def test_webhook_signature_verification(self):
        """Test that invalid signatures are rejected"""
        client = Client()
        response = client.post(
            '/subscription/webhook/',
            data={},
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )
        self.assertEqual(response.status_code, 400)

class IdempotencyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.event_id = 'evt_test_123'
        self.event_type = 'customer.subscription.updated'
        
        # Create an existing event
        WebhookEvent.objects.create(
            stripe_event_id=self.event_id,
            event_type=self.event_type,
            payload={'id': self.event_id}
        )
        
    @patch('stripe.Webhook.construct_event')
    def test_duplicate_event_ignored(self, mock_construct_event):
        """Test that duplicate events are not processed twice"""
        # Mock Stripe event construction
        mock_event = {'id': self.event_id, 'type': self.event_type}
        mock_construct_event.return_value = mock_event
        
        response = self.client.post(
            '/subscription/webhook/',
            data=json.dumps(mock_event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        # Should still be only 1 event in DB
        self.assertEqual(WebhookEvent.objects.filter(stripe_event_id=self.event_id).count(), 1)

class SubscriptionUtilsTests(TestCase):
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.industry = Industry.objects.create(name='Test Industry')
        self.business = Business.objects.create(
            name='Test Business',
            user=self.user,
            industry=self.industry,
            email='test@example.com'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            price=10.00,
            stripe_price_id='price_123'
        )
        
    def test_has_active_subscription_false(self):
        """Test has_active_subscription returns False when no subscription"""
        self.assertFalse(has_active_subscription(self.business))
        
    def test_has_active_subscription_true(self):
        """Test has_active_subscription returns True when active"""
        Subscription.objects.create(
            business=self.business,
            plan=self.plan,
            status='active',
            stripe_customer_id='cus_123',
            stripe_subscription_id='sub_123'
        )
        self.assertTrue(has_active_subscription(self.business))
        
    def test_has_active_subscription_trialing(self):
        """Test has_active_subscription returns True when trialing"""
        Subscription.objects.create(
            business=self.business,
            plan=self.plan,
            status='trialing',
            stripe_customer_id='cus_123',
            stripe_subscription_id='sub_123',
            trial_end=timezone.now() + timezone.timedelta(days=7)
        )
        self.assertTrue(has_active_subscription(self.business))
        
    def test_has_active_subscription_past_due(self):
        """Test has_active_subscription returns False when past_due"""
        Subscription.objects.create(
            business=self.business,
            plan=self.plan,
            status='past_due',
            stripe_customer_id='cus_123',
            stripe_subscription_id='sub_123'
        )
        self.assertFalse(has_active_subscription(self.business))
