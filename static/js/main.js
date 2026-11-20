/**
 * Face Recognition Attendance System
 * 3D Background & Interactive 3D Button Animation Engine
 */

document.addEventListener('DOMContentLoaded', function () {
    // ─── 1. Auto-dismiss alerts after 5 seconds ─────────────────────
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // ─── 2. 3D Animated Background Engine ──────────────────────────
    init3DBackground();

    // ─── 3. 3D Button Click & Card Tilt Effects ────────────────────
    init3DButtonEffects();
    init3DCardTilt();
});

/**
 * Interactive 3D Biometric Particle Network Background
 */
function init3DBackground() {
    const canvas = document.getElementById('bg3d-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    const NUM_PARTICLES = 85;
    const FOV = 360;
    const CAMERA_Z = 450;

    // Mouse tilt & rotation tracking
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

    // Initialize 3D particles in a sphere/cube volume
    for (let i = 0; i < NUM_PARTICLES; i++) {
        particles.push({
            x: (Math.random() - 0.5) * 800,
            y: (Math.random() - 0.5) * 700,
            z: (Math.random() - 0.5) * 600,
            baseRadius: Math.random() * 2.2 + 1.2,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            vz: (Math.random() - 0.5) * 0.4,
            colorHue: Math.random() > 0.4 ? 230 : 260 // Cyber indigo & electric blue
        });
    }

    // Mouse movement adds 3D tilt
    window.addEventListener('mousemove', (e) => {
        const normX = (e.clientX / width) - 0.5;
        const normY = (e.clientY / height) - 0.5;
        targetRotY = normX * 0.45;
        targetRotX = -normY * 0.45;
    });

    let angle = 0;

    function render() {
        ctx.clearRect(0, 0, width, height);

        // Smoothly interpolate rotation towards target
        curRotX += (targetRotX - curRotX) * 0.05;
        curRotY += (targetRotY - curRotY) * 0.05;
        angle += 0.003;

        const totalRotY = curRotY + angle;
        const totalRotX = curRotX + Math.sin(angle * 0.7) * 0.08;

        const cosY = Math.cos(totalRotY);
        const sinY = Math.sin(totalRotY);
        const cosX = Math.cos(totalRotX);
        const sinX = Math.sin(totalRotX);

        const projected = [];

        // Transform, rotate & project particles into 2D
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];

            // Update particle drift
            p.x += p.vx;
            p.y += p.vy;
            p.z += p.vz;

            // Boundary wrap in 3D box
            if (p.x < -400) p.x = 400; if (p.x > 400) p.x = -400;
            if (p.y < -350) p.y = 350; if (p.y > 350) p.y = -350;
            if (p.z < -300) p.z = 300; if (p.z > 300) p.z = -300;

            // Rotate Y
            const x1 = p.x * cosY - p.z * sinY;
            const z1 = p.z * cosY + p.x * sinY;

            // Rotate X
            const y2 = p.y * cosX - z1 * sinX;
            const z2 = z1 * cosX + p.y * sinX;

            const depth = z2 + CAMERA_Z;
            if (depth > 20) {
                const scale = FOV / depth;
                const px = x1 * scale + width / 2;
                const py = y2 * scale + height / 2;
                const alpha = Math.min(Math.max((z2 + 300) / 600, 0.15), 0.95);

                projected.push({
                    x: px,
                    y: py,
                    radius: p.baseRadius * scale * 0.8,
                    alpha: alpha,
                    colorHue: p.colorHue
                });
            } else {
                projected.push(null);
            }
        }

        // Draw 3D connecting constellation lines
        ctx.lineWidth = 0.8;
        for (let i = 0; i < projected.length; i++) {
            const p1 = projected[i];
            if (!p1) continue;

            for (let j = i + 1; j < projected.length; j++) {
                const p2 = projected[j];
                if (!p2) continue;

                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 115) {
                    const lineAlpha = (1 - dist / 115) * Math.min(p1.alpha, p2.alpha) * 0.35;
                    ctx.strokeStyle = `rgba(99, 102, 241, ${lineAlpha})`;
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }
        }

        // Draw 3D nodes
        for (let i = 0; i < projected.length; i++) {
            const p = projected[i];
            if (!p) continue;

            // Glowing outer halo
            ctx.beginPath();
            ctx.arc(p.x, p.y, Math.max(p.radius * 2, 1), 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${p.colorHue}, 85%, 65%, ${p.alpha * 0.25})`;
            ctx.fill();

            // Core dot
            ctx.beginPath();
            ctx.arc(p.x, p.y, Math.max(p.radius, 0.8), 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${p.colorHue}, 90%, 75%, ${p.alpha * 0.85})`;
            ctx.fill();
        }

        requestAnimationFrame(render);
    }

    render();
}

/**
 * 3D Button Click Ripple, Shockwave & 3D Particle Explosion
 */
function init3DButtonEffects() {
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn');
        if (!btn) return;

        // 1. Tactile 3D depression animation
        btn.classList.add('clicked-3d');
        setTimeout(() => btn.classList.remove('clicked-3d'), 250);

        // 2. 3D Radial Ripple inside button
        const rect = btn.getBoundingClientRect();
        const ripple = document.createElement('span');
        ripple.classList.add('ripple-3d');

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const size = Math.max(rect.width, rect.height) * 2;

        ripple.style.width = ripple.style.height = `${size}px`;
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;

        btn.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);

        // 3. 3D Particle Burst flying out into screen space
        create3DParticleBurst(e.clientX, e.clientY);
    });
}

/**
 * Spawns 3D spark particles from click position
 */
function create3DParticleBurst(originX, originY) {
    const colors = ['#6366f1', '#38bdf8', '#a855f7', '#ffffff', '#4f46e5'];
    const count = 12;

    for (let i = 0; i < count; i++) {
        const particle = document.createElement('div');
        particle.classList.add('click-particle-3d');

        const size = Math.random() * 6 + 4;
        const color = colors[Math.floor(Math.random() * colors.length)];

        // Random 3D trajectories
        const angle = Math.random() * Math.PI * 2;
        const distance = Math.random() * 60 + 30;
        const tx = Math.cos(angle) * distance;
        const ty = Math.sin(angle) * distance;
        const tz = (Math.random() - 0.5) * 120; // 3D depth movement

        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.backgroundColor = color;
        particle.style.boxShadow = `0 0 10px ${color}`;
        particle.style.left = `${originX}px`;
        particle.style.top = `${originY}px`;
        particle.style.setProperty('--tx', `${tx}px`);
        particle.style.setProperty('--ty', `${ty}px`);
        particle.style.setProperty('--tz', `${tz}px`);

        document.body.appendChild(particle);
        setTimeout(() => particle.remove(), 700);
    }
}

/**
 * Subtle 3D Card Tilt on Hover
 */
function init3DCardTilt() {
    const cards = document.querySelectorAll('.card');

    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left - (rect.width / 2);
            const y = e.clientY - rect.top - (rect.height / 2);

            const rotateX = -(y / (rect.height / 2)) * 4; // Max 4 deg tilt
            const rotateY = (x / (rect.width / 2)) * 4;

            card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-4px)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)';
        });
    });
}
