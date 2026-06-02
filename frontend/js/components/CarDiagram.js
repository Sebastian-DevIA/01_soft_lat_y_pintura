// CarDiagram — diagrama 2D interactivo (SVG inline, sin librerías) de las zonas
// de carrocería de un vehículo, visto desde arriba. Pensado para latonería/pintura.
//
// Orientación HORIZONTAL (apaisada): el frente del vehículo queda a la IZQUIERDA
// (◀ FRENTE) y el trasero a la derecha. Las zonas del lado izquierdo del coche van en
// la FILA SUPERIOR y las del lado derecho en la FILA INFERIOR.
//
// Uso:
//   const diagram = createCarDiagram({
//     selected: 'Capó',                 // etiqueta inicial seleccionada (opcional)
//     damagedZones: ['Puerta trasera izquierda'],  // zonas con daño → resaltadas
//     readonly: false,                  // true = solo lectura (vista de cotización)
//     onZoneClick: (label) => { ... },  // se llama con la etiqueta legible de la zona
//   });
//   contenedor.appendChild(diagram);
//
// La ETIQUETA legible (p. ej. "Guardabarros trasero izquierdo") es lo que se guarda
// en `item.area_vehiculo`. El `id` del path es solo estado interno del componente.
import { escapeHtml } from '../utils.js';

// Zonas de un carro normal (sedán), vista superior APAISADA. Cada zona lleva:
//  - label: nombre completo legible (lo que se guarda en area_vehiculo y va en aria-label)
//  - short: texto que se DIBUJA sobre la zona (todas lo tienen)
//  - vertical: true si el texto se rota -90° (franjas verticales angostas: paragolpes,
//    capó, techo, baúl). Las aletas/puertas ahora son anchas → texto horizontal sin rotar.
// El conjunto cubre las partes más comunes; agregar otras es OPCIONAL vía el campo de texto.
//
// Transposición desde el layout vertical (giro 90° horario): el eje Y antiguo
// (frente arriba → atrás abajo) pasa a ser el eje X nuevo (frente izquierda → atrás
// derecha); el eje X antiguo (izq↔der del coche) pasa al eje Y nuevo (lado izq → arriba,
// lado der → abajo). viewBox apaisado 520×300, silueta ~488×188.
const ZONES = [
  // Extremos: paragolpes (franjas verticales angostas en los bordes izq/der)
  { id: 'paragolpes-del', label: 'Paragolpes delantero',             short: 'Paragolpes del.', x: 22,  y: 80,  w: 34,  h: 160, rx: 16, vertical: true },
  { id: 'paragolpes-tra', label: 'Paragolpes trasero',               short: 'Paragolpes tras.', x: 462, y: 80,  w: 34,  h: 160, rx: 16, vertical: true },
  // Centro longitudinal: capó (izq-centro) → techo (centro) → baúl (der-centro)
  { id: 'capo',           label: 'Capó',                             short: 'Capó',            x: 64,  y: 120, w: 88,  h: 80,  rx: 8,  vertical: true },
  { id: 'techo',          label: 'Techo',                            short: 'Techo',           x: 160, y: 120, w: 200, h: 80,  rx: 10 },
  { id: 'baul',           label: 'Baúl / Maletero',                  short: 'Baúl',            x: 366, y: 120, w: 88,  h: 80,  rx: 8,  vertical: true },
  // Fila SUPERIOR = lado izquierdo del coche (delante → atrás)
  { id: 'aleta-del-izq',  label: 'Guardabarros delantero izquierdo', short: 'Aleta del. izq.', x: 64,  y: 74,  w: 88,  h: 40,  rx: 8 },
  { id: 'puerta-del-izq', label: 'Puerta delantera izquierda',       short: 'Puerta del. izq.', x: 160, y: 74,  w: 96,  h: 40,  rx: 6 },
  { id: 'puerta-tra-izq', label: 'Puerta trasera izquierda',         short: 'Puerta tras. izq.', x: 262, y: 74,  w: 96,  h: 40,  rx: 6 },
  { id: 'aleta-tra-izq',  label: 'Guardabarros trasero izquierdo',   short: 'Aleta tras. izq.', x: 366, y: 74,  w: 88,  h: 40,  rx: 8 },
  // Fila INFERIOR = lado derecho del coche (delante → atrás)
  { id: 'aleta-del-der',  label: 'Guardabarros delantero derecho',   short: 'Aleta del. der.', x: 64,  y: 206, w: 88,  h: 40,  rx: 8 },
  { id: 'puerta-del-der', label: 'Puerta delantera derecha',         short: 'Puerta del. der.', x: 160, y: 206, w: 96,  h: 40,  rx: 6 },
  { id: 'puerta-tra-der', label: 'Puerta trasera derecha',           short: 'Puerta tras. der.', x: 262, y: 206, w: 96,  h: 40,  rx: 6 },
  { id: 'aleta-tra-der',  label: 'Guardabarros trasero derecho',     short: 'Aleta tras. der.', x: 366, y: 206, w: 88,  h: 40,  rx: 8 },
];

const norm = (s) => (s || '').toString().trim().toLowerCase();

export function createCarDiagram({ selected = null, damagedZones = [], readonly = false, onZoneClick = null } = {}) {
  const damaged = new Set(damagedZones.map(norm));
  let selectedLabel = selected;

  const wrap = document.createElement('div');
  wrap.className = 'car-diagram' + (readonly ? ' readonly' : '');

  const zonesSvg = ZONES.map(z => {
    const isDamaged = damaged.has(norm(z.label));
    const isSelected = norm(z.label) === norm(selectedLabel);
    const cls = ['car-zone', isDamaged ? 'damaged' : '', isSelected ? 'selected' : ''].filter(Boolean).join(' ');
    const cx = z.x + z.w / 2;
    const cy = z.y + z.h / 2;
    const label = `${z.label}${isDamaged ? ' (con daño registrado)' : ''}`;
    const rot = z.vertical ? ` transform="rotate(-90 ${cx} ${cy})"` : '';
    return `
      <g>
        <rect class="${cls}" data-zone="${escapeHtml(z.label)}" data-id="${z.id}"
              x="${z.x}" y="${z.y}" width="${z.w}" height="${z.h}" rx="${z.rx}"
              ${readonly ? '' : 'tabindex="0" role="button"'} aria-label="${escapeHtml(label)}">
          <title>${escapeHtml(label)}</title>
        </rect>
        <text class="car-zone-label" x="${cx}" y="${cy + 3}"${rot}>${escapeHtml(z.short)}</text>
      </g>`;
  }).join('');

  wrap.innerHTML = `
    <svg viewBox="0 0 520 300" role="img" aria-label="Diagrama de zonas del vehículo (vista superior, frente a la izquierda)">
      <defs>
        <linearGradient id="carBody" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="rgba(255,255,255,.55)"/>
          <stop offset="1" stop-color="rgba(255,255,255,.30)"/>
        </linearGradient>
      </defs>
      <!-- silueta del cuerpo (apaisada) -->
      <rect x="16" y="66" width="488" height="188" rx="46" fill="url(#carBody)"
            stroke="var(--glass-border)" stroke-width="1.5"/>
      <!-- guía: frente del vehículo (a la izquierda) -->
      <text x="13" y="160" text-anchor="middle" font-size="9" fill="var(--color-muted)" transform="rotate(-90 13 160)">◀ FRENTE</text>
      ${zonesSvg}
    </svg>
    <div class="car-legend">
      <span><i class="lg-sel"></i> Seleccionada</span>
      <span><i class="lg-dmg"></i> Con daño</span>
    </div>
    <div class="car-diagram-caption" aria-live="polite">${
      readonly
        ? `${damaged.size} zona(s) con daño registrado`
        : (selectedLabel ? `Zona: <strong>${escapeHtml(selectedLabel)}</strong>` : 'Toca una zona del vehículo para seleccionarla')
    }</div>`;

  if (readonly) return wrap;

  const caption = wrap.querySelector('.car-diagram-caption');
  const select = (rect) => {
    const label = rect.getAttribute('data-zone');
    selectedLabel = label;
    wrap.querySelectorAll('.car-zone.selected').forEach(r => r.classList.remove('selected'));
    rect.classList.add('selected');
    caption.innerHTML = `Zona: <strong>${escapeHtml(label)}</strong>`;
    if (onZoneClick) onZoneClick(label);
  };

  wrap.querySelectorAll('.car-zone').forEach(rect => {
    rect.addEventListener('click', () => select(rect));
    rect.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(rect); }
    });
  });

  return wrap;
}

// Lista de etiquetas válidas (útil para validación o sugerencias).
export const CAR_ZONE_LABELS = ZONES.map(z => z.label);
