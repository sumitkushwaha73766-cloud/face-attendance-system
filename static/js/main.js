/**
 * FaceAttend — Futuristic Biometric UI Engine
 * Features:
 *   1. Theme Switcher (Dark Obsidian Glassmorphism <-> Modern Light)
 *   2. Web Audio API Biometric Sci-Fi Synthesizer (Chime, Alert, Scan)
 *   3. 3D Interactive Particle Matrix with Gyro/Mouse Tilt
 *   4. Biometric Floating Glass Toasts
 *   5. Live Digital HUD Clock
 *   6. Stat Card Animated Number Count-Up
 *   7. 3D Button Clicks & Ripple Effects
 */

// ─── Global State ──────────────────────────────────────────
let audioCtx = null;
let soundEnabled = localStorage.getItem('faceattend-sound') !== 'false';

// ─── 1. Initialization on DOM Load ─────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    initClock();
    initCountUp();
    init3DBackground();
    init3DButtonEffects();
    init3DCardTilt();
    updateSoundUI();
});

// ─── 2. Theme Engine (Dark Mode Default) ───────────────────
function initTheme() {
    const savedTheme = localStorage.getItem('faceattend-theme') || 'dark';
    setTheme(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('faceattend-theme', theme);

    const themeIcon = document.getElementById('themeIcon');
    const themeBtn = document.getElementById('themeToggleBtn');
    if (themeIcon) {
        if (theme === 'dark') {
            themeIcon.className = 'bi bi-moon-stars-fill text-warning';
            if (themeBtn) themeBtn.title = 'Switch to Light Theme';
        } else {
            themeIcon.className = 'bi bi-sun-fill text-warning';
            if (themeBtn) themeBtn.title = 'Switch to Dark Cyber Theme';
        }
    }
}

// ─── 3. Web Audio API Sci-Fi Synthesizer ───────────────────
function getAudioContext() {
    if (!audioCtx) {
        const AudioClass = window.AudioContext || window.webkitAudioContext;
        if (AudioClass) {
            audioCtx = new AudioClass();
        }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    return audioCtx;
}

function toggleSystemSound() {
    soundEnabled = !soundEnabled;
    localStorage.setItem('faceattend-sound', soundEnabled);
    updateSoundUI();
    if (soundEnabled) {
        playBiometricSound('success');
    }
}

function updateSoundUI() {
    const icon = document.getElementById('soundIcon');
    const btn = document.getElementById('soundToggleBtn');
    if (icon) {
        icon.className = soundEnabled ? 'bi bi-volume-up-fill text-info' : 'bi bi-volume-mute-fill text-muted';
    }
    if (btn) {
        btn.title = soundEnabled ? 'Sound Effects Enabled (Click to Mute)' : 'Sound Muted (Click to Enable)';
    }
}

function playBiometricSound(type) {
    if (!soundEnabled) return;
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const now = ctx.currentTime;

        if (type === 'success') {
            // Futuristic dual-tone chime (Access Granted / Face Verified)
            const osc1 = ctx.createOscillator();
            const osc2 = ctx.createOscillator();
            const gain = ctx.createGain();

            osc1.type = 'sine';
            osc2.type = 'triangle';

            // High-tech ascending frequencies: 587.33Hz (D5) -> 880Hz (A5)
            osc1.frequency.setValueAtTime(587.33, now);
            osc1.frequency.exponentialRampToValueAtTime(880, now + 0.12);

            osc2.frequency.setValueAtTime(880, now);
            osc2.frequency.exponentialRampToValueAtTime(1174.66, now + 0.18);

            gain.gain.setValueAtTime(0.18, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);

            osc1.connect(gain);
            osc2.connect(gain);
            gain.connect(ctx.destination);

            osc1.start(now);
            osc2.start(now);
            osc1.stop(now + 0.45);
            osc2.stop(now + 0.45);
        } else if (type === 'scan') {
            // High-tech radar chirp / blip
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(1200, now);
            osc.frequency.exponentialRampToValueAtTime(800, now + 0.06);

            gain.gain.setValueAtTime(0.04, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);

            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.06);
        } else if (type === 'alert') {
            // Warning tone for unknown face
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(320, now);
            osc.frequency.linearRampToValueAtTime(260, now + 0.18);

            gain.gain.setValueAtTime(0.08, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);

            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.22);
        }
    } catch (e) {
        console.warn('Audio synthesis notice:', e);
    }
}

// ─── 4. Biometric Floating Toast Notifications ─────────────
function showBiometricToast(title, subtitle, type = 'success') {
    let container = document.getElementById('biometricToastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'biometricToastContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '99999';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `biometric-toast ${type === 'warning' ? 'toast-warning' : ''}`;
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="bi bi-${type === 'success' ? 'patch-check-fill' : 'exclamation-diamond-fill'}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-sub">${subtitle}</div>
        </div>
        <button type="button" class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;

    container.appendChild(toast);
    playBiometricSound(type);

    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 400);
    }, 4500);
}

// ─── 5. Live Digital HUD Clock ─────────────────────────────
function initClock() {
    const clockEl = document.getElementById('clockTime');
    if (!clockEl) return;

    function update() {
        const d = new Date();
        const hrs = String(d.getHours()).padStart(2, '0');
        const mins = String(d.getMinutes()).padStart(2, '0');
        const secs = String(d.getSeconds()).padStart(2, '0');
        clockEl.innerHTML = `${hrs}<span style="opacity: 0.6; animation: blink 1s infinite;">:</span>${mins}<span style="opacity: 0.6; animation: blink 1s infinite;">:</span>${secs}`;
    }
    update();
    setInterval(update, 1000);
}

// ─── 6. Animated Counter Numbers ───────────────────────────
function initCountUp() {
    const counters = document.querySelectorAll('[data-countup]');
    counters.forEach(el => {
        const target = parseFloat(el.getAttribute('data-countup')) || 0;
        const isDecimal = target % 1 !== 0;
        const duration = 1200;
        const startTime = performance.now();

        function step(now) {
            const progress = Math.min((now - startTime) / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = progress * target;
            el.textContent = isDecimal ? (easeOut * target).toFixed(1) : Math.floor(easeOut * target);
            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                el.textContent = isDecimal ? target.toFixed(1) : target;
            }
        }
        requestAnimationFrame(step);
    });
}

// ─── 7. 3D Particle Network Canvas ─────────────────────────
function init3DBackground() {
    const canvas = document.getElementById('bg3d-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    const NUM_PARTICLES = 80;

    let targetRotX = 0;
    let targetRotY = 0;
    let curRotX = 0;
    let curRotY = 0;

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    for (let i = 0; i < NUM_PARTICLES; i++) {
        particles.push({
            x: (Math.random() - 0.5) * 900,
            y: (Math.random() - 0.5) * 800,
            z: (Math.random() - 0.5) * 700,
            baseRadius: Math.random() * 2.2 + 1.2,
            vx: (Math.random() - 0.5) * 0.35,
            vy: (Math.random() - 0.5) * 0.35,
            vz: (Math.random() - 0.5) * 0.35,
        });
    }

    window.addEventListener('mousemove', (e) => {
        const normX = (e.clientX / width) - 0.5;
        const normY = (e.clientY / height) - 0.5;
        targetRotY = normX * 0.4;
        targetRotX = -normY * 0.4;
    });

    let angle = 0;

    function render() {
        ctx.clearRect(0, 0, width, height);

        curRotX += (targetRotX - curRotX) * 0.05;
        curRotY += (targetRotY - curRotY) * 0.05;
        angle += 0.0025;

        const totalRotY = curRotY + angle;
        const totalRotX = curRotX;

        const cosY = Math.cos(totalRotY);
        const sinY = Math.sin(totalRotY);
        const cosX = Math.cos(totalRotX);
        const sinX = Math.sin(totalRotX);

        const projected = [];
        const fov = 380;
        const camZ = 460;

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.z += p.vz;

            if (p.x > 450) p.x = -450;
            if (p.x < -450) p.x = 450;
            if (p.y > 400) p.y = -400;
            if (p.y < -400) p.y = 400;
            if (p.z > 350) p.z = -350;
            if (p.z < -350) p.z = 350;

            const x1 = p.x * cosY + p.z * sinY;
            const z1 = -p.x * sinY + p.z * cosY;
            const y1 = p.y * cosX - z1 * sinX;
            const z2 = p.y * sinX + z1 * cosX;

            const scale = fov / (fov + z2 + camZ);
            const projX = (x1 * scale) + (width / 2);
            const projY = (y1 * scale) + (height / 2);
            const radius = Math.max(0.6, p.baseRadius * scale);
            const alpha = Math.min(0.85, Math.max(0.12, (scale - 0.25) * 1.2));

            projected.push({ x: projX, y: projY, r: radius, a: alpha });
        }

        // Draw connecting neural lines
        for (let i = 0; i < projected.length; i++) {
            for (let j = i + 1; j < projected.length; j++) {
                const dx = projected[i].x - projected[j].x;
                const dy = projected[i].y - projected[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 110) {
                    const lineAlpha = (1 - dist / 110) * 0.18;
                    ctx.beginPath();
                    ctx.moveTo(projected[i].x, projected[i].y);
                    ctx.lineTo(projected[j].x, projected[j].y);
                    ctx.strokeStyle = `rgba(6, 182, 212, ${lineAlpha})`;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            }
        }

        // Draw glowing nodes
        for (let i = 0; i < projected.length; i++) {
            const pt = projected[i];
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, pt.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(6, 182, 212, ${pt.a})`;
            ctx.shadowBlur = 8;
            ctx.shadowColor = 'rgba(6, 182, 212, 0.6)';
            ctx.fill();
            ctx.shadowBlur = 0;
        }

        requestAnimationFrame(render);
    }
    requestAnimationFrame(render);
}

// ─── 8. 3D Card Tilt & Button Shockwave ────────────────────
function init3DButtonEffects() {
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn');
        if (!btn) return;

        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const ripple = document.createElement('span');
        ripple.className = 'ripple-3d';
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;
        const size = Math.max(rect.width, rect.height) * 2;
        ripple.style.width = `${size}px`;
        ripple.style.height = `${size}px`;

        btn.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    });
}

function init3DCardTilt() {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            card.style.transform = `perspective(1000px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg) translateY(-4px)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });
}
