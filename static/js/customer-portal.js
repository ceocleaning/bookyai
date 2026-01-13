// Customer Portal JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Booking cancellation confirmation
    const cancelButtons = document.querySelectorAll('.btn-cancel-booking');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to cancel this booking?')) {
                e.preventDefault();
            }
        });
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Business switcher
    const businessLinks = document.querySelectorAll('.business-switch-link');
    businessLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const businessId = this.dataset.businessId;
            const businessName = this.dataset.businessName;
            
            // Show loading state
            const spinner = document.createElement('span');
            spinner.className = 'loading-spinner ms-2';
            this.appendChild(spinner);
            
            // Navigate to switch business URL
            window.location.href = this.href;
        });
    });
    
    // Date picker initialization (if needed)
    const datePickers = document.querySelectorAll('input[type="date"]');
    datePickers.forEach(picker => {
        // Set min date to today for future bookings
        if (picker.classList.contains('future-date-only')) {
            const today = new Date().toISOString().split('T')[0];
            picker.setAttribute('min', today);
        }
    });
    
    // Notification preferences toggle
    const notificationToggles = document.querySelectorAll('.notification-toggle');
    notificationToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const label = this.closest('.form-check').querySelector('label');
            if (this.checked) {
                label.classList.add('text-success');
                label.classList.remove('text-secondary');
            } else {
                label.classList.add('text-secondary');
                label.classList.remove('text-success');
            }
        });
    });
    
    // Invoice payment modal (placeholder for future implementation)
    const paymentButtons = document.querySelectorAll('.btn-pay-invoice');
    paymentButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            // Payment modal logic will be implemented here
            console.log('Payment modal to be implemented');
        });
    });
    
    // Search functionality for bookings/invoices
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const items = document.querySelectorAll('.searchable-item');
            
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // Status filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const selectedStatus = this.value;
            const items = document.querySelectorAll('.filterable-item');
            
            items.forEach(item => {
                const itemStatus = item.dataset.status;
                if (selectedStatus === 'all' || itemStatus === selectedStatus) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
});

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

function formatTime(timeString) {
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
}
