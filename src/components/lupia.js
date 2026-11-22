// Piezas compartidas de LupIA: formatos, estados, señales y pequeños gráficos en tinta.
import * as Plot from "npm:@observablehq/plot";
import {html, svg} from "npm:htl";

export {Plot};

export const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

// Las fechas sin hora se leen como medianoche UTC: se formatean en UTC para no correrse un día.
function aFecha(d) {
  if (d instanceof Date) return d;
  const s = String(d);
  return new Date(s.length <= 10 ? `${s}T00:00:00Z` : s.replace(" ", "T") + "Z");
}
export const fecha = (d) => (d == null || d === "" ? "—" : `${aFecha(d).getUTCDate()} ${MESES[aFecha(d).getUTCMonth()]}`);
export const fechaLarga = (d) => `${aFecha(d).getUTCDate()} ${MESES[aFecha(d).getUTCMonth()]} ${aFecha(d).getUTCFullYear()}`;
export const fechaTexto = (d) => `${aFecha(d).getUTCDate()} de ${MESES_LARGOS[aFecha(d).getUTCMonth()]} de ${aFecha(d).getUTCFullYear()}`;
export const hora = (t) => String(t).slice(11, 16);
export const num = (x, decimales = 1) => Number(x).toLocaleString("es-CR", {maximumFractionDigits: decimales});
export const millones = (crc) => `₡${num(crc / 1e6, 0)} millones`;
export const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;

// Estados de un día o una semana: tinta, vacío, rayado de plano o gris de obra terminada.
export const ESTADOS = {
  actividad: {label: "Actividad", fill: "var(--tinta)"},
  sin_actividad: {label: "Sin actividad", fill: "var(--papel)"},
  sin_datos: {label: "Sin datos de la cámara", fill: "url(#lupia-rayado)"},
  terminada: {label: "Obra terminada", fill: "var(--niebla)"}
};
export const escalaEstados = (claves = Object.keys(ESTADOS)) => ({
  type: "ordinal", domain: claves.map((k) => ESTADOS[k].label), range: claves.map((k) => ESTADOS[k].fill), legend: false
});

function muestra(k, tam = 12) {
  return svg`<svg width=${tam} height=${tam} aria-hidden="true"><rect x="0.75" y="0.75" width=${tam - 1.5} height=${tam - 1.5} rx="2" fill=${ESTADOS[k].fill} stroke=${k === "actividad" ? "var(--tinta)" : "var(--trazo)"} stroke-width="1"/></svg>`;
}
export function leyendaEstados(claves = Object.keys(ESTADOS)) {
  return html`<div class="leyenda">${claves.map((k) => html`<span>${muestra(k)}${ESTADOS[k].label}</span>`)}</div>`;
}

// Las cinco señales, siempre en este orden.
export const SENALES = [
  {key: "inactividad", label: "Inactividad con cámara funcionando", corto: "Inactividad"},
  {key: "atraso", label: "Atraso frente al cronograma", corto: "Atraso"},
  {key: "brecha", label: "Brecha entre lo reportado y lo observado", corto: "Brecha"},
  {key: "contrato", label: "Cambios contractuales", corto: "Contrato"},
  {key: "ciudadania", label: "Reportes ciudadanos", corto: "Ciudadanía"}
];
export const nombreSenal = Object.fromEntries(SENALES.map((s) => [s.key, s.label]));

// Puntaje de 0 a 100 con los pesos que elija el auditor.
export function puntaje(obra, pesos) {
  const total = SENALES.reduce((a, s) => a + pesos[s.key], 0) || 1;
  return (100 * SENALES.reduce((a, s) => a + pesos[s.key] * obra[`senal_${s.key}`], 0)) / total;
}

export const alertasDe = (o) => (o.alertas ? String(o.alertas).split(";") : []);

// Razones en lenguaje claro, una por alerta. "explicada" marca las que tienen una explicación posible.
export function razones(o) {
  const texto = {
    inactividad: () => ({
      texto: `${plural(o.racha_inactividad_dias, "día hábil", "días hábiles")} seguidos sin actividad con la cámara funcionando` +
        (o.explicacion_inactividad ? `. Posible explicación: ${o.explicacion_inactividad}.` : "."),
      explicada: Boolean(o.explicacion_inactividad)
    }),
    atraso: () => ({texto: `${num(o.atraso_pts)} puntos de atraso frente al cronograma vigente.`}),
    brecha: () => ({texto: `Reporta ${num(o.incremento_reportado_pts)} puntos más de avance en 12 semanas, pero solo hubo actividad en ${num(100 * o.proporcion_semanas_activas, 0)} % de ellas.`}),
    contrato: () => ({texto: (o.aumento_monto_pct > 0 ? `Monto aumentado en ${num(o.aumento_monto_pct)} %` : "Prórroga aprobada en los últimos 90 días") +
      (o.aumento_monto_pct > 0 && o.prorroga_reciente ? " y una prórroga reciente." : ".")}),
    ciudadania: () => ({texto: `${plural(o.reportes_30d, "reporte ciudadano", "reportes ciudadanos")} en los últimos 30 días.`})
  };
  return alertasDe(o).map((a) => ({clave: a, ...texto[a]()}));
}

// Identificador de obra, como el número de lámina de un plano.
export const lamina = (id) => html`<span class="lamina" aria-hidden="true">${id}</span>`;

// Pulso: una celda por semana (las últimas 12).
export function pulso(semanas, {celda = 11, alto = 18, sep = 3} = {}) {
  const n = semanas.length;
  const activas = semanas.filter((s) => s.estado_semana === "actividad").length;
  const sinDatos = semanas.filter((s) => s.estado_semana === "sin_datos").length;
  const etiqueta = `Últimas ${n} semanas: ${activas} con actividad` + (sinDatos ? `, ${sinDatos} sin datos` : "");
  return svg`<svg width=${n * (celda + sep)} height=${alto} role="img" aria-label=${etiqueta}>${semanas.map((s, i) => svg`<rect
    x=${i * (celda + sep) + 0.5} y="0.5" width=${celda} height=${alto - 1} rx="2"
    fill=${ESTADOS[s.estado_semana].fill}
    stroke=${s.estado_semana === "actividad" ? "var(--tinta)" : "var(--trazo)"} stroke-width="1"><title>${`Semana del ${fecha(s.semana)}: ${ESTADOS[s.estado_semana].label.toLowerCase()}` + (s.con_explicacion ? " (con explicación)" : "")}</title></rect>${
    s.con_explicacion ? svg`<circle cx=${i * (celda + sep) + 0.5 + celda / 2} cy=${alto / 2} r="2" fill="var(--grafito)"/>` : ""}`)}</svg>`;
}

// Señales: cinco cuadros en tinta; más oscuro = señal más fuerte; borde grueso = alerta.
export function senalesMini(o, {tam = 14, sep = 4} = {}) {
  const alertas = new Set(alertasDe(o));
  const etiqueta = SENALES.map((s) => `${s.corto} ${num(o[`senal_${s.key}`], 2)}${alertas.has(s.key) ? " (alerta)" : ""}`).join(", ");
  return svg`<svg width=${5 * (tam + sep)} height=${tam + 2} role="img" aria-label=${`Señales: ${etiqueta}`}>${SENALES.map((s, i) => {
    const v = o[`senal_${s.key}`];
    const alerta = alertas.has(s.key);
    return svg`<rect x=${i * (tam + sep) + 1} y="1" width=${tam} height=${tam} rx="2"
      fill="var(--tinta)" fill-opacity=${v > 0 ? 0.12 + 0.88 * v : 0}
      stroke=${alerta ? "var(--tinta)" : "var(--trazo)"} stroke-width=${alerta ? 2 : 1}><title>${`${s.label}: ${num(v, 2)}${alerta ? " · alerta" : ""}`}</title></rect>`;
  })}</svg>`;
}

// Patrón rayado (como en los planos) para "sin datos": se agrega una vez al documento.
export function asegurarRayado() {
  if (document.getElementById("lupia-defs")) return;
  const defs = svg`<svg id="lupia-defs" width="0" height="0" style="position: absolute" aria-hidden="true"><defs>
    <pattern id="lupia-rayado" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="5" height="5" fill="var(--papel)"/><line x1="0" y1="0" x2="0" y2="5" stroke="var(--trazo)" stroke-width="1.6"/>
    </pattern></defs></svg>`;
  document.body.appendChild(defs);
}

// Gráfico de Plot sin las etiquetas ARIA inválidas que Plot pone en sus grupos internos.
export function grafico(opciones) {
  const figura = Plot.plot(opciones);
  figura.querySelectorAll("g[aria-label]").forEach((g) => g.removeAttribute("aria-label"));
  figura.querySelectorAll("svg").forEach((s) => s.setAttribute("aria-hidden", "true"));
  return figura;
}

// Estilo común para los gráficos de Plot.
export const estiloPlot = {fontFamily: "Public Sans, system-ui, sans-serif", fontSize: "12px", color: "var(--grafito)", background: "transparent", overflow: "visible"};
