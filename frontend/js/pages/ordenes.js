import { api } from '../api.js';
import { formatCurrency, formatDate, stateBadge, toast, renderLoader, renderError, showModal } from '../utils.js';

export const ordenes = {
  title: 'Órdenes de Trabajo',
  async render(container, ordenId) {
    if (ordenId) {
      await renderDetalle(container, ordenId);
    } else {
      await renderLista(container);
    }
  }
};

async function renderLista(container) {
  container.innerHTML = renderLoader();
  try {
    const data = await api.ordenes.list();
    container.innerHTML = `
      <div class="flex justify-between align-center mb-2">
        <h2>Órdenes de Trabajo</h2>
        <a class="btn btn-primary" href="#/ordenes/nueva">+ Nueva Orden</a>
      </div>
      <div class="search-bar">
        <select class="form-control" id="filtro-estado" style="max-width:200px">
          <option value="">Todos los estados</option>
          <option>PERITAJE</option><option>COTIZACION</option><option>APROBACION</option>
          <option>EN_PROCESO</option><option>ENTREGADO</option><option>CANCELADO</option>
        </select>
      </div>
      <div class="card">
        <div class="table-wrapper">
          <table class="data-table">
            <thead><tr><th>ID</th><th>Vehículo</th><th>Estado</th><th>Total</th><th>Ingreso</th><th></th></tr></thead>
            <tbody id="tbody-ordenes">${renderFilasOrdenes(data)}</tbody>
          </table>
        </div>
      </div>`;

    container.querySelector('#filtro-estado').onchange = async (e) => {
      const estado = e.target.value;
      const res = await api.ordenes.list(estado ? `?estado=${estado}` : '');
      container.querySelector('#tbody-ordenes').innerHTML = renderFilasOrdenes(res);
    };
  } catch (err) {
    container.innerHTML = renderError(err.message);
  }
}

function renderFilasOrdenes(lista) {
  if (!lista.length) return '<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--color-muted)">Sin órdenes</td></tr>';
  return lista.map(o => `
    <tr>
      <td><strong>#${o.id}</strong></td>
      <td>Vehículo #${o.vehiculo_id}</td>
      <td>${stateBadge(o.estado)}</td>
      <td>${formatCurrency(o.total_con_descuento)}</td>
      <td>${formatDate(o.fecha_ingreso)}</td>
      <td><a class="btn btn-outline btn-sm" href="#/ordenes/${o.id}">Ver detalle</a></td>
    </tr>`).join('');
}

async function renderDetalle(container, ordenId) {
  container.innerHTML = renderLoader();
  try {
    const orden = await api.ordenes.get(ordenId);
    const fases = await api.fases.byOrden(ordenId).catch(() => []);

    container.innerHTML = `
      <div class="flex align-center gap-2 mb-2">
        <a class="btn btn-outline btn-sm" href="#/ordenes">← Volver</a>
        <h2>Orden #${orden.id}</h2>
        ${stateBadge(orden.estado)}
      </div>
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

    // Agregar ítem
    container.querySelector('#btn-agregar-item')?.addEventListener('click', () => {
      mostrarFormularioItem(container, ordenId, orden);
    });

    // Aprobar orden
    container.querySelector('#btn-aprobar')?.addEventListener('click', async () => {
      if (!confirm('¿Confirmar aprobación del cliente?')) return;
      try {
        await api.ordenes.aprobar(ordenId);
        toast('Orden aprobada', 'success');
        renderDetalle(container, ordenId);
      } catch (err) { toast(err.message, 'error'); }
    });

    // Eliminar ítems
    container.querySelectorAll('.btn-delete-item').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (!confirm('¿Eliminar este ítem?')) return;
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

function renderTabPeritaje(orden) {
  const puedeEditar = ['PERITAJE', 'COTIZACION'].includes(orden.estado);
  return `
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
                <td><strong>${i.area_vehiculo}</strong></td>
                <td>${i.descripcion}</td>
                <td class="text-right">${i.cantidad}</td>
                <td class="text-right">${formatCurrency(i.precio_unitario)}</td>
                <td class="text-right">${formatCurrency(i.subtotal)}</td>
                ${puedeEditar ? `<td><button class="btn btn-danger btn-sm btn-delete-item" data-id="${i.id}">✕</button></td>` : ''}
              </tr>`).join('')
              : `<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--color-muted)">Sin ítems. Agregue las áreas a reparar.</td></tr>`}
          </tbody>
        </table>
      </div>
    </div>`;
}

function renderTabCotizacion(orden) {
  const puedeAprobar = orden.estado === 'COTIZACION' && orden.items.length > 0;
  return `
    <div class="card">
      <h3 class="mb-2">Resumen de Cotización</h3>
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
          <strong>${f.fase}</strong>
          <span class="badge ${estadoColor[f.estado] || ''}">${f.estado}</span>
        </div>
        ${f.notas ? `<p class="text-muted mt-1" style="font-size:.85rem">${f.notas}</p>` : ''}
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
            <h3>Factura ${f.numero_factura}</h3>
            <span class="badge badge-${f.estado}">${f.estado}</span>
          </div>
          <div class="totales-box">
            <div class="total-row"><span>Total</span><span>${formatCurrency(f.monto_total)}</span></div>
            <div class="total-row"><span>Adelanto (50%)</span><span>${formatCurrency(f.monto_adelanto)}</span></div>
            <div class="total-row"><span>Saldo (50%)</span><span>${formatCurrency(f.monto_saldo)}</span></div>
            <div class="total-row"><span>Pagado</span><span>${formatCurrency(f.monto_pagado)}</span></div>
            <div class="total-row total-final"><span>Pendiente</span><span>${formatCurrency(f.monto_total - f.monto_pagado)}</span></div>
          </div>
          <div class="mt-2 flex gap-2">
            <a class="btn btn-outline btn-sm" href="${api.facturas.pdfUrl(f.id)}" target="_blank">📄 Descargar PDF</a>
            ${f.estado !== 'PAGADA' ? '<button class="btn btn-success btn-sm" id="btn-registrar-pago">Registrar Pago</button>' : ''}
          </div>
        </div>`;
      div.querySelector('#btn-registrar-pago')?.addEventListener('click', () => {
        mostrarFormularioPago(div, f, ordenId, container);
      });
    } else {
      div.innerHTML = '<div class="card"><p class="text-muted" style="padding:16px">La factura se emite después de que el cliente aprueba la cotización.</p></div>';
    }
  } catch (err) { div.innerHTML = renderError(err.message); }
}

function mostrarFormularioItem(container, ordenId, orden) {
  showModal({
    title: 'Agregar Área Dañada',
    body: `
      <div class="form-group"><label>Área del vehículo*</label><input class="form-control" id="f-area" placeholder="Ej: Puerta trasera izquierda" /></div>
      <div class="form-group"><label>Descripción*</label><input class="form-control" id="f-desc" placeholder="Ej: Abolladuras profundas y rayones" /></div>
      <div class="form-group"><label>Precio unitario (COP)*</label><input class="form-control" id="f-precio" type="number" min="1" /></div>
      <div class="form-group"><label>Cantidad</label><input class="form-control" id="f-cant" type="number" value="1" min="1" /></div>`,
    confirmText: 'Agregar',
    onConfirm: async (overlay) => {
      const payload = {
        area_vehiculo:   overlay.querySelector('#f-area').value.trim(),
        descripcion:     overlay.querySelector('#f-desc').value.trim(),
        precio_unitario: parseFloat(overlay.querySelector('#f-precio').value),
        cantidad:        parseInt(overlay.querySelector('#f-cant').value),
      };
      try {
        await api.ordenes.addItem(ordenId, payload);
        toast('Área agregada', 'success');
        renderDetalle(container, ordenId);
      } catch (err) { toast(err.message, 'error'); }
    }
  });
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
