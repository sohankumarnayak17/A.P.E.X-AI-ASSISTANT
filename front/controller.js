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
        // Scroll to bottom of chatbox
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
        // Scroll to bottom of chatbox
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

// Show loading / thinking indicator
eel.expose(showLoader);
function showLoader() {
    $("#loader").removeAttr("hidden");
}

// Hide loading / thinking indicator
eel.expose(hideLoader);
function hideLoader() {
    $("#loader").attr("hidden", true);
}

// Clear all chat messages
eel.expose(clearChat);
function clearChat() {
    document.getElementById("chat-canvas-body").innerHTML = "";
}

// Toggle chat canvas visibility
eel.expose(toggleChat);
function toggleChat() {
    var chatCanvas = $("#chat-canvas");
    if (chatCanvas.hasClass("open")) {
        chatCanvas.removeClass("open");
    } else {
        chatCanvas.addClass("open");
    }
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