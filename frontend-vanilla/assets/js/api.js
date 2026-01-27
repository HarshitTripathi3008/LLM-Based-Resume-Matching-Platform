// API Config
const API_BASE_URL = 'https://llm-based-resume-matching-platform.onrender.com/api';

// Helper for Fetch requests
async function request(endpoint, method = 'GET', body = null, isFile = false) {
    const token = localStorage.getItem('token');

    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (!isFile) headers['Content-Type'] = 'application/json';

    const config = {
        method,
        headers,
    };

    if (body) {
        config.body = isFile ? body : JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Something went wrong');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

export const api = {
    // Auth
    login: (creds) => request('/auth/login', 'POST', creds),
    register: (creds) => request('/auth/register', 'POST', creds),
    getMe: () => request('/auth/me'),

    // Resumes
    uploadResume: (formData) => request('/resumes/upload', 'POST', formData, true),
    getMyResumes: () => request('/resumes'),
    getResume: (id) => request(`/resumes/${id}`),

    // Jobs
    createJob: (data) => request('/jobs', 'POST', data),
    getJobs: () => request('/jobs'),
    matchJob: (id) => request(`/jobs/${id}/match`)
};
