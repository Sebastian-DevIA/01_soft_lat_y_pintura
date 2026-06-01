// CarDiagram — diagrama 2D interactivo (SVG inline, sin librerías) de las zonas
// de carrocería de un vehículo, visto desde arriba. Pensado para latonería/pintura.
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

// Definición de zonas: id interno, etiqueta legible (lo que se persiste) y rect.
const ZONES = [
  { id: 'paragolpes-del', label: 'Paragolpes delantero',            x: 80,  y: 22,  w: 160, h: 34, rx: 16 },
  { id: 'aleta-del-izq',  label: 'Guardabarros delantero izquierdo', x: 74,  y: 64,  w: 40,  h: 88, rx: 8 },
  { id: 'capo',           label: 'Capó',                            x: 120, y: 64,  w: 80,  h: 88, rx: 8 },
  { id: 'aleta-del-der',  label: 'Guardabarros delantero derecho',   x: 206, y: 64,  w: 40,  h: 88, rx: 8 },
  { id: 'puerta-del-izq', label: 'Puerta delantera izquierda',       x: 74,  y: 160, w: 40,  h: 96, rx: 6 },
  { id: 'techo',          label: 'Techo',                           x: 120, y: 160, w: 80,  h: 200, rx: 10 },
  { id: 'puerta-del-der', label: 'Puerta delantera derecha',         x: 206, y: 160, w: 40,  h: 96, rx: 6 },
  { id: 'puerta-tra-izq', label: 'Puerta trasera izquierda',         x: 74,  y: 262, w: 40,  h: 96, rx: 6 },
  { id: 'puerta-tra-der', label: 'Puerta trasera derecha',           x: 206, y: 262, w: 40,  h: 96, rx: 6 },
  { id: 'aleta-tra-izq',  label: 'Guardabarros trasero izquierdo',   x: 74,  y: 366, w: 40,  h: 88, rx: 8 },
  { id: 'baul',           label: 'Baúl / Maletero',                 x: 120, y: 366, w: 80,  h: 88, rx: 8 },
  { id: 'aleta-tra-der',  label: 'Guardabarros trasero derecho',     x: 206, y: 366, w: 40,  h: 88, rx: 8 },
  { id: 'paragolpes-tra', label: 'Paragolpes trasero',              x: 80,  y: 462, w: 160, h: 34, rx: 16 },
];

// Etiquetas visibles solo en las zonas grandes (las demás usan tooltip + aria-label).
const VISIBLE_LABELS = {
  capo: 'Capó',
  techo: 'Techo',
  baul: 'Baúl',
};

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
    const cy = z.y + z.h / 2 + 4;
    const visible = VISIBLE_LABELS[z.id];
    const label = `${z.label}${isDamaged ? ' (con daño registrado)' : ''}`;
    return `
      <g>
        <rect class="${cls}" data-zone="${escapeHtml(z.label)}" data-id="${z.id}"
              x="${z.x}" y="${z.y}" width="${z.w}" height="${z.h}" rx="${z.rx}"
              ${readonly ? '' : 'tabindex="0" role="button"'} aria-label="${escapeHtml(label)}">
          <title>${escapeHtml(label)}</title>
        </rect>
        ${visible ? `<text class="car-zone-label" x="${cx}" y="${cy}">${escapeHtml(visible)}</text>` : ''}
      </g>`;
  }).join('');

  wrap.innerHTML = `
    <svg viewBox="0 0 320 520" role="img" aria-label="Diagrama de zonas del vehículo (vista superior)">
      <defs>
        <linearGradient id="carBody" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="rgba(255,255,255,.55)"/>
          <stop offset="1" stop-color="rgba(255,255,255,.30)"/>
        </linearGradient>
      </defs>
      <!-- silueta del cuerpo -->
      <rect x="66" y="16" width="188" height="488" rx="46" fill="url(#carBody)"
            stroke="var(--glass-border)" stroke-width="1.5"/>
      <!-- guía: frente del vehículo -->
      <text x="160" y="13" text-anchor="middle" font-size="9" fill="var(--color-muted)">▲ FRENTE</text>
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
