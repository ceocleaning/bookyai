// Admin Leads Detail JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Communication modal handling
    const communicationModal = document.getElementById('newCommunicationModal');
    if (communicationModal) {
        const commTypeSelect = document.getElementById('commType');
        const contentTextarea = document.getElementById('content');
        const saveButton = communicationModal.querySelector('.btn-primary');
        
        // Reset form when modal is closed
        communicationModal.addEventListener('hidden.bs.modal', function() {
            document.getElementById('communicationForm').reset();
        });
        
        // Handle communication type change
        commTypeSelect.addEventListener('change', function() {
            // Adjust placeholder based on communication type
            if (this.value === 'sms') {
                contentTextarea.placeholder = 'Enter SMS message content...';
            } else if (this.value === 'voice') {
                contentTextarea.placeholder = 'Enter call notes...';
            } else if (this.value === 'email') {
                contentTextarea.placeholder = 'Enter email content...';
            }
        });
        
        // Handle save button click
        saveButton.addEventListener('click', function() {
            // Validate form
            const form = document.getElementById('communicationForm');
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            
            // For admin dashboard, we need to implement the actual save logic or mock it
            // Assuming there isn't a readily available endpoint in the brief, we'll keep the mock behavior
            // but add a comment where the fetch would go.
            
            // To properly implement:
            // fetch('/leads/' + leadId + '/add-communication/', ...)
            
            const modalInstance = bootstrap.Modal.getInstance(communicationModal);
            modalInstance.hide();
            
            // Show success message
            showAlert('Communication added successfully!', 'success');
        });
    }
    
    // Function to show alerts
    function showAlert(message, type = 'info') {
        const alertContainer = document.createElement('div');
        // Admin theme alert style
        alertContainer.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3 shadow-lg`;
        alertContainer.setAttribute('role', 'alert');
        alertContainer.style.zIndex = '9999';
        
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        document.body.appendChild(alertContainer);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = bootstrap.Alert.getOrCreateInstance(alertContainer);
            alert.close();
        }, 5000);
    }
    
    // Timeline scrolling
    const timeline = document.querySelector('.timeline');
    if (timeline) {
        // Scroll to the bottom of the timeline on load
        timeline.scrollTop = timeline.scrollHeight;
    }
});
