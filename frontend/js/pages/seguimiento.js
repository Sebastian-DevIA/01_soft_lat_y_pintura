import { api } from '../api.js';
import { renderLoader, renderError, toast } from '../utils.js';

const FASES_ORDEN = ['INGRESO', 'REPARACION', 'ENTREGA'];
const FASES_LABEL = { INGRESO: 'Ingreso', REPARACION: 'Reparación', ENTREGA: 'Entrega' };

export const seguimiento = {
  title: 'Seguimiento de Vehículos',
  async render(container) {
    container.innerHTML = renderLoader();
    try {
      const ordenes = await api.ordenes.list('?limite=100');
      const activas = ordenes.filter(o => ['EN_PROCESO'].includes(o.estado));

      // Cargar fases de cada orden activa
      const ordenesConFases = await Promise.all(
        activas.map(async o => {
          const fases = await api.fases.byOrden(o.id).catch(() => []);
          return { ...o, fases };
        })
      );

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

      // Eventos en cards
      container.querySelectorAll('.kanban-card[data-orden-id]').forEach(card => {
        card.addEventListener('click', () => {
          location.hash = `#/ordenes/${card.dataset.ordenId}`;
        });
      });
      container.querySelectorAll('.btn-avanzar-fase').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const faseId = btn.dataset.faseId;
          const nuevoEstado = btn.dataset.estado;
          try {
            await api.fases.avanzar(faseId, nuevoEstado, null);
            toast('Fase actualizada', 'success');
            seguimiento.render(container);
          } catch (err) {
            toast(err.message, 'error');
          }
        });
      });
    } catch (err) {
      container.innerHTML = renderError(err.message);
    }
  }
};

function renderCard(orden, fase) {
  const puedeAvanzar = fase && fase.estado !== 'COMPLETADA';
  return `
    <div class="kanban-card" data-orden-id="${orden.id}">
      <div class="placa">Orden #${orden.id}</div>
      <div class="cliente">Vehículo ID: ${orden.vehiculo_id}</div>
      <div class="info">
        ${fase ? `Fase: <strong>${fase.fase}</strong> — ${fase.estado}` : 'Sin fase asignada'}
      </div>
      ${puedeAvanzar ? `
        <div class="mt-1">
          ${fase.estado === 'PENDIENTE' ? `
            <button class="btn btn-accent btn-sm btn-avanzar-fase" data-fase-id="${fase.id}" data-estado="EN_PROGRESO">
              Iniciar
            </button>` : `
            <button class="btn btn-success btn-sm btn-avanzar-fase" data-fase-id="${fase.id}" data-estado="COMPLETADA">
              Completar
            </button>`}
        </div>` : ''}
    </div>`;
}
