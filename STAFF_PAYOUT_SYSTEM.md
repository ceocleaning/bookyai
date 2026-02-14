# Staff Payout System - Automatic Payout Creation

## Overview

The Staff Payout System has been simplified and now automatically creates payouts when bookings are completed.

## Changes Made

### 1. **Simplified StaffPayout Model** (`bookings/models.py`)

- **Removed** the `StaffPayoutBooking` intermediate model
- **Removed** fields: `period_start`, `period_end`, `total_revenue`, `payout_percentage`, `payout_amount`, `total_bookings`, `created_by`
- **Changed** to use a direct Many-to-Many relationship with `Booking` model
- **Added** helper methods:
  - `get_total_bookings()` - Returns count of bookings in the payout
  - `get_total_revenue()` - Calculates total revenue from all bookings
  - `get_payout_amount()` - Calculates payout based on business configuration percentage

### 2. **Automatic Payout Creation** (`bookings/signals.py`)

- Updated `create_or_update_payout_for_booking()` function
- **When a booking status changes to COMPLETED:**
  1.  System loops through all staff members assigned to the booking
  2.  For each staff member, it finds or creates a PENDING payout
  3.  Adds the completed booking to the payout's bookings M2M field
  4.  Only creates payouts if `staff_pay_percentage` is configured in business settings

### 3. **Updated Admin Interface** (`bookings/admin.py`)

- Removed `StaffPayoutBooking` admin registration
- Updated `StaffPayoutAdmin` to show relevant fields
- Added `filter_horizontal` for easier M2M management of bookings

### 4. **Updated Views** (`bookings/payout_views.py`)

- Removed all references to `StaffPayoutBooking`
- Updated queries to use the new M2M `bookings` relationship
- Modified payout creation to use `payout.bookings.set()`
- Updated summary calculations to use the new helper methods

## How It Works

### Automatic Payout Creation Flow:

```
1. Booking status changes from ANY status → COMPLETED
   ↓
2. Signal handler detects the status change
   ↓
3. For each staff member assigned to the booking:
   a. Check if staff_pay_percentage > 0 in business configuration
   b. Find existing PENDING payout for this staff member
   c. If no pending payout exists, create a new one
   d. Add the booking to the payout's bookings M2M field
```

### Key Features:

- ✅ **One booking can be assigned to multiple staff members** - The system loops through all `BookingStaffAssignment` records
- ✅ **Each staff member gets their own payout** - Separate payout instances per staff member
- ✅ **Automatic accumulation** - Completed bookings are automatically added to pending payouts
- ✅ **No duplicate bookings** - System checks if booking already exists in payout before adding
- ✅ **Configurable percentage** - Uses `staff_pay_percentage` from `BusinessConfiguration`

## Configuration Required

To enable automatic payout creation, ensure the business has configured the staff payout percentage:

1. Go to Business Configuration
2. Set `staff_pay_percentage` (e.g., 50.00 for 50%)
3. System will automatically create payouts when bookings are completed

## Database Migration

Migration `0012_alter_staffpayout_options_and_more.py` was created and applied, which:

- Removes the `StaffPayoutBooking` model
- Adds the `bookings` M2M field to `StaffPayout`
- Removes obsolete fields from `StaffPayout`

## Example Usage

```python
# When a booking is completed
booking.status = BookingStatus.COMPLETED
booking.save()  # Signal automatically creates/updates payouts

# View payout details
payout = StaffPayout.objects.get(id=payout_id)
total_bookings = payout.get_total_bookings()  # Count of bookings
total_revenue = payout.get_total_revenue()    # Sum of all booking revenues
payout_amount = payout.get_payout_amount()    # Calculated payout (revenue * percentage)

# Mark payout as paid
payout.mark_as_paid(
    payment_method='Bank Transfer',
    payment_reference='TXN123456',
    paid_date=timezone.now().date()
)
```

## Notes

- Payouts remain in PENDING status until manually marked as PAID
- Only one PENDING payout exists per staff member at a time
- New completed bookings are added to the existing PENDING payout
- Once a payout is marked as PAID, a new PENDING payout will be created for future bookings
