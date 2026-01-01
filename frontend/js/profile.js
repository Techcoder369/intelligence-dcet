/**
 * Profile Page Script
 * Handles profile details, daily statistics, subject statistics,
 * and weekly activity visualization
 */

document.addEventListener('DOMContentLoaded', initProfilePage);

async function initProfilePage() {
    if (!requireAuth()) return;

    await Promise.all([
        loadProfile(),
        loadDailyStats(),
        loadSubjectStats()
    ]);
}

/* ================================
   PROFILE
================================ */

async function loadProfile() {
    const result = await StudentAPI.getProfile();
    if (!result?.success) return;

    const user = result.user || {};

    setText('profileName', user.dcet_reg_number || 'Student');

    setValue('username', user.dcet_reg_number || '');
    setValue('displayMobile', user.mobile_number || '');

    setValue('collegeName', user.college_name || '');
    setValue('branch', user.branch || '');
    setValue('semester', user.semester || '');
    setValue('targetYear', user.target_dcet_year || '');
}


/* ================================
   DAILY STATS
================================ */

async function loadDailyStats() {
    const result = await StudentAPI.getDailyStats();
    if (!result?.success || !Array.isArray(result.stats)) return;

    renderWeeklyChart(result.stats);
    updateTodayStats(result.stats[0]);
}

function updateTodayStats(stats) {
    if (!stats) return;

    setText('todayQuizzes', stats.quizzes_taken ?? 0);
    setText('todayFlashcards', stats.flashcards_reviewed ?? 0);
    setText('todayAccuracy', `${stats.accuracy ?? 0}%`);
    setText('todayTime', `${stats.time_spent_minutes ?? 0}m`);
}

/* ================================
   SUBJECT STATS
================================ */

async function loadSubjectStats() {
    const result = await StudentAPI.getStatsBySubject();
    if (!result?.success) return;

    const container = document.getElementById('subjectStats');
    if (!container) return;

    if (!result.stats?.length) {
        container.innerHTML = `
            <p class="text-muted">
                No subject statistics yet. Start taking quizzes!
            </p>`;
        return;
    }

    container.innerHTML = result.stats.map(renderSubjectCard).join('');
}

function renderSubjectCard(stat) {
    return `
        <div class="stat-card">
            <div class="stat-value">${stat.accuracy ?? 0}%</div>
            <div class="stat-label">${stat.short_name || stat.subject_name}</div>
            <div class="stat-subtext">
                ${stat.quizzes_taken ?? 0} quizzes
            </div>
        </div>
    `;
}

/* ================================
   WEEKLY CHART
================================ */

function renderWeeklyChart(stats) {
    const canvas = document.getElementById('weeklyChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const data = [...stats].reverse();

    const width = canvas.width;
    const height = canvas.height;

    const paddingLeft = 60;   // space for Y-axis numbers
    const paddingBottom = 40;
    const paddingTop = 40;
    const paddingRight = 20;

    const chartWidth = width - paddingLeft - paddingRight;
    const chartHeight = height - paddingTop - paddingBottom;

    ctx.clearRect(0, 0, width, height);

    const maxValue = Math.max(...data.map(d => d.quizzes_taken), 5);
    const steps = 5;
    const stepValue = Math.ceil(maxValue / steps);

    /* ======================
       DRAW GRID + Y AXIS
    ====================== */
    ctx.strokeStyle = '#374151';
    ctx.fillStyle = '#9ca3af';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'right';

    for (let i = 0; i <= steps; i++) {
        const value = i * stepValue;
        const y = paddingTop + chartHeight - (value / (stepValue * steps)) * chartHeight;

        // Grid line
        ctx.beginPath();
        ctx.moveTo(paddingLeft, y);
        ctx.lineTo(width - paddingRight, y);
        ctx.stroke();

        // Y-axis label
        ctx.fillText(value, paddingLeft - 10, y + 4);
    }

    /* ======================
       DRAW BARS
    ====================== */
    const barWidth = chartWidth / (data.length * 2);

    data.forEach((item, index) => {
        const barHeight = (item.quizzes_taken / (stepValue * steps)) * chartHeight;
        const x = paddingLeft + (chartWidth / data.length) * index + barWidth / 2;
        const y = paddingTop + chartHeight - barHeight;

        const gradient = ctx.createLinearGradient(0, y, 0, paddingTop + chartHeight);
        gradient.addColorStop(0, '#6366f1');
        gradient.addColorStop(1, '#818cf8');

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, 6);
        ctx.fill();

        // X-axis labels (days)
        ctx.fillStyle = '#9ca3af';
        ctx.textAlign = 'center';
        const day = new Date(item.date).toLocaleDateString('en-US', { weekday: 'short' });
        ctx.fillText(day, x + barWidth / 2, height - 12);
    });

    /* ======================
       TITLE
    ====================== */
    ctx.fillStyle = '#e5e7eb';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Quizzes per Day (Last 7 Days)', width / 2, 22);
}

/* ================================
   PROFILE UPDATE
================================ */

document.getElementById('profileForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
        username: getValue('username'),
        college_name: getValue('collegeName'),
        branch: getValue('branch'),
        semester: getValue('semester'),
        target_dcet_year: getValue('targetYear')
    };

    const btn = e.target.querySelector('button[type="submit"]');
    toggleButton(btn, true, 'Saving...');

    const result = await StudentAPI.updateProfile(data);

    toggleButton(btn, false, 'Save Changes');

    if (result?.success) {
        showAlert('Profile updated successfully!', 'success');
        localStorage.setItem('user', JSON.stringify({ ...getUser(), ...result.user }));
    } else {
        showAlert(result?.message || 'Failed to update profile', 'error');
    }
});

/* ================================
   LOGOUT
================================ */

document.getElementById('logoutBtn')?.addEventListener('click', () => {
    if (confirm('Are you sure you want to logout?')) {
        logout();
    }
});

/* ================================
   UTILITIES
================================ */

function setText(id, value = '') {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function setValue(id, value = '') {
    const el = document.getElementById(id);
    if (el) el.value = value;
}

function getValue(id) {
    return document.getElementById(id)?.value || '';
}

function toggleButton(btn, disabled, text) {
    if (!btn) return;
    btn.disabled = disabled;
    btn.textContent = text;
}

function showAlert(message, type) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    Object.assign(alert.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 1000
    });

    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 3000);
}
