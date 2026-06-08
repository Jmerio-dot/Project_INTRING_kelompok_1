// ── API Configuration ────────────────────────────────────────────────────────
// Ganti ke port 8000 (Django) atau 3000 (Node.js)
// Django backend: http://localhost:8000/api
// Node.js backend: http://localhost:3000/api
const API = 'http://localhost:8000/api';

function getToken() { return localStorage.getItem('ie_token'); }
function getUser()  { try { return JSON.parse(localStorage.getItem('ie_user')); } catch { return null; } }

function requireAuth() {
  if (!getToken()) { window.location.href = '/login.html'; return false; }
  return true;
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  
  const isFormData = options.body instanceof FormData;
  
  const headers = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
  
  if (!isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(API + path, {
    ...options,
    headers,
    body: isFormData ? options.body : (options.body ? JSON.stringify(options.body) : undefined),
  });

  let data;
  try { data = await res.json(); } catch { data = {}; }

  if (res.status === 401) {
    localStorage.removeItem('ie_token');
    localStorage.removeItem('ie_user');
    window.location.href = '/login.html';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    let errMsg = data.error || data.detail;
    if (!errMsg && typeof data === 'object') {
      const keys = Object.keys(data);
      if (keys.length > 0) {
        if (Array.isArray(data[keys[0]])) {
          errMsg = `${keys[0]}: ${data[keys[0]][0]}`;
        } else if (typeof data[keys[0]] === 'string') {
          errMsg = data[keys[0]];
        }
      }
    }
    if (!errMsg) errMsg = `Request failed (${res.status})`;
    throw new Error(errMsg);
  }
  return data;
}

function logout() {
  localStorage.removeItem('ie_token');
  localStorage.removeItem('ie_user');
  window.location.href = '/login.html';
}

// ── Helpers ─────────────────────────────────────────────────────────────────
const PRIORITY_COLOR = { critical: '#dc2626', high: '#ea580c', medium: '#ca8a04', low: '#16a34a' };
const PRIORITY_ICON  = { critical: '🔴', high: '🟠', medium: '🟡', low: '🟢' };
const TYPE_ICON      = { story: '📗', task: '✅', bug: '🐛', epic: '⚡', subtask: '🔲' };
const STATUS_LABEL   = { todo: 'To Do', in_progress: 'In Progress', in_review: 'In Review', done: 'Done' };
const STATUS_COLOR   = { todo: '#64748b', in_progress: '#0369a1', in_review: '#6d28d9', done: '#15803d' };

function formatDate(str) {
  if (!str) return '—';
  return new Date(str).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
}

function timeAgo(str) {
  const diff = Date.now() - new Date(str).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'Baru saja';
  if (m < 60) return `${m} mnt lalu`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} jam lalu`;
  return `${Math.floor(h / 24)} hari lalu`;
}

// ── Toast ────────────────────────────────────────────────────────────────────
function showToast(msg, type = 'success') {
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.classList.add('show'), 10);
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 300); }, 3200);
}
