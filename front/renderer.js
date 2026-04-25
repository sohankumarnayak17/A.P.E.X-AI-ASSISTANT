$(document).ready(function () {

  // Textilate animation
  $('text').textilate({
    loop: true,
    sync: true,
    in: {
      effect: "bounceIn",
    },
    out: {
      effect: "bounceOut",
    },
  });

  // SiriWave initialisation — under orb
  var siriWave = new SiriWave({
    container: document.getElementById("siri-container"),
    width: 400,
    height: 100,
    style: "ios9",
    amplitude: 1,
    speed: 0.30,
    autostart: true,
  });

  // ── TYPEWRITER for APEX response box ──
  function typeWrite(text) {
    $("#responseText").text("");
    var i = 0;
    var timer = setInterval(function () {
      if (i < text.length) {
        $("#responseText").text($("#responseText").text() + text.charAt(i));
        i++;
      } else {
        clearInterval(timer);
      }
    }, 40);
  }

  // ── SEND QUERY TO APEX ──
  function sendToApex(query) {
    if (!query || query.trim() === "") return;
    $("#transcriptText").text(query);
    $("#responseText").text("Processing...");
    eel.processQuery(query)(function (response) {
      if (response) {
        typeWrite(response);
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
        $("#responseText").text("Awaiting your command, Boss.");
      }
    });
  }

  // Bottom mic icon
  $("#mic").click(function () { startListening(); });

  // HOLD TO SPEAK button
  $("#talkBtn").click(function () { startListening(); });

  // CHAT BUTTON — typed input
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