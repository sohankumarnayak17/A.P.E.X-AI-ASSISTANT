// ── APEX renderer.js ──

// DOM
const talkBtn      = document.getElementById('talkBtn')
const muteBtn      = document.getElementById('muteBtn')
const status       = document.getElementById('status')
const listenStatus = document.getElementById('listenStatus')
const apiStatus    = document.getElementById('apiStatus')
const responseText = document.getElementById('responseText')
const transcriptEl = document.getElementById('transcriptText')
const clockEl      = document.getElementById('clock')

// ── CLOCK ──
function updateClock() {
  const now = new Date()
  clockEl.textContent = now.toLocaleTimeString('en-US', { hour12: false })
}
setInterval(updateClock, 1000)
updateClock()

// ══════════════════════════════════════
//   3D PARTICLE SPHERE — red wine theme
// ══════════════════════════════════════
const canvas  = document.getElementById('particleCanvas')
const ctx     = canvas.getContext('2d')
const W       = canvas.width
const H       = canvas.height
const cx      = W / 2
const cy      = H / 2

let listening  = false
let angleX     = 0
let angleY     = 0
const RADIUS   = 100
const NUM_DOTS = 280

// Generate points on sphere surface using fibonacci lattice
function fibonacciSphere(n, r) {
  const pts = []
  const golden = Math.PI * (3 - Math.sqrt(5))
  for (let i = 0; i < n; i++) {
    const y   = 1 - (i / (n - 1)) * 2
    const rad = Math.sqrt(1 - y * y)
    const theta = golden * i
    pts.push({
      x: Math.cos(theta) * rad * r,
      y: y * r,
      z: Math.sin(theta) * rad * r,
    })
  }
  return pts
}

let dots = fibonacciSphere(NUM_DOTS, RADIUS)

// Rotation helpers
function rotateX(p, a) {
  const cos = Math.cos(a), sin = Math.sin(a)
  return { x: p.x, y: p.y * cos - p.z * sin, z: p.y * sin + p.z * cos }
}
function rotateY(p, a) {
  const cos = Math.cos(a), sin = Math.sin(a)
  return { x: p.x * cos + p.z * sin, y: p.y, z: -p.x * sin + p.z * cos }
}

// Wine red color palette
function getDotColor(z, alpha) {
  const t = (z + RADIUS) / (2 * RADIUS) // 0 to 1
  if (t > 0.75) return `rgba(255, 60, 60, ${alpha})`
  if (t > 0.5)  return `rgba(200, 10, 10, ${alpha})`
  if (t > 0.25) return `rgba(140,  0,  0, ${alpha})`
  return                `rgba( 80,  0,  0, ${alpha})`
}

function drawSphere() {
  ctx.clearRect(0, 0, W, H)

  // Draw connection lines between nearby dots
  const projected = dots.map(p => {
    let r = rotateY(p, angleY)
    r = rotateX(r, angleX)
    const scale = (RADIUS + r.z) / (2 * RADIUS)
    return {
      sx: cx + r.x * scale,
      sy: cy + r.y * scale,
      z:  r.z,
      scale
    }
  })

  // Draw lines first (behind dots)
  for (let i = 0; i < projected.length; i++) {
    for (let j = i + 1; j < projected.length; j++) {
      const a = projected[i]
      const b = projected[j]
      const dx = a.sx - b.sx
      const dy = a.sy - b.sy
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < 28) {
        const alpha = (1 - dist / 28) * 0.25 * ((a.z + b.z) / 2 + RADIUS) / (2 * RADIUS)
        ctx.beginPath()
        ctx.moveTo(a.sx, a.sy)
        ctx.lineTo(b.sx, b.sy)
        ctx.strokeStyle = `rgba(150, 0, 0, ${Math.max(0, alpha)})`
        ctx.lineWidth = 0.4
        ctx.stroke()
      }
    }
  }

  // Draw dots
  projected.forEach(p => {
    const norm  = (p.z + RADIUS) / (2 * RADIUS)
    const alpha = listening ? norm * 0.9 + 0.1 : norm * 0.75 + 0.08
    const size  = listening ? p.scale * 3.2 : p.scale * 2.5

    // Glow for front dots
    if (norm > 0.7) {
      ctx.beginPath()
      ctx.arc(p.sx, p.sy, size * 2.5, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(200, 0, 0, ${alpha * 0.15})`
      ctx.fill()
    }

    ctx.beginPath()
    ctx.arc(p.sx, p.sy, size, 0, Math.PI * 2)
    ctx.fillStyle = getDotColor(p.z, alpha)
    ctx.fill()
  })

  // Draw glowing core center
  const coreGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, listening ? 22 : 14)
  coreGlow.addColorStop(0, `rgba(255, 80, 80, ${listening ? 0.95 : 0.7})`)
  coreGlow.addColorStop(0.4, `rgba(180, 0, 0, ${listening ? 0.5 : 0.3})`)
  coreGlow.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.beginPath()
  ctx.arc(cx, cy, listening ? 22 : 14, 0, Math.PI * 2)
  ctx.fillStyle = coreGlow
  ctx.fill()
}

function animate() {
  angleY += listening ? 0.012 : 0.006
  angleX += listening ? 0.005 : 0.002
  drawSphere()
  requestAnimationFrame(animate)
}

animate()

// ── MUTE ──
let isMuted = false
muteBtn.addEventListener('click', () => {
  isMuted = !isMuted
  muteBtn.textContent      = isMuted ? 'UNMUTE' : 'MUTE'
  listenStatus.textContent = isMuted ? 'MIC: MUTED' : 'MIC: OFF'
})

// ── TALK BUTTON ──
talkBtn.addEventListener('mousedown', () => {
  if (isMuted) return
  startListening()
})
talkBtn.addEventListener('mouseup',    () => stopListening())
talkBtn.addEventListener('mouseleave', () => stopListening())
talkBtn.addEventListener('touchstart', (e) => { e.preventDefault(); if (!isMuted) startListening() })
talkBtn.addEventListener('touchend',   () => stopListening())

function startListening() {
  listening = true
  document.body.classList.add('listening')
  status.textContent       = 'LISTENING...'
  listenStatus.textContent = 'MIC: ACTIVE'
}

function stopListening() {
  listening = false
  document.body.classList.remove('listening')
  listenStatus.textContent = isMuted ? 'MIC: MUTED' : 'MIC: OFF'
  status.textContent       = 'STANDBY'
}

// ── BRING TO FRONT (called by Python on clap) ──
function bringToFront() {
  window.focus()
  listening = true
  document.body.classList.add('listening')
  status.textContent = 'ONLINE'
  setTimeout(() => {
    listening = false
    document.body.classList.remove('listening')
    status.textContent = 'STANDBY'
  }, 3000)
}

// ── SHOW/HIDE SEND BUTTON ──
function showhidebutton(val) {
  const btn = document.getElementById('sendbtn')
  if (val.trim() !== '') {
    btn.removeAttribute('hidden')
  } else {
    btn.setAttribute('hidden', true)
  }
}

// ── CLOCK ──
function updateClock() {
  const now = new Date()
  document.getElementById('clock').textContent =
    now.toLocaleTimeString('en-US', { hour12: false })
}
setInterval(updateClock, 1000)
updateClock()