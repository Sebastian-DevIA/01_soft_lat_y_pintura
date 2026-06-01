import { api } from '../api.js';
import { renderLoader, renderError, toast, showModal, confirmDialog, escapeHtml } from '../utils.js';

const FASES_ORDEN = ['INGRESO', 'REPARACION', 'ENTREGA'];
const FASES_LABEL = { INGRESO: 'Ingreso', REPARACION: 'Reparación', ENTREGA: 'Entrega' };

// Etiqueta legible del vehículo (campos enriquecidos con fallback seguro).
function vehiculoLabel(o) {
  const placa = o.vehiculo_placa ? String(o.vehiculo_placa).trim() : '';
  const desc = o.vehiculo_descripcion ? String(o.vehiculo_descripcion).trim() : '';
  return placa || desc || `Vehículo #${o.vehiculo_id}`;
}

export const seguimiento = {
  title: 'Seguimiento de Vehículos',
  async render(container) {
    container.innerHTML = renderLoader();
    try {
      const ordenes = await api.ordenes.list('?limit=100');
      const activas = ordenes.filter(o => ['EN_PROCESO'].includes(o.estado));

      // Cargar fases de cada orden activa
      const ordenesConFases = await Promise.all(
        activas.map(async o => {
          const fases = await api.fases.byOrden(o.id).catch(() => []);
          return { ...o, fases };
        })
      );

      // Personal disponible (para los modales de asignación). Tolerante a fallo.
      const personalDisponible = await api.personal.list().catch(() => []);

      // Agrupar por fase activa
      const columnas = { INGRESO: [], REPARACION: [], ENTREGA: [] };
      for (const o of ordenesConFases) {
        const faseActiva = o.fases.find(f => f.estado === 'EN_PROGRESO')
          || o.fases.find(f => f.estado === 'PENDIENTE');
        const key = faseActiva?.fase || 'INGRESO';
        if (columnas[key]) columnas[key].push({ orden: o, fase: faseActiva });
      }

      container.innerHTML = `
        <div class="flex justify-between align-center mb-2">
          <h2>Kanban de Reparaciones</h2>
          <span class="text-muted" style="font-size:.85rem">Vehículos en proceso: ${activas.length}</span>
        </div>
        <div class="kanban-board" id="kanban-board">
          ${FASES_ORDEN.map(fase => `
            <div class="kanban-col">
              <div class="kanban-col-header">
                ${FASES_LABEL[fase]}
                <span class="count">${columnas[fase].length}</span>
              </div>
              <div id="col-${fase}">
                ${columnas[fase].map(({ orden, fase: f }) => renderCard(orden, f)).join('')
                  || '<p style="font-size:.82rem;color:var(--color-muted);text-align:center;padding:16px">Sin vehículos</p>'}
              </div>
            </div>`).join('')}
        </div>`;

      // Navegación al detalle (click en la card)
      container.querySelectorAll('.kanban-card[data-orden-id]').forEach(card => {
        card.addEventListener('click', () => {
          location.hash = `#/ordenes/${card.dataset.ordenId}`;
        });
      });

      // Avanzar fase
      container.querySelectorAll('.btn-avanzar-fase').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          try {
            await api.fases.avanzar(btn.dataset.faseId, btn.dataset.estado, null);
            toast('Fase actualizada', 'success');
            seguimiento.render(container);
          } catch (err) { toast(err.message, 'error'); }
        });
      });

      // Asignar personal
      container.querySelectorAll('.btn-asignar').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          mostrarAsignar(container, btn.dataset.faseId, personalDisponible);
        });
      });

      // Quitar personal
      container.querySelectorAll('.btn-quitar').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const ok = await confirmDialog({
            title: 'Quitar técnico',
            message: '¿Quitar a este técnico de la fase?',
            confirmText: 'Sí, quitar',
          });
          if (!ok) return;
          try {
            await api.fases.removerPersonal(btn.dataset.faseId, btn.dataset.personalId);
            toast('Técnico removido', 'success');
            seguimiento.render(container);
          } catch (err) { toast(err.message, 'error'); }
        });
      });
    } catch (err) {
      container.innerHTML = renderError(err.message);
    }
  }
};

// Nombre legible de un técnico desde una asignación (tolerante a varias formas del payload).
function tecnicoNombre(a) {
  const p = a.personal || {};
  const nombre = [p.nombre, p.apellido].filter(Boolean).join(' ').trim();
  return nombre || a.personal_nombre || `Técnico #${a.personal_id}`;
}

function renderTecnicos(fase) {
  const asigs = fase?.asignaciones || [];
  if (!asigs.length) {
    return '<div class="info">Sin técnicos asignados</div>';
  }
  const chips = asigs.map(a => `
    <span class="badge badge-APROBACION" style="display:inline-flex;align-items:center;gap:6px">
      ${escapeHtml(tecnicoNombre(a))}
      <button class="btn btn-danger btn-sm btn-quitar" style="padding:0 6px;line-height:1.4"
              data-fase-id="${fase.id}" data-personal-id="${a.personal_id}"
              aria-label="Quitar técnico">✕</button>
    </span>`).join(' ');
  return `<div class="info" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">${chips}</div>`;
}

function renderCard(orden, fase) {
  const puedeAvanzar = fase && fase.estado !== 'COMPLETADA';
  return `
    <div class="kanban-card" data-orden-id="${orden.id}">
      <div class="placa">${escapeHtml(vehiculoLabel(orden))}</div>
      <div class="cliente">${escapeHtml(orden.cliente_nombre || `Orden #${orden.id}`)}</div>
      <div class="info">
        ${fase ? `Fase: <strong>${escapeHtml(fase.fase)}</strong> — ${escapeHtml(fase.estado)}` : 'Sin fase asignada'}
      </div>
      ${fase ? renderTecnicos(fase) : ''}
      <div class="mt-1 flex gap-1" style="flex-wrap:wrap">
        ${puedeAvanzar ? (fase.estado === 'PENDIENTE'
          ? `<button class="btn btn-accent btn-sm btn-avanzar-fase" data-fase-id="${fase.id}" data-estado="EN_PROGRESO">Iniciar</button>`
          : `<button class="btn btn-success btn-sm btn-avanzar-fase" data-fase-id="${fase.id}" data-estado="COMPLETADA">Completar</button>`) : ''}
        ${fase ? `<button class="btn btn-outline btn-sm btn-asignar" data-fase-id="${fase.id}">+ Asignar</button>` : ''}
      </div>
    </div>`;
}

function mostrarAsignar(container, faseId, personalDisponible) {
  const opciones = (personalDisponible || [])
    .map(p => `<option value="${p.id}">${escapeHtml(p.nombre)} ${escapeHtml(p.apellido)} — ${escapeHtml(p.rol)}</option>`)
    .join('');
  showModal({
    title: 'Asignar Técnico',
    body: personalDisponible && personalDisponible.length ? `
      <div class="form-group"><label>Técnico*</label>
        <select class="form-control" id="a-personal">${opciones}</select>
      </div>
      <div class="form-group"><label>Notas</label><input class="form-control" id="a-notas" placeholder="Opcional" /></div>`
      : '<p class="text-muted">No hay personal activo disponible. Registra empleados en la sección Personal.</p>',
    confirmText: 'Asignar',
    onConfirm: async (overlay) => {
      const select = overlay.querySelector('#a-personal');
      if (!select) return; // sin personal disponible
      const payload = {
        personal_id: parseInt(select.value, 10),
        notas:       overlay.querySelector('#a-notas').value.trim() || null,
      };
      try {
        await api.fases.asignarPersonal(faseId, payload);
        toast('Técnico asignado', 'success');
        seguimiento.render(container);
      } catch (err) { toast(err.message, 'error'); return false; }
    }
  });
}
