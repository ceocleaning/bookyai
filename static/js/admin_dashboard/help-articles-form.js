/**
 * Help Articles Form - Admin Dashboard
 * Handles article creation/editing with preview and auto-slug generation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const titleInput = document.getElementById('title');
    const slugInput = document.getElementById('slug');
    const contentEditor = document.getElementById('contentEditor');
    const isPublishedCheckbox = document.getElementById('isPublished');
    const publishStatusText = document.getElementById('publishStatusText');
    const articleForm = document.getElementById('articleForm');
    const editorButtons = document.querySelectorAll('.editor-btn');
    
    // Preview Panel Elements (No Modal)
    const previewPanel = document.getElementById('previewPanel');
    const previewOverlay = document.getElementById('previewOverlay');
    const closePanelBtn = document.getElementById('closePanelBtn');
    const closePanelFooterBtn = document.getElementById('closePanelFooterBtn');
    const previewContent = document.getElementById('previewContent');
    const toggleFullscreenBtn = document.getElementById('toggleFullscreenPanel');

    // Auto-generate slug from title
    if (titleInput && slugInput) {
        titleInput.addEventListener('input', function() {
            if (!slugInput.dataset.manuallyEdited) {
                slugInput.value = generateSlug(this.value);
            }
        });

        slugInput.addEventListener('input', function() {
            this.dataset.manuallyEdited = 'true';
        });
    }

    // Generate slug function
    function generateSlug(text) {
        return text
            .toLowerCase()
            .trim()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    // Publish status toggle
    if (isPublishedCheckbox && publishStatusText) {
        isPublishedCheckbox.addEventListener('change', function() {
            publishStatusText.textContent = this.checked ? 'Published' : 'Draft';
        });
    }

    // Editor toolbar actions
    editorButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const action = this.dataset.action;

            switch(action) {
                case 'bold':
                    insertMarkdown('**', '**', 'bold text');
                    break;
                case 'italic':
                    insertMarkdown('*', '*', 'italic text');
                    break;
                case 'heading':
                    insertMarkdown('## ', '', 'Heading');
                    break;
                case 'link':
                    insertLink();
                    break;
                case 'list':
                    insertList();
                    break;
                case 'code':
                    insertMarkdown('`', '`', 'code');
                    break;
                case 'preview':
                    showPreview();
                    break;
            }
        });
    });

    // Insert markdown helper
    function insertMarkdown(before, after, placeholder) {
        const start = contentEditor.selectionStart;
        const end = contentEditor.selectionEnd;
        const selectedText = contentEditor.value.substring(start, end);
        const textToInsert = selectedText || placeholder;
        const newText = before + textToInsert + after;

        contentEditor.setRangeText(newText, start, end, 'end');
        contentEditor.focus();

        // Select the inserted text (excluding markers)
        if (!selectedText) {
            contentEditor.setSelectionRange(start + before.length, start + before.length + placeholder.length);
        }
    }

    // Insert link
    function insertLink() {
        const url = prompt('Enter URL:');
        if (url) {
            const text = prompt('Enter link text:', 'link text');
            if (text) {
                const markdown = `[${text}](${url})`;
                const start = contentEditor.selectionStart;
                contentEditor.setRangeText(markdown, start, start, 'end');
                contentEditor.focus();
            }
        }
    }

    // Insert list
    function insertList() {
        const start = contentEditor.selectionStart;
        const listItems = '- Item 1\n- Item 2\n- Item 3';
        contentEditor.setRangeText(listItems, start, start, 'end');
        contentEditor.focus();
    }

    // Show preview (Panel instead of Modal)
    function showPreview() {
        const content = contentEditor.value;
        const title = titleInput.value || 'Untitled Article';
        const categorySelect = document.getElementById('category');
        const categoryText = categorySelect.options[categorySelect.selectedIndex]?.text || 'Uncategorized';
        
        // Update preview title
        document.getElementById('previewTitle').textContent = title;
        
        // Update preview category
        const categorySpan = document.querySelector('#previewCategory span');
        if (categorySpan) {
            categorySpan.textContent = categoryText;
        }
        
        // Update preview date
        const previewDate = document.getElementById('previewDate');
        if (previewDate) {
            const now = new Date();
            previewDate.textContent = now.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        }
        
        // Simple markdown to HTML conversion (basic)
        let html = content
            // Headers
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // Bold
            .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.*?)\*/gim, '<em>$1</em>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2">$1</a>')
            // Code
            .replace(/`([^`]+)`/gim, '<code>$1</code>')
            // Lists
            .replace(/^- (.*$)/gim, '<li>$1</li>')
            // Paragraphs
            .replace(/\n\n/gim, '</p><p>')
            // Line breaks
            .replace(/\n/gim, '<br>');

        // Wrap in paragraph if not already wrapped
        if (!html.startsWith('<')) {
            html = '<p>' + html + '</p>';
        }

        previewContent.innerHTML = html || '<p class="text-muted">No content to preview</p>';
        
        // Show panel
        previewPanel.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }

    // Close panel function
    function closePanel() {
        previewPanel.classList.remove('active');
        previewPanel.classList.remove('fullscreen');
        document.body.style.overflow = ''; // Restore scrolling
        
        // Reset fullscreen button
        if (toggleFullscreenBtn) {
            const icon = toggleFullscreenBtn.querySelector('i');
            icon.className = 'fas fa-expand';
            toggleFullscreenBtn.title = 'Toggle Fullscreen';
        }
    }

    // Close panel on button click
    if (closePanelBtn) {
        closePanelBtn.addEventListener('click', closePanel);
    }

    if (closePanelFooterBtn) {
        closePanelFooterBtn.addEventListener('click', closePanel);
    }

    // Close panel on overlay click
    if (previewOverlay) {
        previewOverlay.addEventListener('click', closePanel);
    }

    // Close panel on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && previewPanel.classList.contains('active')) {
            closePanel();
        }
    });

    // Fullscreen toggle for panel
    if (toggleFullscreenBtn) {
        toggleFullscreenBtn.addEventListener('click', function() {
            previewPanel.classList.toggle('fullscreen');
            const icon = this.querySelector('i');
            if (previewPanel.classList.contains('fullscreen')) {
                icon.className = 'fas fa-compress';
                this.title = 'Exit Fullscreen';
            } else {
                icon.className = 'fas fa-expand';
                this.title = 'Toggle Fullscreen';
            }
        });
    }

    // Form validation
    if (articleForm) {
        articleForm.addEventListener('submit', function(e) {
            const title = titleInput.value.trim();
            const content = contentEditor.value.trim();
            const category = document.getElementById('category').value;

            if (!title) {
                e.preventDefault();
                showNotification('Please enter a title', 'error');
                titleInput.focus();
                return false;
            }

            if (!content) {
                e.preventDefault();
                showNotification('Please enter article content', 'error');
                contentEditor.focus();
                return false;
            }

            if (!category) {
                e.preventDefault();
                showNotification('Please select a category', 'error');
                document.getElementById('category').focus();
                return false;
            }

            // Show loading state
            const submitBtn = articleForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
            }
        });
    }

    // Auto-save draft (every 30 seconds)
    let autoSaveTimer;
    function startAutoSave() {
        autoSaveTimer = setInterval(() => {
            if (contentEditor.value.trim()) {
                saveDraft();
            }
        }, 30000); // 30 seconds
    }

    function saveDraft() {
        const formData = new FormData(articleForm);
        formData.set('is_published', 'false'); // Always save as draft for auto-save

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Draft saved automatically', 'success', 2000);
            }
        })
        .catch(error => {
            console.error('Auto-save error:', error);
        });
    }

    // Start auto-save if editing
    if (document.querySelector('[name="is_published"]')) {
        startAutoSave();
    }

    // Clear auto-save on page unload
    window.addEventListener('beforeunload', function() {
        if (autoSaveTimer) {
            clearInterval(autoSaveTimer);
        }
    });

    // Keyboard shortcuts
    contentEditor.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + B for bold
        if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
            e.preventDefault();
            insertMarkdown('**', '**', 'bold text');
        }
        // Ctrl/Cmd + I for italic
        if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
            e.preventDefault();
            insertMarkdown('*', '*', 'italic text');
        }
        // Ctrl/Cmd + K for link
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            insertLink();
        }
        // Tab for indentation
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = this.selectionStart;
            this.setRangeText('    ', start, start, 'end');
        }
    });

    // Character counter
    const charCounter = document.createElement('div');
    charCounter.className = 'form-help-text';
    charCounter.style.textAlign = 'right';
    contentEditor.parentNode.appendChild(charCounter);

    function updateCharCounter() {
        const count = contentEditor.value.length;
        charCounter.textContent = `${count.toLocaleString()} characters`;
    }

    contentEditor.addEventListener('input', updateCharCounter);
    updateCharCounter();

    // Show notification
    function showNotification(message, type = 'info', duration = 3000) {
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
        }, duration);
    }

    // Warn before leaving if there are unsaved changes
    let formChanged = false;
    const formInputs = articleForm.querySelectorAll('input, textarea, select');
    
    formInputs.forEach(input => {
        input.addEventListener('change', () => {
            formChanged = true;
        });
    });

    window.addEventListener('beforeunload', function(e) {
        if (formChanged) {
            e.preventDefault();
            e.returnValue = '';
            return '';
        }
    });

    articleForm.addEventListener('submit', function() {
        formChanged = false;
    });
});
