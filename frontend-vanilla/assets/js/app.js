import { api } from './api.js';

// State
const state = {
    user: null,
    resumes: [],
    jobs: []
};

// DOM Elements
const pages = {
    auth: document.getElementById('auth-page'),
    dashboard: document.getElementById('dashboard-page'),
    jobs: document.getElementById('jobs-page'),
    match: document.getElementById('match-page')
};

const nav = document.getElementById('navbar');

// --- Initialization ---
async function init() {
    const token = localStorage.getItem('token');
    if (token) {
        try {
            const res = await api.getMe();
            state.user = res.data;
            showDashboard();
        } catch (e) {
            logout();
        }
    } else {
        showAuth();
    }
    setupEventListeners();
}

// --- Navigation ---
function navigate(pageName) {
    // Hide all pages
    Object.values(pages).forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.nav-links a').forEach(el => el.classList.remove('active'));

    // Show target
    if (pages[pageName]) {
        pages[pageName].classList.remove('hidden');
        const link = document.querySelector(`[data-page="${pageName}"]`);
        if (link) link.classList.add('active');
    }
}

function showAuth() {
    state.user = null;
    nav.classList.add('hidden');
    navigate('auth');
}

async function showDashboard() {
    nav.classList.remove('hidden');
    navigate('dashboard');
    loadDashboardData();
}

function logout() {
    localStorage.removeItem('token');
    showAuth();
}

// --- Data Loading ---
async function loadDashboardData() {
    try {
        const [resResumes, resJobs] = await Promise.all([
            api.getMyResumes(),
            api.getJobs()
        ]);

        state.resumes = resResumes.data;
        state.jobs = resJobs.data;

        // Update Stats
        document.getElementById('stat-resumes').innerText = state.resumes.length;
        document.getElementById('stat-jobs').innerText = state.jobs.length;

        renderResumeList();
    } catch (e) {
        console.error(e);
    }
}

// --- Rendering ---
function renderResumeList() {
    const list = document.getElementById('dashboard-resume-list');
    list.innerHTML = state.resumes.map(r => `
        <div class="glass-card resume-item">
            <div>
                <h4>${r.originalName}</h4>
                <small>${new Date(r.createdAt).toLocaleDateString()}</small>
            </div>
            <span class="badg ${r.status}">${r.status}</span>
        </div>
    `).join('');
}

function renderJobList() {
    const list = document.getElementById('job-list');
    list.innerHTML = state.jobs.map(j => `
        <div class="glass-card job-item">
            <h3>${j.title}</h3>
            <p class="company">${j.company}</p>
            <p class="desc">${j.description.substring(0, 100)}...</p>
            <div class="actions">
                <button class="btn-secondary btn-sm" onclick="app.matchJob('${j._id}', '${j.title}')">✨ Find Matches</button>
            </div>
        </div>
    `).join('');
}

// --- Actions ---
window.app = {
    matchJob: async (id, title) => {
        document.getElementById('match-job-title').innerText = `Matches for: ${title}`;
        navigate('match');
        const container = document.getElementById('match-results');
        container.innerHTML = '<div class="loading-spinner"></div>';

        try {
            const res = await api.matchJob(id);
            if (res.candidates.length === 0) {
                container.innerHTML = '<p>No candidates found.</p>';
                return;
            }

            container.innerHTML = res.candidates.map(c => `
                <div class="glass-card match-item">
                    <div class="score-circle" style="--percent:${c.score * 100}">
                        <span>${Math.round(c.score * 100)}%</span>
                    </div>
                    <div class="match-info">
                        <h4>${c.resume.originalName}</h4>
                        <p class="missing-keywords">Missing: ${c.missing_keywords.join(', ') || 'None! Perfect Match'}</p>
                    </div>
                    <button class="btn-primary">Contact</button>
                </div>
            `).join('');
        } catch (e) {
            container.innerHTML = `<p class="error">Error: ${e.message}</p>`;
        }
    }
};

// --- Event Listeners ---
function setupEventListeners() {
    // Nav
    document.querySelectorAll('.nav-links a').forEach(a => {
        a.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.target.dataset.page;
            navigate(page);
            if (page === 'dashboard') loadDashboardData();
            if (page === 'jobs') { renderJobList(); }
        });
    });

    // Back Button in Match View
    document.querySelector('.btn-back').addEventListener('click', () => {
        navigate('jobs');
    });

    document.getElementById('logout-btn').addEventListener('click', logout);

    // Auth Forms
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            const res = await api.login({ email, password });
            localStorage.setItem('token', res.token);
            await init();
        } catch (err) {
            alert(err.message);
        }
    });

    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;

        try {
            const res = await api.register({ name, email, password });
            localStorage.setItem('token', res.token);
            await init();
        } catch (err) {
            alert(err.message);
        }
    });

    // Toggle Auth
    document.getElementById('show-register').addEventListener('click', () => {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    });

    document.getElementById('show-login').addEventListener('click', () => {
        document.getElementById('register-form').classList.add('hidden');
        document.getElementById('login-form').classList.remove('hidden');
    });
}

// Start App
init();
