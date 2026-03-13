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
    resumes: document.getElementById('resumes-page'),
    match: document.getElementById('match-page')
};

const nav = document.getElementById('navbar');

// --- Google Login Handler ---
window.handleGoogleLogin = async (response) => {
    try {
        const res = await api.googleLogin(response.credential);
        localStorage.setItem('token', res.token);
        state.user = res.user;
        showDashboard();
    } catch (err) {
        console.error('Login Failed:', err);
        alert('Login failed: ' + err.message);
    }
};

async function initGoogleLogin() {
    try {
        const res = await api.getGoogleConfig();
        const clientId = res.data.clientId;

        if (!clientId || clientId === 'YOUR_GOOGLE_CLIENT_ID') {
            console.warn('Google Client ID not configured on backend.');
            return;
        }

        google.accounts.id.initialize({
            client_id: clientId,
            callback: window.handleGoogleLogin
        });

        google.accounts.id.renderButton(
            document.getElementById("google-login-container"),
            { theme: "outline", size: "large", text: "signin_with" }
        );
    } catch (err) {
        console.error('Failed to initialize Google Login:', err);
    }
}

// --- Initialization ---
async function init() {
    const token = localStorage.getItem('token');
    
    // Always initialize Google Login on start (or when on auth page)
    initGoogleLogin();

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
    Object.values(pages).forEach(el => {
        el.classList.add('hidden');
        el.style.opacity = '0';
        el.style.transform = 'translateY(10px)';
    });
    document.querySelectorAll('.nav-links a').forEach(el => el.classList.remove('active'));

    // Show target
    if (pages[pageName]) {
        pages[pageName].classList.remove('hidden');
        // Simple entrance animation
        setTimeout(() => {
            pages[pageName].style.transition = 'all 0.4s ease-out';
            pages[pageName].style.opacity = '1';
            pages[pageName].style.transform = 'translateY(0)';
        }, 10);
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

        renderResumeList(); // Dashboard list

        // Populate the resume selector on the jobs page
        populateResumeSelector();

        // Fetch Recommendations if resumes exist
        if (state.resumes.length > 0) {
            loadRecommendedJobs(state.resumes[0]._id);
        } else {
            const container = document.getElementById('external-jobs-container');
            if (container) container.innerHTML = '<p style="color: var(--text-muted); padding: 20px 0;">Upload a resume to get external job recommendations.</p>';
        }

    } catch (e) {
        console.error(e);
    }
}

async function loadRecommendedJobs(resumeId) {
    const container = document.getElementById('external-jobs-container');
    if (!container) return;
    container.innerHTML = '<div class="loading-spinner"></div>';

    try {
        const res = await api.getRecommendedJobs(resumeId);
        if (res.data.length === 0) {
            container.innerHTML = '<p>No external jobs found.</p>';
            return;
        }

        container.innerHTML = res.data.map(job => `
            <div class="glass-card job-card">
                <div class="job-header">
                    <h4>${job.title}</h4>
                    <span class="badge-external">External</span>
                </div>
                <p class="company">${job.company}${job.location ? ' &middot; ' + job.location : ''}</p>
                <p class="job-description">${job.description}</p>
                <div class="job-footer">
                    <a href="${job.url}" target="_blank" rel="noopener noreferrer" class="btn-apply">Apply on ${job.source}</a>
                </div>
            </div>
        `).join('');

    } catch (err) {
        container.innerHTML = `<p class="error">Failed to load recommendations: ${err.message}</p>`;
    }
}

// --- Rendering ---
function renderResumeList() {
    // Dashboard Mini List
    const list = document.getElementById('dashboard-resume-list');
    list.innerHTML = state.resumes.slice(0, 3).map(r => `
        <div class="resume-item">
            <div class="resume-info">
                <h4>${r.originalName}</h4>
                <small>${new Date(r.createdAt).toLocaleDateString()}</small>
            </div>
            <span class="badge ${r.status}">${r.status}</span>
        </div>
    `).join('');
}

function renderMyResumesPage() {
    const list = document.getElementById('resumes-list-container');
    if (state.resumes.length === 0) {
        list.innerHTML = '<p>No resumes uploaded yet.</p>';
        return;
    }

    list.innerHTML = state.resumes.map((r, index) => `
        <div class="resume-item full-width">
            <div class="resume-info">
                <h4>${r.originalName} ${index === 0 ? '<span class="badge-new">Latest</span>' : ''}</h4>
                <small>Uploaded: ${new Date(r.createdAt).toLocaleString()}</small>
            </div>
            <div class="resume-actions">
                <span class="badge ${r.status}">${r.status}</span>
                <button class="btn-danger" onclick="app.deleteResume('${r._id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function renderJobList() {
    const list = document.getElementById('job-list');
    list.innerHTML = state.jobs.map(j => `
        <div class="glass-card job-card">
            <div class="job-header">
                <h4>${j.title}</h4>
            </div>
            <p class="company">${j.company}</p>
            <p class="job-description">${j.description.substring(0, 100)}...</p>
            <div class="job-footer">
                <button class="btn-primary" onclick="app.matchJob('${j._id}', '${j.title}')">Find Matches</button>
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
                <div class="match-item">
                    <div class="score-circle" style="--percent:${c.score * 100}">
                        <span>${Math.round(c.score * 100)}%</span>
                    </div>
                    <div class="match-info">
                        <h4>${c.resume.originalName}</h4>
                        <div class="missing-keywords">
                            ${c.missing_keywords.length > 0 
                                ? c.missing_keywords.map(kw => `<span>${kw}</span>`).join('') 
                                : '<span>Perfect Match!</span>'}
                        </div>
                    </div>
                    <button class="btn-primary">Contact</button>
                </div>
            `).join('');
        } catch (e) {
            container.innerHTML = `<p class="error">Error: ${e.message}</p>`;
        }
    },

    deleteResume: async (id) => {
        if (!confirm('Are you sure? This cannot be undone.')) return;
        try {
            await api.deleteResume(id);
            // Refresh data
            await loadDashboardData();
            // Re-render current view if on resumes page
            renderMyResumesPage();
        } catch (e) {
            alert(e.message);
        }
    }
};

// --- Resume Selector ---
function populateResumeSelector() {
    const select = document.getElementById('resume-select');
    if (!select) return;

    // Save currently selected value
    const current = select.value;

    // Rebuild options
    select.innerHTML = state.resumes.map((r, i) =>
        `<option value="${r._id}" ${i === 0 && !current ? 'selected' : ''} ${r._id === current ? 'selected' : ''}>
            ${r.originalName}
        </option>`
    ).join('');

    if (state.resumes.length === 0) {
        select.innerHTML = '<option value="">No resumes uploaded</option>';
    }
}

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
            if (page === 'resumes') { renderMyResumesPage(); }
        });
    });

    // Resume Selector — change selection
    document.getElementById('resume-select').addEventListener('change', (e) => {
        const resumeId = e.target.value;
        if (resumeId) loadRecommendedJobs(resumeId);
    });

    // Resume Selector — Refresh button
    document.getElementById('refresh-recommendations').addEventListener('click', () => {
        const resumeId = document.getElementById('resume-select').value;
        if (resumeId) loadRecommendedJobs(resumeId);
    });

    // Back Button in Match View
    document.querySelector('.btn-back').addEventListener('click', () => {
        navigate('jobs');
    });

    document.getElementById('logout-btn').addEventListener('click', logout);

    // Auth Forms (Removed legacy listeners as we use Google Login)

    // --- Upload Modal ---
    const uploadModal = document.getElementById('upload-modal');

    // Open Modal
    document.getElementById('upload-new-resume').addEventListener('click', () => {
        uploadModal.classList.remove('hidden');
    });

    // Close Modal
    document.querySelector('.close-modal').addEventListener('click', () => {
        uploadModal.classList.add('hidden');
    });

    // Close on click outside
    window.addEventListener('click', (e) => {
        if (e.target == uploadModal) {
            uploadModal.classList.add('hidden');
        }
    });

    // File Upload Handler
    let isUploading = false;
    document.getElementById('resume-file').addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file || isUploading) return;

        isUploading = true;

        // Show Progress
        document.getElementById('drop-zone').classList.add('hidden');
        document.getElementById('upload-progress').classList.remove('hidden');

        try {
            const formData = new FormData();
            formData.append('resume', file); // Field name must match backend 'resume'

            // Call API
            await api.uploadResume(formData);

            // Success
            alert('Resume Uploaded Successfully!');
            uploadModal.classList.add('hidden');
            loadDashboardData(); // Refresh list

        } catch (err) {
            alert('Upload Failed: ' + err.message);
        } finally {
            isUploading = false;
            // Reset Modal
            document.getElementById('drop-zone').classList.remove('hidden');
            document.getElementById('upload-progress').classList.add('hidden');
            e.target.value = ''; // Reset input
        }
    });
}

// Start App
init();
