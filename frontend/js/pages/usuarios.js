import { api } from '../api.js';
import { renderLoader, renderError, renderEmpty, toast, showModal, confirmDialog, escapeHtml } from '../utils.js';
import { getCurrentUser, clearUserCache, PERFIL_LABEL } from '../auth.js';

const PERFILES = ['ADMIN', 'RECEPCION', 'TECNICO', 'ENTREGA'];

// Pista de qué hace cada perfil (se muestra al crear/editar).
const PERFIL_AYUDA = {
  ADMIN: 'Gestiona todo el sistema, incluidos los usuarios.',
  RECEPCION: 'Atiende el ingreso del vehículo (fase INGRESO).',
  TECNICO: 'Trabaja la reparación (fase REPARACIÓN).',
  ENTREGA: 'Gestiona la entrega final (fase ENTREGA).',
};

function opcionesPerfil(seleccionado) {
  return PERFILES
    .map(p => `<option value="${p}" ${p === seleccionado ? 'selected' : ''}>${PERFIL_LABEL[p]}</option>`)
    .join('');
}

function perfilBadge(perfil) {
  const cls = perfil === 'ADMIN' ? 'badge-APROBACION' : 'badge-COTIZACION';
  return `<span class="badge ${cls}">${escapeHtml(PERFIL_LABEL[perfil] || perfil)}</span>`;
}

function estadoBadge(activo) {
  return activo
    ? '<span class="badge badge-ENTREGADO">Activo</span>'
    : '<span class="badge badge-CANCELADO">Inactivo</span>';
}

export const usuarios = {
  title: 'Usuarios',
  async render(container) {
    container.innerHTML = renderLoader();

    // Solo administradores pueden entrar aquí.
    let yo = null;
    try { yo = await getCurrentUser(); } catch { /* sin sesión válida */ }
    if (!yo || !yo.is_admin) {
      container.innerHTML = renderEmpty('Acceso restringido: solo los administradores pueden gestionar usuarios.', '🔒');
      return;
    }

    try {
      const lista = await api.usuarios.list();
      container.innerHTML = `
        <div class="flex justify-between align-center mb-2">
          <h2>Usuarios y perfiles</h2>
          <button class="btn btn-primary" id="btn-nuevo-usuario">+ Nuevo usuario</button>
        </div>
        <p class="text-muted mb-2" style="font-size:.85rem">
          Cada usuario entra con su perfil y, según él, ve el estado de los vehículos y
          actualiza solo la fase que le corresponde. El perfil <strong>Administrador</strong>
          gestiona todo.
        </p>
        <div class="card">
          <div class="table-wrapper">
            <table class="data-table">
              <thead><tr><th>Usuario</th><th>Nombre</th><th>Email</th><th>Perfil</th><th>Estado</th><th>Acciones</th></tr></thead>
              <tbody id="tbody-usuarios">${renderFilas(lista, yo)}</tbody>
            </table>
          </div>
        </div>`;

      container.querySelector('#btn-nuevo-usuario').onclick = () => formularioUsuario(null, () => this.render(container));
      attachEventos(container, lista, yo, () => this.render(container));
    } catch (err) {
      container.innerHTML = renderError(err.message);
    }
  }
};

function renderFilas(lista, yo) {
  if (!lista.length) {
    return `<tr><td colspan="6">${renderEmpty('Sin usuarios.', '👥')}</td></tr>`;
  }
  return lista.map(u => {
    const esYo = u.id === yo.id;
    const toggle = u.is_active
      ? `<button class="btn btn-danger btn-sm" data-id="${u.id}" data-action="desactivar" ${esYo ? 'disabled title="No puedes desactivar tu propio usuario"' : ''}>Desactivar</button>`
      : `<button class="btn btn-success btn-sm" data-id="${u.id}" data-action="activar">Activar</button>`;
    return `
      <tr>
        <td><strong>${escapeHtml(u.username)}</strong>${esYo ? ' <span class="text-muted" style="font-size:.78rem">(tú)</span>' : ''}</td>
        <td>${escapeHtml(u.nombre_completo || '—')}</td>
        <td>${escapeHtml(u.email || '—')}</td>
        <td>${perfilBadge(u.perfil)}</td>
        <td>${estadoBadge(u.is_active)}</td>
        <td class="flex gap-1">
          <button class="btn btn-outline btn-sm" data-id="${u.id}" data-action="editar">Editar</button>
          ${toggle}
        </td>
      </tr>`;
  }).join('');
}

function attachEventos(container, lista, yo, refrescar) {
  container.querySelectorAll('[data-action="editar"]').forEach(btn => {
    btn.onclick = () => {
      const u = lista.find(x => String(x.id) === btn.dataset.id);
      formularioUsuario(u, refrescar);
    };
  });
  container.querySelectorAll('[data-action="desactivar"]').forEach(btn => {
    btn.onclick = async () => {
      const ok = await confirmDialog({
        title: 'Desactivar usuario',
        message: 'El usuario no podrá iniciar sesión hasta reactivarlo. ¿Continuar?',
        confirmText: 'Desactivar',
        confirmClass: 'btn-danger',
      });
      if (!ok) return;
      try {
        await api.usuarios.update(btn.dataset.id, { is_active: false });
        toast('Usuario desactivado', 'success');
        refrescar();
      } catch (err) { toast(err.message, 'error'); }
    };
  });
  container.querySelectorAll('[data-action="activar"]').forEach(btn => {
    btn.onclick = async () => {
      try {
        await api.usuarios.update(btn.dataset.id, { is_active: true });
        toast('Usuario activado', 'success');
        refrescar();
      } catch (err) { toast(err.message, 'error'); }
    };
  });
}

// Crear (usuario=null) o editar un usuario.
function formularioUsuario(usuario, onSuccess) {
  const editar = !!usuario;
  showModal({
    title: editar ? `Editar usuario: ${usuario.username}` : 'Nuevo usuario',
    body: `
      ${editar ? '' : `
        <div class="form-group"><label for="u-username">Usuario*</label>
          <input class="form-control" id="u-username" autocomplete="off" placeholder="Ej: jperez" /></div>`}
      <div class="form-group"><label for="u-nombre">Nombre completo</label>
        <input class="form-control" id="u-nombre" value="${escapeHtml(usuario?.nombre_completo || '')}" /></div>
      <div class="form-group"><label for="u-email">Email</label>
        <input class="form-control" id="u-email" type="email" value="${escapeHtml(usuario?.email || '')}" /></div>
      <div class="form-group"><label for="u-perfil">Perfil*</label>
        <select class="form-control" id="u-perfil">${opcionesPerfil(usuario?.perfil || 'RECEPCION')}</select>
        <p class="text-muted" id="u-perfil-ayuda" style="font-size:.82rem;margin:4px 0 0">—</p>
      </div>
      <div class="form-group"><label for="u-password">${editar ? 'Nueva contraseña (opcional)' : 'Contraseña*'}</label>
        <input class="form-control" id="u-password" type="password" autocomplete="new-password" placeholder="${editar ? 'Dejar vacío para no cambiarla' : 'Mínimo 6 caracteres'}" /></div>`,
    confirmText: editar ? 'Guardar' : 'Crear usuario',
    onConfirm: async (overlay) => {
      const perfil = overlay.querySelector('#u-perfil').value;
      const nombre = overlay.querySelector('#u-nombre').value.trim();
      const email = overlay.querySelector('#u-email').value.trim();
      const password = overlay.querySelector('#u-password').value;

      try {
        if (editar) {
          const body = {
            perfil,
            nombre_completo: nombre || null,
            email: email || null,
          };
          if (password) body.password = password;
          await api.usuarios.update(usuario.id, body);
          // Si me edité a mí mismo, refrescar el perfil cacheado.
          clearUserCache();
          toast('Usuario actualizado', 'success');
        } else {
          const username = overlay.querySelector('#u-username').value.trim();
          if (!username || username.length < 3) {
            toast('El usuario debe tener al menos 3 caracteres', 'error');
            return false;
          }
          if (!password || password.length < 6) {
            toast('La contraseña debe tener al menos 6 caracteres', 'error');
            return false;
          }
          await api.usuarios.create({
            username,
            password,
            perfil,
            nombre_completo: nombre || null,
            email: email || null,
          });
          toast('Usuario creado', 'success');
        }
        if (onSuccess) onSuccess();
      } catch (err) { toast(err.message, 'error'); return false; }
    }
  });

  // Pista del perfil seleccionado, en vivo.
  const sel = document.querySelector('.modal-overlay #u-perfil');
  const ayuda = document.querySelector('.modal-overlay #u-perfil-ayuda');
  if (sel && ayuda) {
    const pintar = () => { ayuda.textContent = PERFIL_AYUDA[sel.value] || ''; };
    sel.addEventListener('change', pintar);
    pintar();
  }
}
