$(document).ready(function () {

  // ── SIRIWAVE INIT ──
  var siriWave = new SiriWave({
    container: document.getElementById("siri-container"),
    width: 640,
    height: 200,
    style: "ios9",
    amplitude: 1,
    speed: 0.30,
    autostart: true,
  });

  // ── TYPEWRITER ──
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

    $("#transcriptText").text(query);
    $("#responseText").text("Processing...");

    eel.processQuery(query)(function (response) {
      if (response) {
        typeWrite("#responseText", response, 40);
      } else {
        $("#responseText").text("No response, Boss.");
      }
    });
  }

  // ── START LISTENING ──
  function startListening() {
    $("#orb-wrapper").attr("hidden", true);
    $("#siri-container").removeAttr("hidden");
    $("#transcriptText").text("Listening...");
    $("#responseText").text("");

    eel.allcommand()(function (response) {
      $("#orb-wrapper").removeAttr("hidden");
      $("#siri-container").attr("hidden", true);
      if (response && response.trim() !== "") {
        typeWrite("#responseText", response, 40);
      } else {
        $("#transcriptText").text("Could not hear you. Try again.");
      }
    });
  }

  // ── PLAY ASSISTANT (text input submit) ──
  function playassistant(message) {
    if (message !== "") {
      $("#orb-wrapper").attr("hidden", true);
      $("#siri-container").removeAttr("hidden");
      eel.processQuery(message)(function (response) {
        $("#orb-wrapper").removeAttr("hidden");
        $("#siri-container").attr("hidden", true);
        if (response && response.trim() !== "") {
          typeWrite("#responseText", response, 40);
        }
      });
      $("#chatbox").val("");
    }
  }

  // ── BUTTON BINDINGS ──
  $("#mic").click(function ()    { startListening(); });
  $("#talkBtn").click(function (){ startListening(); });

  $("#chat").click(function () {
    var message = $("#chatbox").val().trim();
    if (message) {
      $("#chatbox").val("");
      sendToApex(message);
    }
  });

  // ── SEND BUTTON ──
  $("#sendbtn").click(function () {
    var message = $("#chatbox").val().trim();
    if (message) {
      playassistant(message);
    }
  });

  $("#chatbox").keypress(function (e) {
    if (e.which === 13) { $("#sendbtn").click(); }
  });

  document.addEventListener("keyup", function (e) {
    if (e.key === "a" && e.metaKey) {
      startListening();
    }
  }, false);

});


// ── SHOW/HIDE MIC vs SEND BUTTON ──
function showhidebutton(message) {                        // ✅ FIX 1: added missing closing ) for if block
  if (message.length === 0) {                             // ✅ FIX 2: use === for strict equality
    $("#micbtn").removeAttr("hidden");                    // ✅ FIX 3: removeAttr("hidden") to show, not attr("hidden", false)
    $("#sendbtn").attr("hidden", true);                   // ✅ FIX 4: hide sendbtn with true, not false
  } else {
    $("#micbtn").attr("hidden", true);                    // ✅ FIX 5: hide micbtn properly
    $("#sendbtn").removeAttr("hidden");                   // ✅ FIX 6: was missing # selector → $("sendbtn") → $("#sendbtn"), and use removeAttr to show
  }

  $("#sendbtn").click(function () {                       // ✅ FIX 7: added # to sendbtn selector
    let message = $("#chatbox").val();                    // ✅ FIX 8: was #chatbtn (wrong id) → #chatbox
    playassistant(message);
  });                                                     // ✅ FIX 9: was missing closing }) for the click handler AND the function body
}