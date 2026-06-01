import { api } from '../api.js';
import {
  toast, renderLoader, renderError, renderEmpty, showModal,
  confirmDialog, escapeHtml, formatDate,
} from '../utils.js';

// Estado del filtro de la lista (true = activos, false = inactivos)
let _verActivos = true;

export const clientes = {
  title: 'Clientes',
  async render(container, clienteId) {
    if (clienteId && /^\d+$/.test(clienteId)) {
      await renderDetalle(container, clienteId);
    } else {
      await renderLista(container);
    }
  }
};

// ── Lista ──────────────────────────────────────────────────────────────────
async function renderLista(container) {
  container.innerHTML = renderLoader();
  try {
    const data = await api.clientes.list(`?activo=${_verActivos}`);
    container.innerHTML = `
      <div class="flex justify-between align-center mb-2">
        <h2>Clientes</h2>
        <button class="btn btn-primary" id="btn-nuevo-cliente">+ Nuevo Cliente</button>
      </div>
      <div class="toolbar mb-2">
        <div class="search-bar">
          <input class="form-control" id="busqueda" placeholder="Buscar por nombre o cédula..." />
        </div>
        <div class="segmented" role="tablist" aria-label="Filtrar por estado">
          <button class="seg-btn ${_verActivos ? 'active' : ''}" id="seg-activos" role="tab" aria-selected="${_verActivos}">Activos</button>
          <button class="seg-btn ${!_verActivos ? 'active' : ''}" id="seg-inactivos" role="tab" aria-selected="${!_verActivos}">Inactivos</button>
        </div>
      </div>
      <div class="card">
        <div class="table-wrapper">
          <table class="data-table">
            <thead><tr><th>Nombre</th><th>Cédula/RUC</th><th>Teléfono</th><th>Estado</th><th>Acciones</th></tr></thead>
            <tbody id="tabla-clientes">${renderFilas(data)}</tbody>
          </table>
        </div>
      </div>`;

    container.querySelector('#btn-nuevo-cliente').onclick = () =>
      _formularioCliente(null, () => renderLista(container));

    const recargar = async (q = '') => {
      const params = `?activo=${_verActivos}${q ? `&busqueda=${encodeURIComponent(q)}` : ''}`;
      const res = await api.clientes.list(params);
      container.querySelector('#tabla-clientes').innerHTML = renderFilas(res);
      attachRowEvents(container);
    };

    container.querySelector('#busqueda').oninput = (e) => recargar(e.target.value.trim());
    container.querySelector('#seg-activos').onclick = () => { _verActivos = true; renderLista(container); };
    container.querySelector('#seg-inactivos').onclick = () => { _verActivos = false; renderLista(container); };
    attachRowEvents(container);
  } catch (err) {
    container.innerHTML = renderError(err.message);
  }
}

function renderFilas(lista) {
  if (!lista.length) {
    const msg = _verActivos ? 'Sin clientes activos. Crea el primero.' : 'No hay clientes inactivos.';
    return `<tr><td colspan="5">${renderEmpty(msg, '👤')}</td></tr>`;
  }
  return lista.map(c => `
    <tr>
      <td><strong>${escapeHtml(c.nombre)} ${escapeHtml(c.apellido)}</strong></td>
      <td>${escapeHtml(c.cedula_ruc)}</td>
      <td>${escapeHtml(c.telefono)}</td>
      <td><span class="badge ${c.activo ? 'badge-EN_PROCESO' : 'badge-CANCELADO'}">${c.activo ? 'Activo' : 'Inactivo'}</span></td>
      <td class="flex gap-1">
        <button class="btn btn-outline btn-sm" data-id="${c.id}" data-action="ver">Ver</button>
        ${c.activo
          ? `<button class="btn btn-outline btn-sm" data-id="${c.id}" data-action="editar">Editar</button>
             <button class="btn btn-danger btn-sm" data-id="${c.id}" data-action="eliminar">Eliminar</button>`
          : `<button class="btn btn-success btn-sm" data-id="${c.id}" data-action="reactivar">Reactivar</button>`}
      </td>
    </tr>`).join('');
}

function attachRowEvents(container) {
  container.querySelectorAll('[data-action="ver"]').forEach(btn => {
    btn.onclick = () => location.hash = `#/clientes/${btn.dataset.id}`;
  });
  container.querySelectorAll('[data-action="editar"]').forEach(btn => {
    btn.onclick = async () => {
      try {
        const cliente = await api.clientes.get(btn.dataset.id);
        _formularioCliente(cliente, () => renderLista(container));
      } catch (err) { toast(err.message, 'error'); }
    };
  });
  container.querySelectorAll('[data-action="eliminar"]').forEach(btn => {
    btn.onclick = async () => {
      const ok = await confirmDialog({
        title: 'Eliminar cliente',
        message: 'El cliente se marcará como inactivo (no se borra su historial). Podrás reactivarlo después. ¿Continuar?',
        confirmText: 'Sí, eliminar',
      });
      if (!ok) return;
      try {
        await api.clientes.delete(btn.dataset.id);
        toast('Cliente desactivado', 'success');
        renderLista(container);
      } catch (err) { toast(err.message, 'error'); }
    };
  });
  container.querySelectorAll('[data-action="reactivar"]').forEach(btn => {
    btn.onclick = async () => {
      try {
        await api.clientes.activar(btn.dataset.id);
        toast('Cliente reactivado', 'success');
        renderLista(container);
      } catch (err) { toast(err.message, 'error'); }
    };
  });
}

// Formulario unificado crear/editar cliente. `cliente` null = crear.
function _formularioCliente(cliente, onSuccess) {
  showModal({
    title: cliente ? 'Editar Cliente' : 'Nuevo Cliente',
    body: `
      <div class="form-group"><label>Nombre*</label><input class="form-control" id="f-nombre" value="${escapeHtml(cliente?.nombre || '')}" /></div>
      <div class="form-group"><label>Apellido*</label><input class="form-control" id="f-apellido" value="${escapeHtml(cliente?.apellido || '')}" /></div>
      <div class="form-group"><label>Cédula / RUC*</label><input class="form-control" id="f-cedula" value="${escapeHtml(cliente?.cedula_ruc || '')}" /></div>
      <div class="form-group"><label>Teléfono*</label><input class="form-control" id="f-telefono" value="${escapeHtml(cliente?.telefono || '')}" /></div>
      <div class="form-group"><label>Email</label><input class="form-control" id="f-email" type="email" value="${escapeHtml(cliente?.email || '')}" /></div>
      <div class="form-group"><label>Dirección</label><input class="form-control" id="f-direccion" value="${escapeHtml(cliente?.direccion || '')}" /></div>`,
    confirmText: 'Guardar',
    onConfirm: async (overlay) => {
      const payload = {
        nombre:     overlay.querySelector('#f-nombre').value.trim(),
        apellido:   overlay.querySelector('#f-apellido').value.trim(),
        cedula_ruc: overlay.querySelector('#f-cedula').value.trim(),
        telefono:   overlay.querySelector('#f-telefono').value.trim(),
        email:      overlay.querySelector('#f-email').value.trim() || null,
        direccion:  overlay.querySelector('#f-direccion').value.trim() || null,
      };
      if (!payload.nombre || !payload.apellido || !payload.cedula_ruc || !payload.telefono) {
        toast('Nombre, apellido, cédula y teléfono son obligatorios', 'error');
        return false;
      }
      try {
        if (cliente) {
          await api.clientes.update(cliente.id, payload);
          toast('Cliente actualizado', 'success');
        } else {
          await api.clientes.create(payload);
          toast('Cliente creado', 'success');
        }
        if (onSuccess) onSuccess();
      } catch (err) {
        toast(err.message, 'error');
        return false;
      }
    }
  });
}

// ── Detalle (ficha + vehículos) ─────────────────────────────────────────────
async function renderDetalle(container, clienteId) {
  container.innerHTML = renderLoader();
  try {
    const cliente = await api.clientes.get(clienteId);
    const vehiculos = await api.vehiculos.list(`?cliente_id=${clienteId}`).catch(() => []);

    container.innerHTML = `
      <div class="flex justify-between align-center mb-2">
        <div class="flex align-center gap-2">
          <a class="btn btn-outline btn-sm" href="#/clientes">← Volver</a>
          <h2>${escapeHtml(cliente.nombre)} ${escapeHtml(cliente.apellido)}</h2>
          <span class="badge ${cliente.activo ? 'badge-EN_PROCESO' : 'badge-CANCELADO'}">${cliente.activo ? 'Activo' : 'Inactivo'}</span>
        </div>
        <button class="btn btn-outline btn-sm" id="btn-editar-cliente">Editar cliente</button>
      </div>

      <div class="card mb-2">
        <h3 class="mb-2">Ficha del cliente</h3>
        <div class="totales-box">
          <div class="total-row"><span>Cédula / RUC</span><span>${escapeHtml(cliente.cedula_ruc)}</span></div>
          <div class="total-row"><span>Teléfono</span><span>${escapeHtml(cliente.telefono)}</span></div>
          <div class="total-row"><span>Email</span><span>${escapeHtml(cliente.email || '—')}</span></div>
          <div class="total-row"><span>Dirección</span><span>${escapeHtml(cliente.direccion || '—')}</span></div>
          <div class="total-row"><span>Registrado</span><span>${formatDate(cliente.created_at)}</span></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3>Vehículos</h3>
          <button class="btn btn-primary btn-sm" id="btn-nuevo-vehiculo">+ Nuevo vehículo</button>
        </div>
        <div id="tabla-vehiculos">${renderTablaVehiculos(vehiculos)}</div>
      </div>`;

    container.querySelector('#btn-editar-cliente').onclick = () =>
      _formularioCliente(cliente, () => renderDetalle(container, clienteId));
    container.querySelector('#btn-nuevo-vehiculo').onclick = () => mostrarFormularioVehiculo(container, clienteId, null);
    attachVehiculoEvents(container, clienteId, vehiculos);
  } catch (err) {
    container.innerHTML = renderError(err.message);
  }
}

function renderTablaVehiculos(lista) {
  if (!lista.length) return renderEmpty('Este cliente aún no tiene vehículos registrados.', '🚗');
  return `
    <div class="table-wrapper">
      <table class="data-table">
        <thead><tr><th>Placa</th><th>Marca / Modelo</th><th>Año</th><th>Color</th><th>Km</th><th>Acciones</th></tr></thead>
        <tbody>
          ${lista.map(v => `
            <tr>
              <td><strong>${escapeHtml(v.placa)}</strong></td>
              <td>${escapeHtml(v.marca)} ${escapeHtml(v.modelo)}</td>
              <td>${escapeHtml(v.anio ?? '—')}</td>
              <td>${escapeHtml(v.color || '—')}</td>
              <td>${escapeHtml(v.kilometraje ?? '—')}</td>
              <td class="flex gap-1">
                <button class="btn btn-outline btn-sm btn-edit-veh" data-id="${v.id}">Editar</button>
                <button class="btn btn-danger btn-sm btn-del-veh" data-id="${v.id}">Eliminar</button>
              </td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
}

function attachVehiculoEvents(container, clienteId, vehiculos) {
  container.querySelectorAll('.btn-edit-veh').forEach(btn => {
    btn.onclick = () => {
      const v = vehiculos.find(x => String(x.id) === btn.dataset.id);
      mostrarFormularioVehiculo(container, clienteId, v);
    };
  });
  container.querySelectorAll('.btn-del-veh').forEach(btn => {
    btn.onclick = async () => {
      const ok = await confirmDialog({
        title: 'Eliminar vehículo',
        message: '¿Eliminar este vehículo? Esta acción lo marcará como inactivo.',
        confirmText: 'Sí, eliminar',
      });
      if (!ok) return;
      try {
        await api.vehiculos.delete(btn.dataset.id);
        toast('Vehículo eliminado', 'success');
        renderDetalle(container, clienteId);
      } catch (err) { toast(err.message, 'error'); }
    };
  });
}

// Crear/editar vehículo asociado al cliente
function mostrarFormularioVehiculo(container, clienteId, vehiculo) {
  showModal({
    title: vehiculo ? 'Editar Vehículo' : 'Nuevo Vehículo',
    body: `
      <div class="form-group"><label>Placa*</label><input class="form-control" id="v-placa" value="${escapeHtml(vehiculo?.placa || '')}" /></div>
      <div class="form-group"><label>Marca*</label><input class="form-control" id="v-marca" value="${escapeHtml(vehiculo?.marca || '')}" /></div>
      <div class="form-group"><label>Modelo*</label><input class="form-control" id="v-modelo" value="${escapeHtml(vehiculo?.modelo || '')}" /></div>
      <div class="form-group"><label>Año</label><input class="form-control" id="v-anio" type="number" min="1900" max="2100" value="${escapeHtml(vehiculo?.anio ?? '')}" /></div>
      <div class="form-group"><label>Color</label><input class="form-control" id="v-color" value="${escapeHtml(vehiculo?.color || '')}" /></div>
      <div class="form-group"><label>VIN</label><input class="form-control" id="v-vin" value="${escapeHtml(vehiculo?.vin || '')}" /></div>
      <div class="form-group"><label>Kilometraje</label><input class="form-control" id="v-km" type="number" min="0" value="${escapeHtml(vehiculo?.kilometraje ?? '')}" /></div>`,
    confirmText: 'Guardar',
    onConfirm: async (overlay) => {
      const anio = overlay.querySelector('#v-anio').value.trim();
      const km = overlay.querySelector('#v-km').value.trim();
      const payload = {
        cliente_id:  parseInt(clienteId, 10),
        placa:       overlay.querySelector('#v-placa').value.trim(),
        marca:       overlay.querySelector('#v-marca').value.trim(),
        modelo:      overlay.querySelector('#v-modelo').value.trim(),
        anio:        anio ? parseInt(anio, 10) : null,
        color:       overlay.querySelector('#v-color').value.trim() || null,
        vin:         overlay.querySelector('#v-vin').value.trim() || null,
        kilometraje: km ? parseInt(km, 10) : null,
      };
      if (!payload.placa || !payload.marca || !payload.modelo) {
        toast('Placa, marca y modelo son obligatorios', 'error');
        return false;
      }
      try {
        if (vehiculo) {
          await api.vehiculos.update(vehiculo.id, payload);
          toast('Vehículo actualizado', 'success');
        } else {
          await api.vehiculos.create(payload);
          toast('Vehículo registrado', 'success');
        }
        renderDetalle(container, clienteId);
      } catch (err) { toast(err.message, 'error'); return false; }
    }
  });
}
