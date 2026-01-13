// Voice Conversations Page JavaScript

// Store all call data (will be populated from Django template)
let callData = [];

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for jQuery and other libraries to load
    setTimeout(function() {
        initializeDateRangePicker();
        initializeFilterTabs();
        initializeChatItems();
        initializeRecordingPlayer();
        
        // If there are calls, select the first one by default
        const chatItems = document.querySelectorAll('.chat-item');
        if (chatItems.length > 0) {
            chatItems[0].click();
        }
    }, 100);
});

/**
 * Initialize date range picker
 */
function initializeDateRangePicker() {
    // Check if jQuery and daterangepicker are loaded
    if (typeof jQuery === 'undefined' || typeof jQuery.fn.daterangepicker === 'undefined') {
        console.warn('jQuery or daterangepicker not loaded. Date picker will not be initialized.');
        return;
    }
    
    const startDate = document.getElementById('start-date-value').value;
    const endDate = document.getElementById('end-date-value').value;
    
    $('#dateRangePicker').daterangepicker({
        startDate: moment(startDate),
        endDate: moment(endDate),
        ranges: {
           'Today': [moment(), moment()],
           'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
           'Last 7 Days': [moment().subtract(6, 'days'), moment()],
           'Last 30 Days': [moment().subtract(29, 'days'), moment()],
           'This Month': [moment().startOf('month'), moment().endOf('month')],
           'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        }
    }, function(start, end, label) {
        // Update the date range text
        let dateText;
        if (start.format('YYYY-MM-DD') === end.format('YYYY-MM-DD')) {
            dateText = start.format('MMM D, YYYY');
        } else {
            dateText = start.format('MMM D, YYYY') + ' - ' + end.format('MMM D, YYYY');
        }
        $('#dateRangePicker span').text(dateText);
        
        // Redirect with new date range when selected
        window.location.href = `?start_date=${start.format('YYYY-MM-DD')}&end_date=${end.format('YYYY-MM-DD')}`;
    });
}

/**
 * Initialize filter tabs
 */
function initializeFilterTabs() {
    const filterTabs = document.querySelectorAll('.filter-tab');
    const chatItems = document.querySelectorAll('.chat-item');
    
    // Count calls by type
    const counts = {
        all: chatItems.length,
        outbound: 0,
        inbound: 0,
        phone_call: 0,
        web_call: 0
    };
    
    // Count calls by type
    chatItems.forEach(item => {
        const callType = item.getAttribute('data-call-type');
        if (callType === 'outbound') counts.outbound++;
        if (callType === 'inbound') counts.inbound++;
        if (callType === 'phone_call') counts.phone_call++;
        if (callType === 'web_call') counts.web_call++;
    });
    
    // Update count badges
    document.getElementById('all-count').textContent = counts.all;
    document.getElementById('outbound-count').textContent = counts.outbound;
    document.getElementById('inbound-count').textContent = counts.inbound;
    document.getElementById('phone-count').textContent = counts.phone_call;
    document.getElementById('web-count').textContent = counts.web_call;
    
    // Handle filter tab clicks
    filterTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            filterTabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Get filter value
            const filter = this.getAttribute('data-filter');
            
            // Filter chat items
            chatItems.forEach(item => {
                const callType = item.getAttribute('data-call-type');
                
                if (filter === 'all') {
                    item.style.display = 'block';
                } else if (filter === 'outbound' && callType === 'outbound') {
                    item.style.display = 'block';
                } else if (filter === 'inbound' && callType === 'inbound') {
                    item.style.display = 'block';
                } else if (filter === 'phone_call' && callType === 'phone_call') {
                    item.style.display = 'block';
                } else if (filter === 'web_call' && callType === 'web_call') {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
            
            // If there are visible items, select the first one
            const visibleItems = document.querySelectorAll('.chat-item[style="display: block"]');
            if (visibleItems.length > 0) {
                visibleItems[0].click();
            } else {
                // Hide conversation view if no items are visible
                document.getElementById('no-conversation-selected').style.display = 'flex';
                document.getElementById('conversation-view').style.display = 'none';
                document.getElementById('call-details-container').style.display = 'none';
            }
        });
    });
}

/**
 * Initialize chat item click handlers
 */
function initializeChatItems() {
    const chatItems = document.querySelectorAll('.chat-item');
    
    chatItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            chatItems.forEach(i => i.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Get call ID and display conversation
            const callId = this.getAttribute('data-call-id');
            displayConversation(callId);
        });
    });
}

/**
 * Initialize recording player
 */
function initializeRecordingPlayer() {
    const playRecordingBtn = document.getElementById('play-recording-btn');
    if (playRecordingBtn) {
        playRecordingBtn.addEventListener('click', function() {
            const audioPlayerContainer = document.getElementById('audio-player-container');
            
            // Toggle audio player visibility
            if (audioPlayerContainer.style.display === 'none' || audioPlayerContainer.style.display === '') {
                audioPlayerContainer.style.display = 'block';
                // Start playing
                document.getElementById('audio-player').play();
            } else {
                audioPlayerContainer.style.display = 'none';
                // Pause playing
                document.getElementById('audio-player').pause();
            }
        });
    }
}

/**
 * Display conversation for a selected call
 * @param {string} callId - The ID of the call to display
 */
function displayConversation(callId) {
    // Find the call data
    const call = callData.find(c => c.call_id === callId);
    if (!call) return;
    
    // Hide no conversation selected message and show conversation view
    document.getElementById('no-conversation-selected').style.display = 'none';
    document.getElementById('conversation-view').style.display = 'flex';
    document.getElementById('call-details-container').style.display = 'block';
    
    // Update conversation header
    let title = call.customer_name;
    if (title === "Unknown") {
        title = call.call_type === "inbound" ? "Inbound Call" : "Outbound Call";
    }
    document.getElementById('conversation-title').textContent = title;
    document.getElementById('conversation-date').textContent = call.start_time;
    document.getElementById('conversation-duration').textContent = call.duration;
    
    // Handle recording
    const recordingContainer = document.getElementById('recording-container');
    const playRecordingBtn = document.getElementById('play-recording-btn');
    const audioPlayer = document.getElementById('audio-player');
    const audioPlayerContainer = document.getElementById('audio-player-container');
    
    if (call.recording_url) {
        // Set the audio source
        audioPlayer.src = call.recording_url;
        // Show the recording container
        recordingContainer.style.display = 'block';
        // Hide the audio player initially
        audioPlayerContainer.style.display = 'none';
    } else {
        // No recording available
        recordingContainer.style.display = 'none';
    }
    
    // Update call details
    document.getElementById('call-type').textContent = call.call_type.charAt(0).toUpperCase() + call.call_type.slice(1);
    
    // Update call status with badge
    const callStatus = call.call_status.charAt(0).toUpperCase() + call.call_status.slice(1);
    document.getElementById('call-status').textContent = callStatus;
    
    // Update status badge
    const statusBadge = document.getElementById('status-badge');
    const statusText = document.getElementById('status-text');
    
    statusBadge.className = 'status-badge ms-2 status-' + call.call_status.toLowerCase();
    statusText.textContent = callStatus;
    
    // Update other details
    document.getElementById('disconnection-reason').textContent = call.disconnection_reason ? 
        (call.disconnection_reason.charAt(0).toUpperCase() + call.disconnection_reason.slice(1)).replace(/_/g, ' ') : 
        'N/A';
    document.getElementById('user-sentiment').textContent = call.user_sentiment;
    document.getElementById('call-success').textContent = call.call_successful ? 'Yes' : 'No';
    document.getElementById('call-id').textContent = call.call_id;
    document.getElementById('call-summary').textContent = call.call_summary || 'No summary available';
    
    // Clear and populate messages
    const messagesContainer = document.getElementById('conversation-messages');
    messagesContainer.innerHTML = '';
    
    if (call.messages && call.messages.length > 0) {
        // Generate timestamps for messages if they don't exist
        let messageTime = moment(call.start_time, "MMM DD, YYYY hh:mm A");
        
        call.messages.forEach((message, index) => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message message-${message.role}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = message.content;
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            
            // Use provided timestamp or generate one
            let timestamp = message.timestamp;
            if (!timestamp) {
                // Add 30 seconds for each message to simulate a conversation flow
                if (index > 0) {
                    messageTime.add(30, 'seconds');
                }
                timestamp = messageTime.format('hh:mm A');
            }
            
            timeDiv.textContent = timestamp;
            
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(timeDiv);
            messagesContainer.appendChild(messageDiv);
        });
        
        // Scroll to bottom of messages
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } else {
        // Show empty state if no messages
        messagesContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-comment-slash"></i>
                <h5>No transcript available</h5>
                <p>This call doesn't have a transcript</p>
            </div>
        `;
    }
}

/**
 * Set call data from Django template
 * @param {Array} data - Array of call objects
 */
function setCallData(data) {
    callData = data;
}
