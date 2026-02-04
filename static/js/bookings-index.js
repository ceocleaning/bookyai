/**
 * bookings-index.js - JavaScript for the redesigned Bookings Management Page
 * Handles filters, view toggling, and date presets.
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeStatusFilters();
    initializeDatePresets();
    restoreViewPreference();
    initializeBulkActions();
});

/**
 * Handle bulk selection and deletion
 */
function initializeBulkActions() {
    const selectAll = document.getElementById('selectAllBookings');
    const checkboxes = document.querySelectorAll('.booking-checkbox');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');

    if (!selectAll || !bulkDeleteBtn) return;

    // Handle "Select All" click
    selectAll.addEventListener('change', function() {
        checkboxes.forEach(cb => {
            cb.checked = this.checked;
        });
        updateBulkDeleteVisibility();
    });

    // Handle individual checkbox clicks
    checkboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            // Update "Select All" state if all items are selected manually
            const allChecked = Array.from(checkboxes).every(c => c.checked);
            selectAll.checked = allChecked;
            
            // If at least one is unchecked, Select All should be unchecked
            const anyChecked = Array.from(checkboxes).some(c => c.checked);
            if (!anyChecked) selectAll.checked = false;
            
            updateBulkDeleteVisibility();
        });
    });

    function updateBulkDeleteVisibility() {
        const checkedCount = document.querySelectorAll('.booking-checkbox:checked').length;
        if (checkedCount > 0) {
            bulkDeleteBtn.classList.remove('d-none');
        } else {
            bulkDeleteBtn.classList.add('d-none');
        }
    }

    // Handle Bulk Delete Click
    bulkDeleteBtn.addEventListener('click', function() {
        const selectedIds = Array.from(document.querySelectorAll('.booking-checkbox:checked'))
                                .map(cb => cb.value);
        
        if (selectedIds.length === 0) return;

        if (confirm(`Are you sure you want to delete ${selectedIds.length} selected booking(s)? This action cannot be undone.`)) {
            performBulkDelete(selectedIds);
        }
    });

    async function performBulkDelete(ids) {
        // Show loading state
        bulkDeleteBtn.disabled = true;
        bulkDeleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const response = await fetch('/bookings/bulk-delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ booking_ids: ids })
            });

            const result = await response.json();

            if (result.status === 'success') {
                // Remove deleted rows from DOM
                ids.forEach(id => {
                    const row = document.querySelector(`tr[data-booking-id="${id}"]`);
                    if (row) row.remove();
                });
                
                // Refresh page if no bookings left on current page
                if (document.querySelectorAll('.booking-checkbox').length === 0) {
                    window.location.reload();
                } else {
                    // Update UI
                    selectAll.checked = false;
                    updateBulkDeleteVisibility();
                    showNotification(result.message, 'success');
                }
            } else {
                showNotification(result.message || 'Error occurred', 'error');
            }
        } catch (error) {
            console.error('Bulk delete error:', error);
            showNotification('Failed to connect to the server.', 'error');
        } finally {
            bulkDeleteBtn.disabled = false;
            bulkDeleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
        }
    }
}

/**
 * Get cookie by name
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
 * Handle quick status filter pills
 */
function initializeStatusFilters() {
    const statusPills = document.querySelectorAll('.pill-filter');
    const advancedStatusHidden = document.getElementById('hidden-status');
    const advancedFilterForm = document.getElementById('advanced-filter-form');
    
    statusPills.forEach(pill => {
        pill.addEventListener('click', function() {
            const status = this.getAttribute('data-status');
            
            // Update hidden input in advanced form to keep them in sync
            if (advancedStatusHidden) {
                advancedStatusHidden.value = status;
            }
            
            // Redirect with the new status filter
            const url = new URL(window.location.href);
            if (status) {
                url.searchParams.set('status', status);
            } else {
                url.searchParams.delete('status');
            }
            
            // Clear page param if it exists since results will change
            url.searchParams.delete('page');
            
            window.location.href = url.toString();
        });
    });
}

/**
 * Handle date presets in the advanced filter drawer
 */
function initializeDatePresets() {
    const presetBtns = document.querySelectorAll('.date-preset');
    const dateFromInput = document.getElementById('date_from');
    const dateToInput = document.getElementById('date_to');
    
    presetBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const preset = this.getAttribute('data-preset');
            const today = new Date();
            let fromDate, toDate;
            
            switch(preset) {
                case 'today':
                    fromDate = toDate = today;
                    break;
                case 'tomorrow':
                    const tomorrow = new Date(today);
                    tomorrow.setDate(today.getDate() + 1);
                    fromDate = toDate = tomorrow;
                    break;
                case 'this_week':
                    // Start of week (Sunday or Monday, using Monday here)
                    const day = today.getDay();
                    const diff = today.getDate() - day + (day === 0 ? -6 : 1);
                    fromDate = new Date(today.setDate(diff));
                    toDate = new Date(today.setDate(diff + 6));
                    break;
                case 'this_month':
                    fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
                    toDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
                    break;
            }
            
            if (fromDate && toDate) {
                dateFromInput.value = fromDate.toISOString().split('T')[0];
                dateToInput.value = toDate.toISOString().split('T')[0];
                
                // Active state feedback
                presetBtns.forEach(b => b.classList.remove('btn-primary'));
                presetBtns.forEach(b => b.classList.add('btn-outline-secondary'));
                this.classList.remove('btn-outline-secondary');
                this.classList.add('btn-primary');
            }
        });
    });
}

/**
 * Toggle between List and Card views
 * @param {string} viewType - 'list' or 'card'
 */
function toggleView(viewType) {
    const listView = document.getElementById('listView');
    const cardView = document.getElementById('cardView');
    const listViewBtn = document.getElementById('listViewBtn');
    const cardViewBtn = document.getElementById('cardViewBtn');
    
    if (viewType === 'list') {
        listView.style.display = 'block';
        cardView.style.display = 'none';
        listViewBtn.classList.add('active');
        cardViewBtn.classList.remove('active');
    } else {
        listView.style.display = 'none';
        cardView.style.display = 'block';
        listViewBtn.classList.remove('active');
        cardViewBtn.classList.add('active');
    }
    
    // Save preference to local storage
    localStorage.setItem('bookingViewPreference', viewType);
}

/**
 * Restore user's view preference on page load
 */
function restoreViewPreference() {
    const savedPreference = localStorage.getItem('bookingViewPreference');
    if (savedPreference) {
        toggleView(savedPreference);
    }
}

/**
 * Show temporary notification
 */
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `custom-toast ${type}`;
    toast.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
