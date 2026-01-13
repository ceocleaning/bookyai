// booking-preferences.js - Manage booking event types and reminder types

document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                     document.querySelector('meta[name="csrf-token"]')?.content;
    
    // Initialize modals
    const editEventModalEl = document.getElementById('editEventModal');
    const editReminderModalEl = document.getElementById('editReminderModal');
    
    const editEventModal = editEventModalEl ? new bootstrap.Modal(editEventModalEl) : null;
    const editReminderModal = editReminderModalEl ? new bootstrap.Modal(editReminderModalEl) : null;
    
    // Initialize drag-and-drop for event types
    const eventTypesTable = document.getElementById('eventTypesTable');
    if (eventTypesTable && typeof Sortable !== 'undefined') {
        new Sortable(eventTypesTable, {
            handle: '.handle',
            animation: 150,
            onEnd: async function(evt) {
                // Update display_order for all items
                const rows = eventTypesTable.querySelectorAll('tr');
                const updates = [];
                
                rows.forEach((row, index) => {
                    const eventId = row.dataset.eventId;
                    if (eventId) {
                        updates.push(updateEventType(eventId, { display_order: index }));
                    }
                });
                
                await Promise.all(updates);
                showAlert('success', 'Event types reordered successfully');
            }
        });
    }
    
    // Initialize drag-and-drop for reminder types
    const reminderTypesTable = document.getElementById('reminderTypesTable');
    if (reminderTypesTable && typeof Sortable !== 'undefined') {
        new Sortable(reminderTypesTable, {
            handle: '.handle',
            animation: 150,
            onEnd: async function(evt) {
                // Update display_order for all items
                const rows = reminderTypesTable.querySelectorAll('tr');
                const updates = [];
                
                rows.forEach((row, index) => {
                    const reminderId = row.dataset.reminderId;
                    if (reminderId) {
                        updates.push(updateReminderType(reminderId, { display_order: index }));
                    }
                });
                
                await Promise.all(updates);
                showAlert('success', 'Reminder types reordered successfully');
            }
        });
    }
    
    // Event Type Toggle Handlers
    document.querySelectorAll('.event-enabled-toggle').forEach(toggle => {
        toggle.addEventListener('change', async function() {
            const eventId = this.dataset.eventId;
            const isEnabled = this.checked;
            
            await updateEventType(eventId, { is_enabled: isEnabled });
            
            // Enable/disable related toggles
            const row = this.closest('tr');
            const timelineToggle = row.querySelector('.event-timeline-toggle');
            const reasonToggle = row.querySelector('.event-reason-toggle');
            
            timelineToggle.disabled = !isEnabled;
            reasonToggle.disabled = !isEnabled;
        });
    });
    
    document.querySelectorAll('.event-timeline-toggle').forEach(toggle => {
        toggle.addEventListener('change', async function() {
            const eventId = this.dataset.eventId;
            const showInTimeline = this.checked;
            
            await updateEventType(eventId, { show_in_timeline: showInTimeline });
        });
    });
    
    document.querySelectorAll('.event-reason-toggle').forEach(toggle => {
        toggle.addEventListener('change', async function() {
            const eventId = this.dataset.eventId;
            const requiresReason = this.checked;
            
            await updateEventType(eventId, { requires_reason: requiresReason });
        });
    });
    
    // Edit Event Type Button
    document.querySelectorAll('.edit-event-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const eventId = this.dataset.eventId;
            const eventName = this.dataset.eventName;
            const eventIcon = this.dataset.eventIcon;
            const eventColor = this.dataset.eventColor;
            
            document.getElementById('editEventId').value = eventId;
            document.getElementById('editEventName').value = eventName;
            document.getElementById('editEventIcon').value = eventIcon;
            document.getElementById('editEventColor').value = eventColor;
            
            // Fetch current allowed_roles from backend
            try {
                const response = await fetch(`/business/event-type/${eventId}/get/`);
                const result = await response.json();
                
                if (result.success) {
                    const allowedRoles = result.event_type.allowed_roles || [];
                    
                    // Uncheck all role checkboxes first
                    const roleBusinessOwner = document.getElementById('roleBusinessOwner');
                    const roleStaff = document.getElementById('roleStaff');
                    const roleCustomer = document.getElementById('roleCustomer');

                    if (roleBusinessOwner) roleBusinessOwner.checked = false;
                    if (roleStaff) roleStaff.checked = false;
                    if (roleCustomer) roleCustomer.checked = false;
                    
                    // Check the roles that are allowed
                    if (allowedRoles.includes('business') && roleBusinessOwner) {
                        roleBusinessOwner.checked = true;
                    }
                    if (allowedRoles.includes('staff') && roleStaff) {
                        roleStaff.checked = true;
                    }
                    if (allowedRoles.includes('customer') && roleCustomer) {
                        roleCustomer.checked = true;
                    }
                }
            } catch (error) {
                console.error('Error fetching event type details:', error);
            }
            
            if (editEventModal) editEventModal.show();
        });
    });
    
    // Save Event Type Changes
    const saveEventBtn = document.getElementById('saveEventBtn');
    if (saveEventBtn) {
        saveEventBtn.addEventListener('click', async function() {
            const editEventId = document.getElementById('editEventId');
            const editEventName = document.getElementById('editEventName');
            const editEventIcon = document.getElementById('editEventIcon');
            const editEventColor = document.getElementById('editEventColor');

            if (!editEventId || !editEventName || !editEventIcon || !editEventColor) return;

            const eventId = editEventId.value;
            const name = editEventName.value;
            const icon = editEventIcon.value;
            const color = editEventColor.value;
            
            // Collect selected roles
            const allowedRoles = [];
            const roleBusinessOwner = document.getElementById('roleBusinessOwner');
            const roleStaff = document.getElementById('roleStaff');
            const roleCustomer = document.getElementById('roleCustomer');

            if (roleBusinessOwner?.checked) {
                allowedRoles.push('business');
            }
            if (roleStaff?.checked) {
                allowedRoles.push('staff');
            }
            if (roleCustomer?.checked) {
                allowedRoles.push('customer');
            }
            
            if (!name || !icon || !color) {
                showAlert('danger', 'Please fill in all fields');
                return;
            }
            
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
            
            const success = await updateEventType(eventId, { name, icon, color, allowed_roles: allowedRoles });
            
            if (success) {
                if (editEventModal) editEventModal.hide();
                setTimeout(() => window.location.reload(), 1000);
            }
            
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-save me-2"></i>Save Changes';
        });
    }
    
    // Reminder Type Toggle Handlers
    document.querySelectorAll('.reminder-enabled-toggle').forEach(toggle => {
        toggle.addEventListener('change', async function() {
            const reminderId = this.dataset.reminderId;
            const isEnabled = this.checked;
            
            await updateReminderType(reminderId, { is_enabled: isEnabled });
            
            // Enable/disable hours input
            const row = this.closest('tr');
            const hoursInput = row.querySelector('.reminder-hours-input');
            hoursInput.disabled = !isEnabled;
        });
    });
    
    // Reminder Hours Input Handler (with debounce)
    let hoursTimeout;
    document.querySelectorAll('.reminder-hours-input').forEach(input => {
        input.addEventListener('change', function() {
            clearTimeout(hoursTimeout);
            const reminderId = this.dataset.reminderId;
            const hours = parseInt(this.value);
            
            if (hours < 1 || hours > 168) {
                showAlert('danger', 'Hours must be between 1 and 168');
                return;
            }
            
            hoursTimeout = setTimeout(async () => {
                await updateReminderType(reminderId, { default_hours_before: hours });
            }, 500);
        });
    });
    
    // Edit Reminder Type Button
    document.querySelectorAll('.edit-reminder-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const reminderId = this.dataset.reminderId;
            const reminderName = this.dataset.reminderName;
            const reminderIcon = this.dataset.reminderIcon;
            
            document.getElementById('editReminderId').value = reminderId;
            document.getElementById('editReminderName').value = reminderName;
            document.getElementById('editReminderIcon').value = reminderIcon;
            
            if (editReminderModal) editReminderModal.show();
        });
    });
    
    // Save Reminder Type Changes
    const saveReminderBtn = document.getElementById('saveReminderBtn');
    if (saveReminderBtn) {
        saveReminderBtn.addEventListener('click', async function() {
            const reminderId = document.getElementById('editReminderId').value;
            const name = document.getElementById('editReminderName').value;
            const icon = document.getElementById('editReminderIcon').value;
            
            if (!name || !icon) {
                showAlert('danger', 'Please fill in all fields');
                return;
            }
            
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
            
            const success = await updateReminderType(reminderId, { name, icon });
            
            if (success) {
                if (editReminderModal) editReminderModal.hide();
                setTimeout(() => window.location.reload(), 1000);
            }
            
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-save me-2"></i>Save Changes';
        });
    }
    
    // Helper Functions
    async function updateEventType(eventId, data) {
        try {
            const response = await fetch(`/business/event-type/${eventId}/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showAlert('success', result.message);
                return true;
            } else {
                showAlert('danger', result.message);
                return false;
            }
        } catch (error) {
            showAlert('danger', 'An error occurred while updating event type');
            return false;
        }
    }
    
    async function updateReminderType(reminderId, data) {
        try {
            const response = await fetch(`/business/reminder-type/${reminderId}/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showAlert('success', result.message);
                return true;
            } else {
                showAlert('danger', result.message);
                return false;
            }
        } catch (error) {
            showAlert('danger', 'An error occurred while updating reminder type');
            return false;
        }
    }
    
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }
});
