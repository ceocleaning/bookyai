/**
 * Help Articles List - Admin Dashboard
 * Handles filtering, search, deletion, and bulk operations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const searchInput = document.getElementById('searchArticles');
    const filterCategory = document.getElementById('filterCategory');
    const filterStatus = document.getElementById('filterStatus');
    const resetFiltersBtn = document.getElementById('resetFilters');
    const selectAllCheckbox = document.getElementById('selectAll');
    const articleCheckboxes = document.querySelectorAll('.article-checkbox');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    
    // Delete Panel Elements
    const deletePanel = document.getElementById('deletePanel');
    const deletePanelOverlay = document.getElementById('deletePanelOverlay');
    const closeDeletePanel = document.getElementById('closeDeletePanel');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    const deleteArticleTitle = document.getElementById('deleteArticleTitle');
    
    let currentDeleteId = null;
    let selectedArticles = new Set();

    // Panel functions
    function showPanel() {
        deletePanel.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function hidePanel() {
        deletePanel.classList.remove('active');
        document.body.style.overflow = '';
    }

    // Close panel on overlay click
    if (deletePanelOverlay) {
        deletePanelOverlay.addEventListener('click', hidePanel);
    }

    // Close panel on close button
    if (closeDeletePanel) {
        closeDeletePanel.addEventListener('click', hidePanel);
    }

    // Close panel on cancel button
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', hidePanel);
    }

    // Close panel on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && deletePanel.classList.contains('active')) {
            hidePanel();
        }
    });

    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function(e) {
            filterArticles();
        }, 300));
    }

    // Category filter
    if (filterCategory) {
        filterCategory.addEventListener('change', function() {
            filterArticles();
        });
    }

    // Status filter
    if (filterStatus) {
        filterStatus.addEventListener('change', function() {
            filterArticles();
        });
    }

    // Reset filters
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            searchInput.value = '';
            filterCategory.value = '';
            filterStatus.value = '';
            filterArticles();
        });
    }

    // Filter articles function
    function filterArticles() {
        const searchTerm = searchInput.value.toLowerCase();
        const categoryFilter = filterCategory.value;
        const statusFilter = filterStatus.value;
        const rows = document.querySelectorAll('#articlesTableBody tr[data-article-id]');

        rows.forEach(row => {
            const title = row.querySelector('.article-title-cell strong')?.textContent.toLowerCase() || '';
            const slug = row.querySelector('.article-title-cell small')?.textContent.toLowerCase() || '';
            const category = row.querySelector('.badge-category')?.textContent.toLowerCase() || '';
            const status = row.querySelector('.badge-status')?.classList.contains('status-published') ? 'published' : 'draft';

            let showRow = true;

            // Search filter
            if (searchTerm && !title.includes(searchTerm) && !slug.includes(searchTerm)) {
                showRow = false;
            }

            // Category filter
            if (categoryFilter && !category.includes(categoryFilter.toLowerCase())) {
                showRow = false;
            }

            // Status filter
            if (statusFilter && status !== statusFilter) {
                showRow = false;
            }

            row.style.display = showRow ? '' : 'none';
        });

        updateEmptyState();
    }

    // Update empty state
    function updateEmptyState() {
        const visibleRows = document.querySelectorAll('#articlesTableBody tr[data-article-id]:not([style*="display: none"])');
        const emptyRow = document.querySelector('#articlesTableBody tr:not([data-article-id])');
        
        if (visibleRows.length === 0 && !emptyRow) {
            const tbody = document.getElementById('articlesTableBody');
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-5">
                        <div class="empty-state">
                            <i class="fas fa-search fa-3x mb-3 text-muted"></i>
                            <p class="text-muted">No articles found matching your criteria.</p>
                        </div>
                    </td>
                </tr>
            `;
        }
    }

    // Select all functionality
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            articleCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
                if (isChecked) {
                    selectedArticles.add(checkbox.value);
                } else {
                    selectedArticles.delete(checkbox.value);
                }
            });
            updateBulkDeleteButton();
        });
    }

    // Individual checkbox selection
    articleCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                selectedArticles.add(this.value);
            } else {
                selectedArticles.delete(this.value);
                selectAllCheckbox.checked = false;
            }
            updateBulkDeleteButton();
        });
    });

    // Update bulk delete button visibility
    function updateBulkDeleteButton() {
        if (bulkDeleteBtn) {
            bulkDeleteBtn.style.display = selectedArticles.size > 0 ? 'inline-flex' : 'none';
            bulkDeleteBtn.innerHTML = `
                <i class="fas fa-trash me-2"></i>
                Delete Selected (${selectedArticles.size})
            `;
        }
    }

    // Delete button click handlers
    const deleteButtons = document.querySelectorAll('.btn-action-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            currentDeleteId = this.dataset.articleId;
            const articleTitle = this.dataset.articleTitle;
            deleteArticleTitle.textContent = articleTitle;
            showPanel(); // Use slide-in panel
        });
    });

    // Confirm delete
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            if (currentDeleteId) {
                deleteArticle(currentDeleteId);
            }
        });
    }

    // Delete article function
    function deleteArticle(articleId) {
        // Show loading state
        confirmDeleteBtn.disabled = true;
        confirmDeleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Deleting...';

        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        // Send delete request
        fetch(`/admin-dashboard/help-articles/${articleId}/delete/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove row from table
                const row = document.querySelector(`tr[data-article-id="${articleId}"]`);
                if (row) {
                    row.style.transition = 'opacity 0.3s ease';
                    row.style.opacity = '0';
                    setTimeout(() => {
                        row.remove();
                        updateEmptyState();
                        updateStats();
                    }, 300);
                }

                // Show success message
                showNotification('Article deleted successfully', 'success');
                
                // Close panel
                hidePanel(); // Use slide-in panel
            } else {
                showNotification(data.message || 'Failed to delete article', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while deleting the article', 'error');
        })
        .finally(() => {
            confirmDeleteBtn.disabled = false;
            confirmDeleteBtn.innerHTML = '<i class="fas fa-trash me-2"></i>Delete Article';
            currentDeleteId = null;
        });
    }

    // Bulk delete
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', function() {
            if (selectedArticles.size === 0) return;

            if (confirm(`Are you sure you want to delete ${selectedArticles.size} article(s)? This action cannot be undone.`)) {
                bulkDeleteArticles(Array.from(selectedArticles));
            }
        });
    }

    // Bulk delete function
    function bulkDeleteArticles(articleIds) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        fetch('/admin-dashboard/help-articles/bulk-delete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ article_ids: articleIds })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove rows from table
                articleIds.forEach(id => {
                    const row = document.querySelector(`tr[data-article-id="${id}"]`);
                    if (row) {
                        row.style.transition = 'opacity 0.3s ease';
                        row.style.opacity = '0';
                        setTimeout(() => row.remove(), 300);
                    }
                });

                // Reset selection
                selectedArticles.clear();
                selectAllCheckbox.checked = false;
                updateBulkDeleteButton();
                
                // Update UI
                setTimeout(() => {
                    updateEmptyState();
                    updateStats();
                }, 300);

                showNotification(`${articleIds.length} article(s) deleted successfully`, 'success');
            } else {
                showNotification(data.message || 'Failed to delete articles', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while deleting articles', 'error');
        });
    }

    // Update statistics
    function updateStats() {
        // This would typically fetch updated stats from the server
        // For now, we'll just update the counts based on visible rows
        const totalArticles = document.querySelectorAll('#articlesTableBody tr[data-article-id]').length;
        const publishedArticles = document.querySelectorAll('.status-published').length;
        const draftArticles = document.querySelectorAll('.status-draft').length;

        document.getElementById('totalArticles').textContent = totalArticles;
        document.getElementById('publishedArticles').textContent = publishedArticles;
        document.getElementById('draftArticles').textContent = draftArticles;
    }

    // Show notification
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
            ${message}
        `;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'success' ? 'var(--admin-success)' : 'var(--admin-danger)'};
            color: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            z-index: 9999;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Export functionality
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            window.location.href = '/admin-dashboard/help-articles/export/';
        });
    }

    // Debounce helper function
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
