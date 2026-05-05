// ── APEX controller.js ──

// Display spoken message
eel.expose(DisplayMessage);
function DisplayMessage(message) {
    $("#transcriptText").text(message);
    $("#transcriptText").textillate('start');
}

// Show orb, hide siriwave
eel.expose(showhood);
function showhood() {
    $("#orb-wrapper").removeAttr("hidden");
    $("#siri-container").attr("hidden", true);
}

// Hide orb, show siriwave
eel.expose(hidehood);
function hidehood() {
    $("#orb-wrapper").attr("hidden", true);
    $("#siri-container").removeAttr("hidden");
}

// Send message (user side)
eel.expose(sendertext);
function sendertext(message) {
    var chatbox = document.getElementById("chat-canvas-body");
    if (message.trim() !== "") {
        chatbox.innerHTML += `
            <div class="row justify-content-end mb-4">
                <div class="width-size">
                    <div class="sender_message">${message}</div>
                </div>
            </div>
        `;
        chatbox.scrollTop = chatbox.scrollHeight;
    }
}

// Receive message (bot side)
eel.expose(recievertext);
function recievertext(message) {
    var chatbox = document.getElementById("chat-canvas-body");
    if (message.trim() !== "") {
        chatbox.innerHTML += `
            <div class="row justify-content-start mb-4">
                <div class="width-size">
                    <div class="receiver_message">${message}</div>
                </div>
            </div>
        `;
        chatbox.scrollTop = chatbox.scrollHeight;
    }
}

// Clear transcript text
eel.expose(clearTranscript);
function clearTranscript() {
    $("#transcriptText").text("");
}

// Show mic button, hide stop button
eel.expose(showMic);
function showMic() {
    $("#mic-btn").removeAttr("hidden");
    $("#stop-btn").attr("hidden", true);
}

// Hide mic button, show stop button
eel.expose(hideMic);
function hideMic() {
    $("#mic-btn").attr("hidden", true);
    $("#stop-btn").removeAttr("hidden");
}

// Show loading indicator
eel.expose(showLoader);
function showLoader() {
    $("#loader").removeAttr("hidden");
}

// Hide loading indicator
eel.expose(hideLoader);
function hideLoader() {
    $("#loader").attr("hidden", true);
}

// Clear all chat messages from chatbox
eel.expose(clearChat);
function clearChat() {
    document.getElementById("chat-canvas-body").innerHTML = "";
}

// Update assistant status text
eel.expose(updateStatus);
function updateStatus(status) {
    $("#status-text").text(status);
}

// Play animation on orb
eel.expose(playOrbAnimation);
function playOrbAnimation() {
    $("#orb").addClass("active");
}

// Stop animation on orb
eel.expose(stopOrbAnimation);
function stopOrbAnimation() {
    $("#orb").removeClass("active");
}


// ══════════════════════════════
//   CHAT HISTORY SIDEBAR
// ══════════════════════════════

// Called live by Python each time a new message is processed
eel.expose(appendHistoryItem);
function appendHistoryItem(sender, message, time) {
    var historyList = document.getElementById("history-list");
    if (!historyList) return;

    var isApex = sender === "apex";
    var item = document.createElement("div");
    item.className = "history-item " + (isApex ? "history-apex" : "history-user");
    item.innerHTML = `
        <div class="history-sender">${isApex ? "⚡ APEX" : "🧑 You"}</div>
        <div class="history-text">${message}</div>
        <div class="history-time">${time}</div>
    `;
    historyList.appendChild(item);
    historyList.scrollTop = historyList.scrollHeight;
}

// Load full history from DB when sidebar opens
async function loadChatHistory() {
    var historyList = document.getElementById("history-list");
    if (!historyList) return;

    historyList.innerHTML = '<div class="history-loading">Loading history...</div>';

    var history = await eel.getChatHistory(50)();
    historyList.innerHTML = "";

    if (history.length === 0) {
        historyList.innerHTML = '<div class="history-empty">No chat history yet, Boss.</div>';
        return;
    }

    history.forEach(function (item) {
        var time = item.timestamp.split(" ")[1].substring(0, 5); // HH:MM
        appendHistoryItem(item.sender, item.message, time);
    });
}

// Clear history button handler
async function clearHistory() {
    var ok = await eel.clearChatHistory()();
    if (ok) {
        document.getElementById("history-list").innerHTML =
            '<div class="history-empty">History cleared, Boss.</div>';
    }
}

// Toggle sidebar open / close
function toggleHistorySidebar() {
    var sidebar = document.getElementById("history-sidebar");
    var isOpen = sidebar.classList.contains("open");
    if (isOpen) {
        sidebar.classList.remove("open");
    } else {
        sidebar.classList.add("open");
        loadChatHistory();
    }
}