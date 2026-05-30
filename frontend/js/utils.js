// ── Formato de moneda ────────────────────────────────────────────────────
export function formatCurrency(amount) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
    .format(amount);
}

// ── Formato de fecha ─────────────────────────────────────────────────────
export function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

// ── Badge de estado ──────────────────────────────────────────────────────
export function stateBadge(estado) {
  return `<span class="badge badge-${estado}">${estado.replace('_', ' ')}</span>`;
}

// ── Toast ────────────────────────────────────────────────────────────────
export function toast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// ── Modal simple ─────────────────────────────────────────────────────────
export function showModal({ title, body, onConfirm, confirmText = 'Confirmar', confirmClass = 'btn-primary' }) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h3>${title}</h3>
        <button class="btn btn-outline btn-sm btn-close" aria-label="Cerrar">✕</button>
      </div>
      <div class="modal-body">${body}</div>
      <div class="modal-footer">
        <button class="btn btn-outline btn-cancel">Cancelar</button>
        <button class="btn ${confirmClass} btn-confirm">${confirmText}</button>
      </div>
    </div>`;

  const close = () => {
    document.removeEventListener('keydown', onKey);
    overlay.remove();
  };
  const onKey = (e) => { if (e.key === 'Escape') close(); };

  overlay.querySelector('.btn-close').onclick = close;
  overlay.querySelector('.btn-cancel').onclick = close;
  overlay.querySelector('.btn-confirm').onclick = async () => {
    if (onConfirm) await onConfirm(overlay);
    close();
  };
  // Cerrar al hacer clic fuera del cuadro (sobre el overlay)
  overlay.addEventListener('mousedown', (e) => { if (e.target === overlay) close(); });
  document.addEventListener('keydown', onKey);

  document.body.appendChild(overlay);
  // Enfocar el primer campo o el botón de confirmar (accesibilidad)
  const focusable = overlay.querySelector('input, select, textarea, .btn-confirm');
  if (focusable) focusable.focus();
  return overlay;
}

// ── Escapar HTML (evita inyección al renderizar datos del usuario) ─────────
export function escapeHtml(value) {
  if (value === null || value === undefined) return '';
  return String(value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ── Renderizar loader (spinner glass) ──────────────────────────────────────
export function renderLoader(msg = 'Cargando…') {
  return `<div class="loading-state"><div class="spinner" role="status" aria-label="Cargando"></div><span>${escapeHtml(msg)}</span></div>`;
}

// ── Renderizar skeleton (filas fantasma mientras llega la data) ────────────
export function renderSkeleton(rows = 5) {
  const items = Array.from({ length: rows }, () => '<div class="skeleton skeleton-row"></div>').join('');
  return `<div aria-hidden="true">${items}</div>`;
}

// ── Renderizar estado vacío ────────────────────────────────────────────────
export function renderEmpty(msg = 'No hay datos para mostrar', icon = '📭') {
  return `<div class="empty-state"><div class="empty-icon">${icon}</div><p>${escapeHtml(msg)}</p></div>`;
}

// ── Renderizar error (mensaje de red claro) ────────────────────────────────
export function renderError(msg) {
  const friendly = /failed to fetch|networkerror|load failed/i.test(String(msg || ''))
    ? 'No se pudo conectar con el servidor. Verifica que la API esté activa e inténtalo de nuevo.'
    : (msg || 'Ocurrió un error inesperado.');
  return `<div class="empty-state"><div class="empty-icon">⚠️</div><p style="color:var(--color-danger)">${escapeHtml(friendly)}</p></div>`;
}
