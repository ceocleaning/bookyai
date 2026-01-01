/**
 * Help Articles Detail - Admin Dashboard
 * Handles article detail page actions
 */

document.addEventListener('DOMContentLoaded', function() {
    const deleteBtn = document.getElementById('deleteBtn');
    const duplicateBtn = document.getElementById('duplicateBtn');
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    // Delete article
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            deleteModal.show();
        });
    }

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            const articleId = deleteBtn.dataset.articleId;
            deleteArticle(articleId);
        });
    }

    function deleteArticle(articleId) {
        confirmDeleteBtn.disabled = true;
        confirmDeleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Deleting...';

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

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
                showNotification('Article deleted successfully', 'success');
                setTimeout(() => {
                    window.location.href = '/admin-dashboard/help-articles/';
                }, 1000);
            } else {
                showNotification(data.message || 'Failed to delete article', 'error');
                confirmDeleteBtn.disabled = false;
                confirmDeleteBtn.innerHTML = '<i class="fas fa-trash me-2"></i>Delete Article';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while deleting the article', 'error');
            confirmDeleteBtn.disabled = false;
            confirmDeleteBtn.innerHTML = '<i class="fas fa-trash me-2"></i>Delete Article';
        });
    }

    // Duplicate article
    if (duplicateBtn) {
        duplicateBtn.addEventListener('click', function() {
            const articleId = this.dataset.articleId;
            duplicateArticle(articleId);
        });
    }

    function duplicateArticle(articleId) {
        duplicateBtn.disabled = true;
        duplicateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Duplicating...</span>';

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        fetch(`/admin-dashboard/help-articles/${articleId}/duplicate/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Article duplicated successfully', 'success');
                setTimeout(() => {
                    window.location.href = `/admin-dashboard/help-articles/${data.new_article_id}/edit/`;
                }, 1000);
            } else {
                showNotification(data.message || 'Failed to duplicate article', 'error');
                duplicateBtn.disabled = false;
                duplicateBtn.innerHTML = '<i class="fas fa-copy"></i><span>Duplicate Article</span>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while duplicating the article', 'error');
            duplicateBtn.disabled = false;
            duplicateBtn.innerHTML = '<i class="fas fa-copy"></i><span>Duplicate Article</span>';
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
