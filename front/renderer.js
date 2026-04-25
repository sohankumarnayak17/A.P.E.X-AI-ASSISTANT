// ── APEX renderer.js ──

const talkBtn      = document.getElementById('talkBtn')
const muteBtn      = document.getElementById('muteBtn')
const status       = document.getElementById('status')
const listenStatus = document.getElementById('listenStatus')
const apiStatus    = document.getElementById('apiStatus')
const responseText = document.getElementById('responseText')
const transcriptEl = document.getElementById('transcriptText')
const clockEl      = document.getElementById('clock')

// ── LIVE CLOCK ──
function updateClock() {
  const now = new Date()
  clockEl.textContent = now.toLocaleTimeString('en-US', { hour12: false })
}
setInterval(updateClock, 1000)
updateClock()

// ── SIRIWAVE ──
const siriWave = new SiriWave({
  container: document.getElementById('siri-container'),
  width: 640,
  height: 200,
  style: 'ios9',
  amplitude: 1,
  speed: 0.30,
  autostart: true,
})

// ── TYPEWRITER ──
const idleMessages = [
  "Awaiting your command, Boss.",
  "All systems nominal. Ready when you are.",
  "Standing by... speak your order.",
  "A.P.E.X online. What do you need?",
  "Listening... the night is long, Boss."
]

let msgIndex         = 0
let charIndex        = 0
let isDeleting       = false
let typeTimer        = null
let typewriterActive = true

function renderText(text) {
  responseText.innerHTML = text + '<span class="cursor"></span>'
}

function typeLoop() {
  if (!typewriterActive) return
  const current = idleMessages[msgIndex]

  if (!isDeleting) {
    charIndex++
    renderText(current.slice(0, charIndex))
    if (charIndex === current.length) {
      isDeleting = true
      typeTimer = setTimeout(typeLoop, 2200)
      return
    }
    typeTimer = setTimeout(typeLoop, 55)
  } else {
    charIndex--
    renderText(current.slice(0, charIndex))
    if (charIndex === 0) {
      isDeleting = false
      msgIndex = (msgIndex + 1) % idleMessages.length
      typeTimer = setTimeout(typeLoop, 400)
      return
    }
    typeTimer = setTimeout(typeLoop, 28)
  }
}

function startTypewriter() {
  typewriterActive = true
  charIndex  = 0
  isDeleting = false
  clearTimeout(typeTimer)
  typeTimer = setTimeout(typeLoop, 800)
}

function stopTypewriter() {
  typewriterActive = false
  clearTimeout(typeTimer)
  responseText.innerHTML = ''
}

startTypewriter()

// ── SPEECH RECOGNITION ──
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
let recognition = null
let isMuted     = false

if (SpeechRecognition) {
  recognition                = new SpeechRecognition()
  recognition.continuous     = false
  recognition.interimResults = false
  recognition.lang           = 'en-US'

  recognition.onresult = (event) => {
    const transcript         = event.results[0][0].transcript
    transcriptEl.textContent = transcript
    setStatus('PROCESSING...')
    sendToApex(transcript)
  }

  recognition.onerror = () => {
    setStatus('ERROR')
    stopListening()
    setTimeout(() => {
      setStatus('STANDBY')
      startTypewriter()
    }, 2000)
  }

  recognition.onend = () => stopListening()

} else {
  apiStatus.textContent = 'SPEECH: UNSUPPORTED'
}

// ── TALK BUTTON ──
talkBtn.addEventListener('mousedown',  ()  => { if (!isMuted) startListening() })
talkBtn.addEventListener('mouseup',    ()  => { if (recognition) recognition.stop() })
talkBtn.addEventListener('mouseleave', ()  => { if (recognition) recognition.stop() })
talkBtn.addEventListener('touchstart', (e) => { e.preventDefault(); if (!isMuted) startListening() })
talkBtn.addEventListener('touchend',   ()  => { if (recognition) recognition.stop() })

// ── MUTE ──
muteBtn.addEventListener('click', () => {
  isMuted                  = !isMuted
  muteBtn.textContent      = isMuted ? 'UNMUTE' : 'MUTE'
  listenStatus.textContent = isMuted ? 'MIC: MUTED' : 'MIC: OFF'
  if (isMuted && recognition) recognition.stop()
})

// ── TEXT INPUT ──
document.getElementById('chat').addEventListener('click', () => {
  const val = document.getElementById('chatbox').value.trim()
  if (!val) return
  transcriptEl.textContent = val
  document.getElementById('chatbox').value = ''
  setStatus('PROCESSING...')
  sendToApex(val)
})

document.getElementById('chatbox').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') document.getElementById('chat').click()
})

document.getElementById('mic').addEventListener('click', () => {
  if (!isMuted) startListening()
})

// ── STATE HELPERS ──
function startListening() {
  if (!recognition) return
  stopTypewriter()
  document.body.classList.add('listening')
  setStatus('LISTENING...')
  listenStatus.textContent = 'MIC: ACTIVE'
  siriWave.setAmplitude(3)
  siriWave.setSpeed(0.08)
  try { recognition.start() } catch (e) {}
}

function stopListening() {
  document.body.classList.remove('listening')
  listenStatus.textContent = isMuted ? 'MIC: MUTED' : 'MIC: OFF'
  siriWave.setAmplitude(1)
  siriWave.setSpeed(0.30)
}

function setStatus(text) { status.textContent = text }

// ── CLAUDE API ──
async function sendToApex(userMessage) {
  apiStatus.textContent = 'API: THINKING...'
  siriWave.setAmplitude(2)
  siriWave.setSpeed(0.05)
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 300,
        system: `You are APEX — an advanced personal AI assistant.
You are sharp, efficient, and slightly dry in tone.
You call the user "Boss".
Keep all responses under 3 sentences.
Never break character.`,
        messages: [{ role: 'user', content: userMessage }]
      })
    })
    const data  = await response.json()
    const reply = data.content?.[0]?.text || 'No response received, Boss.'

    typewriterActive = false
    clearTimeout(typeTimer)
    typeReply(reply, () => {
      apiStatus.textContent = 'API: CONNECTED'
      setStatus('STANDBY')
      siriWave.setAmplitude(1)
      siriWave.setSpeed(0.30)
      setTimeout(startTypewriter, 6000)
    })

    speak(reply)
  } catch (err) {
    responseText.textContent = 'Connection failure, Boss. Check API config.'
    apiStatus.textContent    = 'API: ERROR'
    setStatus('STANDBY')
    siriWave.setAmplitude(1)
    siriWave.setSpeed(0.30)
    setTimeout(startTypewriter, 4000)
  }
}

function typeReply(text, done) {
  let i = 0
  responseText.innerHTML = '<span class="cursor"></span>'

  function tick() {
    i++
    responseText.innerHTML = text.slice(0, i) + '<span class="cursor"></span>'
    if (i < text.length) {
      typeTimer = setTimeout(tick, 38)
    } else {
      if (done) setTimeout(done, 100)
    }
  }
  typeTimer = setTimeout(tick, 80)
}

// ── TTS ──
function speak(text) {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const utter     = new SpeechSynthesisUtterance(text)
  utter.rate      = 0.95
  utter.pitch     = 0.85
  utter.volume    = 1
  const voices    = window.speechSynthesis.getVoices()
  const preferred = voices.find(v =>
    v.name.includes('Female')                   ||
    v.name.includes('Samantha')                 ||
    v.name.includes('Google UK English Female')
  )
  if (preferred) utter.voice = preferred
  window.speechSynthesis.speak(utter)
}

window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices()