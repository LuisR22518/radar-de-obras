// Funciones y constantes compartidas por las páginas del Radar.
import * as Plot from "npm:@observablehq/plot";

export const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

// Las fechas sin hora se leen como medianoche UTC: se formatean en UTC para no correrse un día.
export function fecha(d) {
  if (d == null || d === "") return "—";
  const x = d instanceof Date ? d : new Date(String(d).length <= 10 ? `${d}T00:00:00Z` : String(d).replace(" ", "T") + "Z");
  return `${x.getUTCDate()} ${MESES[x.getUTCMonth()]}`;
}
export function fechaLarga(d) {
  const x = d instanceof Date ? d : new Date(`${String(d).slice(0, 10)}T00:00:00Z`);
  return `${x.getUTCDate()} ${MESES[x.getUTCMonth()]} ${x.getUTCFullYear()}`;
}
export function hora(texto) {
  return String(texto).slice(11, 16);
}
export function num(x, decimales = 1) {
  return Number(x).toLocaleString("es-CR", {maximumFractionDigits: decimales});
}
export function millones(crc) {
  return `₡${(crc / 1e6).toLocaleString("es-CR", {maximumFractionDigits: 0})} millones`;
}

export const ESTADOS = {
  actividad: {label: "Actividad", fill: "var(--actividad)"},
  sin_actividad: {label: "Sin actividad", fill: "var(--theme-background)"},
  sin_datos: {label: "Sin datos (cámara)", fill: "url(#radar-rayado)"},
  terminada: {label: "Obra terminada", fill: "var(--terminada)"}
};
export const escalaEstados = (claves = Object.keys(ESTADOS)) => ({
  type: "ordinal",
  domain: claves.map((k) => ESTADOS[k].label),
  range: claves.map((k) => ESTADOS[k].fill),
  legend: false
});

// Leyenda propia: cada muestra con borde, para que "sin actividad" (vacío) se distinga del fondo.
export function leyendaEstados(html, claves = Object.keys(ESTADOS)) {
  const muestra = (k) => k === "sin_datos"
    ? html`<svg width="14" height="14" style="vertical-align: -2px"><rect x="0.5" y="0.5" width="13" height="13" rx="2" fill="url(#radar-rayado)" stroke="var(--vacio-borde)"/></svg>`
    : html`<svg width="14" height="14" style="vertical-align: -2px"><rect x="0.5" y="0.5" width="13" height="13" rx="2" fill="${ESTADOS[k].fill}" stroke="var(--vacio-borde)"/></svg>`;
  return html`<div class="nota" style="display: flex; gap: 1rem; flex-wrap: wrap; margin: 0.25rem 0;">${claves.map((k) => html`<span>${muestra(k)} ${ESTADOS[k].label}</span>`)}</div>`;
}
export const nombreCorto = {inactividad: "Inactividad", atraso: "Atraso", brecha: "Brecha reportado-observado", contrato: "Contrato", ciudadania: "Ciudadanía"};

export const SENALES = [
  {key: "inactividad", label: "Inactividad con cámara funcionando", color: "var(--s1)"},
  {key: "atraso", label: "Atraso frente al cronograma", color: "var(--s2)"},
  {key: "brecha", label: "Brecha entre lo reportado y lo observado", color: "var(--s3)"},
  {key: "contrato", label: "Cambios contractuales", color: "var(--s4)"},
  {key: "ciudadania", label: "Reportes ciudadanos", color: "var(--s5)"}
];
export const nombreSenal = Object.fromEntries(SENALES.map((s) => [s.key, s.label]));

// Puntaje de 0 a 100 con los pesos que elija el auditor (se normaliza por la suma de pesos).
export function puntaje(obra, pesos) {
  const total = SENALES.reduce((a, s) => a + pesos[s.key], 0) || 1;
  return (100 * SENALES.reduce((a, s) => a + pesos[s.key] * obra[`senal_${s.key}`], 0)) / total;
}

// Patrón rayado para "sin datos": se agrega una sola vez al documento.
export function asegurarRayado() {
  if (document.getElementById("radar-defs")) return;
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("id", "radar-defs");
  svg.setAttribute("width", 0);
  svg.setAttribute("height", 0);
  svg.style.position = "absolute";
  svg.innerHTML = `<defs><pattern id="radar-rayado" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="6" height="6" fill="var(--theme-background)"/><line x1="0" y1="0" x2="0" y2="6" stroke="var(--sin-datos)" stroke-width="2"/></pattern></defs>`;
  document.body.appendChild(svg);
}

export {Plot};
