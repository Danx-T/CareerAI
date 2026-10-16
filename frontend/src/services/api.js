import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/api/auth/register', data),
  login: (email, password) => {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    return api.post('/api/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  me: () => api.get('/api/auth/me'),
};

// ── CV ───────────────────────────────────────────────────
export const cvAPI = {
  upload: (file) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/api/cv/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  optimize:      (data) => api.post('/api/cv/optimize', data),
  history:       ()     => api.get('/api/cv/history'),
  deleteHistory: (id)   => api.delete(`/api/cv/history/${id}`),
};

// ── Interview ────────────────────────────────────────────
export const interviewAPI = {
  start: (data) => api.post('/api/interview/start', data),
  sessions: () => api.get('/api/interview/sessions'),
  getSession: (id) => api.get(`/api/interview/${id}`),
  saveAnswer: (sessionId, questionId, answer) =>
    api.patch(`/api/interview/${sessionId}/answer/${questionId}`, { answer }),
  complete: (sessionId) => api.post(`/api/interview/${sessionId}/complete`),
};

// ── Admin ─────────────────────────────────────────────────
export const adminAPI = {
  stats:              ()         => api.get('/api/admin/stats'),
  users:              ()         => api.get('/api/admin/users'),
  toggleActive:       (id)       => api.patch(`/api/admin/users/${id}/toggle-active`),
  toggleAdmin:        (id)       => api.patch(`/api/admin/users/${id}/toggle-admin`),
  deleteUser:         (id)       => api.delete(`/api/admin/users/${id}`),
  sessions:           ()         => api.get('/api/admin/sessions'),
  deleteSession:      (id)       => api.delete(`/api/admin/sessions/${id}`),
};

export default api;
