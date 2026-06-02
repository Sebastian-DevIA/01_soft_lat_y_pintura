import { api } from '../api.js';
import { formatCurrency, formatDate, stateBadge, toast, renderLoader, renderError, renderEmpty, showModal, confirmDialog, showPdfViewer, escapeHtml } from '../utils.js';
import { createCarDiagram } from '../components/CarDiagram.js';

// State machine (debe reflejar TRANSICIONES_VALIDAS del backend)
const TRANSICIONES_VALIDAS = {
  PERITAJE:   ['COTIZACION', 'CANCELADO'],
  COTIZACION: ['APROBACION', 'CANCELADO'],
  APROBACION: ['EN_PROCESO', 'CANCELADO'],
  EN_PROCESO: ['ENTREGADO', 'CANCELADO'],
  ENTREGADO:  [],
  CANCELADO:  [],
};

// El vehículo solo puede reasignarse mientras la orden está en peritaje o cotización.
const ESTADOS_REASIGNA_VEHICULO = ['PERITAJE', 'COTIZACION'];
// Estados terminales: el backend bloquea cualquier edición (409).
const ESTADOS_NO_EDITABLES = ['CANCELADO', 'ENTREGADO'];

// Estado de los filtros de la lista (módulo).
let _verActivas = true;      // true = órdenes activas, false = inactivas (historial)
let _filtroEstado = '';      // '' = todos los estados

// Etiqueta legible del vehículo a partir de campos enriquecidos (con fallback seguro).
function vehiculoLabel(o) {
  const placa = o.vehiculo_placa ? String(o.vehiculo_placa).trim() : '';
  const desc = o.vehiculo_descripcion ? String(o.vehiculo_descripcion).trim() : '';
  const principal = placa || desc;
  if (!principal) return `Vehículo #${o.vehiculo_id}`;
  return placa && desc ? `${placa} — ${desc}` : principal;
}

export const ordenes = {
  title: 'Órdenes de Trabajo',
  async render(container, ordenId) {
    if (ordenId === 'nueva') {
      await renderNueva(container);
    } else if (ordenId) {
      await renderDetalle(container, ordenId);
    } else {
      await renderLista(container);
    }
  }
};

// Construye el query string a partir de los filtros de módulo (activo + estado).
function _queryListado() {
  const params = new URLSearchParams();
  params.set('activo', String(_verActivas));
  if (_filtroEstado) params.set('estado', _filtroEstado);
  return `?${params.toString()}`;
}

async function renderLista(container) {
  container.innerHTML = renderLoader();
  try {
    const data = await api.ordenes.list(_queryListado());
    const opciones = ['PERITAJE', 'COTIZACION', 'APROBACION', 'EN_PROCESO', 'ENTREGADO', 'CANCELADO']
      .map(e => `<option value="${e}" ${_filtroEstado === e ? 'selected' : ''}>${e.replace('_', ' ')}</option>`)
      .join('');
    container.innerHTML = `
      <div class="flex justify-between align-center mb-2">
        <h2>Órdenes de Trabajo</h2>
        <a class="btn btn-primary" href="#/ordenes/nueva">+ Nueva Orden</a>
      </div>
      <div class="toolbar mb-2">
        <div class="search-bar">
          <select class="form-control" id="filtro-estado" style="max-width:220px" aria-label="Filtrar por estado">
            <option value="">Todos los estados</option>
            ${opciones}
          </select>
        </div>
        <div class="segmented" role="tablist" aria-label="Filtrar por actividad">
          <button class="seg-btn ${_verActivas ? 'active' : ''}" id="seg-activas" role="tab" aria-selected="${_verActivas}">Activas</button>
          <button class="seg-btn ${!_verActivas ? 'active' : ''}" id="seg-inactivas" role="tab" aria-selected="${!_verActivas}">Inactivas</button>
        </div>
      </div>
      <div class="card">
        <div class="table-wrapper">
          <table class="data-table">
            <thead><tr><th>ID</th><th>Vehículo</th><th>Cliente</th><th>Estado</th><th class="text-right">Total</th><th>Ingreso</th><th>Acciones</th></tr></thead>
            <tbody id="tbody-ordenes">${renderFilasOrdenes(data)}</tbody>
          </table>
        </div>
      </div>`;

    container.querySelector('#filtro-estado').onchange = (e) => {
      _filtroEstado = e.target.value;
      renderLista(container);
    };
    container.querySelector('#seg-activas').onclick = () => { _verActivas = true; renderLista(container); };
    container.querySelector('#seg-inactivas').onclick = () => { _verActivas = false; renderLista(container); };
    attachRowEvents(container);
  } catch (err) {
    container.innerHTML = renderError(err.message);
  }
}

function renderFilasOrdenes(lista) {
  if (!lista.length) {
    const msg = _verActivas
      ? (_filtroEstado ? `Sin órdenes activas en estado ${_filtroEstado.replace('_', ' ')}.` : 'Sin órdenes activas. Crea la primera.')
      : 'No hay órdenes inactivas en el historial.';
    return `<tr><td colspan="7">${renderEmpty(msg, '🧾')}</td></tr>`;
  }
  return lista.map(o => {
    const editable = !ESTADOS_NO_EDITABLES.includes(o.estado);
    const acciones = [
      `<a class="btn btn-outline btn-sm" href="#/ordenes/${o.id}">Ver</a>`,
      editable
        ? `<button class="btn btn-outline btn-sm" data-id="${o.id}" data-action="editar" aria-label="Editar orden #${o.id}">Editar</button>`
        : `<button class="btn btn-outline btn-sm" disabled title="Las órdenes ${o.estado.toLowerCase()} no se pueden editar" aria-label="Edición no disponible">Editar</button>`,
      _verActivas
        ? `<button class="btn btn-danger btn-sm" data-id="${o.id}" data-action="eliminar" aria-label="Eliminar orden #${o.id}">Eliminar</button>`
        : `<button class="btn btn-success btn-sm" data-id="${o.id}" data-action="reactivar" aria-label="Reactivar orden #${o.id}">Reactivar</button>`,
    ].join('');
    return `
    <tr>
      <td><strong>#${o.id}</strong></td>
      <td>${escapeHtml(vehiculoLabel(o))}</td>
      <td>${escapeHtml(o.cliente_nombre || '—')}</td>
      <td>${stateBadge(o.estado)}</td>
      <td class="text-right">${formatCurrency(o.total_con_descuento)}</td>
      <td>${formatDate(o.fecha_ingreso)}</td>
      <td class="flex gap-1">${acciones}</td>
    </tr>`;
  }).join('');
}

function attachRowEvents(container) {
  container.querySelectorAll('[data-action="editar"]').forEach(btn => {
    btn.onclick = async () => {
      try {
        const orden = await api.ordenes.get(btn.dataset.id);
        _formularioEditarOrden(orden, () => renderLista(container));
      } catch (err) { toast(err.message, 'error'); }
    };
  });
  container.querySelectorAll('[data-action="eliminar"]').forEach(btn => {
    btn.onclick = async () => {
      const ok = await confirmDialog({
        title: 'Eliminar orden',
        message: `La orden #${btn.dataset.id} saldrá del historial activo (no se borra: se conserva y puedes reactivarla luego). ¿Continuar?`,
        confirmText: 'Eliminar',
        confirmClass: 'btn-danger',
      });
      if (!ok) return;
      try {
        await api.ordenes.eliminar(btn.dataset.id);
        toast('Orden archivada', 'success');
        renderLista(container);
      } catch (err) { toast(err.message, 'error'); }
    };
  });
  container.querySelectorAll('[data-action="reactivar"]').forEach(btn => {
    btn.onclick = async () => {
      try {
        await api.ordenes.activar(btn.dataset.id);
        toast('Orden reactivada', 'success');
        renderLista(container);
      } catch (err) { toast(err.message, 'error'); }
    };
  });
}

// Convierte un ISO (o null) al formato que espera <input type="datetime-local"> (YYYY-MM-DDTHH:mm).
function _isoADatetimeLocal(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// Formulario de edición de la orden (observaciones, fecha estimada, vehículo).
// Envío PARCIAL: solo se mandan los campos editados/permitidos por el estado.
function _formularioEditarOrden(orden, onSuccess) {
  const puedeReasignar = ESTADOS_REASIGNA_VEHICULO.includes(orden.estado);
  const overlay = showModal({
    title: `Editar Orden #${orden.id}`,
    body: `
      <div class="form-group">
        <label for="o-obs">Observaciones</label>
        <textarea class="form-control" id="o-obs" rows="3" placeholder="Notas del peritaje, daños, comentarios...">${escapeHtml(orden.observaciones || '')}</textarea>
      </div>
      <div class="form-group">
        <label for="o-fecha">Fecha estimada de entrega</label>
        <input class="form-control" id="o-fecha" type="datetime-local" value="${escapeHtml(_isoADatetimeLocal(orden.fecha_estimada_entrega))}" />
      </div>
      <div class="form-group">
        <label for="o-vehiculo">Vehículo</label>
        <select class="form-control" id="o-vehiculo" ${puedeReasignar ? '' : 'disabled'} aria-describedby="${puedeReasignar ? '' : 'o-vehiculo-nota'}">
          <option value="${orden.vehiculo_id}">${escapeHtml(vehiculoLabel(orden))}</option>
        </select>
        ${puedeReasignar
          ? ''
          : `<p class="form-error" id="o-vehiculo-nota" style="color:var(--color-muted)">El vehículo solo se reasigna en peritaje/cotización.</p>`}
      </div>`,
    confirmText: 'Guardar',
    onConfirm: async (ov) => {
      const obs = ov.querySelector('#o-obs').value.trim();
      const fechaLocal = ov.querySelector('#o-fecha').value;
      const body = { observaciones: obs || null };

      if (fechaLocal) {
        const d = new Date(fechaLocal);
        if (Number.isNaN(d.getTime())) {
          toast('La fecha estimada de entrega no es válida', 'error');
          return false;
        }
        // datetime-local no lleva zona: enviar ISO local sin sufijo Z (igual al ejemplo del backend).
        body.fecha_estimada_entrega = `${fechaLocal}:00`;
      } else {
        body.fecha_estimada_entrega = null;
      }

      // vehiculo_id solo si el estado permite reasignación (evita el 409 del backend).
      if (puedeReasignar) {
        const sel = ov.querySelector('#o-vehiculo');
        const nuevoId = parseInt(sel.value, 10);
        if (Number.isInteger(nuevoId) && nuevoId !== orden.vehiculo_id) {
          body.vehiculo_id = nuevoId;
        }
      }

      try {
        await api.ordenes.update(orden.id, body);
        toast('Orden actualizada', 'success');
        if (onSuccess) onSuccess();
      } catch (err) {
        toast(err.message, 'error');
        return false;
      }
    }
  });

  // Poblar el select de vehículos solo cuando se puede reasignar (lista de activos).
  if (puedeReasignar) {
    const sel = overlay.querySelector('#o-vehiculo');
    api.vehiculos.list('?activo=true').then((vehiculos) => {
      if (!sel) return;
      const opts = vehiculos.map(v => {
        const label = `${v.placa} — ${v.marca} ${v.modelo}`;
        const selected = v.id === orden.vehiculo_id ? 'selected' : '';
        return `<option value="${v.id}" ${selected}>${escapeHtml(label)}</option>`;
      }).join('');
      // Si el vehículo actual no está en la lista de activos, conservarlo como primera opción.
      const actualPresente = vehiculos.some(v => v.id === orden.vehiculo_id);
      sel.innerHTML = (actualPresente ? '' : `<option value="${orden.vehiculo_id}" selected>${escapeHtml(vehiculoLabel(orden))}</option>`) + opts;
    }).catch(() => {
      // Si falla la carga, se queda la opción actual (ya renderizada); avisar discretamente.
      toast('No se pudieron cargar los vehículos para reasignar', 'error');
    });
  }
}

// ── Asistente: Nueva Orden ─────────────────────────────────────────────────
async function renderNueva(container) {
  // estado del asistente
  const wiz = { cliente: null, vehiculo: null };
  container.innerHTML = `
    <div class="flex align-center gap-2 mb-2">
      <a class="btn btn-outline btn-sm" href="#/ordenes">← Volver</a>
      <h2>Nueva Orden</h2>
    </div>
    <div class="card">
      <div id="wiz-pasos" class="flex gap-2 mb-2" style="font-size:.85rem;color:var(--color-muted)">
        <span id="paso-lbl-1"><strong>1.</strong> Cliente</span>
        <span>›</span>
        <span id="paso-lbl-2"><strong>2.</strong> Vehículo</span>
        <span>›</span>
        <span id="paso-lbl-3"><strong>3.</strong> Orden</span>
      </div>
      <div id="wiz-body"></div>
    </div>`;
  const body = container.querySelector('#wiz-body');
  renderPasoCliente(container, body, wiz);
}

function marcarPaso(container, n) {
  for (let i = 1; i <= 3; i++) {
    const el = container.querySelector(`#paso-lbl-${i}`);
    if (el) el.style.color = i === n ? 'var(--color-primary)' : '';
  }
}

// Paso 1: seleccionar/crear cliente
function renderPasoCliente(container, body, wiz) {
  marcarPaso(container, 1);
  body.innerHTML = `
    <h3 class="mb-2">Paso 1 — Selecciona el cliente</h3>
    <div class="search-bar">
      <input class="form-control" id="wiz-busqueda" placeholder="Buscar por nombre o cédula..." />
      <button class="btn btn-outline" id="wiz-nuevo-cliente">+ Nuevo cliente</button>
    </div>
    <div class="table-wrapper">
      <table class="data-table">
        <thead><tr><th>Nombre</th><th>Cédula/RUC</th><th>Teléfono</th><th></th></tr></thead>
        <tbody id="wiz-tbody-clientes"><tr><td colspan="4">${renderLoader('Cargando clientes…')}</td></tr></tbody>
      </table>
    </div>`;

  const tbody = body.querySelector('#wiz-tbody-clientes');
  const pintar = (lista) => {
    if (!lista.length) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:24px;color:var(--color-muted)">Sin clientes. Crea uno nuevo.</td></tr>';
      return;
    }
    tbody.innerHTML = lista.map(c => `
      <tr>
        <td><strong>${escapeHtml(c.nombre)} ${escapeHtml(c.apellido)}</strong></td>
        <td>${escapeHtml(c.cedula_ruc)}</td>
        <td>${escapeHtml(c.telefono)}</td>
        <td><button class="btn btn-primary btn-sm wiz-sel-cliente" data-id="${c.id}">Seleccionar</button></td>
      </tr>`).join('');
    tbody.querySelectorAll('.wiz-sel-cliente').forEach(btn => {
      btn.onclick = () => {
        wiz.cliente = lista.find(c => String(c.id) === btn.dataset.id);
        renderPasoVehiculo(container, body, wiz);
      };
    });
  };

  api.clientes.list().then(pintar).catch(err => {
    tbody.innerHTML = `<tr><td colspan="4">${renderError(err.message)}</td></tr>`;
  });

  body.querySelector('#wiz-busqueda').oninput = async (e) => {
    const q = e.target.value.trim();
    try {
      const res = await api.clientes.list(q ? `?busqueda=${encodeURIComponent(q)}` : '');
      pintar(res);
    } catch (err) { toast(err.message, 'error'); }
  };

  body.querySelector('#wiz-nuevo-cliente').onclick = () => {
    showModal({
      title: 'Nuevo Cliente',
      body: `
        <div class="form-group"><label>Nombre*</label><input class="form-control" id="c-nombre" /></div>
        <div class="form-group"><label>Apellido*</label><input class="form-control" id="c-apellido" /></div>
        <div class="form-group"><label>Cédula / RUC*</label><input class="form-control" id="c-cedula" /></div>
        <div class="form-group"><label>Teléfono*</label><input class="form-control" id="c-telefono" /></div>
        <div class="form-group"><label>Email</label><input class="form-control" id="c-email" /></div>
        <div class="form-group"><label>Dirección</label><input class="form-control" id="c-direccion" /></div>`,
      confirmText: 'Crear y continuar',
      onConfirm: async (overlay) => {
        const payload = {
          nombre:     overlay.querySelector('#c-nombre').value.trim(),
          apellido:   overlay.querySelector('#c-apellido').value.trim(),
          cedula_ruc: overlay.querySelector('#c-cedula').value.trim(),
          telefono:   overlay.querySelector('#c-telefono').value.trim(),
          email:      overlay.querySelector('#c-email').value.trim() || null,
          direccion:  overlay.querySelector('#c-direccion').value.trim() || null,
        };
        if (!payload.nombre || !payload.apellido || !payload.cedula_ruc || !payload.telefono) {
          toast('Completa los campos obligatorios', 'error');
          return false;
        }
        try {
          wiz.cliente = await api.clientes.create(payload);
          toast('Cliente creado', 'success');
          renderPasoVehiculo(container, body, wiz);
        } catch (err) { toast(err.message, 'error'); return false; }
      }
    });
  };
}

// Paso 2: seleccionar/crear vehículo del cliente
function renderPasoVehiculo(container, body, wiz) {
  marcarPaso(container, 2);
  const c = wiz.cliente;
  body.innerHTML = `
    <div class="flex justify-between align-center mb-2">
      <h3>Paso 2 — Vehículo de ${escapeHtml(c.nombre)} ${escapeHtml(c.apellido)}</h3>
      <button class="btn btn-outline btn-sm" id="wiz-volver-cliente">← Cambiar cliente</button>
    </div>
    <div class="flex justify-end mb-2">
      <button class="btn btn-outline" id="wiz-nuevo-vehiculo">+ Nuevo vehículo</button>
    </div>
    <div class="table-wrapper">
      <table class="data-table">
        <thead><tr><th>Placa</th><th>Marca / Modelo</th><th>Año</th><th></th></tr></thead>
        <tbody id="wiz-tbody-vehiculos"><tr><td colspan="4">${renderLoader('Cargando vehículos…')}</td></tr></tbody>
      </table>
    </div>`;

  body.querySelector('#wiz-volver-cliente').onclick = () => renderPasoCliente(container, body, wiz);

  const tbody = body.querySelector('#wiz-tbody-vehiculos');
  const pintar = (lista) => {
    if (!lista.length) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:24px;color:var(--color-muted)">Este cliente no tiene vehículos. Registra uno.</td></tr>';
      return;
    }
    tbody.innerHTML = lista.map(v => `
      <tr>
        <td><strong>${escapeHtml(v.placa)}</strong></td>
        <td>${escapeHtml(v.marca)} ${escapeHtml(v.modelo)}</td>
        <td>${escapeHtml(v.anio ?? '—')}</td>
        <td><button class="btn btn-primary btn-sm wiz-sel-veh" data-id="${v.id}">Seleccionar</button></td>
      </tr>`).join('');
    tbody.querySelectorAll('.wiz-sel-veh').forEach(btn => {
      btn.onclick = () => {
        wiz.vehiculo = lista.find(v => String(v.id) === btn.dataset.id);
        renderPasoOrden(container, body, wiz);
      };
    });
  };

  api.vehiculos.list(`?cliente_id=${c.id}`).then(pintar).catch(err => {
    tbody.innerHTML = `<tr><td colspan="4">${renderError(err.message)}</td></tr>`;
  });

  body.querySelector('#wiz-nuevo-vehiculo').onclick = () => mostrarFormularioVehiculo(c.id, null, async (nuevo) => {
    wiz.vehiculo = nuevo;
    renderPasoOrden(container, body, wiz);
  });
}

// Paso 3: crear la orden
function renderPasoOrden(container, body, wiz) {
  marcarPaso(container, 3);
  const v = wiz.vehiculo;
  const c = wiz.cliente;
  body.innerHTML = `
    <div class="flex justify-between align-center mb-2">
      <h3>Paso 3 — Datos de la orden</h3>
      <button class="btn btn-outline btn-sm" id="wiz-volver-vehiculo">← Cambiar vehículo</button>
    </div>
    <div class="totales-box mb-2">
      <div class="total-row"><span>Cliente</span><span>${escapeHtml(c.nombre)} ${escapeHtml(c.apellido)}</span></div>
      <div class="total-row"><span>Vehículo</span><span>${escapeHtml(v.placa)} — ${escapeHtml(v.marca)} ${escapeHtml(v.modelo)}</span></div>
    </div>
    <div class="form-group"><label for="o-obs">Observaciones iniciales</label>
      <textarea class="form-control" id="o-obs" rows="3" placeholder="Estado de ingreso, daños visibles, notas del peritaje..."></textarea>
    </div>
    <div class="flex justify-end gap-2 mt-2">
      <button class="btn btn-primary" id="wiz-crear-orden">Crear orden</button>
    </div>`;

  body.querySelector('#wiz-volver-vehiculo').onclick = () => renderPasoVehiculo(container, body, wiz);

  body.querySelector('#wiz-crear-orden').onclick = async (e) => {
    const btn = e.currentTarget;
    btn.disabled = true;
    const payload = {
      vehiculo_id:   v.id,
      observaciones: body.querySelector('#o-obs').value.trim() || null,
    };
    try {
      const nueva = await api.ordenes.create(payload);
      toast('Orden creada', 'success');
      location.hash = `#/ordenes/${nueva.id}`;
    } catch (err) {
      toast(err.message, 'error');
      btn.disabled = false;
    }
  };
}

// Formulario de vehículo reutilizable (crear/editar). onDone recibe el vehículo resultante.
function mostrarFormularioVehiculo(clienteId, vehiculo, onDone) {
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
    confirmText: vehiculo ? 'Guardar' : 'Crear y continuar',
    onConfirm: async (overlay) => {
      const anio = overlay.querySelector('#v-anio').value.trim();
      const km = overlay.querySelector('#v-km').value.trim();
      const payload = {
        cliente_id:  clienteId,
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
        const res = vehiculo
          ? await api.vehiculos.update(vehiculo.id, payload)
          : await api.vehiculos.create(payload);
        toast(vehiculo ? 'Vehículo actualizado' : 'Vehículo registrado', 'success');
        if (onDone) await onDone(res);
      } catch (err) { toast(err.message, 'error'); return false; }
    }
  });
}

// ── Detalle de orden ───────────────────────────────────────────────────────
async function renderDetalle(container, ordenId) {
  container.innerHTML = renderLoader();
  try {
    const orden = await api.ordenes.get(ordenId);
    const fases = await api.fases.byOrden(ordenId).catch(() => []);

    const puedeCancelar = (TRANSICIONES_VALIDAS[orden.estado] || []).includes('CANCELADO');
    const subtitulo = orden.vehiculo_placa
      ? `<span class="text-muted">${escapeHtml(vehiculoLabel(orden))}${orden.cliente_nombre ? ' · ' + escapeHtml(orden.cliente_nombre) : ''}</span>`
      : '';

    container.innerHTML = `
      <div class="flex justify-between align-center mb-2">
        <div class="flex align-center gap-2">
          <a class="btn btn-outline btn-sm" href="#/ordenes">← Volver</a>
          <h2>Orden #${orden.id}</h2>
          ${stateBadge(orden.estado)}
        </div>
        ${puedeCancelar ? '<button class="btn btn-danger btn-sm" id="btn-cancelar-orden">Cancelar orden</button>' : ''}
      </div>
      ${subtitulo ? `<p class="mb-2">${subtitulo}</p>` : ''}
      <div class="tabs">
        <button class="tab-btn active" data-tab="peritaje">Peritaje</button>
        <button class="tab-btn" data-tab="cotizacion">Cotización</button>
        <button class="tab-btn" data-tab="factura">Factura</button>
        <button class="tab-btn" data-tab="fases">Seguimiento</button>
      </div>
      <div id="tab-peritaje" class="tab-panel active">${renderTabPeritaje(orden)}</div>
      <div id="tab-cotizacion" class="tab-panel">${renderTabCotizacion(orden)}</div>
      <div id="tab-factura" class="tab-panel"><div id="contenido-factura">${renderLoader()}</div></div>
      <div id="tab-fases" class="tab-panel">${renderTabFases(fases)}</div>`;

    // Tab switching
    container.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        container.querySelectorAll('.tab-btn, .tab-panel').forEach(el => el.classList.remove('active'));
        btn.classList.add('active');
        const panel = container.querySelector(`#tab-${btn.dataset.tab}`);
        if (panel) panel.classList.add('active');
        if (btn.dataset.tab === 'factura') await cargarFactura(container, ordenId);
      });
    });

    // Mapa de daños (diagrama solo-lectura) en la pestaña de peritaje
    const peritajeMount = container.querySelector('#peritaje-diagram-mount');
    if (peritajeMount) {
      peritajeMount.appendChild(createCarDiagram({
        readonly: true,
        damagedZones: orden.items.map(i => i.area_vehiculo),
      }));
    }

    // Cancelar orden
    container.querySelector('#btn-cancelar-orden')?.addEventListener('click', async () => {
      const ok = await confirmDialog({
        title: 'Cancelar orden',
        message: '¿Cancelar esta orden? Esta acción no se puede revertir.',
        confirmText: 'Sí, cancelar orden',
      });
      if (!ok) return;
      try {
        await api.ordenes.cambiarEstado(ordenId, 'CANCELADO');
        toast('Orden cancelada', 'success');
        renderDetalle(container, ordenId);
      } catch (err) { toast(err.message, 'error'); }
    });

    // Agregar ítem
    container.querySelector('#btn-agregar-item')?.addEventListener('click', () => {
      mostrarFormularioItem(container, ordenId, null);
    });

    // Editar ítems
    container.querySelectorAll('.btn-edit-item').forEach(btn => {
      btn.addEventListener('click', () => {
        const item = orden.items.find(i => String(i.id) === btn.dataset.id);
        mostrarFormularioItem(container, ordenId, item);
      });
    });

    // Aprobar orden
    container.querySelector('#btn-aprobar')?.addEventListener('click', async () => {
      const ok = await confirmDialog({
        title: 'Aprobar cotización',
        message: '¿Confirmar la aprobación del cliente? Se generará el adelanto del 50% y se crearán las fases de trabajo.',
        confirmText: 'Sí, aprobar',
        confirmClass: 'btn-success',
      });
      if (!ok) return;
      try {
        await api.ordenes.aprobar(ordenId);
        toast('Orden aprobada', 'success');
        renderDetalle(container, ordenId);
      } catch (err) { toast(err.message, 'error'); }
    });

    // Editar descuento
    container.querySelector('#btn-editar-descuento')?.addEventListener('click', () => {
      mostrarFormularioDescuento(container, ordenId, orden);
    });

    // Eliminar ítems
    container.querySelectorAll('.btn-delete-item').forEach(btn => {
      btn.addEventListener('click', async () => {
        const ok = await confirmDialog({
          title: 'Eliminar ítem',
          message: '¿Eliminar esta área dañada de la cotización?',
          confirmText: 'Sí, eliminar',
        });
        if (!ok) return;
        try {
          await api.ordenes.deleteItem(ordenId, btn.dataset.id);
          toast('Ítem eliminado', 'success');
          renderDetalle(container, ordenId);
        } catch (err) { toast(err.message, 'error'); }
      });
    });
  } catch (err) {
    container.innerHTML = renderError(err.message);
  }
}

// Panel lateral: lista legible de las zonas dañadas registradas en el peritaje.
function renderListaDanios(items) {
  if (!items.length) {
    return `<p class="text-muted" style="font-size:.85rem">Sin áreas dañadas registradas.</p>`;
  }
  return `<ul class="damage-list">${items.map(i => {
    const detalle = [
      i.descripcion ? escapeHtml(i.descripcion) : '',
      i.precio_unitario ? formatCurrency(i.precio_unitario) : '',
    ].filter(Boolean).join(' · ');
    return `
      <li class="damage-list-item">
        <span class="damage-dot" aria-hidden="true"></span>
        <div>
          <strong>${escapeHtml(i.area_vehiculo)}</strong>
          ${detalle ? `<span class="damage-detail">${detalle}</span>` : ''}
        </div>
      </li>`;
  }).join('')}</ul>`;
}

function renderTabPeritaje(orden) {
  const puedeEditar = ['PERITAJE', 'COTIZACION'].includes(orden.estado);
  return `
    <div class="card mb-2">
      <h3 class="mb-2">Mapa de daños del vehículo</h3>
      <p class="text-muted mb-2" style="font-size:.85rem">Las zonas marcadas en rojo tienen daño registrado en el peritaje.</p>
      <div class="damage-map-layout">
        <div id="peritaje-diagram-mount"></div>
        <div class="damage-map-side">
          <h4 class="damage-side-title">Áreas dañadas (${orden.items.length})</h4>
          ${renderListaDanios(orden.items)}
        </div>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <h3>Áreas Dañadas</h3>
        ${puedeEditar ? '<button class="btn btn-primary btn-sm" id="btn-agregar-item">+ Agregar área</button>' : ''}
      </div>
      <div class="table-wrapper">
        <table class="data-table">
          <thead><tr><th>Área</th><th>Descripción</th><th class="text-right">Cant.</th><th class="text-right">P. Unit.</th><th class="text-right">Subtotal</th>${puedeEditar ? '<th></th>' : ''}</tr></thead>
          <tbody>
            ${orden.items.length ? orden.items.map(i => `
              <tr>
                <td><strong>${escapeHtml(i.area_vehiculo)}</strong></td>
                <td>${escapeHtml(i.descripcion)}</td>
                <td class="text-right">${i.cantidad}</td>
                <td class="text-right">${formatCurrency(i.precio_unitario)}</td>
                <td class="text-right">${formatCurrency(i.subtotal)}</td>
                ${puedeEditar ? `<td class="flex gap-1">
                  <button class="btn btn-outline btn-sm btn-edit-item" data-id="${i.id}" aria-label="Editar ítem">✎</button>
                  <button class="btn btn-danger btn-sm btn-delete-item" data-id="${i.id}" aria-label="Eliminar ítem">✕</button>
                </td>` : ''}
              </tr>`).join('')
              : `<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--color-muted)">Sin ítems. Agregue las áreas a reparar.</td></tr>`}
          </tbody>
        </table>
      </div>
    </div>`;
}

function renderTabCotizacion(orden) {
  const puedeAprobar = orden.estado === 'COTIZACION' && orden.items.length > 0;
  const puedeEditarDescuento = ['PERITAJE', 'COTIZACION'].includes(orden.estado);
  return `
    <div class="card">
      <div class="card-header">
        <h3>Resumen de Cotización</h3>
        ${puedeEditarDescuento ? '<button class="btn btn-outline btn-sm" id="btn-editar-descuento">Editar descuento</button>' : ''}
      </div>
      <div class="totales-box">
        <div class="total-row"><span>Subtotal</span><span>${formatCurrency(orden.total_cotizado)}</span></div>
        <div class="total-row"><span>Descuento (${orden.descuento_porcentaje}%)</span><span>-${formatCurrency(orden.total_cotizado - orden.total_con_descuento)}</span></div>
        <div class="total-row total-final"><span>TOTAL</span><span>${formatCurrency(orden.total_con_descuento)}</span></div>
      </div>
      ${puedeAprobar ? `
        <div class="mt-2">
          <button class="btn btn-success" id="btn-aprobar">✓ Cliente aprueba — pasa a facturación</button>
        </div>` : ''}
      ${orden.aprobado_por_cliente ? `<p class="mt-1 text-muted">✓ Aprobado el ${formatDate(orden.fecha_aprobacion)}</p>` : ''}
    </div>`;
}

function renderTabFases(fases) {
  if (!fases.length) return '<div class="card"><p class="text-muted" style="padding:16px">Las fases se crean al aprobar la orden.</p></div>';
  const estadoColor = { PENDIENTE: 'badge-COTIZACION', EN_PROGRESO: 'badge-EN_PROCESO', COMPLETADA: 'badge-ENTREGADO' };
  return `<div class="card">
    <h3 class="mb-2">Fases de Trabajo</h3>
    ${fases.map(f => `
      <div style="margin-bottom:16px;padding:12px;border:1px solid var(--color-border);border-radius:var(--radius)">
        <div class="flex justify-between align-center">
          <strong>${escapeHtml(f.fase)}</strong>
          <span class="badge ${estadoColor[f.estado] || ''}">${escapeHtml(f.estado)}</span>
        </div>
        ${f.notas ? `<p class="text-muted mt-1" style="font-size:.85rem">${escapeHtml(f.notas)}</p>` : ''}
        <p class="text-muted mt-1" style="font-size:.78rem">Personal: ${f.asignaciones.length || 'Sin asignar'}</p>
      </div>`).join('')}
  </div>`;
}

async function cargarFactura(container, ordenId) {
  const div = container.querySelector('#contenido-factura');
  try {
    const orden = await api.ordenes.get(ordenId);
    if (!orden.factura && orden.estado === 'APROBACION') {
      div.innerHTML = `
        <div class="card">
          <h3 class="mb-2">Emitir Factura</h3>
          <p class="text-muted mb-2">La orden está aprobada. Emite la factura para registrar el adelanto del 50%.</p>
          <button class="btn btn-primary" id="btn-emitir-factura">Emitir Factura</button>
        </div>`;
      div.querySelector('#btn-emitir-factura').onclick = async () => {
        try {
          await api.facturas.create({ orden_id: parseInt(ordenId) });
          toast('Factura emitida', 'success');
          await cargarFactura(container, ordenId);
        } catch (err) { toast(err.message, 'error'); }
      };
    } else if (orden.factura) {
      const f = orden.factura;
      div.innerHTML = `
        <div class="card">
          <div class="card-header">
            <h3>Factura ${escapeHtml(f.numero_factura)}</h3>
            <span class="badge badge-${f.estado}">${escapeHtml(f.estado)}</span>
          </div>
          <div class="totales-box">
            <div class="total-row"><span>Total</span><span>${formatCurrency(f.monto_total)}</span></div>
            <div class="total-row"><span>Adelanto (50%)</span><span>${formatCurrency(f.monto_adelanto)}</span></div>
            <div class="total-row"><span>Saldo (50%)</span><span>${formatCurrency(f.monto_saldo)}</span></div>
            <div class="total-row"><span>Pagado</span><span>${formatCurrency(f.monto_pagado)}</span></div>
            <div class="total-row total-final"><span>Pendiente</span><span>${formatCurrency(f.monto_total - f.monto_pagado)}</span></div>
          </div>
          <div class="mt-2 flex gap-2 flex-wrap">
            <button class="btn btn-primary btn-sm" id="btn-ver-pdf">📄 Ver PDF</button>
            <button class="btn btn-outline btn-sm" id="btn-descargar-pdf">⬇️ Descargar</button>
            <button class="btn btn-outline btn-sm" id="btn-compartir">📲 Enviar al cliente</button>
            ${f.estado !== 'PAGADA' ? '<button class="btn btn-success btn-sm" id="btn-registrar-pago">Registrar Pago</button>' : ''}
          </div>
        </div>`;

      div.querySelector('#btn-ver-pdf').onclick = (e) => verPdfFactura(e.currentTarget, f);
      div.querySelector('#btn-descargar-pdf').onclick = (e) => descargarPdfFactura(e.currentTarget, f);
      div.querySelector('#btn-compartir').onclick = () => compartirFactura(orden, f);
      div.querySelector('#btn-registrar-pago')?.addEventListener('click', () => {
        mostrarFormularioPago(div, f, ordenId, container);
      });
    } else {
      div.innerHTML = '<div class="card"><p class="text-muted" style="padding:16px">La factura se emite después de que el cliente aprueba la cotización.</p></div>';
    }
  } catch (err) { div.innerHTML = renderError(err.message); }
}

// Crear/editar ítem de peritaje. Si `item` viene, es edición.
function mostrarFormularioItem(container, ordenId, item) {
  const overlay = showModal({
    title: item ? 'Editar Área Dañada' : 'Agregar Área Dañada',
    body: `
      <p class="text-muted mb-1" style="font-size:.85rem">Toca la zona dañada en el diagrama (o escríbela abajo).</p>
      <div id="item-diagram-mount" class="mb-2"></div>
      <div class="form-group"><label>Área del vehículo*</label><input class="form-control" id="f-area" value="${escapeHtml(item?.area_vehiculo || '')}" placeholder="Ej: Puerta trasera izquierda" /></div>
      <div class="form-group"><label>Descripción*</label><input class="form-control" id="f-desc" value="${escapeHtml(item?.descripcion || '')}" placeholder="Ej: Abolladuras profundas y rayones" /></div>
      <div class="form-group"><label>Precio unitario (COP)*</label><input class="form-control" id="f-precio" type="number" min="1" value="${escapeHtml(item?.precio_unitario ?? '')}" /></div>
      <div class="form-group"><label>Cantidad</label><input class="form-control" id="f-cant" type="number" value="${escapeHtml(item?.cantidad ?? 1)}" min="1" /></div>`,
    confirmText: item ? 'Guardar' : 'Agregar',
    onConfirm: async (overlay) => {
      const payload = {
        area_vehiculo:   overlay.querySelector('#f-area').value.trim(),
        descripcion:     overlay.querySelector('#f-desc').value.trim(),
        precio_unitario: parseFloat(overlay.querySelector('#f-precio').value),
        cantidad:        parseInt(overlay.querySelector('#f-cant').value),
      };
      if (!payload.area_vehiculo || !payload.descripcion || !(payload.precio_unitario > 0) || !(payload.cantidad >= 1)) {
        toast('Revisa los campos: área, descripción, precio > 0 y cantidad ≥ 1', 'error');
        return false;
      }
      try {
        if (item) {
          await api.ordenes.updateItem(ordenId, item.id, payload);
          toast('Ítem actualizado', 'success');
        } else {
          await api.ordenes.addItem(ordenId, payload);
          toast('Área agregada', 'success');
        }
        renderDetalle(container, ordenId);
      } catch (err) { toast(err.message, 'error'); return false; }
    }
  });

  // Diagrama interactivo: al elegir una zona, rellena el campo "Área del vehículo".
  const mount = overlay.querySelector('#item-diagram-mount');
  if (mount) {
    mount.appendChild(createCarDiagram({
      selected: item?.area_vehiculo || null,
      onZoneClick: (label) => {
        const input = overlay.querySelector('#f-area');
        if (input) input.value = label;
      },
    }));
  }
}

function mostrarFormularioDescuento(container, ordenId, orden) {
  showModal({
    title: 'Editar Descuento',
    body: `
      <p class="mb-2 text-muted">Se aplica sobre el subtotal de la cotización.</p>
      <div class="form-group"><label>Descuento (%)*</label>
        <input class="form-control" id="f-pct" type="number" min="0" max="100" step="0.1" value="${escapeHtml(orden.descuento_porcentaje ?? 0)}" />
      </div>`,
    confirmText: 'Aplicar',
    onConfirm: async (overlay) => {
      const pct = parseFloat(overlay.querySelector('#f-pct').value);
      if (!(pct >= 0 && pct <= 100)) {
        toast('El descuento debe estar entre 0 y 100', 'error');
        return false;
      }
      try {
        await api.ordenes.descuento(ordenId, pct);
        toast('Descuento aplicado', 'success');
        renderDetalle(container, ordenId);
      } catch (err) { toast(err.message, 'error'); return false; }
    }
  });
}

// Ver la factura en PDF dentro de un visor (fetch con JWT → Blob → objectURL).
async function verPdfFactura(btn, f) {
  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = 'Generando…';
  try {
    const blob = await api.facturas.pdfBlob(f.id);
    const url = URL.createObjectURL(blob);
    showPdfViewer({ url, title: `Factura ${f.numero_factura}`, filename: `${f.numero_factura}.pdf` });
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

// Descargar el PDF directamente (mismo fetch autenticado, sin abrir el visor).
async function descargarPdfFactura(btn, f) {
  btn.disabled = true;
  try {
    const blob = await api.facturas.pdfBlob(f.id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${f.numero_factura}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

// Enviar al cliente: comparte un resumen por WhatsApp (compatible, sin SMTP en el server).
function compartirFactura(orden, f) {
  const pendiente = f.monto_total - f.monto_pagado;
  const lineas = [
    `*Taller LatonPaint* — Factura ${f.numero_factura}`,
    orden.cliente_nombre ? `Cliente: ${orden.cliente_nombre}` : null,
    orden.vehiculo_placa ? `Vehículo: ${orden.vehiculo_placa} (${orden.vehiculo_descripcion || ''})`.trim() : null,
    `Total: ${formatCurrency(f.monto_total)}`,
    `Pagado: ${formatCurrency(f.monto_pagado)}`,
    `Saldo pendiente: ${formatCurrency(pendiente)}`,
    f.estado === 'PAGADA'
      ? '✅ Factura PAGADA. El vehículo puede ser entregado.'
      : 'El vehículo se entrega al cancelar el saldo pendiente.',
    'Gracias por confiar en nosotros.',
  ].filter(Boolean);
  const texto = encodeURIComponent(lineas.join('\n'));
  window.open(`https://wa.me/?text=${texto}`, '_blank', 'noopener');
}

function mostrarFormularioPago(div, factura, ordenId, container) {
  showModal({
    title: 'Registrar Pago',
    body: `
      <p class="mb-2 text-muted">Saldo pendiente: <strong>${formatCurrency(factura.monto_total - factura.monto_pagado)}</strong></p>
      <div class="form-group"><label>Monto*</label><input class="form-control" id="f-monto" type="number" step="0.01" min="1" /></div>
      <div class="form-group"><label>Tipo</label>
        <select class="form-control" id="f-tipo"><option>ADELANTO</option><option>SALDO</option><option>ABONO</option></select>
      </div>
      <div class="form-group"><label>Método</label>
        <select class="form-control" id="f-metodo"><option>EFECTIVO</option><option>TRANSFERENCIA</option><option>TARJETA</option></select>
      </div>`,
    confirmText: 'Registrar',
    confirmClass: 'btn-success',
    onConfirm: async (overlay) => {
      const payload = {
        factura_id: factura.id,
        monto:      parseFloat(overlay.querySelector('#f-monto').value),
        tipo:       overlay.querySelector('#f-tipo').value,
        metodo:     overlay.querySelector('#f-metodo').value,
      };
      try {
        await api.pagos.create(payload);
        toast('Pago registrado', 'success');
        await cargarFactura(container, ordenId);
      } catch (err) { toast(err.message, 'error'); }
    }
  });
}
