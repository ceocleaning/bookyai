// bookings-edit-booking.js - Edit Booking page with restricted date/time/staff modification
// This is a separate JS file for the edit booking page that does NOT include
// date/time modification, end-time auto-calculation, or staff availability logic.

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('create-booking-form');
    if (!form) return;

    // Cache DOM elements
    const serviceTypeSelect = document.getElementById('service_type');
    const serviceDetailsDiv = document.getElementById('service-details');
    const serviceDurationSpan = document.getElementById('service-duration');
    const servicePriceSpan = document.getElementById('service-price');
    const serviceItemsContainer = document.getElementById('service-items-container');
    const bookingSummary = document.getElementById('booking-summary');
    const summaryService = document.getElementById('summary-service');
    const summaryDateTime = document.getElementById('summary-datetime');
    const summaryLocation = document.getElementById('summary-location');
    const summaryDuration = document.getElementById('summary-duration');
    const totalPriceSpan = document.getElementById('total-price');
    const locationTypeSelect = document.getElementById('location_type');
    const locationDetailsInput = document.getElementById('location_details');

    // Check if we're using the multi-step form
    const isMultiStepForm = document.querySelector('.steps-progress') !== null;

    // State variables
    let selectedServiceId = null;
    let basePrice = 0;
    let baseDuration = 0;
    let serviceItems = [];
    let selectedItems = {};
    let totalPrice = 0;
    let totalDuration = 0;

    // Service selection change handler
    if (serviceTypeSelect) {
        if (serviceTypeSelect.tagName === 'SELECT') {
            serviceTypeSelect.addEventListener('change', handleServiceChange);
        }
    }

    // Handle radio button service selection
    const serviceRadios = document.querySelectorAll('input[name="service_type"]');
    if (serviceRadios.length > 0) {
        serviceRadios.forEach(radio => {
            radio.addEventListener('change', handleServiceChange);
        });
    }

    function handleServiceChange(event) {
        const target = event.target;
        let serviceId, duration, price;

        if (target.tagName === 'SELECT') {
            serviceId = target.value;
            if (serviceId) {
                const selectedOption = target.options[target.selectedIndex];
                duration = selectedOption.dataset.duration;
                price = selectedOption.dataset.price;
            }
        } else if (target.type === 'radio') {
            serviceId = target.value;
            duration = target.dataset.duration;
            price = target.dataset.price;
        }

        selectedServiceId = serviceId;

        if (serviceId) {
            basePrice = parseFloat(price);

            if (serviceDurationSpan) serviceDurationSpan.textContent = duration;
            if (servicePriceSpan) servicePriceSpan.textContent = price;
            if (serviceDetailsDiv) serviceDetailsDiv.classList.remove('d-none');

            baseDuration = parseInt(duration);
            totalDuration = baseDuration;

            // Clear selected items when service changes
            selectedItems = {};
            updateTotalPrice();

            // Fetch service items
            fetchServiceItems(serviceId);

            // Update summary
            updateBookingSummary();
        } else {
            if (serviceDetailsDiv) serviceDetailsDiv.classList.add('d-none');
            if (serviceItemsContainer) {
                serviceItemsContainer.innerHTML = '<div class="alert alert-info">Please select a service to view available items</div>';
            }
            if (bookingSummary) bookingSummary.classList.add('d-none');
            basePrice = 0;
            totalPrice = 0;
            selectedItems = {};
            updateTotalPrice();
        }
    }

    // Location change handlers
    if (locationTypeSelect) {
        locationTypeSelect.addEventListener('change', function() {
            updateBookingSummary();

            if (this.value === 'onsite' || this.value === 'virtual') {
                locationDetailsInput.closest('.mb-3').classList.remove('d-none');
                if (this.value === 'onsite') {
                    locationDetailsInput.placeholder = 'Enter client address';
                } else {
                    locationDetailsInput.placeholder = 'Enter meeting link or details';
                }
            } else {
                locationDetailsInput.closest('.mb-3').classList.add('d-none');
            }
        });

        locationDetailsInput.addEventListener('change', updateBookingSummary);
    }

    // Fetch service items for the selected service
    function fetchServiceItems(serviceId) {
        serviceItemsContainer.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';

        let url = `/bookings/api/service-items/${serviceId}/`;
        const urlParams = new URLSearchParams(window.location.search);
        const businessId = document.getElementById('business_id')?.value || urlParams.get('business_id');

        if (businessId) {
            url += `?business_id=${businessId}`;
        }

        fetch(url)
            .then(response => response.json())
            .then(data => {
                serviceItems = data.items || [];
                renderServiceItems(serviceItems);
            })
            .catch(error => {
                console.error('Error fetching service items:', error);
                serviceItemsContainer.innerHTML = '<div class="alert alert-danger">Error loading service items</div>';
            });
    }

    // Render service items in the container
    function renderServiceItems(items) {
        if (!items || items.length === 0) {
            serviceItemsContainer.innerHTML = '<div class="alert alert-info">No additional service items available</div>';
            return;
        }

        let html = '<div class="row">';
        items.forEach(item => {
            const isFreeItem = item.price_type === 'free';
            const shouldShowQuantity = item.max_quantity > 1 &&
                                      !((item.price_type === 'free' && ['text', 'textarea', 'select', 'boolean'].includes(item.field_type)) ||
                                        (item.price_type !== 'free' && item.field_type === 'number'));

            html += `
                <div class="col-md-6 mb-3">
                    <div class="service-item-card-wrapper">
                        <input class="service-item-checkbox-input"
                               type="checkbox"
                               id="item_${item.id}"
                               name="service_items[]"
                               value="${item.id}"
                               data-price="${item.price_value}"
                               data-duration="${item.duration_minutes || 0}"
                               data-field-type="${item.field_type}"
                               data-price-type="${item.price_type}"
                               data-required="${!item.is_optional}"
                               ${item.is_optional ? '' : 'checked'}>
                        <label class="service-item-card ${item.is_optional ? '' : 'service-item-required'}" for="item_${item.id}">
                            <div class="service-item-header">
                                <div class="service-item-check-icon">
                                    <i class="fas fa-check"></i>
                                </div>
                                <div class="service-item-info">
                                    <h5 class="service-item-title">${item.name}</h5>
                                    <span class="service-item-badge ${item.is_optional ? 'badge-optional' : 'badge-required'}">
                                        ${item.is_optional ? 'Optional' : 'Required'}
                                    </span>
                                </div>
                            </div>

                            ${item.description ? `<p class="service-item-description">${item.description}</p>` : ''}

                            <div class="service-item-pricing">
                                <span class="service-item-price">${item.price_type !== 'free' ? '$' + item.price_value : 'Free'}</span>
                                ${parseInt(item.duration_minutes) > 0 ? `<span class="service-item-duration"><i class="fas fa-clock me-1"></i>+${item.duration_minutes} min</span>` : ''}
                            </div>
                        </label>

                        <!-- Field input based on field_type and price_type -->
                        <div class="mt-3 item-field-container ${item.is_optional ? 'd-none' : ''}" id="field_container_${item.id}">
                            ${renderItemField(item)}
                        </div>

                        ${shouldShowQuantity ? `
                        <div class="quantity-control ${item.is_optional && !selectedItems[item.id] ? 'd-none' : ''}">
                            <label for="quantity_${item.id}">Quantity:</label>
                            <div class="input-group input-group-sm">
                                <button type="button" class="btn btn-outline-secondary decrease-qty" data-item-id="${item.id}">-</button>
                                <input type="number" class="form-control text-center item-quantity"
                                       id="quantity_${item.id}"
                                       name="item_quantity_${item.id}"
                                       min="1"
                                       default="1"
                                       max="${item.max_quantity}"
                                       value="${selectedItems[item.id]?.quantity || 1}">
                                <button type="button" class="btn btn-outline-secondary increase-qty" data-item-id="${item.id}">+</button>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        html += '</div>';

        serviceItemsContainer.innerHTML = html;

        // Helper function to render the appropriate field
        function renderItemField(item) {
            if (item.field_type === 'number' && item.price_type === 'paid') {
                return `
                    <div class="form-group">
                        <label for="field_${item.id}">Quantity: <span class="text-muted small">(Max: ${item.max_quantity})</span></label>
                        <input type="number"
                               class="form-control item-number-input"
                               id="field_${item.id}"
                               name="item_field_${item.id}"
                               data-item-id="${item.id}"
                               placeholder="Enter quantity"
                               min="1"
                               max="${item.max_quantity}"
                               value="1">
                    </div>
                `;
            }

            if (item.field_type === 'boolean' && item.option_pricing) {
                const yesConfig = item.option_pricing.yes || { price_type: 'free', price_value: 0 };
                const noConfig = item.option_pricing.no || { price_type: 'free', price_value: 0 };

                return `
                    <div class="form-group">
                        <label>Select an option:</label>
                        <div class="form-check">
                            <input type="radio"
                                   class="form-check-input item-boolean-input"
                                   id="field_${item.id}_yes"
                                   name="item_field_${item.id}"
                                   value="yes"
                                   data-item-id="${item.id}"
                                   data-price-type="${yesConfig.price_type}"
                                   data-price-value="${yesConfig.price_value}">
                            <label class="form-check-label" for="field_${item.id}_yes">
                                Yes ${yesConfig.price_type === 'paid' ? '<span class="text-success">($' + yesConfig.price_value + ')</span>' : '<span class="text-muted">(Free)</span>'}
                            </label>
                        </div>
                        <div class="form-check">
                            <input type="radio"
                                   class="form-check-input item-boolean-input"
                                   id="field_${item.id}_no"
                                   name="item_field_${item.id}"
                                   value="no"
                                   data-item-id="${item.id}"
                                   data-price-type="${noConfig.price_type}"
                                   data-price-value="${noConfig.price_value}">
                            <label class="form-check-label" for="field_${item.id}_no">
                                No ${noConfig.price_type === 'paid' ? '<span class="text-success">($' + noConfig.price_value + ')</span>' : '<span class="text-muted">(Free)</span>'}
                            </label>
                        </div>
                    </div>
                `;
            }

            if (item.field_type === 'select' && item.option_pricing && item.field_options) {
                let options = '<option value="">Choose...</option>';
                item.field_options.forEach(option => {
                    const optionKey = option.toLowerCase();
                    const optionConfig = item.option_pricing[optionKey] || { price_type: 'free', price_value: 0 };
                    const priceText = optionConfig.price_type === 'paid'
                        ? ` - $${optionConfig.price_value}`
                        : ' - Free';

                    options += `<option value="${option}"
                                        data-price-type="${optionConfig.price_type}"
                                        data-price-value="${optionConfig.price_value}">${option}${priceText}</option>`;
                });

                return `
                    <div class="form-group">
                        <label for="field_${item.id}">Select an option:</label>
                        <select class="form-select item-select-input"
                                id="field_${item.id}"
                                name="item_field_${item.id}"
                                data-item-id="${item.id}">
                            ${options}
                        </select>
                    </div>
                `;
            }

            // Legacy/fallback rendering
            switch(item.field_type) {
                case 'text':
                    return `
                        <div class="form-group">
                            <label for="field_${item.id}">Value:</label>
                            <input type="text"
                                   class="form-control"
                                   id="field_${item.id}"
                                   name="item_field_${item.id}"
                                   placeholder="Enter text">
                        </div>
                    `;
                case 'textarea':
                    return `
                        <div class="form-group">
                            <label for="field_${item.id}">Value:</label>
                            <textarea class="form-control"
                                      id="field_${item.id}"
                                      name="item_field_${item.id}"
                                      rows="3"
                                      placeholder="Enter details"></textarea>
                        </div>
                    `;
                case 'number':
                    return `
                        <div class="form-group">
                            <label for="field_${item.id}">Quantity: <span class="text-muted small">(Max: ${item.max_quantity})</span></label>
                            <input type="number"
                                   class="form-control item-number-input"
                                   id="field_${item.id}"
                                   name="item_field_${item.id}"
                                   data-item-id="${item.id}"
                                   placeholder="Enter quantity"
                                   min="1"
                                   max="${item.max_quantity}"
                                   value="1">
                        </div>
                    `;
                case 'boolean':
                    return `
                        <div class="form-group">
                            <label>Select an option:</label>
                            <div class="form-check">
                                <input type="radio"
                                       class="form-check-input"
                                       id="field_${item.id}_yes"
                                       name="item_field_${item.id}"
                                       value="yes">
                                <label class="form-check-label" for="field_${item.id}_yes">Yes</label>
                            </div>
                            <div class="form-check">
                                <input type="radio"
                                       class="form-check-input"
                                       id="field_${item.id}_no"
                                       name="item_field_${item.id}"
                                       value="no">
                                <label class="form-check-label" for="field_${item.id}_no">No</label>
                            </div>
                        </div>
                    `;
                case 'select':
                    let selectOptions = '<option value="">Choose...</option>';
                    if (item.field_options && Array.isArray(item.field_options)) {
                        item.field_options.forEach(option => {
                            selectOptions += `<option value="${option}">${option}</option>`;
                        });
                    }
                    return `
                        <div class="form-group">
                            <label for="field_${item.id}">Select an option:</label>
                            <select class="form-select"
                                    id="field_${item.id}"
                                    name="item_field_${item.id}">
                                ${selectOptions}
                            </select>
                        </div>
                    `;
                default:
                    return `
                        <div class="form-group">
                            <label for="field_${item.id}">Value:</label>
                            <input type="text"
                                   class="form-control"
                                   id="field_${item.id}"
                                   name="item_field_${item.id}"
                                   placeholder="Enter value">
                        </div>
                    `;
            }
        }

        // Add event listeners to checkboxes
        document.querySelectorAll('.service-item-checkbox-input').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const itemId = this.value;
                const item = serviceItems.find(i => i.id === itemId);
                const fieldContainer = document.getElementById(`field_container_${itemId}`);
                const isRequired = this.dataset.required === 'true';

                // Prevent unchecking required items
                if (isRequired && !this.checked) {
                    this.checked = true;
                    return;
                }

                if (this.checked) {
                    const itemData = serviceItems.find(i => i.id === itemId);

                    let initialPrice = 0;
                    if (item.field_type === 'number' && item.price_type === 'paid') {
                        initialPrice = parseFloat(item.price_value);
                    }

                    selectedItems[itemId] = {
                        name: itemData ? itemData.name : 'Unknown Item',
                        price: initialPrice,
                        quantity: 1,
                        duration: itemData ? parseInt(itemData.duration_minutes || 0) : 0,
                        inputValue: null,
                        fieldType: item.field_type,
                        optionPricing: item.option_pricing
                    };

                    if (fieldContainer) {
                        fieldContainer.classList.remove('d-none');
                    }

                    if (item && item.max_quantity > 1) {
                        const quantityControl = this.closest('.card-body').querySelector('.quantity-control');
                        if (quantityControl) {
                            quantityControl.classList.remove('d-none');
                        }
                    }
                } else {
                    delete selectedItems[itemId];

                    if (fieldContainer) {
                        fieldContainer.classList.add('d-none');
                    }

                    const quantityControl = this.closest('.card-body').querySelector('.quantity-control');
                    if (quantityControl) {
                        quantityControl.classList.add('d-none');
                    }
                }

                updateTotalPrice();
            });
        });

        // Quantity controls
        document.querySelectorAll('.decrease-qty').forEach(btn => {
            btn.addEventListener('click', function() {
                const itemId = this.dataset.itemId;
                const input = document.getElementById(`quantity_${itemId}`);
                const currentValue = parseInt(input.value);
                if (currentValue > 1) {
                    input.value = currentValue - 1;
                    if (selectedItems[itemId]) {
                        selectedItems[itemId].quantity = currentValue - 1;
                        updateTotalPrice();
                    }
                }
            });
        });

        document.querySelectorAll('.increase-qty').forEach(btn => {
            btn.addEventListener('click', function() {
                const itemId = this.dataset.itemId;
                const input = document.getElementById(`quantity_${itemId}`);
                const currentValue = parseInt(input.value);
                const maxValue = parseInt(input.max);
                if (currentValue < maxValue) {
                    input.value = currentValue + 1;
                    if (selectedItems[itemId]) {
                        selectedItems[itemId].quantity = currentValue + 1;
                        updateTotalPrice();
                    }
                }
            });
        });

        document.querySelectorAll('.item-quantity').forEach(input => {
            input.addEventListener('change', function() {
                const itemId = this.id.replace('quantity_', '');
                const value = parseInt(this.value);
                if (selectedItems[itemId]) {
                    selectedItems[itemId].quantity = value;
                    updateTotalPrice();
                }
            });
        });

        // Number inputs
        document.querySelectorAll('.item-number-input').forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('is-invalid');

                const itemId = this.dataset.itemId;
                const item = serviceItems.find(i => i.id === itemId);
                const quantity = parseInt(this.value) || 0;

                if (selectedItems[itemId] && item) {
                    if (quantity > item.max_quantity) {
                        this.value = item.max_quantity;
                        selectedItems[itemId].quantity = item.max_quantity;
                    } else {
                        selectedItems[itemId].quantity = quantity;
                    }
                    selectedItems[itemId].inputValue = selectedItems[itemId].quantity;
                    selectedItems[itemId].price = parseFloat(item.price_value) * selectedItems[itemId].quantity;

                    updateTotalPrice();
                }
            });
        });

        // Boolean inputs
        document.querySelectorAll('.item-boolean-input').forEach(input => {
            input.addEventListener('change', function() {
                const formGroup = this.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.remove('is-invalid');
                }

                if (this.checked) {
                    const itemId = this.dataset.itemId;
                    const priceType = this.dataset.priceType;
                    const priceValue = parseFloat(this.dataset.priceValue) || 0;

                    if (selectedItems[itemId]) {
                        selectedItems[itemId].inputValue = this.value;
                        if (priceType === 'paid') {
                            selectedItems[itemId].price = priceValue;
                        } else {
                            selectedItems[itemId].price = 0;
                        }
                        updateTotalPrice();
                    }
                }
            });
        });

        // Select inputs
        document.querySelectorAll('.item-select-input').forEach(input => {
            input.addEventListener('change', function() {
                this.classList.remove('is-invalid');

                const itemId = this.dataset.itemId;
                const selectedOption = this.options[this.selectedIndex];

                if (selectedItems[itemId] && selectedOption && this.value) {
                    selectedItems[itemId].inputValue = this.value;
                    const priceType = selectedOption.dataset.priceType;
                    const priceValue = parseFloat(selectedOption.dataset.priceValue) || 0;

                    if (priceType === 'paid') {
                        selectedItems[itemId].price = priceValue;
                    } else {
                        selectedItems[itemId].price = 0;
                    }
                    updateTotalPrice();
                }
            });
        });

        // Other field inputs
        document.querySelectorAll('input[id^="field_"]:not(.item-number-input):not(.item-boolean-input), textarea[id^="field_"], select[id^="field_"]:not(.item-select-input)').forEach(input => {
            input.addEventListener('input', function() {
                const itemId = this.id.replace('field_', '');
                if (selectedItems[itemId]) {
                    selectedItems[itemId].inputValue = this.value;
                }
            });
        });

        // Initialize selected items from required items
        items.forEach(item => {
            if (!item.is_optional) {
                let initialPrice = 0;
                if (item.field_type === 'number' && item.price_type === 'paid') {
                    initialPrice = parseFloat(item.price_value);
                }

                selectedItems[item.id] = {
                    name: item.name,
                    price: initialPrice,
                    quantity: 1,
                    duration: parseInt(item.duration_minutes || 0),
                    inputValue: null,
                    fieldType: item.field_type,
                    optionPricing: item.option_pricing
                };
            }
        });

        updateTotalPrice();
    }

    // Calculate and update total price and duration
    function updateTotalPrice() {
        totalPrice = basePrice;
        totalDuration = baseDuration;

        Object.entries(selectedItems).forEach(([itemId, item]) => {
            const itemPrice = item.price * item.quantity;
            totalPrice += itemPrice;
            totalDuration += item.duration * item.quantity;
        });

        if (totalPriceSpan) totalPriceSpan.textContent = totalPrice.toFixed(2);

        // Dispatch event for multi-step form to update summary
        if (isMultiStepForm) {
            const event = new CustomEvent('serviceItemsUpdated', {
                detail: { items: selectedItems }
            });
            document.dispatchEvent(event);
        }

        // Update service duration display
        if (serviceDurationSpan) {
            serviceDurationSpan.textContent = totalDuration;
        }

        // Update summary duration display
        if (summaryDuration) {
            const hours = Math.floor(totalDuration / 60);
            const minutes = totalDuration % 60;
            let durationText = '';

            if (hours > 0) {
                durationText += `${hours} hour${hours > 1 ? 's' : ''}`;
                if (minutes > 0) durationText += ' ';
            }

            if (minutes > 0 || hours === 0) {
                durationText += `${minutes} minute${minutes !== 1 ? 's' : ''}`;
            }

            summaryDuration.textContent = durationText;
        }

        // Update booking summary
        updateBookingSummary();
    }

    // Update booking summary
    function updateBookingSummary() {
        let serviceName = '';
        let hasService = false;

        if (serviceTypeSelect && serviceTypeSelect.tagName === 'SELECT' && serviceTypeSelect.value) {
            serviceName = serviceTypeSelect.options[serviceTypeSelect.selectedIndex].text;
            hasService = true;
        } else {
            const selectedRadio = document.querySelector('input[name="service_type"]:checked');
            if (selectedRadio) {
                serviceName = selectedRadio.dataset.name || selectedRadio.value;
                hasService = true;
            }
        }

        if (!hasService) return;

        if (summaryService) summaryService.textContent = serviceName;

        // Format duration in summary
        if (summaryDuration) {
            if (totalDuration > 0) {
                const hours = Math.floor(totalDuration / 60);
                const minutes = totalDuration % 60;
                let durationText = '';

                if (hours > 0) {
                    durationText += `${hours} hour${hours > 1 ? 's' : ''}`;
                    if (minutes > 0) durationText += ' ';
                }

                if (minutes > 0 || hours === 0) {
                    durationText += `${minutes} minute${minutes !== 1 ? 's' : ''}`;
                }

                summaryDuration.textContent = durationText;
            } else {
                summaryDuration.textContent = '-';
            }
        }

        // Format location
        if (summaryLocation && locationTypeSelect) {
            const locationType = locationTypeSelect.value;
            let locationText = '';

            switch (locationType) {
                case 'business':
                    locationText = 'At Business Location';
                    break;
                case 'onsite':
                    locationText = 'On-site (Client Location)';
                    if (locationDetailsInput && locationDetailsInput.value) {
                        locationText += `: ${locationDetailsInput.value}`;
                    }
                    break;
                case 'virtual':
                    locationText = 'Virtual Meeting';
                    if (locationDetailsInput && locationDetailsInput.value) {
                        locationText += `: ${locationDetailsInput.value}`;
                    }
                    break;
                default:
                    locationText = '-';
            }

            summaryLocation.textContent = locationText;
        }

        if (bookingSummary) bookingSummary.classList.remove('d-none');
    }

    // Format time from 24h to 12h format
    function formatTime(time24) {
        const [hours, minutes] = time24.split(':');
        const hour = parseInt(hours, 10);
        const period = hour >= 12 ? 'PM' : 'AM';
        const hour12 = hour % 12 || 12;
        return `${hour12}:${minutes} ${period}`;
    }

    // Form validation
    form.addEventListener('submit', function(e) {
        let valid = true;
        form.querySelectorAll('[required]').forEach(function(input) {
            if (input.type === 'radio') {
                const radioGroup = form.querySelectorAll(`input[name="${input.name}"]`);
                const isAnyChecked = Array.from(radioGroup).some(radio => radio.checked);
                if (!isAnyChecked) {
                    valid = false;
                    radioGroup.forEach(radio => radio.classList.add('is-invalid'));
                } else {
                    radioGroup.forEach(radio => radio.classList.remove('is-invalid'));
                }
            }
            else if (input.type === 'checkbox') {
                if (!input.checked) {
                    valid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            }
            else {
                if (!input.value || !input.value.trim()) {
                    valid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            }
        });

        // Ensure items with values have their checkboxes checked
        document.querySelectorAll('.service-item-checkbox-input').forEach(function(checkbox) {
            const itemId = checkbox.value;
            const fieldType = checkbox.dataset.fieldType;
            let hasValue = false;

            if (fieldType === 'boolean') {
                const yesRadio = document.getElementById(`field_${itemId}_yes`);
                const noRadio = document.getElementById(`field_${itemId}_no`);
                if ((yesRadio && yesRadio.checked) || (noRadio && noRadio.checked)) {
                    hasValue = true;
                }
            } else {
                const fieldInput = document.getElementById(`field_${itemId}`);
                if (fieldInput && fieldInput.value && fieldInput.value.trim()) {
                    hasValue = true;
                }
            }

            if (hasValue) {
                checkbox.checked = true;
            }
        });

        // Validate checked items
        document.querySelectorAll('.service-item-checkbox-input:checked').forEach(function(checkbox) {
            const itemId = checkbox.value;
            const fieldType = checkbox.dataset.fieldType;

            if (fieldType === 'select') {
                const fieldInput = document.getElementById(`field_${itemId}`);
                if (fieldInput && !fieldInput.value) {
                    valid = false;
                    fieldInput.classList.add('is-invalid');
                }
            } else if (fieldType === 'boolean') {
                const yesRadio = document.getElementById(`field_${itemId}_yes`);
                const noRadio = document.getElementById(`field_${itemId}_no`);
                if (!yesRadio || !noRadio || (!yesRadio.checked && !noRadio.checked)) {
                    valid = false;
                    if (yesRadio && yesRadio.closest('.form-group')) {
                        yesRadio.closest('.form-group').classList.add('is-invalid');
                    }
                }
            } else if (fieldType === 'number') {
                const fieldInput = document.getElementById(`field_${itemId}`);
                if (fieldInput && (!fieldInput.value || isNaN(parseFloat(fieldInput.value)) || parseFloat(fieldInput.value) <= 0)) {
                    valid = false;
                    fieldInput.classList.add('is-invalid');
                }
            } else if (fieldType === 'text' || fieldType === 'textarea') {
                const fieldInput = document.getElementById(`field_${itemId}`);
                if (fieldInput && !fieldInput.value.trim()) {
                    valid = false;
                    fieldInput.classList.add('is-invalid');
                }
            }
        });

        // Create hidden input for selected items data
        if (valid) {
            const selectedItemsData = {};

            document.querySelectorAll('.service-item-checkbox-input:checked').forEach(function(checkbox) {
                const itemId = checkbox.value;
                const fieldType = checkbox.dataset.fieldType;
                const quantityInput = document.getElementById(`quantity_${itemId}`);
                let fieldValue = '';

                if (fieldType === 'boolean') {
                    const yesRadio = document.getElementById(`field_${itemId}_yes`);
                    const noRadio = document.getElementById(`field_${itemId}_no`);
                    if (yesRadio && yesRadio.checked) {
                        fieldValue = yesRadio.value;
                    } else if (noRadio && noRadio.checked) {
                        fieldValue = noRadio.value;
                    }
                } else {
                    const fieldInput = document.getElementById(`field_${itemId}`);
                    if (fieldInput) {
                        fieldValue = fieldInput.value;
                    }
                }

                selectedItemsData[itemId] = {
                    value: fieldValue,
                    quantity: quantityInput ? parseInt(quantityInput.value) : 1
                };
            });

            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'selected_items_data';
            hiddenInput.value = JSON.stringify(selectedItemsData);
            form.appendChild(hiddenInput);
        }

        if (!valid) {
            e.preventDefault();

            const firstInvalid = form.querySelector('.is-invalid');
            let fieldName = 'Unknown field';

            if (firstInvalid) {
                if (firstInvalid.id && firstInvalid.id.startsWith('field_')) {
                    const itemId = firstInvalid.id.replace('field_', '').split('_')[0];
                    const itemCheckbox = document.querySelector(`.service-item-checkbox-input[value="${itemId}"]`);
                    if (itemCheckbox) {
                        const itemCard = itemCheckbox.nextElementSibling;
                        const itemTitle = itemCard ? itemCard.querySelector('.service-item-title') : null;
                        if (itemTitle) {
                            fieldName = itemTitle.textContent.trim();
                        } else {
                            fieldName = 'Service Item';
                        }
                    }
                } else {
                    const label = form.querySelector(`label[for="${firstInvalid.id}"]`);
                    if (label) {
                        fieldName = label.textContent.replace('*', '').trim();
                    } else if (firstInvalid.name === 'service_type') {
                        fieldName = 'Service Type';
                    } else if (firstInvalid.name) {
                        fieldName = firstInvalid.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    }
                }

                alert(`Please fill in all required fields. Missing: ${fieldName}`);
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                alert('Please fill in all required fields.');
            }
        }
    });

    // Remove highlight on input
    form.querySelectorAll('[required]').forEach(function(input) {
        if (input.type === 'radio') {
            input.addEventListener('change', function() {
                const radioGroup = form.querySelectorAll(`input[name="${input.name}"]`);
                radioGroup.forEach(radio => radio.classList.remove('is-invalid'));
            });
        } else if (input.type === 'checkbox') {
            input.addEventListener('change', function() {
                if (input.checked) {
                    input.classList.remove('is-invalid');
                }
            });
        } else {
            input.addEventListener('input', function() {
                if (input.value) {
                    input.classList.remove('is-invalid');
                }
            });
        }
    });
});
