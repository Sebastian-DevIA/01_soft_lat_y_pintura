import { api } from '../api.js';
import { toast, renderLoader, renderError, showModal } from '../utils.js';

export const clientes = {
  title: 'Clientes',
  async render(container) {
    container.innerHTML = renderLoader();
    try {
      const data = await api.clientes.list();
      container.innerHTML = `
        <div class="flex justify-between align-center mb-2">
          <h2>Clientes</h2>
          <button class="btn btn-primary" id="btn-nuevo-cliente">+ Nuevo Cliente</button>
        </div>
        <div class="search-bar">
          <input class="form-control" id="busqueda" placeholder="Buscar por nombre o cédula..." />
        </div>
        <div class="card">
          <div class="table-wrapper">
            <table class="data-table">
              <thead><tr><th>Nombre</th><th>Cédula/RUC</th><th>Teléfono</th><th>Estado</th><th>Acciones</th></tr></thead>
              <tbody id="tabla-clientes">${renderFilas(data)}</tbody>
            </table>
          </div>
        </div>`;

      container.querySelector('#btn-nuevo-cliente').onclick = () => mostrarFormulario(container, null);
      container.querySelector('#busqueda').oninput = async (e) => {
        const q = e.target.value.trim();
        const res = await api.clientes.list(q ? `?busqueda=${q}` : '');
        container.querySelector('#tabla-clientes').innerHTML = renderFilas(res);
        attachRowEvents(container);
      };
      attachRowEvents(container);
    } catch (err) {
      container.innerHTML = renderError(err.message);
    }
  }
};

function renderFilas(lista) {
  if (!lista.length) return '<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--color-muted)">Sin clientes</td></tr>';
  return lista.map(c => `
    <tr>
      <td><strong>${c.nombre} ${c.apellido}</strong></td>
      <td>${c.cedula_ruc}</td>
      <td>${c.telefono}</td>
      <td><span class="badge ${c.activo ? 'badge-EN_PROCESO' : 'badge-CANCELADO'}">${c.activo ? 'Activo' : 'Inactivo'}</span></td>
      <td>
        <button class="btn btn-outline btn-sm" data-id="${c.id}" data-action="ver">Ver</button>
      </td>
    </tr>`).join('');
}

function attachRowEvents(container) {
  container.querySelectorAll('[data-action="ver"]').forEach(btn => {
    btn.onclick = () => location.hash = `#/clientes/${btn.dataset.id}`;
  });
}

function mostrarFormulario(container, cliente) {
  showModal({
    title: cliente ? 'Editar Cliente' : 'Nuevo Cliente',
    body: `
      <div class="form-group"><label>Nombre*</label><input class="form-control" id="f-nombre" value="${cliente?.nombre || ''}" /></div>
      <div class="form-group"><label>Apellido*</label><input class="form-control" id="f-apellido" value="${cliente?.apellido || ''}" /></div>
      <div class="form-group"><label>Cédula / RUC*</label><input class="form-control" id="f-cedula" value="${cliente?.cedula_ruc || ''}" /></div>
      <div class="form-group"><label>Teléfono*</label><input class="form-control" id="f-telefono" value="${cliente?.telefono || ''}" /></div>
      <div class="form-group"><label>Email</label><input class="form-control" id="f-email" value="${cliente?.email || ''}" /></div>
      <div class="form-group"><label>Dirección</label><input class="form-control" id="f-direccion" value="${cliente?.direccion || ''}" /></div>`,
    confirmText: 'Guardar',
    onConfirm: async (overlay) => {
      const payload = {
        nombre:      overlay.querySelector('#f-nombre').value.trim(),
        apellido:    overlay.querySelector('#f-apellido').value.trim(),
        cedula_ruc:  overlay.querySelector('#f-cedula').value.trim(),
        telefono:    overlay.querySelector('#f-telefono').value.trim(),
        email:       overlay.querySelector('#f-email').value.trim() || null,
        direccion:   overlay.querySelector('#f-direccion').value.trim() || null,
      };
      try {
        if (cliente) {
          await api.clientes.update(cliente.id, payload);
          toast('Cliente actualizado', 'success');
        } else {
          await api.clientes.create(payload);
          toast('Cliente creado', 'success');
        }
        clientes.render(container);
      } catch (err) {
        toast(err.message, 'error');
        return false;
      }
    }
  });
}
