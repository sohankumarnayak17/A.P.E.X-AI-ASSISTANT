$(document).ready(function () {

  // SiriWave initialisation
  var siriWave = new SiriWave({
    container: document.getElementById("siri-container"),
    width: 640,
    height: 200,
    style: "ios9",
    amplitude: 1,
    speed: 0.30,
    autostart: true,
  });

  // ── TYPEWRITER for response box ──
  function typeWrite(element, text, speed) {
    $(element).text("");
    var i = 0;
    var timer = setInterval(function () {
      if (i < text.length) {
        $(element).text($(element).text() + text.charAt(i));
        i++;
      } else {
        clearInterval(timer);
      }
    }, speed || 40);
  }

  // ── SEND QUERY TO APEX ──
  function sendToApex(query) {
    if (!query || query.trim() === "") return;

    // Show user query in transcript
    $("#transcriptText").text(query);

    // Show thinking in response box
    $("#responseText").text("Processing...");

    // Send to Python via eel
    eel.processQuery(query)(function (response) {
      if (response) {
        typeWrite("#responseText", response, 40);
      } else {
        $("#responseText").text("No response, Boss.");
      }
    });
  }

  // ── TRIGGER MIC ──
  function startListening() {
    $("#orb-wrapper").attr("hidden", true);
    $("#siri-container").removeAttr("hidden");
    $("#transcriptText").text("Listening...");
    $("#responseText").text("");

    eel.takecommand()(function (query) {
      $("#orb-wrapper").removeAttr("hidden");
      $("#siri-container").attr("hidden", true);
      if (query && query.trim() !== "") {
        sendToApex(query);
      } else {
        $("#transcriptText").text("Could not hear you. Try again.");
      }
    });
  }

  // Bottom mic icon
  $("#mic").click(function () { startListening(); });

  // HOLD TO SPEAK button
  $("#talkBtn").click(function () { startListening(); });

  // CHAT BUTTON
  $("#chat").click(function () {
    var message = $("#chatbox").val().trim();
    if (message) {
      $("#chatbox").val("");
      sendToApex(message);
    }
  });

  // ENTER KEY
  $("#chatbox").keypress(function (e) {
    if (e.which === 13) { $("#chat").click(); }
  });

});