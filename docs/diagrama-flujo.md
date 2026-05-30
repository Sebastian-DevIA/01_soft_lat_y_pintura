# Diagrama de Flujo — Taller LatonPaint

## Flujo completo del vehículo

```
CLIENTE LLEGA AL TALLER
         │
         ▼
┌─────────────────────┐
│  REGISTRO EN SISTEMA │
│  - Datos del cliente │
│  - Datos del vehículo│
│  - Crea OrdenTrabajo │
│  Estado: PERITAJE    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     PERITAJE        │
│ Inspección visual   │
│ Se agregan ítems:   │
│  - Área del vehículo │
│  - Precio individual │
│  (editable por ítem) │
│  Estado: COTIZACION  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   COTIZACIÓN        │
│ Suma de todos los   │
│ ítems de reparación │
│ ¿Descuento? → Sí/No │
│ Total ajustado      │
└──────────┬──────────┘
           │
           ├── Cliente rechaza → CANCELADO
           │
           ▼ (Cliente acepta)
┌─────────────────────┐
│   APROBACIÓN        │
│ Cliente firma/aprueba│
│ Se genera Factura   │
│  - 50% ADELANTO     │
│  - 50% AL ENTREGAR  │
│ Se crean 3 fases:   │
│  INGRESO/REPARACION │
│  /ENTREGA           │
│ Estado: APROBACION  │
└──────────┬──────────┘
           │ (Se registra pago adelanto)
           ▼
┌─────────────────────┐
│    EN PROCESO       │
│                     │
│  [INGRESO]          │
│  Recepción formal   │
│  Asignar personal   │
│       │             │
│       ▼             │
│  [REPARACIÓN]       │
│  Latonería y pintura│
│  Personal: latonero │
│  + pintor asignados │
│       │             │
│       ▼             │
│  [ENTREGA]          │
│  ¿Saldo pagado?     │
│  Sí → continuar     │
│  No → BLOQUEAR      │
└──────────┬──────────┘
           │ (Solo si Factura.estado == PAGADA)
           ▼
┌─────────────────────┐
│     ENTREGADO       │
│ Vehículo entregado  │
│ Orden cerrada       │
│ Fecha de entrega    │
│ registrada          │
└─────────────────────┘
```

## Flujo de pagos

```
Factura emitida (monto_total = $X)
         │
         ├──→ Adelanto = $X * 50%  → Estado: PARCIAL
         │
         └──→ Saldo    = $X * 50%  → Estado: PAGADA
                                       → Desbloquea ENTREGA
```

## Asignación de personal por fase

```
INGRESO     → Recepcionista / Jefe de taller
REPARACIÓN  → Latonero + Pintor (+ Auxiliar opcional)
ENTREGA     → Jefe de taller / Pulidor
```
