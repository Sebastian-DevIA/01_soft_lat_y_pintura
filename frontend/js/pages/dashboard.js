import { api } from '../api.js';
import { formatCurrency, renderLoader, renderError } from '../utils.js';

export const dashboard = {
  title: 'Dashboard',
  async render(container) {
    container.innerHTML = renderLoader();
    try {
      const [activas, cotizacion, proceso, entregadas] = await Promise.all([
        api.ordenes.list('?limit=100'),
        api.ordenes.list('?estado=COTIZACION&limit=50'),
        api.ordenes.list('?estado=EN_PROCESO&limit=50'),
        api.ordenes.list('?estado=ENTREGADO&limit=100'),
      ]);

      const total = activas.length;
      const enProceso = proceso.length;
      const pendientesAprobacion = cotizacion.length;

      container.innerHTML = `
        <h2 class="mb-2">Resumen del Taller</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">Total órdenes activas</div>
            <div class="stat-value">${total}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">En reparación</div>
            <div class="stat-value" style="color:var(--color-success)">${enProceso}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Pendientes de aprobación</div>
            <div class="stat-value" style="color:var(--color-warning)">${pendientesAprobacion}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Entregados (histórico)</div>
            <div class="stat-value" style="color:var(--color-muted)">${entregadas.length}</div>
          </div>
        </div>

        <div class="card mt-2">
          <div class="card-header"><h3>Últimas órdenes</h3></div>
          <div class="table-wrapper">
            <table class="data-table">
              <thead><tr><th>ID</th><th>Estado</th><th>Total</th><th>Ingreso</th></tr></thead>
              <tbody>
                ${activas.slice(0, 10).map(o => `
                  <tr onclick="location.hash='#/ordenes/${o.id}'" style="cursor:pointer">
                    <td><strong>#${o.id}</strong></td>
                    <td><span class="badge badge-${o.estado}">${o.estado}</span></td>
                    <td>${formatCurrency(o.total_con_descuento)}</td>
                    <td>${new Date(o.fecha_ingreso).toLocaleDateString('es-CO')}</td>
                  </tr>`).join('') || '<tr><td colspan="4" style="text-align:center;color:var(--color-muted);padding:24px">Sin órdenes</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>`;
    } catch (err) {
      container.innerHTML = renderError(err.message);
    }
  }
};
