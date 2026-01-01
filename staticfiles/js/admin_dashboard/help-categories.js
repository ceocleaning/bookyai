/**
 * Help Categories - Admin Dashboard
 * Handles category delete operations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get delete modal elements
    const deleteCategoryModalEl = document.getElementById('deleteCategoryModal');
    const confirmDeleteCategoryBtn = document.getElementById('confirmDeleteCategoryBtn');
    const deleteCategoryName = document.getElementById('deleteCategoryName');
    const deleteWarning = document.getElementById('deleteWarning');
    const articleCount = document.getElementById('articleCount');

    let deleteCategoryModal = null;
    let currentDeleteId = null;
    let hasArticles = false;

    // Initialize delete modal
    if (deleteCategoryModalEl) {
        deleteCategoryModal = new bootstrap.Modal(deleteCategoryModalEl);
    }

    // Delete category buttons
    const deleteButtons = document.querySelectorAll('.btn-action-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            currentDeleteId = this.dataset.categoryId;
            const categoryNameVal = this.dataset.categoryName;
            const articlesCount = parseInt(this.dataset.hasArticles) || 0;
            
            deleteCategoryName.textContent = categoryNameVal;
            hasArticles = articlesCount > 0;

            // Show/hide warning based on article count
            if (hasArticles) {
                articleCount.textContent = articlesCount;
                deleteWarning.style.display = 'block';
                confirmDeleteCategoryBtn.disabled = true;
                confirmDeleteCategoryBtn.innerHTML = '<i class="fas fa-ban me-2"></i>Cannot Delete';
            } else {
                deleteWarning.style.display = 'none';
                confirmDeleteCategoryBtn.disabled = false;
                confirmDeleteCategoryBtn.innerHTML = '<i class="fas fa-trash me-2"></i>Delete Category';
            }

            if (deleteCategoryModal) {
                deleteCategoryModal.show();
            }
        });
    });

    // Confirm delete
    if (confirmDeleteCategoryBtn) {
        confirmDeleteCategoryBtn.addEventListener('click', function() {
            if (currentDeleteId && !hasArticles) {
                deleteCategory(currentDeleteId);
            }
        });
    }

    function deleteCategory(categoryId) {
        confirmDeleteCategoryBtn.disabled = true;
        confirmDeleteCategoryBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Deleting...';

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        fetch(`/admin-dashboard/help-categories/${categoryId}/delete/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Category deleted successfully', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification(data.message || 'Failed to delete category', 'error');
                confirmDeleteCategoryBtn.disabled = false;
                confirmDeleteCategoryBtn.innerHTML = '<i class="fas fa-trash me-2"></i>Delete Category';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while deleting the category', 'error');
            confirmDeleteCategoryBtn.disabled = false;
            confirmDeleteCategoryBtn.innerHTML = '<i class="fas fa-trash me-2"></i>Delete Category';
        })
        .finally(() => {
            currentDeleteId = null;
        });
    }

    // Show notification
    function showNotification(message, type = 'info') {
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

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
});
