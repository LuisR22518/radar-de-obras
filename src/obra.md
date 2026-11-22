---
title: Análisis de obra
---

<div class="banner">Prototipo académico · detecciones simuladas con el formato real de dIAra · obras y contratistas seudonimizados</div>

```js
import {Plot, num, fecha, fechaLarga, hora, millones, ESTADOS, escalaEstados, leyendaEstados, SENALES, nombreSenal, asegurarRayado} from "./components/radar.js";
asegurarRayado();
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const fichas = await FileAttachment("data/obras.csv").csv({typed: true});
const diario = await FileAttachment("data/estado_diario.csv").csv({typed: true});
const semanal = await FileAttachment("data/matriz_semanal.csv").csv({typed: true});
const serie = await FileAttachment("data/serie_avance.csv").csv({typed: true});
const eventos = await FileAttachment("data/eventos.csv").csv({typed: true});
const evidencia = await FileAttachment("data/evidencia.csv").csv({typed: true});
const resumen = await FileAttachment("data/resumen.json").json();
const porId = new Map(senales.map((d) => [d.obra_id, d]));
const fichaPorId = new Map(fichas.map((d) => [d.obra_id, d]));
const DIA = 864e5;
const corte = new Date(`${resumen.fecha_corte}T00:00:00Z`);
const inicioMonitoreo = d3.min(diario, (d) => d.fecha);
```

```js
const pedida = new URLSearchParams(location.search).get("id");
const selector = Inputs.select(senales.map((d) => d.obra_id), {
  label: "Obra", value: porId.has(pedida) ? pedida : senales[0].obra_id,
  format: (id) => `${id} · ${porId.get(id).nombre}`
});
const obraId = view(selector);
```

```js
history.replaceState(null, "", `?id=${obraId}`);
const o = porId.get(obraId);
const ficha = fichaPorId.get(obraId);
const dias = diario.filter((d) => d.obra_id === obraId);
const ultimas4 = dias.filter((d) => d.fecha > new Date(+corte - 28 * DIA));
const habiles4 = ultimas4.filter((d) => d.es_habil);
const ultimoActivo = d3.max(dias.filter((d) => d.estado === "actividad"), (d) => d.fecha);
const alertas = o.alertas ? String(o.alertas).split(";") : [];
```

## ${o.obra_id} · ${o.nombre}

<p class="nota">${o.tipo} · ${o.canton} · ${o.institucion_ejecutora} · ${o.contratista} · prioridad ${o.prioridad} de ${senales.length}</p>

<div class="grid grid-cols-4">
  <div class="card"><h3>Puntaje de atención</h3><span class="big">${Math.round(o.puntaje)}</span><span class="muted"> / 100</span></div>
  <div class="card"><h3>Monto vigente</h3><span class="big">${millones(o.monto_vigente_crc)}</span><br><span class="muted">${o.aumento_monto_pct > 0 ? `original ${millones(o.monto_original_crc)} (+${num(o.aumento_monto_pct)} %)` : "sin modificaciones"}</span></div>
  <div class="card"><h3>Plazo</h3><span class="big">${fecha(ficha.fecha_inicio)} → ${fechaLarga(o.fecha_fin_vigente)}</span><br><span class="muted">${o.prorroga_reciente ? "incluye una prórroga reciente" : o.fase === "terminada" ? "obra terminada" : "plazo original"}</span></div>
  <div class="card"><h3>Avance al ${fecha(o.fecha_ultimo_informe)}</h3><span class="big">${num(o.avance_reportado_pct)} %</span><span class="muted"> reportado</span><br><span class="muted">el cronograma vigente preveía ${num(o.avance_previsto_pct)} %</span></div>
</div>

```js
const textoAlerta = {
  inactividad: () => `${o.racha_inactividad_dias} días hábiles seguidos sin actividad con la cámara funcionando.` +
    (o.explicacion_inactividad ? ` Posible explicación: ${o.explicacion_inactividad}.` : " No hay feriado, suspensión ni lluvia fuerte que lo explique."),
  atraso: () => `${num(o.atraso_pts)} puntos de atraso: la ejecutora reporta ${num(o.avance_reportado_pct)} % y el cronograma vigente preveía ${num(o.avance_previsto_pct)} %.`,
  brecha: () => `El avance reportado subió ${num(o.incremento_reportado_pts)} puntos en 12 semanas, pero solo ${Math.round(100 * o.proporcion_semanas_activas)} % de las semanas tuvo actividad observada.`,
  contrato: () => [o.aumento_monto_pct > 0 ? `aumento de monto de ${o.aumento_monto_pct} %` : "", o.prorroga_reciente ? "prórroga aprobada en los últimos 90 días" : ""].filter(Boolean).join(" y ") + ".",
  ciudadania: () => `${o.reportes_30d} reportes ciudadanos en los últimos 30 días.`
};
const queSabemos = [
  `En las últimas 4 semanas hubo actividad en ${habiles4.filter((d) => d.estado === "actividad").length} de ${habiles4.length} días hábiles.`,
  ultimoActivo ? `El último día con actividad fue el ${fechaLarga(ultimoActivo)}.` : "No se observó actividad en el período.",
  `La cámara envió en promedio ${Math.round(100 * d3.mean(ultimas4, (d) => d.cobertura))} % de las fotos esperadas en esas 4 semanas.`,
  `Último informe de la ejecutora: ${num(o.avance_reportado_pct)} % al ${fechaLarga(o.fecha_ultimo_informe)}.`
];
const noSePuede = [
  "Si la obra avanza físicamente: la cámara mide presencia de personas y máquinas, no avance.",
  "Qué pasa fuera del ángulo de la cámara.",
  "Si hay una irregularidad: la señal solo indica que conviene revisar.",
  "El modelo detecta unas 85 de cada 100 personas visibles y se entrenó solo con imágenes de la Escuela de Pocosí."
];
const nSinDatos = dias.filter((d) => d.estado === "sin_datos").length;
if (nSinDatos) noSePuede.push(nSinDatos === 1 ? "Lo ocurrido en el día sin datos de la cámara." : `Lo ocurrido en los ${nSinDatos} días sin datos de la cámara.`);
```

<div class="card">
  <h2>${o.en_cola_dispositivos ? "Cámara sin datos" : alertas.length ? "Por qué amerita revisión" : "Sin alertas"}</h2>
  ${o.en_cola_dispositivos ? html`<p><span class="chip disp">Cola de dispositivos</span> La cámara lleva <strong>${o.dias_sin_datos} días</strong> sin enviar datos (última captura: ${fecha(o.ultima_captura)}, ${hora(o.ultima_captura)}). Primero hay que repararla.</p>` : ""}
  ${alertas.map((a) => html`<p><span class="chip alerta">${nombreSenal[a]}</span> ${textoAlerta[a]()}</p>`)}
  ${!alertas.length && !o.en_cola_dispositivos ? html`<p>Ninguna señal supera su umbral${o.fase === "terminada" ? ": la obra ya fue recibida" : ""}.</p>` : ""}
  <div class="saber">
    <div><h4>Qué sabemos</h4><ul>${queSabemos.map((t) => html`<li>${t}</li>`)}</ul></div>
    <div><h4>Qué no se puede concluir</h4><ul>${noSePuede.map((t) => html`<li>${t}</li>`)}</ul></div>
  </div>
</div>

```js
function lineaTiempo(width) {
  const datos = dias.map((d) => ({...d, estadoVista: ESTADOS[d.fase === "terminada" && d.estado !== "actividad" ? "terminada" : d.estado].label}));
  const ev = eventos.filter((e) => e.obra_id === obraId || e.obra_id === "*");
  const susp = dias.filter((d) => d.suspendido);
  const dominio = [inicioMonitoreo, new Date(+corte + DIA)];
  const categoria = {contrato: "Contrato", ciudadania: "Reporte ciudadano", feriado: "Feriado"};
  return Plot.plot({
    width, height: 170, marginLeft: 120, marginTop: 10,
    x: {type: "utc", domain: dominio, label: null, tickFormat: fecha},
    y: {domain: [0, 2.1], axis: null},
    color: escalaEstados(),
    symbol: {domain: Object.values(categoria), range: ["diamond2", "triangle2", "square2"], legend: true},
    marks: [
      Plot.rect(susp, {x1: "fecha", x2: (d) => new Date(+d.fecha + DIA), y1: 0, y2: 2, fill: "var(--tinte)"}),
      Plot.rect(datos, {
        x1: "fecha", x2: (d) => new Date(+d.fecha + 0.88 * DIA), y1: 0, y2: 1, fill: "estadoVista",
        stroke: "var(--vacio-borde)", strokeWidth: 0.5,
        title: (d) => `${fechaLarga(d.fecha)}: ${d.estadoVista}\nCobertura ${Math.round(100 * d.cobertura)} % · ${Math.round(100 * d.pct_actividad)} % de fotos con actividad` +
          (d.explicacion ? `\nContexto: ${d.explicacion}` : ""), tip: true
      }),
      Plot.dot(datos.filter((d) => d.explicacion), {x: (d) => new Date(+d.fecha + 0.44 * DIA), y: 0.5, r: 2.5, fill: "var(--theme-foreground-muted)"}),
      Plot.dot(ev, {
        x: (d) => new Date(+d.fecha + 0.44 * DIA), y: 1.5, symbol: (d) => categoria[d.categoria], r: 6,
        stroke: "var(--theme-foreground)", fill: "var(--theme-background)",
        title: (d) => `${fechaLarga(d.fecha)} · ${categoria[d.categoria]}\n${d.detalle}`, tip: true
      }),
      Plot.ruleX([new Date(+corte + DIA)], {stroke: "var(--theme-foreground-muted)", strokeDasharray: "3,3"}),
      Plot.text(["Estado del día", "Eventos"], {x: dominio[0], y: [0.5, 1.5], text: (d) => d, textAnchor: "end", dx: -8, fill: "var(--theme-foreground-muted)"})
    ]
  });
}

function lluvia(width) {
  const dominio = [inicioMonitoreo, new Date(+corte + DIA)];
  return Plot.plot({
    width, height: 110, marginLeft: 120, marginTop: 8,
    x: {type: "utc", domain: dominio, label: null, tickFormat: fecha},
    y: {label: "Lluvia (mm)", grid: true, ticks: 3},
    marks: [
      Plot.rectY(dias, {x1: "fecha", x2: (d) => new Date(+d.fecha + 0.8 * DIA), y: "lluvia_mm", fill: "var(--s1)", rx: 1,
        title: (d) => `${fechaLarga(d.fecha)}: ${d.lluvia_mm} mm`, tip: true}),
      Plot.ruleY([20], {stroke: "var(--theme-foreground-muted)", strokeDasharray: "3,3"}),
      Plot.text([20], {x: dominio[1], y: 20, text: () => "lluvia fuerte (20 mm)", textAnchor: "end", dy: -6, fill: "var(--theme-foreground-muted)"})
    ]
  });
}
```

<div class="card">
  <h2>Línea de tiempo · tarea 5: ¿la alerta tiene explicación?</h2>
  <h3>Cada día de las últimas 12 semanas, con feriados, eventos del contrato, reportes ciudadanos y lluvia</h3>
  ${leyendaEstados(html)}
  ${resize((width) => lineaTiempo(width))}
  ${resize((width) => lluvia(width))}
  <p class="nota">La franja azul clara marca días con suspensión aprobada. ● = el día sin actividad tiene una explicación posible. Lluvia: ${resumen.origen_clima.join(", ")}.</p>
</div>

```js
function contraste(width) {
  const s = serie.filter((d) => d.obra_id === obraId);
  const nombres = {previsto: "Previsto (cronograma vigente)", reportado: "Reportado por la ejecutora", pagado: "Pagado"};
  const datos = s.map((d) => ({...d, nombre: nombres[d.serie]}));
  const dominio = [ficha.fecha_inicio, d3.max(s, (d) => d.fecha)];
  const ultimo = datos.filter((d) => d.serie === "reportado").at(-1);
  const prevEnUltimo = o.avance_previsto_pct;
  return Plot.plot({
    width, height: 280, marginLeft: 50, marginRight: 30,
    x: {type: "utc", domain: dominio, label: null, tickFormat: (d) => `${fecha(d)}`},
    y: {domain: [0, 100], label: "↑ Avance o pago (% del contrato)", grid: true},
    color: {domain: Object.values(nombres), range: ["var(--previsto)", "var(--s1)", "var(--s2)"], legend: true},
    marks: [
      Plot.rect([0], {x1: inicioMonitoreo, x2: new Date(+corte + DIA), y1: 0, y2: 100, fill: "var(--tinte)"}),
      Plot.text([0], {x: inicioMonitoreo, y: 97, text: () => "con cámara", dx: 4, textAnchor: "start", fill: "var(--theme-foreground-muted)"}),
      Plot.line(datos.filter((d) => d.serie === "previsto"), {x: "fecha", y: "valor_pct", stroke: "nombre", strokeDasharray: "5,4", strokeWidth: 2}),
      Plot.line(datos.filter((d) => d.serie === "pagado"), {x: "fecha", y: "valor_pct", stroke: "nombre", curve: "step-after", strokeWidth: 2}),
      Plot.line(datos.filter((d) => d.serie === "reportado"), {x: "fecha", y: "valor_pct", stroke: "nombre", strokeWidth: 2}),
      Plot.dot(datos.filter((d) => d.serie !== "previsto"), {x: "fecha", y: "valor_pct", fill: "nombre", r: 4, stroke: "var(--theme-background)",
        title: (d) => `${d.nombre}\n${fechaLarga(d.fecha)}: ${d.valor_pct} %`, tip: true}),
      ultimo && o.atraso_pts >= 5 ? Plot.link([0], {x1: ultimo.fecha, x2: ultimo.fecha, y1: ultimo.valor_pct, y2: prevEnUltimo, stroke: "var(--critico)", strokeWidth: 1.5, markerStart: "dot", markerEnd: "dot"}) : null,
      ultimo && o.atraso_pts >= 5 ? Plot.text([0], {x: ultimo.fecha, y: (ultimo.valor_pct + prevEnUltimo) / 2, text: () => `${num(o.atraso_pts)} pts de atraso`, dx: 8, textAnchor: "start", fill: "var(--theme-foreground)"}) : null
    ]
  });
}

function franjaSemanas(width) {
  const s = serie.filter((d) => d.obra_id === obraId);
  const dominio = [ficha.fecha_inicio, d3.max(s, (d) => d.fecha)];
  const datos = semanal.filter((d) => d.obra_id === obraId).map((d) => ({...d, estado: ESTADOS[d.estado_semana].label}));
  return Plot.plot({
    width, height: 64, marginLeft: 50, marginRight: 30, marginTop: 4,
    x: {type: "utc", domain: dominio, axis: null},
    y: {axis: null},
    color: escalaEstados(),
    marks: [
      Plot.rect(datos, {x1: "semana", x2: (d) => new Date(+d.semana + 6.3 * DIA), y1: 0, y2: 1, fill: "estado", stroke: "var(--vacio-borde)", strokeWidth: 0.5,
        title: (d) => `Semana del ${fecha(d.semana)}: ${d.estado}`, tip: true}),
      Plot.text([0], {frameAnchor: "left", text: () => "Actividad observada por semana", dx: 2, dy: 22, fill: "var(--theme-foreground-muted)"})
    ]
  });
}
```

<div class="card">
  <h2>Contraste · tarea 6: ¿lo reportado coincide con lo observado?</h2>
  <h3>Avance previsto, avance reportado y pagos; abajo, la actividad que vio la cámara cada semana</h3>
  ${resize((width) => contraste(width))}
  ${resize((width) => franjaSemanas(width))}
  <p class="nota">La actividad observada no mide el avance físico: sirve para detectar avances reportados que la cámara no respalda.</p>
</div>

```js
const evObra = evidencia.filter((d) => d.obra_id === obraId);
const diasEvidencia = [...new Set(evObra.map((d) => String(d.fecha_hora).slice(0, 10)))].sort().reverse();
const estadoPorDia = new Map(dias.map((d) => [d.fecha.toISOString().slice(0, 10), d]));
const selectorDia = Inputs.select(diasEvidencia, {
  label: "Día",
  format: (d) => `${fecha(d)} · ${ESTADOS[estadoPorDia.get(d)?.estado ?? "sin_datos"].label.toLowerCase()}`
});
const diaEvidencia = Generators.input(selectorDia);
```

```js
function marco(nombre, filas) {
  const esc = 0.25;
  const W = 1280 * esc, H = 1024 * esc;
  const dets = filas.filter((d) => d.clase);
  const svg = d3.create("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("width", "100%").attr("role", "img")
    .attr("aria-label", `Foto ${hora(filas[0].fecha_hora)}: ${dets.length} detecciones`);
  svg.append("rect").attr("x", 0.5).attr("y", 0.5).attr("width", W - 1).attr("height", H - 1).attr("rx", 4).attr("fill", "var(--theme-background)").attr("stroke", "var(--theme-foreground-faint)");
  svg.append("text").attr("x", W / 2).attr("y", H / 2).attr("text-anchor", "middle").attr("fill", "var(--theme-foreground-faint)")
    .attr("font-size", 12).text("foto no disponible (dato simulado)");
  for (const d of dets) {
    const color = d.clase === "Persona" ? "var(--s1)" : "var(--s2)";
    svg.append("rect").attr("x", d.x1 * esc).attr("y", d.y1 * esc).attr("width", (d.x2 - d.x1) * esc).attr("height", (d.y2 - d.y1) * esc)
      .attr("fill", "none").attr("stroke", color).attr("stroke-width", 1.5)
      .append("title").text(`${d.clase} · probabilidad ${d.probabilidad.toFixed(2)}`);
  }
  const personas = dets.filter((d) => d.clase === "Persona").length;
  const maquinas = dets.length - personas;
  return html`<figure style="margin: 0;">${svg.node()}<figcaption>${hora(filas[0].fecha_hora)} · ${personas} ${personas === 1 ? "persona" : "personas"} · ${maquinas} ${maquinas === 1 ? "máquina" : "máquinas"}<br><span class="muted">${nombre}</span></figcaption></figure>`;
}
const imagenesDia = d3.groups(evObra.filter((d) => String(d.fecha_hora).startsWith(diaEvidencia)), (d) => d.nombre_imagen);
```

<div class="card">
  <h2>Evidencia · tarea 7: ¿la evidencia sostiene la alerta?</h2>
  <h3>Cuatro fotos del día (cerca de las 8, 10, 13 y 15 h) con los recuadros que detectó el modelo</h3>
  ${selectorDia}
  <div class="fotos">${imagenesDia.map(([nombre, filas]) => marco(nombre, filas))}</div>
  ${imagenesDia.length ? "" : html`<p>Ese día la cámara no envió fotos.</p>`}
  <p class="nota"><span style="color: var(--s1)">▭</span> persona · <span style="color: var(--s2)">▭</span> maquinaria. Pasa el cursor por un recuadro para ver su probabilidad. Como las detecciones son simuladas, no hay fotos: se muestran los recuadros del CSV sobre un marco de 1280 × 1024.</p>
  <details><summary>Ver una foto real de muestra de una cámara de dIAra</summary>
    <img src="./data/ejemplo-camara-diara.jpg" alt="Foto real de una cámara de dIAra en el piloto: terreno en movimiento de tierras con una vagoneta y un cargador al fondo y un trabajador de espaldas." style="max-width: 640px; width: 100%; border-radius: 6px;">
    <p class="nota">Imagen 20240319-085919.jpg del repositorio público de dIAra (CGR y Universidad CENFOTEC), piloto de 2024.</p>
  </details>
</div>

```js
function comparacion(width) {
  const datos = senales.filter((d) => d.fase !== "terminada" && !d.en_cola_dispositivos)
    .map((d) => ({...d, grupo: d.obra_id === obraId ? "Esta obra" : "Otras obras"}));
  return Plot.plot({
    width, height: 110, marginLeft: 20, marginRight: 20,
    x: {domain: [0, 1], label: "Proporción de semanas con actividad observada →", tickFormat: "%", grid: true},
    y: {axis: null},
    color: {domain: ["Esta obra", "Otras obras"], range: ["var(--s1)", "var(--theme-foreground-faint)"], legend: true},
    marks: [
      Plot.dot(datos, Plot.dodgeY({x: "proporcion_semanas_activas", fill: "grupo", r: 8, stroke: "var(--theme-background)", strokeWidth: 2,
        title: (d) => `${d.obra_id} · ${d.nombre}: ${Math.round(100 * d.proporcion_semanas_activas)} %`, tip: true})),
      Plot.text(datos, Plot.dodgeY({x: "proporcion_semanas_activas", r: 8, text: "obra_id", fill: (d) => (d.obra_id === obraId ? "white" : "var(--theme-foreground)"), fontSize: 10}))
    ]
  });
}
```

<div class="card">
  <h2>Comparación con el resto de la cartera</h2>
  <h3>¿Es atípica la actividad de esta obra?</h3>
  ${resize((width) => comparacion(width))}
</div>

```js
const clave = `radar-decision-${obraId}`;
let guardado = null;
try { guardado = JSON.parse(localStorage.getItem(clave) ?? "null"); } catch {}
guardado ??= {estado: "Nueva", motivo: "", nota: ""};
const formDecision = Inputs.form({
  estado: Inputs.radio(["Nueva", "En análisis", "Descartada", "Remitida"], {label: "Estado de la alerta", value: guardado.estado}),
  motivo: Inputs.select(["", "Feriado o lluvia", "Suspensión aprobada", "Falla de cámara", "Obra terminada", "Otro"], {label: "Motivo si se descarta", value: guardado.motivo}),
  nota: Inputs.textarea({label: "Nota del auditor", value: guardado.nota, rows: 3, width: 520})
});
const decision = Generators.input(formDecision);
```

```js
try { localStorage.setItem(clave, JSON.stringify({...decision, actualizado: new Date().toISOString()})); } catch {}

function expedienteCSV() {
  const esc = (v) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  const filas = [
    ["Expediente del Radar de Obras (prototipo académico; detecciones simuladas)"],
    ["Fecha de corte", resumen.fecha_corte], ["Generado", new Date().toISOString()], [],
    ["Obra", `${o.obra_id} · ${o.nombre}`], ["Tipo", o.tipo], ["Cantón", o.canton],
    ["Institución ejecutora", o.institucion_ejecutora], ["Contratista", o.contratista],
    ["Monto vigente (CRC)", o.monto_vigente_crc], ["Fin vigente", o.fecha_fin_vigente], [],
    ["Puntaje de atención", o.puntaje], ["Prioridad", o.prioridad],
    ...SENALES.map((s) => [`Señal: ${s.label}`, o[`senal_${s.key}`], `peso ${resumen.pesos[s.key]}`]),
    ["Alertas", alertas.map((a) => textoAlerta[a]()).join(" | ")], [],
    ["Decisión del auditor", decision.estado], ["Motivo", decision.motivo], ["Nota", decision.nota], [],
    ["Fecha", "Estado del día", "Cobertura de la cámara", "Fotos con actividad", "Contexto"],
    ...dias.map((d) => [d.fecha.toISOString().slice(0, 10), ESTADOS[d.estado].label, d.cobertura, d.pct_actividad, d.explicacion]),
    [], ["Metodología", "Estado diario: sin datos si llega menos del 50 % de las fotos; actividad si 15 % o más de las fotos laborales tienen detecciones. Detalle en la página Metodología y datos."]
  ];
  return filas.map((f) => f.map(esc).join(",")).join("\n");
}
function descargar() {
  const blob = new Blob(["﻿" + expedienteCSV()], {type: "text/csv;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `expediente-obra-${obraId}-${resumen.fecha_corte}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}
```

<div class="card">
  <h2>Registro y expediente · tarea 8: ¿qué decidí y con qué respaldo?</h2>
  <h3>La decisión se guarda en este navegador; el expediente sirve como papel de trabajo (normas 208.02 y 208.04)</h3>
  ${formDecision}
  <p class="no-imprimir">${Inputs.button("Descargar expediente (CSV)", {reduce: descargar})} ${Inputs.button("Imprimir o guardar en PDF", {reduce: () => window.print()})}</p>
</div>
