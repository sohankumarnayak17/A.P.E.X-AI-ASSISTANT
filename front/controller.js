// ── APEX renderer.js ──

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