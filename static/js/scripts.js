/**
 * LocalBiz Portal Frontend JavaScript Helpers
 * Includes AI Chatbot Widget & Track Location Near Me Tool
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss flash alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 6000);
    });

    // 2. Coupon code copy to clipboard helper
    const copyButtons = document.querySelectorAll('.btn-copy-coupon');
    copyButtons.forEach(function (button) {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const code = this.getAttribute('data-coupon');
            if (code) {
                navigator.clipboard.writeText(code).then(() => {
                    const originalText = this.innerHTML;
                    this.innerHTML = '<i class="bi bi-check-lg"></i> Copied!';
                    this.classList.remove('btn-outline-primary', 'btn-outline-warning');
                    this.classList.add('btn-success');

                    setTimeout(() => {
                        this.innerHTML = originalText;
                        this.classList.remove('btn-success');
                        this.classList.add('btn-outline-primary');
                    }, 2000);
                });
            }
        });
    });

    // 3. Interactive Star Rating selector for review form
    const starLabels = document.querySelectorAll('.star-rating-input label');
    starLabels.forEach(function (label, idx) {
        label.addEventListener('mouseover', function () {
            starLabels.forEach((l, i) => {
                if (i <= idx) l.classList.add('text-warning');
                else l.classList.remove('text-warning');
            });
        });
    });

    const ratingContainer = document.querySelector('.star-rating-input');
    if (ratingContainer) {
        ratingContainer.addEventListener('mouseleave', function () {
            const checked = ratingContainer.querySelector('input:checked');
            const checkedVal = checked ? parseInt(checked.value) : 0;
            starLabels.forEach((l, i) => {
                if (i < checkedVal) l.classList.add('text-warning');
                else l.classList.remove('text-warning');
            });
        });
    }

    // 4. Initialize Track Location & AI Chatbot
    initLocationTracking();
    initAiChatbot();
});

/* ==========================================================================
   TRACK LOCATION & NEAR ME TOOLS
   ========================================================================== */
function initLocationTracking() {
    const savedLat = sessionStorage.getItem('localbiz_user_lat');
    const savedLng = sessionStorage.getItem('localbiz_user_lng');
    const savedName = sessionStorage.getItem('localbiz_user_loc_name');

    if (savedLat && savedLng) {
        updateLocationStatusBadge(savedName || 'Current Location', savedLat, savedLng);
    }
}

function detectUserLocation() {
    const statusEl = document.getElementById('locationStatusText');
    if (statusEl) statusEl.innerHTML = '<span class="spinner-border spinner-border-sm text-primary"></span> Detecting GPS coordinates...';

    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser. You can select a preset town like Hiriyur or Chitradurga.');
        return;
    }

    navigator.geolocation.getCurrentPosition(
        function (pos) {
            const lat = pos.coords.latitude.toFixed(4);
            const lng = pos.coords.longitude.toFixed(4);
            saveLocationAndReload('Detected GPS Location', lat, lng);
        },
        function (err) {
            console.warn('Geolocation error:', err.message);
            // Graceful fallback to default town (Hiriyur)
            alert('Location permission was denied or unavailable. Setting default location to Hiriyur Town Center.');
            setPresetLocation('Hiriyur Town Center', 13.9450, 76.6210);
        },
        { timeout: 10000, enableHighAccuracy: true }
    );
}

function setPresetLocation(name, lat, lng) {
    saveLocationAndReload(name, lat, lng);
}

function saveLocationAndReload(name, lat, lng) {
    sessionStorage.setItem('localbiz_user_lat', lat);
    sessionStorage.setItem('localbiz_user_lng', lng);
    sessionStorage.setItem('localbiz_user_loc_name', name);

    // If currently on explore page, update URL params with coordinates and reload
    const currentUrl = new URL(window.location.href);
    if (currentUrl.pathname.includes('/explore')) {
        currentUrl.searchParams.set('lat', lat);
        currentUrl.searchParams.set('lng', lng);
        if (!currentUrl.searchParams.has('sort')) {
            currentUrl.searchParams.set('sort', 'nearest');
        }
        window.location.href = currentUrl.toString();
    } else {
        updateLocationStatusBadge(name, lat, lng);
        const toastNotice = document.getElementById('locationNoticeToast');
        if (toastNotice) toastNotice.style.display = 'block';
    }
}

function clearUserLocation() {
    sessionStorage.removeItem('localbiz_user_lat');
    sessionStorage.removeItem('localbiz_user_lng');
    sessionStorage.removeItem('localbiz_user_loc_name');

    const currentUrl = new URL(window.location.href);
    if (currentUrl.searchParams.has('lat') || currentUrl.searchParams.has('lng')) {
        currentUrl.searchParams.delete('lat');
        currentUrl.searchParams.delete('lng');
        currentUrl.searchParams.delete('radius');
        window.location.href = currentUrl.toString();
    } else {
        window.location.reload();
    }
}

function updateLocationStatusBadge(name, lat, lng) {
    const badge = document.getElementById('activeLocationBadge');
    if (badge) {
        badge.innerHTML = `<i class="bi bi-geo-alt-fill text-danger me-1"></i> <strong>${name}</strong> (${lat}° N, ${lng}° E) <button onclick="clearUserLocation()" class="btn btn-sm btn-link text-danger p-0 ms-2 text-decoration-none" title="Clear Location"><i class="bi bi-x-circle-fill"></i></button>`;
        badge.classList.remove('d-none');
    }
}

/* ==========================================================================
   AI CHATBOT WIDGET CLIENT
   ========================================================================== */
function initAiChatbot() {
    const chatInput = document.getElementById('aiChatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendAiMessage();
            }
        });
    }
}

function toggleAiChat() {
    const popup = document.getElementById('aiChatPopup');
    if (!popup) return;
    if (popup.style.display === 'flex') {
        popup.style.display = 'none';
    } else {
        popup.style.display = 'flex';
        const chatInput = document.getElementById('aiChatInput');
        if (chatInput) chatInput.focus();
    }
}

function sendAiMessage(customText) {
    const input = document.getElementById('aiChatInput');
    const message = customText ? customText.trim() : (input ? input.value.trim() : '');
    if (!message) return;

    if (input && !customText) input.value = '';

    const body = document.getElementById('aiChatBody');
    if (!body) return;

    // Render User Bubble
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble chat-bubble-user';
    userBubble.innerText = message;
    body.appendChild(userBubble);
    body.scrollTop = body.scrollHeight;

    // Render Typing Indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'chat-bubble chat-bubble-bot';
    typingIndicator.id = 'aiTypingIndicator';
    typingIndicator.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span> Thinking...';
    body.appendChild(typingIndicator);
    body.scrollTop = body.scrollHeight;

    // Send to backend
    const userLat = sessionStorage.getItem('localbiz_user_lat');
    const userLng = sessionStorage.getItem('localbiz_user_lng');

    fetch('/api/ai-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            lat: userLat,
            lng: userLng
        })
    })
    .then(res => res.json())
    .then(data => {
        // Remove typing indicator
        const indicator = document.getElementById('aiTypingIndicator');
        if (indicator) indicator.remove();

        // Render Bot Bubble
        const botBubble = document.createElement('div');
        botBubble.className = 'chat-bubble chat-bubble-bot';

        // Format markdown bold & linebreaks
        let formatted = data.reply
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code class="bg-light px-1 py-0 rounded text-dark">$1</code>')
            .replace(/\n/g, '<br>');

        botBubble.innerHTML = formatted;

        // Render Action Buttons if available
        if (data.actions && data.actions.length > 0) {
            const actionContainer = document.createElement('div');
            actionContainer.className = 'mt-2 pt-2 border-top d-flex flex-wrap gap-1';
            data.actions.forEach(a => {
                const btn = document.createElement('a');
                btn.href = a.url;
                btn.className = 'btn btn-primary btn-sm rounded-pill py-0 px-2 fw-semibold';
                btn.style.fontSize = '0.78rem';
                btn.innerHTML = `${a.label} <i class="bi bi-arrow-right small"></i>`;
                actionContainer.appendChild(btn);
            });
            botBubble.appendChild(actionContainer);
        }

        // Render Suggestion Chips
        if (data.suggestions && data.suggestions.length > 0) {
            const sugContainer = document.createElement('div');
            sugContainer.className = 'mt-2 d-flex flex-wrap gap-1';
            data.suggestions.forEach(s => {
                const chip = document.createElement('span');
                chip.className = 'chat-suggestion-chip';
                chip.innerText = s;
                chip.onclick = function () { sendAiMessage(s); };
                sugContainer.appendChild(chip);
            });
            botBubble.appendChild(sugContainer);
        }

        body.appendChild(botBubble);
        body.scrollTop = body.scrollHeight;
    })
    .catch(err => {
        const indicator = document.getElementById('aiTypingIndicator');
        if (indicator) indicator.remove();

        const errorBubble = document.createElement('div');
        errorBubble.className = 'chat-bubble chat-bubble-bot text-danger';
        errorBubble.innerText = 'Sorry, could not connect to AI Assistant. Please check connection and try again.';
        body.appendChild(errorBubble);
        body.scrollTop = body.scrollHeight;
    });
}
