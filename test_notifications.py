"""
Test Script for Automated Notifications System
Run this in Django shell to test the notification signals.

Usage:
    python manage.py shell < test_notifications.py

Or in Django shell:
    exec(open('test_notifications.py').read())
"""

print("=" * 70)
print("Testing Automated Notifications System")
print("=" * 70)

# Import required models
from leads.models import Lead
from bookings.models import Booking, BookingStatus
from invoices.models import Invoice, Payment
from subscription.models import Subscription
from business.models import Business
from notifications.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

# Get or create test business
business = Business.objects.first()
if not business:
    print("❌ No business found. Please create a business first.")
    exit()

print(f"\n✅ Using business: {business.name}")

# Get business owner
user = business.user
if not user:
    print("❌ No user found for business. Please create a user first.")
    exit()

print(f"✅ Using user: {user.email}")

# Count notifications before tests
initial_notification_count = Notification.objects.count()
print(f"\n📊 Initial notification count: {initial_notification_count}")

print("\n" + "=" * 70)
print("TEST 1: Lead Creation")
print("=" * 70)

try:
    # Create a test lead
    lead = Lead.objects.create(
        business=business,
        first_name="Test",
        last_name="Lead",
        email="testlead@example.com",
        phone="1234567890",
        source='website'
    )
    print(f"✅ Created lead: {lead.get_full_name()}")
    
    # Check if notification was created
    lead_notifications = Notification.objects.filter(
        notification_type='lead_created',
        related_object_id=lead.id
    )
    if lead_notifications.exists():
        print(f"✅ Lead notification created! Count: {lead_notifications.count()}")
    else:
        print("❌ No lead notification found")
        
except Exception as e:
    print(f"❌ Error creating lead: {str(e)}")

print("\n" + "=" * 70)
print("TEST 2: Booking Creation")
print("=" * 70)

try:
    from datetime import date, time, timedelta
    from business.models import ServiceOffering
    
    # Get or create a service offering
    service = ServiceOffering.objects.filter(business=business).first()
    if not service:
        print("⚠️  No service offering found. Skipping booking test.")
    else:
        # Create a test booking
        tomorrow = date.today() + timedelta(days=1)
        booking = Booking.objects.create(
            business=business,
            service_offering=service,
            name="Test Customer",
            email="testcustomer@example.com",
            phone_number="9876543210",
            booking_date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            status=BookingStatus.CONFIRMED
        )
        print(f"✅ Created booking: {booking.name} on {booking.booking_date}")
        
        # Check if notification was created
        booking_notifications = Notification.objects.filter(
            notification_type='booking_created',
            related_object_id=booking.id
        )
        if booking_notifications.exists():
            print(f"✅ Booking notification created! Count: {booking_notifications.count()}")
        else:
            print("❌ No booking notification found")
            
except Exception as e:
    print(f"❌ Error creating booking: {str(e)}")

print("\n" + "=" * 70)
print("TEST 3: Booking Status Change (Completion)")
print("=" * 70)

try:
    # Find a confirmed booking to complete
    test_booking = Booking.objects.filter(
        business=business,
        status=BookingStatus.CONFIRMED
    ).first()
    
    if test_booking:
        old_status = test_booking.status
        test_booking.status = BookingStatus.COMPLETED
        test_booking.save()
        print(f"✅ Updated booking status: {old_status} → {test_booking.status}")
        
        # Check if completion notification was created
        completion_notifications = Notification.objects.filter(
            notification_type='booking_completed',
            related_object_id=test_booking.id
        )
        if completion_notifications.exists():
            print(f"✅ Completion notification created! Count: {completion_notifications.count()}")
        else:
            print("❌ No completion notification found")
    else:
        print("⚠️  No confirmed booking found to test completion")
        
except Exception as e:
    print(f"❌ Error updating booking: {str(e)}")

print("\n" + "=" * 70)
print("TEST 4: Payment Creation")
print("=" * 70)

try:
    # Find a pending invoice
    test_invoice = Invoice.objects.filter(
        status='pending',
        booking__business=business
    ).first()
    
    if test_invoice:
        # Create a payment
        payment = Payment.objects.create(
            invoice=test_invoice,
            amount=100.00,
            payment_method='cash'
        )
        print(f"✅ Created payment: ${payment.amount} for Invoice #{test_invoice.invoice_number}")
        
        # Check if payment notification was created
        payment_notifications = Notification.objects.filter(
            notification_type='invoice_paid',
            related_object_id=test_invoice.id
        )
        if payment_notifications.exists():
            print(f"✅ Payment notification created! Count: {payment_notifications.count()}")
        else:
            print("❌ No payment notification found")
    else:
        print("⚠️  No pending invoice found to test payment")
        
except Exception as e:
    print(f"❌ Error creating payment: {str(e)}")

# Final summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

final_notification_count = Notification.objects.count()
new_notifications = final_notification_count - initial_notification_count

print(f"📊 Initial notifications: {initial_notification_count}")
print(f"📊 Final notifications: {final_notification_count}")
print(f"📊 New notifications created: {new_notifications}")

if new_notifications > 0:
    print(f"\n✅ SUCCESS! {new_notifications} notifications were created automatically!")
    print("\n📧 Recent notifications:")
    for notif in Notification.objects.order_by('-created_at')[:5]:
        print(f"   - {notif.notification_type}: {notif.title}")
else:
    print("\n⚠️  No new notifications were created. Check your signal setup.")

print("\n" + "=" * 70)
print("Test Complete!")
print("=" * 70)
