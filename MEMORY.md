# MEMORY.md — Control de pendientes

Fuente **única y viva** de lo que falta por hacer en este proyecto. Los agentes
trabajan **desde aquí**: al iniciar cualquier sesión se lee `CLAUDE.md` + `README.md`
y luego este archivo para saber qué está pendiente.

## Reglas

1. Cada pendiente es una casilla `- [ ]`. Al **completarlo**, se marca `- [x]` y se
   **elimina** de la lista (se deja solo lo que sigue pendiente).
2. Al cerrar un pendiente, **actualizar** `CLAUDE.md` y `README.md` si cambian hechos
   del proyecto (endpoints, convenciones, estructura), sin agregar de más.
3. Pendientes nuevos se **agregan** aquí en cuanto surjan.
4. El trabajo se aborda en **modo agents teams** (delegar a los sub-agentes; ver
   `CLAUDE.md` → "Equipo de agentes").

---

## Pendientes

- [ ] **Mejorar el CRUD de órdenes** — llevarlo al nivel del CRUD de clientes.
  Desde el **historial/listado** de órdenes (`#/ordenes`): poder **editar** cada
  orden al estilo CRUD y **eliminar** (cuando se indique), con validación, estados
  de carga/vacío/error y confirmaciones con `confirmDialog`.
  · Dónde: `frontend/js/pages/ordenes.js` (+ endpoints de `ordenes` si hace falta).

- [ ] **Mapa de daños en horizontal** — el `CarDiagram` está en orientación vertical;
  dejarlo **horizontal** (vista superior apaisada).
  · Dónde: `frontend/js/components/CarDiagram.js`, `frontend/css/components.css`.

- [ ] **Áreas dañadas al lado del mapa** — mostrar la lista/visualización de zonas
  dañadas **junto** al diagrama del carro (layout en dos columnas) para que sea más
  visible.
  · Dónde: `frontend/js/pages/ordenes.js`, `frontend/css/components.css`.

---

## Hecho recientemente

- CRUD completo de clientes (editar/eliminar/reactivar, filtro activos/inactivos).
- Visor de PDF de factura autenticado (JWT→Blob) + desglose de IVA + envío por WhatsApp.
- Mapa de daños `CarDiagram` (SVG interactivo, 13 zonas nombradas) integrado en peritaje y orden.
- Documentación estandarizada: este `MEMORY.md` es el control de pendientes.
