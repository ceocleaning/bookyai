// Subscription Plans Admin JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Feature Management
    initializeFeatureManagement();
    
    // Toggle Status Buttons
    initializeToggleStatus();
    
    // Form Submission
    initializeFormSubmission();
});

/**
 * Initialize dynamic feature management
 */
function initializeFeatureManagement() {
    const addFeatureBtn = document.getElementById('addFeature');
    const featuresContainer = document.getElementById('featuresContainer');
    
    if (!addFeatureBtn || !featuresContainer) return;
    
    // Add new feature input
    addFeatureBtn.addEventListener('click', function() {
        const featureItem = document.createElement('div');
        featureItem.className = 'feature-item mb-2';
        featureItem.innerHTML = `
            <div class="input-group">
                <input type="text" class="form-control feature-input" placeholder="Enter feature">
                <button type="button" class="btn btn-outline-danger remove-feature">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        featuresContainer.appendChild(featureItem);
        
        // Focus on new input
        featureItem.querySelector('.feature-input').focus();
    });
    
    // Remove feature (event delegation)
    featuresContainer.addEventListener('click', function(e) {
        if (e.target.closest('.remove-feature')) {
            const featureItem = e.target.closest('.feature-item');
            
            // Keep at least one feature input
            if (featuresContainer.querySelectorAll('.feature-item').length > 1) {
                featureItem.style.opacity = '0';
                featureItem.style.transform = 'translateX(-20px)';
                setTimeout(() => featureItem.remove(), 300);
            } else {
                // Clear the input instead of removing
                featureItem.querySelector('.feature-input').value = '';
            }
        }
    });
}

/**
 * Initialize toggle status functionality
 */
function initializeToggleStatus() {
    const toggleButtons = document.querySelectorAll('.toggle-status');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const planId = this.dataset.planId;
            const currentStatus = this.dataset.currentStatus === 'true';
            
            if (!confirm(`Are you sure you want to ${currentStatus ? 'deactivate' : 'activate'} this plan?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/admin-dashboard/subscription-plans/${planId}/toggle-status/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Show success message
                    showToast('Success', data.message, 'success');
                    
                    // Reload page to reflect changes
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showToast('Error', data.message || 'Failed to toggle status', 'error');
                }
            } catch (error) {
                console.error('Error toggling status:', error);
                showToast('Error', 'An error occurred. Please try again.', 'error');
            }
        });
    });
}

/**
 * Initialize form submission
 */
function initializeFormSubmission() {
    const planForm = document.getElementById('planForm');
    
    if (!planForm) return;
    
    planForm.addEventListener('submit', function(e) {
        // Collect features from inputs
        const featureInputs = document.querySelectorAll('.feature-input');
        const features = [];
        
        featureInputs.forEach(input => {
            const value = input.value.trim();
            if (value) {
                features.push(value);
            }
        });
        
        // Set features JSON
        document.getElementById('featuresJson').value = JSON.stringify(features);
        
        // Validate
        if (features.length === 0) {
            e.preventDefault();
            showToast('Validation Error', 'Please add at least one feature', 'warning');
            return false;
        }
    });
}

/**
 * Get CSRF token from cookies
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Show toast notification
 */
function showToast(title, message, type = 'info') {
    // Check if Bootstrap toast is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        // Use Bootstrap toast if available
        const toastHTML = `
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'warning'} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <strong>${title}</strong><br>${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
    } else {
        // Fallback to alert
        alert(`${title}: ${message}`);
    }
}

/**
 * Initialize existing features on edit page
 */
if (typeof window.existingFeatures !== 'undefined' && window.existingFeatures.length > 0) {
    // Features are already rendered in the template
    console.log('Loaded existing features:', window.existingFeatures);
}
