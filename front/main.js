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

  // ── CLOCK ──
  function updateClock() {
    var now = new Date();
    var h   = String(now.getHours()).padStart(2, '0');
    var m   = String(now.getMinutes()).padStart(2, '0');
    var s   = String(now.getSeconds()).padStart(2, '0');
    $("#clock").text(h + ":" + m + ":" + s);
  }
  updateClock();
  setInterval(updateClock, 1000);

  // ── STARTUP GREETING ──
  // Waits 2s for UI to settle then calls Python:
  // speaks greeting → date → weather → agenda
  setTimeout(function () {
    if (typeof eel !== 'undefined') {
      eel.runStartupSequence()();
    }
  }, 2000);

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
  $("#mic").click(function ()     { startListening(); });
  $("#talkBtn").click(function () { startListening(); });

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

  // ── LOAD HISTORY WHEN SIDEBAR OPENS ──
  var chatHistoryPanel = document.getElementById('offcanvasScrolling');
  if (chatHistoryPanel) {
    chatHistoryPanel.addEventListener('show.bs.offcanvas', function () {
      var list  = document.getElementById('historyList');
      var noMsg = document.querySelector('.no-history-msg');
      if (!list) return;

      list.innerHTML = '';
      eel.getChatHistory(50)(function (history) {
        if (!history || history.length === 0) {
          if (noMsg) noMsg.style.display = 'block';
          return;
        }
        if (noMsg) noMsg.style.display = 'none';
        history.forEach(function (item) {
          var time = item.timestamp ? item.timestamp.slice(11, 16) : '';
          appendHistoryItem(item.sender, item.message, time);
        });
      });
    });
  }

});


// ── SHOW/HIDE MIC vs SEND BUTTON ──
function showhidebutton(message) {
  if (message.length === 0) {
    $("#micbtn").removeAttr("hidden");
    $("#sendbtn").attr("hidden", true);
  } else {
    $("#micbtn").attr("hidden", true);
    $("#sendbtn").removeAttr("hidden");
  }

  $("#sendbtn").click(function () {
    let message = $("#chatbox").val().trim();
    if (message) {
      playassistant(message);
    }
  });
}


// ── APPEND HISTORY ITEM (called from Python via eel) ──
function appendHistoryItem(sender, message, time) {
  var list  = document.getElementById('historyList');
  var noMsg = document.querySelector('.no-history-msg');
  if (!list) return;
  if (noMsg) noMsg.style.display = 'none';

  var entry = document.createElement('div');
  entry.className = 'history-entry';
  entry.innerHTML =
    '<div class="history-' + (sender === 'user' ? 'user' : 'apex') + '">' +
      '<span>' + (sender === 'user' ? 'YOU' : 'APEX') + '</span>' +
      '<small style="opacity:0.45;font-size:0.58rem;margin-left:6px">' + time + '</small>' +
      '<div style="margin-top:4px">' + message + '</div>' +
    '</div>';

  list.appendChild(entry);
  list.scrollTop = list.scrollHeight;
}

eel.expose(appendHistoryItem);