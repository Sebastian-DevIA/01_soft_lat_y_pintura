import { api } from '../api.js';
import { toast, renderLoader, renderError, showModal } from '../utils.js';

const ROLES = ['LATONERO', 'PINTOR', 'PULIDOR', 'AUXILIAR', 'JEFE_TALLER', 'RECEPCIONISTA'];

export const personal = {
  title: 'Personal',
  async render(container) {
    container.innerHTML = renderLoader();
    try {
      const data = await api.personal.list();
      container.innerHTML = `
        <div class="flex justify-between align-center mb-2">
          <h2>Equipo del Taller</h2>
          <button class="btn btn-primary" id="btn-nuevo">+ Nuevo Empleado</button>
        </div>
        <div class="card">
          <div class="table-wrapper">
            <table class="data-table">
              <thead><tr><th>Nombre</th><th>Rol</th><th>Teléfono</th><th>Estado</th><th>Acciones</th></tr></thead>
              <tbody>
                ${data.map(p => `
                  <tr>
                    <td><strong>${p.nombre} ${p.apellido}</strong></td>
                    <td>${p.rol}</td>
                    <td>${p.telefono || '—'}</td>
                    <td><span class="badge ${p.activo ? 'badge-EN_PROCESO' : 'badge-CANCELADO'}">${p.activo ? 'Activo' : 'Inactivo'}</span></td>
                    <td>
                      <button class="btn btn-outline btn-sm" data-id="${p.id}" data-action="toggle">
                        ${p.activo ? 'Desactivar' : 'Activar'}
                      </button>
                    </td>
                  </tr>`).join('') || '<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--color-muted)">Sin personal registrado</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>`;

      container.querySelector('#btn-nuevo').onclick = () => mostrarFormulario(container);
      container.querySelectorAll('[data-action="toggle"]').forEach(btn => {
        btn.onclick = async () => {
          try {
            await api.personal.toggle(btn.dataset.id);
            toast('Estado actualizado', 'success');
            personal.render(container);
          } catch (err) { toast(err.message, 'error'); }
        };
      });
    } catch (err) {
      container.innerHTML = renderError(err.message);
    }
  }
};

function mostrarFormulario(container) {
  showModal({
    title: 'Nuevo Empleado',
    body: `
      <div class="form-group"><label>Nombre*</label><input class="form-control" id="f-nombre" /></div>
      <div class="form-group"><label>Apellido*</label><input class="form-control" id="f-apellido" /></div>
      <div class="form-group"><label>Rol*</label>
        <select class="form-control" id="f-rol">${ROLES.map(r => `<option>${r}</option>`).join('')}</select>
      </div>
      <div class="form-group"><label>Teléfono</label><input class="form-control" id="f-tel" /></div>`,
    confirmText: 'Guardar',
    onConfirm: async (overlay) => {
      const payload = {
        nombre:   overlay.querySelector('#f-nombre').value.trim(),
        apellido: overlay.querySelector('#f-apellido').value.trim(),
        rol:      overlay.querySelector('#f-rol').value,
        telefono: overlay.querySelector('#f-tel').value.trim() || null,
      };
      try {
        await api.personal.create(payload);
        toast('Empleado registrado', 'success');
        personal.render(container);
      } catch (err) { toast(err.message, 'error'); }
    }
  });
}
