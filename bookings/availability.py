from django.utils import timezone
from datetime import datetime, timedelta, time
from django.db.models import Q

from bookings.models import (
    StaffMember, 
    StaffAvailability, 
    Booking, 
    BookingStatus, 
    AVAILABILITY_TYPE, 
    BookingStaffAssignment,
    StaffServiceAssignment,
    Business
)


def check_timeslot_availability(business, start_time, duration_minutes, service=None):
    """
    Check if a specific time slot is available.
    
    Args:
        business: Business object or ID
        start_time: Datetime object for the start time
        duration_minutes: Duration of the appointment in minutes
        service: Optional ServiceOffering object
        
    Returns:
        Tuple of (is_available, reason, available_staff)
    """
    try:
        print(f"[DEBUG] check_timeslot_availability called with: business={business}, start_time={start_time}, duration_minutes={duration_minutes}, service={service}")
        
        # Convert business ID to object if needed
        if not isinstance(business, Business):
            try:
                print(f"[DEBUG] Converting business ID to object: {business}")
                business = Business.objects.get(id=business)
                print(f"[DEBUG] Found business: {business.name}")
            except Business.DoesNotExist:
                print(f"[DEBUG] Business with ID {business} not found")
                return False, f"Business with ID {business} not found", []
        
        # Calculate end time
        end_time = start_time + timedelta(minutes=duration_minutes)
        print(f"[DEBUG] Calculated end time: {end_time}")
        
        # Note: We don't check business hours separately because staff availability IS the business hours
        
        # Build valid booking statuses for per-staff conflict checks
        valid_statuses = []
        for status in BookingStatus:
            if str(status).upper() in ('CONFIRMED', 'PENDING', 'RESCHEDULED'):
                valid_statuses.append(status)
        
        print(f"[DEBUG] Valid booking statuses: {valid_statuses}")
        
        # Check if any staff is available
        try:
            # Get staff members - filter by service if provided
            if service:
                # Get staff members who are assigned to this service
                staff_with_service = StaffServiceAssignment.objects.filter(
                    service_offering=service
                ).values_list('staff_member_id', flat=True)
                
                all_staff = StaffMember.objects.filter(
                    business=business, 
                    is_active=True,
                    id__in=staff_with_service
                )
                print(f"[DEBUG] Filtering by service: {service.name}")
            else:
                all_staff = StaffMember.objects.filter(business=business, is_active=True)
            
            print(f"[DEBUG] Checking availability for {all_staff.count()} staff members")
            
            if not all_staff.exists():
                if service:
                    print(f"[DEBUG] No staff members assigned to service: {service.name}")
                    return False, f"No staff members available for {service.name}", []
                else:
                    print(f"[DEBUG] No staff members found for this business")
                    return False, "No staff members found for this business", []
            
            # For each staff member, check if they're available
            available_staff = []
            for staff in all_staff:
                try:
                    # First check if staff has any service assignments
                    has_service_assignment = StaffServiceAssignment.objects.filter(
                        staff_member=staff
                    ).exists()
                    
                    if not has_service_assignment:
                        print(f"[DEBUG] Staff {staff.id} has no service assignments - skipping")
                        continue
                    
                    # Check if staff has schedule availability (weekly/specific rules)
                    if not is_staff_available(staff, start_time.date(), start_time.time(), end_time.time()):
                        print(f"[DEBUG] Staff {staff.id} is not available per schedule rules")
                        continue
                    
                    # Check if staff has any conflicting bookings at this time
                    staff_has_conflict = BookingStaffAssignment.objects.filter(
                        staff_member=staff,
                        booking__booking_date=start_time.date(),
                        booking__start_time__lt=end_time.time(),
                        booking__end_time__gt=start_time.time(),
                        booking__status__in=valid_statuses
                    ).exists()
                    
                    if staff_has_conflict:
                        print(f"[DEBUG] Staff {staff.id} has a conflicting booking - skipping")
                        continue
                    
                    available_staff.append(staff)
                    print(f"[DEBUG] Staff {staff.id} is available")
                except Exception as e:
                    print(f"[DEBUG] Error checking availability for staff {staff.id}: {str(e)}")
                    # Continue to the next staff member
                    continue
            
            print(f"[DEBUG] Found {len(available_staff)} available staff members")
            
            if not available_staff:
                return False, "No staff available at this time", []
            
            # Convert staff members to a serializable format
            staff_data = []
            for staff in available_staff:
                staff_data.append({
                    'id': str(staff.id),
                    'name': staff.get_full_name(),
                    'email': staff.email,
                    'phone': staff.phone
                })
            
            return True, "Available", staff_data
            
        except Exception as e:
            import traceback
            print(f"[DEBUG] Error in check_timeslot_availability: {str(e)}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return False, f"Error checking availability: {str(e)}", []

    except Exception as e:
        import traceback
        print(f"[DEBUG] Error in check_timeslot_availability: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return False, f"Error checking availability: {str(e)}", []
    

# Business hours are determined by staff availability, not a separate setting


def get_alternate_timeslots(business_id, date, start_time, duration_minutes, service_offering_id=None, staff_member_id=None):
    """
    Find alternate available timeslots when the requested slot is unavailable.
    
    Args:
        business_id (UUID): ID of the business
        date (date): Date to check
        start_time (time): Start time that was unavailable
        duration_minutes (int): Duration of the appointment in minutes
        service_offering_id (UUID, optional): ID of the service offering
        staff_member_id (UUID, optional): ID of a specific staff member to check
        
    Returns:
        list: List of dicts with alternate date/time options
    """
    print(f"[DEBUG] get_alternate_timeslots called with: business_id={business_id}, date={date}, start_time={start_time}, duration_minutes={duration_minutes}, service_offering_id={service_offering_id}, staff_member_id={staff_member_id}")
    
    alternate_slots = []
    current_date = date
    
    # Try same day, different times
    same_day_slots = find_available_slots_on_date(
        business_id, 
        current_date, 
        duration_minutes, 
        None, 
        staff_member_id,
        max_slots=3
    )
    
    alternate_slots.extend(same_day_slots)
    
    print(f"[DEBUG] Found {len(alternate_slots)} alternate slots on same day")
    
    # If we don't have enough slots, try the next day
    if len(alternate_slots) < 3:
        next_day = current_date + timedelta(days=1)
        next_day_slots = find_available_slots_on_date(
            business_id, 
            next_day, 
            duration_minutes, 
            None, 
            staff_member_id,
            max_slots=3 - len(alternate_slots)
        )
        alternate_slots.extend(next_day_slots)
        
        print(f"[DEBUG] Found {len(alternate_slots)} alternate slots on next day")
    
    # If we still don't have enough slots, try two days later
    if len(alternate_slots) < 3:
        two_days_later = current_date + timedelta(days=2)
        two_days_later_slots = find_available_slots_on_date(
            business_id, 
            two_days_later, 
            duration_minutes, 
            None, 
            staff_member_id,
            max_slots=3 - len(alternate_slots)
        )
        alternate_slots.extend(two_days_later_slots)
        
        print(f"[DEBUG] Found {len(alternate_slots)} alternate slots on two days later")
    
    return alternate_slots


def find_available_slots_on_date(business_id, date, duration_minutes, service_offering_id=None, staff_member_id=None, max_slots=3):
    """
    Find available time slots on a specific date.
    
    Args:
        business_id (UUID): ID of the business
        date (date): Date to check
        duration_minutes (int): Duration of the appointment in minutes
        service_offering_id (UUID, optional): ID of the service offering
        staff_member_id (UUID, optional): ID of a specific staff member to check
        max_slots (int): Maximum number of slots to return
        
    Returns:
        list: List of dicts with available time slots
    """
    print(f"[DEBUG] find_available_slots_on_date called with: business_id={business_id}, date={date}, duration_minutes={duration_minutes}, service_offering_id={service_offering_id}, staff_member_id={staff_member_id}, max_slots={max_slots}")
    
    available_slots = []
    
    # Get qualified staff members
    staff_query = Q(business_id=business_id, is_active=True, is_available=True)
    
    if staff_member_id:
        staff_query &= Q(id=staff_member_id)
    
    # Filter by service if provided
    if service_offering_id:
        # Get staff members who are assigned to this service
        staff_with_service = StaffServiceAssignment.objects.filter(
            service_offering_id=service_offering_id
        ).values_list('staff_member_id', flat=True)
        
        staff_query &= Q(id__in=staff_with_service)
        print(f"[DEBUG] Filtering staff by service offering: {service_offering_id}")
    
    qualified_staff = StaffMember.objects.filter(staff_query).distinct()
    
    print(f"[DEBUG] Found {qualified_staff.count()} qualified staff members")
    
    if not qualified_staff.exists():
        return []
    
    # Get all existing bookings for this date
    existing_bookings = Booking.objects.filter(
        business_id=business_id,
        booking_date=date,
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.RESCHEDULED]
    ).order_by('start_time')
    
    print(f"[DEBUG] Found {existing_bookings.count()} existing bookings")
    
    # Get earliest and latest availability from all qualified staff
    # This determines the "business hours" based on staff availability
    earliest_start = time(9, 0)  # Default fallback
    latest_end = time(17, 0)     # Default fallback
    
    # Get the actual range from staff availability
    for staff in qualified_staff:
        staff_avail = staff.availability.filter(
            Q(availability_type=AVAILABILITY_TYPE.WEEKLY, weekday=date.weekday()) |
            Q(availability_type=AVAILABILITY_TYPE.SPECIFIC, specific_date=date)
        ).exclude(off_day=True)
        
        for avail in staff_avail:
            if avail.start_time < earliest_start:
                earliest_start = avail.start_time
            if avail.end_time > latest_end:
                latest_end = avail.end_time
    
    business_start = earliest_start
    business_end = latest_end
    
    # If checking for today, start from current time
    if date == timezone.now().date() and timezone.now().time() > business_start:
        current_time = timezone.now().time()
        # Round up to the nearest half hour
        minutes = current_time.minute
        if minutes < 30:
            business_start = time(current_time.hour, 30)
        else:
            business_start = time(current_time.hour + 1, 0)
    
    # Generate potential time slots at 30-minute intervals
    slot_interval = 30  # minutes
    slot_start = datetime.combine(date, business_start)
    slot_end = datetime.combine(date, business_end)
    
    print(f"[DEBUG] Generating potential time slots from {slot_start} to {slot_end}")
    
    # Track which staff members are booked at which times
    staff_bookings = {}
    for staff in qualified_staff:
        staff_bookings[str(staff.id)] = []
        
    # Populate staff bookings
    for booking in existing_bookings:
        staff_assignments = BookingStaffAssignment.objects.filter(booking=booking)
        for assignment in staff_assignments:
            staff_id = str(assignment.staff_member.id)
            if staff_id in staff_bookings:
                staff_bookings[staff_id].append({
                    'start': datetime.combine(date, booking.start_time),
                    'end': datetime.combine(date, booking.end_time)
                })
    
    print(f"[DEBUG] Populated staff bookings")
    
    # Track which slots we've already added to avoid duplicates
    added_slots = set()
    
    current_slot = slot_start
    while current_slot + timedelta(minutes=duration_minutes) <= slot_end and len(available_slots) < max_slots:
        slot_start_time = current_slot.time()
        slot_end_time = (current_slot + timedelta(minutes=duration_minutes)).time()
        
        slot_key = f"{slot_start_time.strftime('%H:%M')}-{slot_end_time.strftime('%H:%M')}"
        
        # Skip if we already added this slot
        if slot_key in added_slots:
            current_slot += timedelta(minutes=slot_interval)
            continue
        
        # Check if any staff member is available for this slot
        for staff in qualified_staff:
            staff_id = str(staff.id)
            
            # First check if staff has any service assignments
            has_service_assignment = StaffServiceAssignment.objects.filter(
                staff_member=staff
            ).exists()
            
            if not has_service_assignment:
                print(f"[DEBUG] Staff {staff_id} has no service assignments - skipping")
                continue
            
            # Check if staff has an overlapping booking
            has_overlap = False
            slot_start_dt = datetime.combine(date, slot_start_time)
            slot_end_dt = datetime.combine(date, slot_end_time)
            
            for booking in staff_bookings.get(staff_id, []):
                if (slot_start_dt < booking['end'] and slot_end_dt > booking['start']):
                    has_overlap = True
                    break
            
            if has_overlap:
                print(f"[DEBUG] Staff {staff_id} has overlapping booking")
                continue
                
            # Check staff availability
            if is_staff_available(staff, date, slot_start_time, slot_end_time):
                print(f"[DEBUG] Staff {staff_id} is available")
                # Add this slot to available slots
                available_slots.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'time': slot_start_time.strftime('%H:%M'),
                    'end_time': slot_end_time.strftime('%H:%M'),
                    'staff': {
                        'id': str(staff.id),
                        'name': staff.get_full_name()
                    }
                })
                
                # Mark this slot as added
                added_slots.add(slot_key)
                
                # Also mark this time as booked for this staff member to avoid suggesting overlapping slots
                staff_bookings[staff_id].append({
                    'start': slot_start_dt,
                    'end': slot_end_dt
                })
                
                break  # Found an available staff for this slot
        
        # Move to next slot
        current_slot += timedelta(minutes=slot_interval)
    
    print(f"[DEBUG] Found {len(available_slots)} available slots")
    for slot in available_slots:
        print(f"[DEBUG] Available slot: {slot['date']} {slot['time']}-{slot['end_time']} with {slot['staff']['name']}")
    
    return available_slots

def is_staff_available(staff, booking_date, booking_start_time, booking_end_time):
    """
    Check if a staff member is available at the given date and time.
    
    Args:
        staff (StaffMember): Staff member to check
        booking_date (date): Date of the booking
        booking_start_time (time): Start time of the booking
        booking_end_time (time): End time of the booking
        
    Returns:
        bool: True if staff is available, False otherwise
    """
    print(f"[DEBUG] is_staff_available called with: staff={staff.id}, booking_date={booking_date}, booking_start_time={booking_start_time}, booking_end_time={booking_end_time}")
    
    weekday = booking_date.weekday()
    
    # First check specific date availability/unavailability (higher priority)
    try:
        specific_availabilities = staff.availability.filter(
            availability_type=AVAILABILITY_TYPE.SPECIFIC,
            specific_date=booking_date
        )
        
        print(f"[DEBUG] Found {specific_availabilities.count()} specific date availabilities")
        
        if specific_availabilities.exists():
            # Check if any specific date rule marks this time as unavailable
            for avail in specific_availabilities:
                if avail.off_day:
                    # This is an "off day" record - check if time overlaps with the off period
                    if (booking_start_time < avail.end_time and booking_end_time > avail.start_time):
                        print(f"[DEBUG] Staff {staff.id} has off day record overlapping with booking time")
                        return False
                else:
                    # This is an "available" record - check if time is fully contained in the available period
                    # Handle case where booking crosses midnight
                    if booking_end_time < booking_start_time:  # Crosses midnight
                        # For bookings that cross midnight, check if the start time is within the available period
                        # and the available period extends to midnight
                        if (booking_start_time >= avail.start_time and avail.end_time >= time(23, 59)):
                            print(f"[DEBUG] Staff {staff.id} has available record containing booking start time (crosses midnight)")
                            return True
                    else:  # Normal case: both start and end times are on the same day
                        if (booking_start_time >= avail.start_time and booking_end_time <= avail.end_time):
                            print(f"[DEBUG] Staff {staff.id} has available record containing booking time")
                            return True
            
            # If we have specific date rules but none explicitly allow this time, staff is unavailable
            print(f"[DEBUG] Staff {staff.id} has specific date rules but none allow this time")
            return False
        
        # Check weekly availability if no specific date rules exist
        weekly_availabilities = staff.availability.filter(
            availability_type=AVAILABILITY_TYPE.WEEKLY,
            weekday=weekday
        )
        
        print(f"[DEBUG] Found {weekly_availabilities.count()} weekly availabilities")
        
        if weekly_availabilities.exists():
            # Check if any weekly rule marks this time as unavailable
            for avail in weekly_availabilities:
                if avail.off_day:
                    # This is an "off day" record - check if time overlaps with the off period
                    if (booking_start_time < avail.end_time and booking_end_time > avail.start_time):
                        print(f"[DEBUG] Staff {staff.id} has off day record overlapping with booking time")
                        return False
                else:
                    # This is an "available" record - check if time is fully contained in the available period
                    # Handle case where booking crosses midnight
                    if booking_end_time < booking_start_time:  # Crosses midnight
                        # For bookings that cross midnight, check if the start time is within the available period
                        # and the available period extends to midnight
                        if (booking_start_time >= avail.start_time and avail.end_time >= time(23, 59)):
                            print(f"[DEBUG] Staff {staff.id} has available record containing booking start time (crosses midnight)")
                            return True
                    else:  # Normal case: both start and end times are on the same day
                        if (booking_start_time >= avail.start_time and booking_end_time <= avail.end_time):
                            print(f"[DEBUG] Staff {staff.id} has available record containing booking time")
                            return True
            
            # If we have weekly rules but none explicitly allow this time, staff is unavailable
            print(f"[DEBUG] Staff {staff.id} has weekly rules but none allow this time")
            return False
        
        # If no availability rules exist for this day, staff is NOT available
        # Staff must have explicit availability set to be bookable
        print(f"[DEBUG] Staff {staff.id} has no availability rules for this day - NOT AVAILABLE")
        return False

    except Exception as e:
        import traceback
        print(f"[DEBUG] Error checking staff availability: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        # If there's an error, assume staff is available to avoid blocking bookings
        return True
