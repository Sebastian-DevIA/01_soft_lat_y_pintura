# MEMORY.md — Control de pendientes

Fuente **única y viva** de lo que falta por hacer en este proyecto. Los agentes
trabajan **desde aquí**: al iniciar cualquier sesión se lee `CLAUDE.md` + `README.md`
y luego este archivo para saber qué está pendiente.

## Reglas

1. Cada pendiente es una casilla `- [ ]`. Al **completarlo**, se marca `- [x]` y se
   **elimina** de la lista. No se acumula un log de "hecho": lo terminado se refleja en
   `README.md`/`CLAUDE.md` y se borra de aquí.
2. Al cerrar un pendiente, **actualizar** `CLAUDE.md` y `README.md` si cambian hechos
   del proyecto (endpoints, convenciones, estructura), sin agregar de más.
3. Pendientes nuevos se **agregan** aquí en cuanto surjan.
4. El trabajo se aborda en **modo agents teams** (delegar a los sub-agentes; ver
   `CLAUDE.md` → "Equipo de agentes").

---

## Pendientes

> **Objetivo transversal: endurecer cada endpoint** (validación, tests y coherencia de
> la API), en modo agents teams: `tech-lead` descompone, `backend-fastapi` implementa,
> `qa-tester` cubre con tests y `security-auditor` revisa antes de cerrar. Al terminar
> cada punto, actualizar `README.md`/`CLAUDE.md` y borrarlo de aquí.

- [ ] **Tests de usuarios/roles** (`/api/v1/usuarios`): `POST`/`GET`/`PATCH` con admin
  (201/200), **403** para no-admin (`get_current_admin`), **409** anti-auto-bloqueo y
  username/email duplicado, y `/auth/me` devolviendo `perfil`. (No se tocaron tests en
  esta entrega.)
- [ ] **RBAC duro en backend**: que "cada perfil actualiza solo su fase" se valide en el
  endpoint de fases (hoy es **gating de UI** en `seguimiento.js`); requiere ligar
  `Usuario`↔perfil↔fase y autorizar el avance en el backend.
- [ ] **Tests del borrado permanente de órdenes** (`DELETE /api/v1/ordenes/{id}/permanente`):
  cubrir **409** si la orden está activa, **204** si está inactiva y verificar la
  **cascada** (factura→pagos, fases→asignaciones, items). Subir cobertura y el badge de
  tests del README.
- [ ] **Paginación uniforme en listados**: que `clientes`, `vehiculos`, `facturas`,
  `pagos` y `personal` expongan `skip`/`limit` como ya hace `ordenes` (revisar primero
  cuáles lo tienen para no duplicar).
- [ ] **Coherencia de borrado permanente**: evaluar un `DELETE .../permanente` para
  `Cliente`/`Vehiculo`/`Personal` ya inactivos (mismo patrón que órdenes) o documentar
  por qué se deja solo soft-delete.
- [ ] **Endurecer validación Pydantic** en los schemas `*Request`, endpoint por endpoint
  (placa/cédula/email/teléfono con formato; montos `gt=0`, cantidades `ge=1`), con sus
  tests de casos límite (422).
