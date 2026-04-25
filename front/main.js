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

  // MIC BUTTON
  $("#mic").click(function () {
    $("#orb-wrapper").attr("hidden", true);
    $("#siri-container").removeAttr("hidden");
  });

});