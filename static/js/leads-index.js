/**
 * leads-index.js - JavaScript for the redesigned Leads Management Page
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
    const selectAll = document.getElementById('selectAllLeads');
    const checkboxes = document.querySelectorAll('.lead-checkbox');
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
            const allChecked = Array.from(checkboxes).every(c => c.checked);
            selectAll.checked = allChecked;
            
            const anyChecked = Array.from(checkboxes).some(c => c.checked);
            if (!anyChecked) selectAll.checked = false;
            
            updateBulkDeleteVisibility();
        });
    });

    function updateBulkDeleteVisibility() {
        const checkedCount = document.querySelectorAll('.lead-checkbox:checked').length;
        if (checkedCount > 0) {
            bulkDeleteBtn.classList.remove('d-none');
        } else {
            bulkDeleteBtn.classList.add('d-none');
        }
    }

    // Handle Bulk Delete Click
    bulkDeleteBtn.addEventListener('click', function() {
        const selectedIds = Array.from(document.querySelectorAll('.lead-checkbox:checked'))
                                .map(cb => cb.value);
        
        if (selectedIds.length === 0) return;

        if (confirm(`Are you sure you want to delete ${selectedIds.length} selected lead(s)? This action cannot be undone.`)) {
            performBulkDelete(selectedIds);
        }
    });

    async function performBulkDelete(ids) {
        bulkDeleteBtn.disabled = true;
        bulkDeleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const response = await fetch('/leads/bulk-delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ lead_ids: ids })
            });

            const result = await response.json();

            if (result.status === 'success') {
                ids.forEach(id => {
                    const row = document.querySelector(`tr[data-lead-id="${id}"]`);
                    if (row) row.remove();
                });
                
                if (document.querySelectorAll('.lead-checkbox').length === 0) {
                    window.location.reload();
                } else {
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

    // Handle Individual Delete from Card Menu
    document.querySelectorAll('.delete-lead-single').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            if (confirm('Are you sure you want to delete this lead? This action cannot be undone.')) {
                performBulkDelete([id]);
            }
        });
    });
}

/**
 * Handle quick status filter pills
 */
function initializeStatusFilters() {
    const statusPills = document.querySelectorAll('.pill-filter');
    
    statusPills.forEach(pill => {
        pill.addEventListener('click', function() {
            const status = this.getAttribute('data-status');
            const url = new URL(window.location.href);
            if (status) {
                url.searchParams.set('status', status);
            } else {
                url.searchParams.delete('status');
            }
            url.searchParams.delete('page');
            window.location.href = url.toString();
        });
    });
}

/**
 * Handle date presets
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
                case 'this_week':
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
                presetBtns.forEach(b => b.classList.replace('btn-primary', 'btn-outline-secondary'));
                this.classList.replace('btn-outline-secondary', 'btn-primary');
            }
        });
    });
}

/**
 * Toggle View
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
    localStorage.setItem('leadViewPreference', viewType);
}

function restoreViewPreference() {
    const savedPreference = localStorage.getItem('leadViewPreference');
    if (savedPreference) toggleView(savedPreference);
}

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
    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

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
