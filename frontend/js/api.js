const BASE_URL = 'http://localhost:8000';
const TOKEN_KEY = 'taller_token';

export function getToken() { return localStorage.getItem(TOKEN_KEY); }
export function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
export function clearToken() { localStorage.removeItem(TOKEN_KEY); }

async function request(method, path, body = null) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, opts);

  if (res.status === 401) {
    clearToken();
    location.hash = '#/login';
    throw new Error('Sesión expirada. Por favor inicia sesión nuevamente.');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Error ${res.status}` }));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// Descarga autenticada: devuelve un Blob (para archivos protegidos por JWT, como el PDF).
// Un <a href>/window.open no sirven porque el navegador no adjunta el header Authorization.
async function requestBlob(path) {
  const token = getToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${BASE_URL}${path}`, { method: 'GET', headers });
  if (res.status === 401) {
    clearToken();
    location.hash = '#/login';
    throw new Error('Sesión expirada. Por favor inicia sesión nuevamente.');
  }
  if (!res.ok) {
    throw new Error(`No se pudo generar el documento (error ${res.status}).`);
  }
  return res.blob();
}

export const api = {
  // Auth
  login: (username, password) => {
    const form = new URLSearchParams({ username, password });
    return fetch(`${BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      body: form,
    }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail))));
  },
  me: () => request('GET', '/api/v1/auth/me'),

  // Clientes
  clientes: {
    list:   (params = '') => request('GET', `/api/v1/clientes/${params}`),
    get:    (id)  => request('GET', `/api/v1/clientes/${id}`),
    create: (data) => request('POST', '/api/v1/clientes/', data),
    update: (id, data) => request('PUT', `/api/v1/clientes/${id}`, data),
    delete: (id)  => request('DELETE', `/api/v1/clientes/${id}`),
    activar: (id) => request('PATCH', `/api/v1/clientes/${id}/activar`),
  },

  // Vehículos
  vehiculos: {
    list:   (params = '') => request('GET', `/api/v1/vehiculos/${params}`),
    get:    (id)  => request('GET', `/api/v1/vehiculos/${id}`),
    create: (data) => request('POST', '/api/v1/vehiculos/', data),
    update: (id, data) => request('PUT', `/api/v1/vehiculos/${id}`, data),
    delete: (id)  => request('DELETE', `/api/v1/vehiculos/${id}`),
  },

  // Órdenes
  ordenes: {
    list:      (params = '') => request('GET', `/api/v1/ordenes/${params}`),
    get:       (id)   => request('GET', `/api/v1/ordenes/${id}`),
    create:    (data)  => request('POST', '/api/v1/ordenes/', data),
    update:    (id, data) => request('PUT', `/api/v1/ordenes/${id}`, data),
    eliminar:  (id)   => request('DELETE', `/api/v1/ordenes/${id}`),
    activar:   (id)   => request('PATCH', `/api/v1/ordenes/${id}/activar`),
    cambiarEstado: (id, estado, notas = null) => request('PATCH', `/api/v1/ordenes/${id}/estado`, { estado, notas }),
    aprobar:   (id)   => request('PATCH', `/api/v1/ordenes/${id}/aprobar`),
    descuento: (id, pct) => request('PATCH', `/api/v1/ordenes/${id}/descuento`, { descuento_porcentaje: pct }),
    addItem:   (id, data) => request('POST', `/api/v1/ordenes/${id}/items`, data),
    updateItem:(id, itemId, data) => request('PUT', `/api/v1/ordenes/${id}/items/${itemId}`, data),
    deleteItem:(id, itemId) => request('DELETE', `/api/v1/ordenes/${id}/items/${itemId}`),
  },

  // Facturas
  facturas: {
    list:   (params = '') => request('GET', `/api/v1/facturas/${params}`),
    create: (data) => request('POST', '/api/v1/facturas/', data),
    get:    (id)   => request('GET', `/api/v1/facturas/${id}`),
    pdfUrl: (id)   => `${BASE_URL}/api/v1/facturas/${id}/pdf`,
    pdfBlob:(id)   => requestBlob(`/api/v1/facturas/${id}/pdf`),
  },

  // Pagos
  pagos: {
    list:        (params = '') => request('GET', `/api/v1/pagos/${params}`),
    create:      (data) => request('POST', '/api/v1/pagos/', data),
    byFactura:   (fid)  => request('GET', `/api/v1/pagos/factura/${fid}`),
  },

  // Fases
  fases: {
    byOrden:         (oid) => request('GET', `/api/v1/fases/orden/${oid}`),
    avanzar:         (id, estado, notas) => request('PATCH', `/api/v1/fases/${id}/estado`, { estado, notas }),
    asignarPersonal: (id, data) => request('POST', `/api/v1/fases/${id}/personal`, data),
    removerPersonal: (id, pid) => request('DELETE', `/api/v1/fases/${id}/personal/${pid}`),
  },

  // Personal
  personal: {
    list:   (params = '') => request('GET', `/api/v1/personal/${params}`),
    create: (data) => request('POST', '/api/v1/personal/', data),
    get:    (id)   => request('GET', `/api/v1/personal/${id}`),
    update: (id, data) => request('PUT', `/api/v1/personal/${id}`, data),
    toggle: (id)   => request('PATCH', `/api/v1/personal/${id}/activar`),
  },
};
