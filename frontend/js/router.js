import { isAuthenticated } from './auth.js';

const routes = {};
let currentRoute = null;

export function register(hash, handler) {
  routes[hash] = handler;
}

export function navigate(hash) {
  location.hash = hash;
}

async function handleRoute() {
  const raw = location.hash || '#/dashboard';
  const [base, param] = raw.replace('#/', '').split('/');
  const key = `#/${base}`;

  if (!isAuthenticated() && key !== '#/login') {
    location.hash = '#/login';
    return;
  }

  const handler = routes[key];
  const main = document.getElementById('main');
  const header = document.getElementById('header-title');

  // Actualizar nav activo
  document.querySelectorAll('#sidebar nav a').forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === key);
  });

  if (!handler) {
    if (main) main.innerHTML = '<p style="padding:40px;color:var(--color-muted)">Página no encontrada</p>';
    return;
  }

  currentRoute = key;
  if (handler.title && header) header.textContent = handler.title;
  if (main) await handler.render(main, param);
}

export function initRouter() {
  window.addEventListener('hashchange', handleRoute);
  handleRoute();
}
