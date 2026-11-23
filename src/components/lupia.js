// Piezas compartidas de LupIA: formatos, estados, señales y pequeños gráficos en tinta.
import * as Plot from "npm:@observablehq/plot";
import {html, svg} from "npm:htl";
import * as d3 from "npm:d3";

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
// Puntaje de 0 a 100 con las señales que tienen dato (si falta un dato, su peso se reparte entre las demás)
export function puntaje(obra, pesos) {
  const con = SENALES.filter((s) => obra[`senal_${s.key}`] != null && !Number.isNaN(obra[`senal_${s.key}`]));
  const total = con.reduce((a, s) => a + pesos[s.key], 0);
  return total ? (100 * con.reduce((a, s) => a + pesos[s.key] * obra[`senal_${s.key}`], 0)) / total : 0;
}
export const tieneDato = (v) => v != null && v !== "" && !Number.isNaN(v);

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
    brecha: () => ({texto: `Reporta ${num(o.incremento_reportado_pts)} puntos más de avance en 12 semanas, pero solo hubo actividad en ${num(100 * o.proporcion_semanas_activas, 0)}\u00a0% de ellas.`}),
    contrato: () => ({texto: (o.aumento_monto_pct > 0 ? `Monto aumentado en ${num(o.aumento_monto_pct)}\u00a0%` : "Prórroga aprobada en los últimos 90 días") +
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

// --- Lo que ve el auditor: un estado por obra, en palabras --------------------------

// Tres estados posibles. Solo "revisar" lleva el resaltador.
export const ESTADO_OBRA = {
  revisar: {label: "Necesita revisión", grupo: "Necesitan revisión"},
  sin_alertas: {label: "Sin alertas", grupo: "Sin alertas"},
  sin_datos: {label: "Cámara sin datos", grupo: "Cámara sin datos"},
  historico: {label: "Monitoreo terminado", grupo: "Monitoreo terminado"}
};
export const estadoObra = (o) => (o.historica ? "historico" : o.en_cola_dispositivos ? "sin_datos" : o.amerita_revision ? "revisar" : "sin_alertas");
export const esReal = (o) => o.fuente_datos === "dIAra real";

// Orden de trabajo: primero lo que necesita revisión (por puntaje), luego sin alertas y al final las cámaras sin datos.
export function ordenar(obras, pesos) {
  const rango = {revisar: 0, sin_alertas: 1, sin_datos: 2, historico: 3};
  return obras
    .map((o) => ({...o, estado: estadoObra(o), puntaje_vivo: o.en_cola_dispositivos || o.historica ? 0 : puntaje(o, pesos)}))
    .sort((a, b) => rango[a.estado] - rango[b.estado] || b.puntaje_vivo - a.puntaje_vivo)
    .map((o, i) => ({...o, orden: i + 1}));
}

// Razones cortas, para leer de un vistazo en la lista.
export function razonesCortas(o) {
  if (o.historica) return [esReal(o) ? `datos reales del piloto de dIAra: ${plural(o.dias_con_datos, "día publicado", "días publicados")} entre ${fecha(o.periodo_desde)} y ${fecha(o.fecha_corte_obra)} de ${aFecha(o.fecha_corte_obra).getUTCFullYear()}` : "la cámara ya se retiró de esta obra"];
  if (o.en_cola_dispositivos) return [`No llegan fotos desde hace ${plural(o.dias_sin_datos, "día", "días")}: va a mantenimiento`];
  if (!o.amerita_revision) return [o.fase === "terminada" ? "Obra terminada y recibida" : "Actividad normal y al día"];
  const corto = {
    inactividad: () => `${plural(o.racha_inactividad_dias, "día hábil", "días hábiles")} sin actividad` + (o.explicacion_inactividad ? " (con posible explicación)" : ""),
    atraso: () => `${num(o.atraso_pts)} puntos de atraso`,
    brecha: () => "reporta avance que la cámara no respalda",
    contrato: () => (o.aumento_monto_pct > 0 ? `monto aumentado ${num(o.aumento_monto_pct)}\u00a0%` : "prórroga reciente"),
    ciudadania: () => plural(o.reportes_30d, "reporte ciudadano", "reportes ciudadanos")
  };
  // De la alerta que más pesa a la que menos
  return alertasDe(o).sort((a, b) => o[`aporte_${b}`] - o[`aporte_${a}`]).map((a) => corto[a]());
}
export const unirFrase = (partes) => {
  const p = partes.map((t, i) => (i ? t : t.charAt(0).toUpperCase() + t.slice(1)));
  return (p.length > 1 ? `${p.slice(0, -1).join(", ")} y ${p.at(-1)}` : p[0] ?? "") + ".";
};

// Decisión guardada por el auditor en este navegador
export function leerDecision(id) {
  try { return JSON.parse(localStorage.getItem(`lupia-decision-${id}`) ?? "null"); } catch { return null; }
}

// Ícono de estado (no depende solo del color): círculo resaltado, círculo vacío o rayado
export function iconoEstado(estado, numero, tam = 26) {
  const r = tam / 2 - 1.5;
  const relleno = {revisar: "var(--resaltador)", sin_alertas: "var(--papel)", sin_datos: "url(#lupia-rayado)", historico: "var(--papel)"}[estado];
  const borde = estado === "revisar" ? "var(--tinta)" : "var(--trazo)";
  return svg`<svg class="icono-estado" width=${tam} height=${tam} viewBox="0 0 ${tam} ${tam}" aria-hidden="true">
    <circle cx=${tam / 2} cy=${tam / 2} r=${r} fill=${relleno} stroke=${borde} stroke-width=${estado === "revisar" ? 1.75 : 1.25} stroke-dasharray=${estado === "historico" ? "2.5 2" : "none"} />
    ${numero == null ? "" : svg`<text x=${tam / 2} y=${tam / 2} dy="0.36em" text-anchor="middle" font-size=${tam * 0.46} font-weight="700"
      fill=${estado === "revisar" ? "var(--tinta)" : "var(--grafito)"} paint-order="stroke" stroke=${estado === "sin_datos" ? "var(--papel)" : "none"} stroke-width="3">${numero}</text>`}
  </svg>`;
}
export function leyendaObra() {
  return html`<div class="leyenda">${Object.entries(ESTADO_OBRA).map(([k, e]) => html`<span>${iconoEstado(k, null, 16)}${e.label}</span>`)}</div>`;
}

// Mapa de Costa Rica con un punto por obra; cada punto lleva el número de la lista.
// Dónde va el nombre de cada provincia (el centro geométrico cae mal en las provincias alargadas)
const ETIQUETA_PROVINCIA = {"Guanacaste": [-85.45, 10.45], "Puntarenas": [-83.6, 8.85], "Alajuela": [-84.45, 10.6], "Limón": [-83.25, 9.85],
  "Heredia": [-84.05, 10.4], "San José": [-84.0, 9.55], "Cartago": [-83.7, 9.75]};
export function mapaObras(pais, obras, {width = 520, activo = null, provincias = null} = {}) {
  const alto = Math.round(width * 0.9);
  const proy = d3.geoMercator().fitExtent([[16, 16], [width - 16, alto - 16]], pais);
  const camino = d3.geoPath(proy);
  const tam = width < 420 ? 24 : 28;
  // Las obras con menor prioridad se dibujan primero, para que las urgentes queden encima
  const puntos = [...obras].sort((a, b) => b.orden - a.orden).map((o) => {
    const [x, y] = proy([o.lon, o.lat]);
    return {o, x0: x, y0: y, x, y};
  });
  // Separa los puntos que se tocan (obras cercanas) y deja una línea a su ubicación real
  for (let k = 0; k < 40; k++) {
    for (const a of puntos) for (const b of puntos) {
      if (a === b) continue;
      const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 0.01, min = tam + 3;
      if (d < min) {
        const m = (min - d) / 2;
        a.x -= (dx / d) * m; a.y -= (dy / d) * m;
        b.x += (dx / d) * m; b.y += (dy / d) * m;
      }
    }
  }
  return html`<svg class="mapa" viewBox="0 0 ${width} ${alto}" width=${width} height=${alto} aria-hidden="true">
    ${svg`<text x=${proy([-83.35, 10.95])[0]} y=${proy([-83.35, 10.95])[1]} class="mar">Mar Caribe</text>
    <text x=${proy([-85.55, 8.55])[0]} y=${proy([-85.55, 8.55])[1]} class="mar">Océano Pacífico</text>
    <path d=${camino(pais)} fill="var(--niebla)" stroke="var(--trazo)" stroke-width="1" stroke-linejoin="round"/>
    ${provincias ? provincias.features.map((f) => svg`<path d=${camino(f)} class="provincia" />`) : ""}
    ${provincias && width >= 380 ? provincias.features.map((f) => {
      const [x, y] = proy(ETIQUETA_PROVINCIA[f.properties.nombre] ?? d3.geoCentroid(f));
      return svg`<text x=${x} y=${y} class="nombre-provincia">${f.properties.nombre}</text>`;
    }) : ""}
    ${puntos.map((p) => Math.hypot(p.x - p.x0, p.y - p.y0) > 2 ? svg`<line x1=${p.x0} y1=${p.y0} x2=${p.x} y2=${p.y} stroke="var(--trazo)" stroke-width="1" />
      <circle cx=${p.x0} cy=${p.y0} r="2" fill="var(--grafito)" />` : "")}
    ${puntos.map(({o, x, y}) => svg`<a href=${`./obra.html?id=${o.obra_id}`} tabindex="-1" data-obra=${o.obra_id}
      class=${`pin ${o.estado}${activo && !activo.has(o.obra_id) ? " atenuado" : ""}`} transform=${`translate(${x - tam / 2},${y - tam / 2})`}>
      <title>${`${o.orden}. ${o.nombre} (${o.canton}): ${ESTADO_OBRA[o.estado].label.toLowerCase()}`}</title>
      ${iconoEstado(o.estado, o.orden, tam)}</a>`)}
    ${width >= 420 ? puntos.map(({o, x, y}) => svg`<text x=${x + tam / 2 + 4} y=${y + 4} class=${`canton-pin${activo && !activo.has(o.obra_id) ? " atenuado" : ""}`} aria-hidden="true">${o.canton}</text>`) : ""}`}
  </svg>`;
}
