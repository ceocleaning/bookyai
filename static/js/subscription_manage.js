/**
 * Subscription Management Page JavaScript
 * Handles interactive features for the subscription management page
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Subscription management page loaded');
    
    // Initialize any interactive features here
    initializeSubscriptionPage();
});

/**
 * Initialize subscription page features
 */
function initializeSubscriptionPage() {
    // Add smooth scroll for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                e.preventDefault();
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // Add animation on scroll for cards
    observeElements();
}

/**
 * Observe elements for scroll animations
 */
function observeElements() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe cards and sections
    const elements = document.querySelectorAll('.status-card, .plan-card, .invoice-card, .history-table');
    elements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });
}

/**
 * Format currency values
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Format dates
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

/**
 * Show confirmation dialog for subscription changes
 */
function confirmSubscriptionChange(action) {
    return confirm(`Are you sure you want to ${action} your subscription?`);
}

/**
 * Handle plan upgrade clicks
 */
function handlePlanUpgrade(planName) {
    if (confirmSubscriptionChange(`upgrade to ${planName}`)) {
        // Redirect to pricing page or Stripe checkout
        window.location.href = '/pricing/';
    }
}

/**
 * Copy invoice number to clipboard
 */
function copyInvoiceNumber(invoiceNumber) {
    navigator.clipboard.writeText(invoiceNumber).then(() => {
        showToast('Invoice number copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy invoice number:', err);
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add to toast container
    const toastContainer = document.querySelector('.toast-container');
    if (toastContainer) {
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 3000 });
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

/**
 * Export functions for use in templates
 */
window.subscriptionManagement = {
    handlePlanUpgrade,
    copyInvoiceNumber,
    confirmSubscriptionChange,
    formatCurrency,
    formatDate
};
