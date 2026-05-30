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
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h3>${title}</h3>
        <button class="btn btn-outline btn-sm btn-close">✕</button>
      </div>
      <div class="modal-body">${body}</div>
      <div class="modal-footer">
        <button class="btn btn-outline btn-cancel">Cancelar</button>
        <button class="btn ${confirmClass} btn-confirm">${confirmText}</button>
      </div>
    </div>`;

  const close = () => overlay.remove();
  overlay.querySelector('.btn-close').onclick = close;
  overlay.querySelector('.btn-cancel').onclick = close;
  overlay.querySelector('.btn-confirm').onclick = async () => {
    if (onConfirm) await onConfirm(overlay);
    close();
  };
  document.body.appendChild(overlay);
  return overlay;
}

// ── Renderizar loader ────────────────────────────────────────────────────
export function renderLoader() {
  return '<div style="padding:40px;text-align:center;color:var(--color-muted)">Cargando...</div>';
}

// ── Renderizar error ─────────────────────────────────────────────────────
export function renderError(msg) {
  return `<div style="padding:40px;text-align:center;color:var(--color-danger)">${msg}</div>`;
}
