// Multi-Step Form Navigation and Summary Update for Edit Booking
// This version has only 4 steps (no Date & Time step)
document.addEventListener('DOMContentLoaded', function() {
    let currentStep = 1;
    const totalSteps = 4;

    // Map of step numbers (since step 4 in original is now removed)
    // Step 1: Client Info
    // Step 2: Service Details
    // Step 3: Service Items
    // Step 4: Notes (was step 5 in create booking)

    // Summary data object
    const summaryData = {
        service: null,
        servicePrice: 0,
        serviceDuration: 0,
        items: [],
        itemsPrice: 0,
        itemsDuration: 0,
        date: null,
        time: null,
        taxRate: 0.10 // 10% tax
    };

    // Navigation functions
    function showStep(stepNumber) {
        // Hide all steps
        document.querySelectorAll('.form-step').forEach(step => {
            step.classList.remove('active');
        });

        // Show current step
        const currentStepEl = document.getElementById(`step-${stepNumber}`);
        if (currentStepEl) {
            currentStepEl.classList.add('active');
        }

        // Update progress indicators
        document.querySelectorAll('.step').forEach((step, index) => {
            const stepNum = index + 1;
            step.classList.remove('active', 'completed');

            if (stepNum < stepNumber) {
                step.classList.add('completed');
            } else if (stepNum === stepNumber) {
                step.classList.add('active');
            }
        });

        currentStep = stepNumber;

        // Scroll to top of form
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Next step buttons
    document.querySelectorAll('.next-step').forEach(button => {
        button.addEventListener('click', function() {
            const nextStep = parseInt(this.dataset.next);

            // Validate current step before moving forward
            if (validateStep(currentStep)) {
                showStep(nextStep);
            }
        });
    });

    // Previous step buttons
    document.querySelectorAll('.prev-step').forEach(button => {
        button.addEventListener('click', function() {
            const prevStep = parseInt(this.dataset.prev);
            showStep(prevStep);
        });
    });

    // Click on step indicator to navigate
    document.querySelectorAll('.step').forEach(step => {
        step.addEventListener('click', function() {
            const stepNum = parseInt(this.dataset.step);
            if (stepNum <= currentStep || step.classList.contains('completed')) {
                showStep(stepNum);
            }
        });
    });

    // Validation function
    function validateStep(stepNumber) {
        const stepEl = document.getElementById(`step-${stepNumber}`);
        const requiredFields = stepEl.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });

        if (!isValid) {
            alert('Please fill in all required fields before proceeding.');
        }

        return isValid;
    }

    // Update summary functions
    function updateSummary() {
        updateDateTimeSummary();
        updateDurationSummary();
        updateServiceSummary();
        updateItemsSummary();
        updatePriceSummary();
    }

    function updateDateTimeSummary() {
        // In edit mode, date/time is read-only and already shown in template
        // Just update the summary display from the static values if they exist
        const summaryEl = document.getElementById('summary-datetime');
        if (!summaryEl) return;

        // The date/time info card already shows this info, so we can populate from data attributes
        const dateInfoEl = document.querySelector('.edit-booking-date-value');
        const timeInfoEl = document.querySelector('.edit-booking-time-value');

        if (dateInfoEl && timeInfoEl) {
            summaryEl.innerHTML = `
                <i class="fas fa-calendar text-primary me-2"></i>
                ${dateInfoEl.textContent}<br>
                <i class="fas fa-clock text-primary me-2"></i>
                ${timeInfoEl.textContent}
            `;
        }
    }

    function updateDurationSummary() {
        const totalDuration = summaryData.serviceDuration + summaryData.itemsDuration;
        const summaryEl = document.getElementById('summary-duration');

        if (totalDuration > 0) {
            const hours = Math.floor(totalDuration / 60);
            const minutes = totalDuration % 60;
            let durationText = '';

            if (hours > 0) {
                durationText += `${hours} hour${hours > 1 ? 's' : ''}`;
            }
            if (minutes > 0) {
                if (hours > 0) durationText += ' ';
                durationText += `${minutes} min`;
            }

            summaryEl.innerHTML = `<i class="fas fa-clock text-primary me-2"></i>${durationText}`;
        } else {
            summaryEl.innerHTML = '<i class="fas fa-clock text-muted me-2"></i>0 minutes';
        }
    }

    function updateServiceSummary() {
        const summaryEl = document.getElementById('summary-service');

        if (summaryData.service) {
            summaryEl.innerHTML = `
                <i class="fas fa-briefcase text-primary me-2"></i>
                <strong>${summaryData.service}</strong>
            `;
        } else {
            summaryEl.innerHTML = '<i class="fas fa-briefcase text-muted me-2"></i>Not selected yet';
        }
    }

    function updateItemsSummary() {
        const summaryEl = document.getElementById('summary-items');

        if (summaryData.items.length > 0) {
            let itemsHtml = '';
            summaryData.items.forEach(item => {
                const totalItemPrice = item.price * item.quantity;
                itemsHtml += `
                    <div class="item-entry">
                        <div class="d-flex justify-content-between">
                            <span>${item.name}</span>
                            <span class="text-muted">$${totalItemPrice.toFixed(2)}</span>
                        </div>
                        ${item.quantity > 1 ? `<small class="text-muted">Qty: ${item.quantity}</small>` : ''}
                        ${item.inputValue ? `<small class="text-muted">Value: ${item.inputValue}</small>` : ''}
                    </div>
                `;
            });
            summaryEl.innerHTML = itemsHtml;
        } else {
            summaryEl.innerHTML = '<i class="fas fa-list text-muted me-2"></i>No items selected';
        }
    }

    function updatePriceSummary() {
        const basePrice = summaryData.servicePrice;
        const itemsPrice = summaryData.itemsPrice;
        const subtotal = basePrice + itemsPrice;
        const tax = subtotal * summaryData.taxRate;
        const grandTotal = subtotal + tax;

        document.getElementById('summary-base-price').textContent = `$${basePrice.toFixed(2)}`;
        document.getElementById('summary-items-price').textContent = `$${itemsPrice.toFixed(2)}`;
        document.getElementById('summary-tax').textContent = `$${tax.toFixed(2)}`;
        document.getElementById('summary-grand-total').textContent = `$${grandTotal.toFixed(2)}`;
    }

    // Helper function to format time
    function formatTime(timeString) {
        if (!timeString) return '';
        const [hours, minutes] = timeString.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour % 12 || 12;
        return `${displayHour}:${minutes} ${ampm}`;
    }

    // Service selection - handle radio buttons
    const serviceRadios = document.querySelectorAll('input[name="service_type"]');
    if (serviceRadios.length > 0) {
        serviceRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.checked) {
                    summaryData.service = this.dataset.name;
                    summaryData.servicePrice = parseFloat(this.dataset.price) || 0;
                    summaryData.serviceDuration = parseInt(this.dataset.duration) || 0;
                    updateSummary();
                }
            });
        });
    }

    // Service items handling
    window.updateServiceItemsSummary = function(items) {
        summaryData.items = items;
        summaryData.itemsPrice = items.reduce((total, item) => total + (item.price * item.quantity), 0);
        summaryData.itemsDuration = items.reduce((total, item) => total + (item.duration * item.quantity), 0);
        updateSummary();
    };

    // Listen for service item changes
    document.addEventListener('serviceItemsUpdated', function(event) {
        const items = event.detail.items || {};
        const itemsArray = [];

        Object.values(items).forEach(item => {
            itemsArray.push({
                name: item.name,
                price: item.price,
                quantity: item.quantity,
                duration: item.duration || 0,
                inputValue: item.inputValue || null
            });
        });

        updateServiceItemsSummary(itemsArray);
    });

    // Initialize: check if a service is already selected (for edit mode pre-population)
    const checkedRadio = document.querySelector('input[name="service_type"]:checked');
    if (checkedRadio) {
        summaryData.service = checkedRadio.dataset.name;
        summaryData.servicePrice = parseFloat(checkedRadio.dataset.price) || 0;
        summaryData.serviceDuration = parseInt(checkedRadio.dataset.duration) || 0;
    }

    // Initialize summary
    updateSummary();
});
