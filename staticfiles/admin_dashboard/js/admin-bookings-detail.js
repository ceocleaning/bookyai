// admin-bookings-detail.js - Admin version of booking detail logic

document.addEventListener('DOMContentLoaded', function() {
    // Get booking ID from data attribute or URL
    // In admin URL: /admin-dashboard/businesses/<id>/bookings/<booking_id>/
    // So distinct from public URL. We need to grab the ID carefully.
    // The view should ideally pass the booking ID to a JS variable, but here we try to extract it.
    // Or we can rely on the data attributes in the buttons which usually have IDs.
    
    // Let's rely on window.BOOKING_ID if available, or parse URL.
    const urlParts = window.location.pathname.split('/').filter(Boolean);
    // URL structure: admin-dashboard / businesses / <bus_id> / bookings / <book_id> /
    let bookingId = urlParts[4]; // Adjust based on index (0-based: 0=admin-dashboard, 1=businesses, 2=id, 3=bookings, 4=book_id)
    
    if (!bookingId && window.BOOKING_ID) {
        bookingId = window.BOOKING_ID;
    }

    console.log("Booking ID parsed:", bookingId);
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                     document.querySelector('meta[name="csrf-token"]')?.content;
    
    // Initialize modals
    const cancelModalEl = document.getElementById('cancelBookingModal');
    const rescheduleModalEl = document.getElementById('rescheduleBookingModal');
    
    const cancelModal = cancelModalEl ? new bootstrap.Modal(cancelModalEl) : null;
    const rescheduleModal = rescheduleModalEl ? new bootstrap.Modal(rescheduleModalEl) : null;
    
    // Handle generic event actions
    document.querySelectorAll('.event-action').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const eventKey = this.dataset.eventKey;
            const eventTypeId = this.closest('li').querySelector('[data-event-key]')?.dataset.eventTypeId || 
                               this.dataset.eventTypeId;
            
            // Special handling for cancel and reschedule
            if (eventKey === 'cancelled' && cancelModal) {
                cancelModal.show();
                return;
            }
            if (eventKey === 'rescheduled' && rescheduleModal) {
                rescheduleModal.show();
                return;
            }
            
            // Use generic modal for other events
            if (typeof showEventModal === 'function') {
                showEventModal(eventKey, eventTypeId);
            }
        });
    });
    
    // Handle generic event modal submission
    const eventModalSubmit = document.getElementById('eventModalSubmit');
    if (eventModalSubmit) {
        eventModalSubmit.addEventListener('click', async function() {
            const eventKey = this.dataset.eventKey;
            const eventTypeId = this.dataset.eventTypeId;
            const config = JSON.parse(this.dataset.config || '{}');
            
            // Collect form data
            const formData = {};
            config.fields.forEach(field => {
                if (field.type === 'alert') return;
                
                const element = document.getElementById(field.id);
                if (!element) return;
                
                if (field.type === 'checkbox') {
                    formData[field.id] = element.checked;
                } else {
                    formData[field.id] = element.value;
                }
            });
            
            // Validate required fields
            const missingFields = config.fields
                .filter(f => f.required && !formData[f.id])
                .map(f => f.label);
            
            if (missingFields.length > 0) {
                showAlert('danger', `Please fill in: ${missingFields.join(', ')}`);
                return;
            }
            
            // Submit to backend - Uses main app endpoint
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            
            try {
                const response = await fetch(`/bookings/${bookingId}/trigger-event/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        event_type_id: eventTypeId,
                        event_key: eventKey,
                        data: formData
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    bootstrap.Modal.getInstance(document.getElementById('eventModal')).hide();
                    showAlert('success', config.successMessage || result.message);
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showAlert('danger', result.message);
                }
            } catch (error) {
                console.error(error);
                showAlert('danger', 'An error occurred');
            } finally {
                this.disabled = false;
                this.innerHTML = `<i class="fas fa-check me-2"></i>${config.submitText}`;
            }
        });
    }
    
    // Cancel Booking Functionality
    const cancelBookingBtn = document.getElementById('cancelBookingBtn');
    const confirmCancelBtn = document.getElementById('confirmCancelBtn');
    const cancellationReason = document.getElementById('cancellationReason');
    
    if (cancelBookingBtn && cancelModal) {
        cancelBookingBtn.addEventListener('click', function(e) {
            e.preventDefault();
            cancelModal.show();
        });
    }
    
    if (confirmCancelBtn) {
        confirmCancelBtn.addEventListener('click', async function() {
            const reason = cancellationReason.value.trim();
            
            if (!reason) {
                cancellationReason.classList.add('is-invalid');
                return;
            }
            
            cancellationReason.classList.remove('is-invalid');
            confirmCancelBtn.disabled = true;
            confirmCancelBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Cancelling...';
            
            try {
                const response = await fetch(`/bookings/${bookingId}/cancel/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ reason })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    cancelModal.hide();
                    showAlert('success', data.message);
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showAlert('danger', data.message);
                    confirmCancelBtn.disabled = false;
                    confirmCancelBtn.innerHTML = '<i class="fas fa-times me-2"></i>Cancel Booking';
                }
            } catch (error) {
                showAlert('danger', 'An error occurred while cancelling the booking');
                confirmCancelBtn.disabled = false;
                confirmCancelBtn.innerHTML = '<i class="fas fa-times me-2"></i>Cancel Booking';
            }
        });
    }
    
    // Reschedule Booking Functionality
    const rescheduleBookingBtn = document.getElementById('rescheduleBookingBtn');
    const checkAvailabilityBtn = document.getElementById('checkAvailabilityBtn');
    const backToDateBtn = document.getElementById('backToDateBtn');
    const backToTimeslotsBtn = document.getElementById('backToTimeslotsBtn');
    const confirmRescheduleBtn = document.getElementById('confirmRescheduleBtn');
    const rescheduleDate = document.getElementById('rescheduleDate');
    const rescheduleReason = document.getElementById('rescheduleReason');
    
    let selectedSlot = null;
    
    if (rescheduleBookingBtn && rescheduleModal) {
        rescheduleBookingBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Set minimum date to tomorrow
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            rescheduleDate.min = tomorrow.toISOString().split('T')[0];
            rescheduleModal.show();
        });
    }
    
    if (checkAvailabilityBtn) {
        checkAvailabilityBtn.addEventListener('click', async function() {
            const date = rescheduleDate.value;
            
            if (!date) {
                rescheduleDate.classList.add('is-invalid');
                return;
            }
            
            rescheduleDate.classList.remove('is-invalid');
            checkAvailabilityBtn.disabled = true;
            checkAvailabilityBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
            
            try {
                const response = await fetch(`/bookings/${bookingId}/available-timeslots/?date=${date}`);
                const data = await response.json();
                
                if (data.success) {
                    displayTimeslots(data.timeslots, date, data.duration);
                    document.getElementById('rescheduleStep1').style.display = 'none';
                    document.getElementById('rescheduleStep2').style.display = 'block';
                } else {
                    showAlert('danger', data.message);
                }
            } catch (error) {
                showAlert('danger', 'An error occurred while fetching available timeslots');
            } finally {
                checkAvailabilityBtn.disabled = false;
                checkAvailabilityBtn.innerHTML = '<i class="fas fa-search me-2"></i>Check Available Times';
            }
        });
    }
    
    function displayTimeslots(timeslots, date, duration) {
        const container = document.getElementById('timeslotsContainer');
        const noSlotsMsg = document.getElementById('noTimeslotsMessage');
        const selectedDateDisplay = document.getElementById('selectedDateDisplay');
        
        // Format date for display
        const dateObj = new Date(date + 'T00:00:00');
        selectedDateDisplay.textContent = dateObj.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        
        container.innerHTML = '';
        
        const availableSlots = timeslots.filter(slot => slot.available);
        
        if (availableSlots.length === 0) {
            noSlotsMsg.style.display = 'block';
            return;
        }
        
        noSlotsMsg.style.display = 'none';
        
        availableSlots.forEach(slot => {
            const slotBtn = document.createElement('button');
            slotBtn.type = 'button';
            slotBtn.className = 'timeslot-btn';
            
            // Format end time for display
            const endTimeObj = new Date(`2000-01-01T${slot.end_time}`);
            const displayEndTime = endTimeObj.toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit',
                hour12: true 
            });
            
            slotBtn.innerHTML = `
                <div class="timeslot-time">${slot.display_time}</div>
                <div class="timeslot-separator">-</div>
                <div class="timeslot-time">${displayEndTime}</div>
                <div class="timeslot-duration">${duration} min</div>
            `;
            slotBtn.dataset.startTime = slot.start_time;
            slotBtn.dataset.endTime = slot.end_time;
            slotBtn.dataset.displayTime = slot.display_time;
            slotBtn.dataset.displayEndTime = displayEndTime;
            
            slotBtn.addEventListener('click', function() {
                // Remove active class from all slots
                document.querySelectorAll('.timeslot-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                
                // Add active class to selected slot
                this.classList.add('active');
                
                selectedSlot = {
                    date: date,
                    startTime: this.dataset.startTime,
                    endTime: this.dataset.endTime,
                    displayTime: this.dataset.displayTime,
                    displayEndTime: this.dataset.displayEndTime
                };
                
                // Show step 3 while keeping step 1 and 2 visible but disabled
                document.getElementById('rescheduleStep3').style.display = 'block';
                document.getElementById('newAppointmentTime').textContent = 
                    `${selectedDateDisplay.textContent} from ${selectedSlot.displayTime} to ${selectedSlot.displayEndTime}`;
                confirmRescheduleBtn.style.display = 'inline-block';
            });
            
            container.appendChild(slotBtn);
        });
    }
    
    if (backToDateBtn) {
        backToDateBtn.addEventListener('click', function() {
            document.getElementById('rescheduleStep2').style.display = 'none';
            document.getElementById('rescheduleStep1').style.display = 'block';
        });
    }
    
    if (backToTimeslotsBtn) {
        backToTimeslotsBtn.addEventListener('click', function() {
            document.getElementById('rescheduleStep3').style.display = 'none';
            confirmRescheduleBtn.style.display = 'none';
            // Clear selection
            document.querySelectorAll('.timeslot-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            selectedSlot = null;
        });
    }
    
    if (confirmRescheduleBtn) {
        confirmRescheduleBtn.addEventListener('click', async function() {
            const reason = rescheduleReason.value.trim();
            
            if (!reason) {
                rescheduleReason.classList.add('is-invalid');
                return;
            }
            
            if (!selectedSlot) {
                showAlert('danger', 'Please select a time slot');
                return;
            }
            
            rescheduleReason.classList.remove('is-invalid');
            confirmRescheduleBtn.disabled = true;
            confirmRescheduleBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Rescheduling...';
            
            try {
                const response = await fetch(`/bookings/${bookingId}/reschedule/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        new_date: selectedSlot.date,
                        new_start_time: selectedSlot.startTime,
                        new_end_time: selectedSlot.endTime,
                        reason: reason
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    if (rescheduleModal) rescheduleModal.hide();
                    showAlert('success', data.message);
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showAlert('danger', data.message);
                    confirmRescheduleBtn.disabled = false;
                    confirmRescheduleBtn.innerHTML = '<i class="fas fa-calendar-check me-2"></i>Confirm Reschedule';
                }
            } catch (error) {
                showAlert('danger', 'An error occurred while rescheduling the booking');
                confirmRescheduleBtn.disabled = false;
                confirmRescheduleBtn.innerHTML = '<i class="fas fa-calendar-check me-2"></i>Confirm Reschedule';
            }
        });
    }
    
    // Reset modals on close
    if (cancelModalEl) {
        cancelModalEl.addEventListener('hidden.bs.modal', function() {
            if (cancellationReason) {
                cancellationReason.value = '';
                cancellationReason.classList.remove('is-invalid');
            }
        });
    }
    
    if (rescheduleModalEl) {
        rescheduleModalEl.addEventListener('hidden.bs.modal', function() {
            rescheduleDate.value = '';
            rescheduleReason.value = '';
            rescheduleDate.classList.remove('is-invalid');
            rescheduleReason.classList.remove('is-invalid');
            
            const step1 = document.getElementById('rescheduleStep1');
            const step2 = document.getElementById('rescheduleStep2');
            const step3 = document.getElementById('rescheduleStep3');
            
            if (step1) step1.style.display = 'block';
            if (step2) step2.style.display = 'none';
            if (step3) step3.style.display = 'none';
            
            if (confirmRescheduleBtn) confirmRescheduleBtn.style.display = 'none';
            selectedSlot = null;
        });
    }
    
    // Helper function to show alerts
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        // Admin theme alert
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3 shadow-lg`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
});
