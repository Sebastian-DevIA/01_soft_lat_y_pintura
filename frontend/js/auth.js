import { api, setToken, clearToken, getToken } from './api.js';
import { toast } from './utils.js';

export async function login(username, password) {
  const data = await api.login(username, password);
  setToken(data.access_token);
}

export function logout() {
  clearToken();
  location.hash = '#/login';
}

export function isAuthenticated() {
  return !!getToken();
}

export async function getCurrentUser() {
  return api.me();
}

export function setupLoginForm() {
  const form = document.getElementById('login-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type=submit]');
    btn.disabled = true;
    btn.textContent = 'Ingresando...';

    try {
      const username = form.querySelector('#username').value.trim();
      const password = form.querySelector('#password').value;
      await login(username, password);
      location.hash = '#/dashboard';
    } catch (err) {
      toast(err.message, 'error');
      btn.disabled = false;
      btn.textContent = 'Ingresar';
    }
  });
}
