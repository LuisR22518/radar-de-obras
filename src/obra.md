---
title: Análisis de obra
---

```js
import {Plot, grafico, fecha, fechaLarga, fechaTexto, hora, num, millones, plural, ESTADOS, escalaEstados, leyendaEstados, SENALES, razones, pulso, ESTADO_OBRA, ordenar, razonesCortas, iconoEstado, asegurarRayado, estiloPlot, esReal, tieneDato} from "./components/lupia.js";
asegurarRayado();
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const fichas = await FileAttachment("data/obras.csv").csv({typed: true});
const diario = await FileAttachment("data/estado_diario.csv").csv({typed: true});
const semanal = await FileAttachment("data/matriz_semanal.csv").csv({typed: true});
const serie = await FileAttachment("data/serie_avance.csv").csv({typed: true});
const eventos = await FileAttachment("data/eventos.csv").csv({typed: true});
const evidencia = await FileAttachment("data/evidencia.csv").csv({typed: true});
const resumen = await FileAttachment("data/resumen.json").json();
const lista = ordenar(senales, resumen.pesos);
const porId = new Map(lista.map((d) => [d.obra_id, d]));
const fichaPorId = new Map(fichas.map((d) => [d.obra_id, d]));
const DIA = 864e5;
// Fotos reales del piloto (con las personas difuminadas): se declaran una por una para que se publiquen
const FOTOS = {
  "20240319-085758.jpg": FileAttachment("data/fotos-piloto/20240319-085758.jpg"),
  "20240319-085919.jpg": FileAttachment("data/fotos-piloto/20240319-085919.jpg"),
  "20240319-090039.jpg": FileAttachment("data/fotos-piloto/20240319-090039.jpg"),
  "20240319-090159.jpg": FileAttachment("data/fotos-piloto/20240319-090159.jpg"),
  "20240319-090319.jpg": FileAttachment("data/fotos-piloto/20240319-090319.jpg"),
  "20240319-090439.jpg": FileAttachment("data/fotos-piloto/20240319-090439.jpg")
};
```

```js
const pedida = new URLSearchParams(location.search).get("id");
const selector = Inputs.select(lista.map((d) => d.obra_id), {
  label: "Ir a otra obra", value: porId.has(pedida) ? pedida : lista[0].obra_id,
  format: (id) => `${porId.get(id).orden}. ${porId.get(id).nombre}`
});
const obraId = Generators.input(selector);
```

```js
history.replaceState(null, "", `?id=${obraId}${location.hash}`);
const o = porId.get(obraId);
const ficha = fichaPorId.get(obraId);
const siguiente = lista[o.orden % lista.length];
const dias = diario.filter((d) => d.obra_id === obraId);
// Cada obra se mira en su propio período con cámara (la del piloto es de 2024)
const corte = o.fecha_corte_obra;
const inicioMonitoreo = d3.min(dias, (d) => d.fecha);
const finVentana = new Date(+corte + DIA);
const real = esReal(o);
const ultimas4 = dias.filter((d) => d.fecha > new Date(+corte - 28 * DIA));
const habiles4 = ultimas4.filter((d) => d.es_habil && d.estado !== "sin_datos");
const ultimoActivo = d3.max(dias.filter((d) => d.estado === "actividad"), (d) => d.fecha);
const semanas12 = semanal.filter((d) => d.obra_id === obraId).sort((a, b) => a.semana - b.semana).slice(-12);
// Días de la racha actual de inactividad (los mismos que cuenta la regla en Python)
const racha = [];
for (const d of [...dias].sort((a, b) => b.fecha - a.fecha)) {
  if (!d.es_habil || d.estado === "sin_datos") continue;
  if (d.estado === "actividad") break;
  racha.push(d);
}
const nSinDatos = dias.filter((d) => d.estado === "sin_datos").length;
const porQue = o.estado === "revisar" ? razones(o)
  : o.estado === "historico" ? [
      {texto: `La cámara estuvo en la obra del ${fechaLarga(o.periodo_desde)} al ${fechaLarga(o.fecha_corte_obra)}; ya no envía datos.`},
      ...(real ? [{texto: `dIAra publicó ${plural(o.dias_con_datos, "día", "días")} de ese período, con objetos etiquetados por personas.`}] : [])]
  : [{texto: o.estado === "sin_datos"
      ? `No llegan fotos desde el ${fechaLarga(o.ultima_captura)} (${plural(o.dias_sin_datos, "día", "días")}). Primero hay que reparar la cámara.`
      : o.fase === "terminada" ? "La obra ya fue recibida: no genera alertas." : "Ninguna de las cinco señales pasa su límite."}];
const conAvance = tieneDato(o.avance_reportado_pct) && tieneDato(o.avance_previsto_pct);
const queSabemos = [
  o.estado === "sin_datos" ? `Antes de la falla, la cámara mostraba actividad normal.`
    : `En las últimas 4 semanas con cámara hubo actividad en ${habiles4.filter((d) => d.estado === "actividad").length} de ${habiles4.length} días hábiles con datos.`,
  ultimoActivo ? `El último día con actividad fue el ${fechaLarga(ultimoActivo)}.` : "No se observó actividad en el período.",
  conAvance ? `La ejecutora reporta ${num(o.avance_reportado_pct)}\u00a0% de avance; el cronograma prevé ${num(o.avance_previsto_pct)}\u00a0%.`
    : "No hay contrato ni informes de avance registrados para esta obra."
];
const noSePuede = [
  "Cuánto avanzó la obra: la cámara ve personas y máquinas, no avance físico.",
  real ? `Qué pasó en los ${nSinDatos} días sin archivo: los datos públicos no dicen si no hubo trabajo o si la cámara estaba apagada.`
    : nSinDatos ? `Qué pasó fuera del ángulo de la cámara, ni en ${nSinDatos === 1 ? "el día" : `los ${nSinDatos} días`} sin datos.` : "Qué pasa fuera del ángulo de la cámara.",
  "Si hay una irregularidad: LupIA solo indica dónde conviene revisar."
];
const sinDato = () => html`<span class="tenue">Sin dato</span>`;
```

<div class="ficha-barra no-imprimir">
  <a class="volver" href="./index.html">Volver a la lista</a>
  <div class="ir">${selector}${html`<a class="boton secundario" href=${`./obra.html?id=${siguiente.obra_id}`}>Siguiente obra</a>`}</div>
</div>

<section class="ficha-cabeza" aria-labelledby="nombre-obra">
  <div>
    <p class="estado">${iconoEstado(o.estado, o.orden, 24)}${o.estado === "revisar" ? html`<span class="marca">${ESTADO_OBRA[o.estado].label}</span>` : ESTADO_OBRA[o.estado].label}<span class="posicion">Número ${o.orden} de ${lista.length} en la lista</span></p>
    <h1 id="nombre-obra">${o.nombre}</h1>
    <p class="lugar">${o.tipo} en ${o.canton}, ${o.provincia}. Obra ${o.obra_id}.</p>
    <p class="procedencia">${real
      ? html`<span class="etiqueta-real">Datos reales</span> Detecciones del piloto de dIAra, etiquetadas por personas. El contrato de esta obra no es público.`
      : html`<span class="etiqueta-simulada">Simulada</span> Lo que ve su cámara se arma con fotos reales del piloto de dIAra; el contrato y los informes son ficticios.`}</p>
    <h2>${o.estado === "revisar" ? "Por qué necesita revisión" : "Situación"}</h2>
    <ul class="razones">${porQue.map((r) => html`<li class=${r.explicada ? "explicada" : ""}>${r.texto}</li>`)}</ul>
  </div>
  <dl class="datos-clave">
    <div><dt>Institución ejecutora</dt><dd>${o.institucion_ejecutora}</dd></div>
    <div><dt>Contratista</dt><dd>${o.contratista || sinDato()}</dd></div>
    <div><dt>Monto vigente</dt><dd>${tieneDato(o.monto_vigente_crc) ? html`${millones(o.monto_vigente_crc)}<small>${o.aumento_monto_pct > 0 ? `Original ${millones(o.monto_original_crc)}` : "Sin cambios"}</small>` : sinDato()}</dd></div>
    <div><dt>Termina</dt><dd>${o.fecha_fin_vigente ? html`${fechaLarga(o.fecha_fin_vigente)}<small>${o.fase === "terminada" ? "Obra recibida" : o.prorroga_reciente ? "Con prórroga reciente" : "Plazo original"}</small>` : sinDato()}</dd></div>
    <div><dt>Avance reportado</dt><dd>${tieneDato(o.avance_reportado_pct) ? html`${num(o.avance_reportado_pct)}&nbsp;%<small>Al ${fechaLarga(o.fecha_ultimo_informe)}</small>` : sinDato()}</dd></div>
    <div><dt>Avance previsto</dt><dd>${tieneDato(o.avance_previsto_pct) ? html`${num(o.avance_previsto_pct)}&nbsp;%<small>Según el cronograma vigente</small>` : sinDato()}</dd></div>
  </dl>
</section>

```js
const PESTANAS = [["resumen", "Resumen"], ["actividad", "Actividad diaria"], ["avance", "Avance y pagos"], ["fotos", "Fotos"], ["decision", "Hallazgo y acción"]];
const claves = PESTANAS.map(([k]) => k);
const pestanas = html`<div class="pestanas" role="tablist" aria-label="Análisis de la obra">${PESTANAS.map(([k, t]) =>
  html`<button type="button" role="tab" id=${`t-${k}`} aria-controls=${`p-${k}`} data-k=${k}>${t}</button>`)}</div>`;
const desdeEnlace = location.hash.slice(1);
pestanas.value = claves.includes(desdeEnlace) ? desdeEnlace : "resumen";
function elegir(k, enfocar = false) {
  pestanas.value = k;
  if (enfocar) pestanas.querySelector(`[data-k="${k}"]`).focus();
  pestanas.dispatchEvent(new Event("input", {bubbles: true}));
}
pestanas.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) elegir(b.dataset.k); });
pestanas.addEventListener("keydown", (e) => {
  const i = claves.indexOf(pestanas.value);
  const destino = {ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: claves.length - 1}[e.key];
  if (destino == null) return;
  e.preventDefault();
  elegir(claves[(destino + claves.length) % claves.length], true);
});
const alCambiarEnlace = () => { const k = location.hash.slice(1); if (claves.includes(k) && k !== pestanas.value) elegir(k); };
addEventListener("hashchange", alCambiarEnlace);
invalidation.then(() => removeEventListener("hashchange", alCambiarEnlace));
const pestana = Generators.input(pestanas);
```

```js
// Muestra solo la pestaña elegida y la recuerda en el enlace (#fotos, #decision...)
for (const k of claves) {
  const boton = pestanas.querySelector(`[data-k="${k}"]`);
  boton.setAttribute("aria-selected", String(k === pestana));
  boton.tabIndex = k === pestana ? 0 : -1;
  document.getElementById(`p-${k}`).hidden = k !== pestana;
}
history.replaceState(null, "", `${location.search}${pestana === "resumen" ? "" : `#${pestana}`}`);
```

<div class="contenedor-pestanas">${pestanas}</div>

<section class="pestana" id="p-resumen" role="tabpanel" aria-labelledby="t-resumen">
  <h2>Lo esencial</h2>
  <p>Lo que los datos permiten afirmar y lo que no, antes de abrir el detalle.</p>
  <div class="saber">
    <div><h3>Qué sabemos</h3><ul>${queSabemos.map((t) => html`<li>${t}</li>`)}</ul></div>
    <div><h3>Qué no se puede concluir</h3><ul>${noSePuede.map((t) => html`<li>${t}</li>`)}</ul></div>
  </div>
  <h3 style="margin-top: 2.5rem;">Actividad por semana (hasta 12)</h3>
  ${leyendaEstados(["actividad", "sin_actividad", "sin_datos", "terminada"])}
  <div style="margin-top: 0.5rem;">${pulso(semanas12, {celda: 30, alto: 30, sep: 5})}</div>
  <p class="nota-tabla">Cada cuadro es una semana. Un punto marca una semana sin actividad que tiene una explicación posible, como un feriado o lluvia fuerte.</p>
  <p>${html`<button class="boton" type="button" onclick=${() => elegir("actividad")}>Ver la actividad día por día</button>`}</p>
</section>

```js
const CATEGORIA = {contrato: "Evento del contrato", ciudadania: "Reporte ciudadano", feriado: "Feriado"};
function lineaTiempo(width) {
  const datos = dias.map((d) => ({...d, estadoVista: ESTADOS[d.fase === "terminada" && d.estado !== "actividad" ? "terminada" : d.estado].label}));
  const ev = eventos.filter((e) => e.obra_id === obraId || e.obra_id === "*");
  const susp = dias.filter((d) => d.suspendido);
  const inicioRacha = racha.length >= 5 ? d3.min(racha, (d) => d.fecha) : null;
  return grafico({
    width, height: 176, marginLeft: width < 560 ? 64 : 112, marginTop: 24, marginRight: 8, style: estiloPlot,
    x: {type: "utc", domain: [inicioMonitoreo, finVentana], label: null, tickFormat: fecha, ticks: width < 560 ? 4 : 8},
    y: {domain: [0, 2.2], axis: null},
    color: escalaEstados(),
    symbol: {domain: Object.values(CATEGORIA), range: ["diamond2", "triangle2", "square2"], legend: true},
    marks: [
      inicioRacha ? Plot.rect([0], {x1: inicioRacha, x2: finVentana, y1: -0.1, y2: 2.1, fill: "var(--resaltador)", fillOpacity: 0.5}) : null,
      inicioRacha ? Plot.text([0], {x: finVentana, y: 2.2, text: () => `Racha sin actividad: ${plural(racha.length, "día hábil", "días hábiles")}`, textAnchor: "end", fill: "var(--tinta)", fontWeight: 600, dy: -4}) : null,
      Plot.rect(susp, {x1: "fecha", x2: (d) => new Date(+d.fecha + DIA), y1: 1.1, y2: 1.9, fill: "var(--niebla)"}),
      Plot.rect(datos, {
        x1: "fecha", x2: (d) => new Date(+d.fecha + 0.86 * DIA), y1: 0, y2: 1, fill: "estadoVista", stroke: "var(--trazo)", strokeWidth: 0.6,
        title: (d) => `${fechaLarga(d.fecha)}: ${d.estadoVista.toLowerCase()}\n` + (d.cobertura_supuesta
            ? `Hay archivo de ese día (la cámara no reporta cuántas fotos tomó); ${num(100 * d.pct_actividad, 0)}\u00a0% de las fotos esperadas con actividad`
            : d.cobertura == null ? "No hay archivo de ese día"
            : `La cámara envió ${num(100 * d.cobertura, 0)}\u00a0% de las fotos; ${num(100 * d.pct_actividad, 0)}\u00a0% con actividad`) +
          (d.explicacion ? `\nContexto: ${d.explicacion}` : ""), tip: true
      }),
      Plot.dot(datos.filter((d) => d.explicacion && d.estado === "sin_actividad"), {x: (d) => new Date(+d.fecha + 0.43 * DIA), y: 0.5, r: 2, fill: "var(--grafito)"}),
      Plot.dot(ev, {
        x: (d) => new Date(+d.fecha + 0.43 * DIA), y: 1.5, symbol: (d) => CATEGORIA[d.categoria], r: 6, stroke: "var(--tinta)", strokeWidth: 1.5, fill: "var(--papel)",
        title: (d) => `${fechaLarga(d.fecha)}. ${CATEGORIA[d.categoria]}\n${d.detalle}`, tip: true
      }),
      Plot.text([width < 560 ? "Días" : "Estado del día", "Eventos"], {x: inicioMonitoreo, y: [0.5, 1.5], text: (d) => d, textAnchor: "end", dx: -10, fill: "var(--grafito)"})
    ]
  });
}
function lluvia(width) {
  return grafico({
    width, height: 104, marginLeft: width < 560 ? 64 : 112, marginTop: 10, marginRight: 8, style: estiloPlot,
    x: {type: "utc", domain: [inicioMonitoreo, finVentana], label: null, tickFormat: fecha, ticks: width < 560 ? 4 : 8},
    y: {label: "Lluvia (mm)", labelArrow: "none", grid: true, ticks: 3},
    marks: [
      Plot.rectY(dias, {x1: "fecha", x2: (d) => new Date(+d.fecha + 0.78 * DIA), y: "lluvia_mm", fill: "var(--grafito)", fillOpacity: 0.55,
        title: (d) => `${fechaLarga(d.fecha)}: ${num(d.lluvia_mm)} mm`, tip: true}),
      Plot.ruleY([20], {stroke: "var(--tinta)", strokeDasharray: "3,3"}),
      Plot.text([20], {x: finVentana, y: 20, text: () => "Lluvia fuerte: 20 mm", textAnchor: "end", dy: -7, fill: "var(--tinta)", stroke: "var(--papel)", strokeWidth: 4, paintOrder: "stroke"})
    ]
  });
}
```

```js
const eventosObra = eventos.filter((e) => e.obra_id === obraId).sort((a, b) => b.fecha - a.fecha);
```

<section class="pestana" id="p-actividad" role="tabpanel" aria-labelledby="t-actividad" hidden>
  <h2>¿Hubo trabajo en la obra?</h2>
  <p>Cada día del período con cámara (hasta 12 semanas), con los feriados, los eventos del contrato, los reportes ciudadanos y la lluvia.</p>
  ${leyendaEstados()}
  <figure aria-label="Estado de cada día y eventos de la obra">${resize((width) => lineaTiempo(width))}</figure>
  <figure aria-label="Lluvia diaria en la obra">${resize((width) => lluvia(width))}</figure>
  <p class="nota-tabla">La franja resaltada marca la racha actual de días hábiles sin actividad. El gris claro en la fila de eventos marca una suspensión aprobada. Pase el cursor por un día para ver su detalle.</p>
  <h3 style="margin-top: 2rem;">Eventos de esta obra</h3>
  ${eventosObra.length ? html`<ul class="eventos">${eventosObra.map((e) => html`<li><b>${fechaLarga(e.fecha)}.</b> ${e.categoria === "ciudadania" ? "Reporte ciudadano" : "Contrato"}: ${e.detalle}</li>`)}</ul>` : html`<p class="tenue">Sin eventos del contrato ni reportes ciudadanos en el período.</p>`}
</section>

```js
const NOMBRES = {previsto: "Previsto", reportado: "Reportado", pagado: "Pagado"};
function contraste(width) {
  const s = serie.filter((d) => d.obra_id === obraId);
  const dominio = [ficha.fecha_inicio, d3.max(s, (d) => d.fecha)];
  const porSerie = (k) => s.filter((d) => d.serie === k).sort((a, b) => a.fecha - b.fecha);
  // Etiquetas al final de cada línea, separadas para que no se encimen
  const finales = ["previsto", "reportado", "pagado"].map((k) => ({...porSerie(k).filter((d) => d.fecha <= finVentana).at(-1), nombre: NOMBRES[k]}))
    .filter((d) => d.fecha).sort((a, b) => b.valor_pct - a.valor_pct);
  for (let i = 0; i < finales.length; i++) finales[i].y = i ? Math.min(finales[i].valor_pct, finales[i - 1].y - 7) : finales[i].valor_pct;
  const ultimo = porSerie("reportado").at(-1);
  return grafico({
    width, height: 300, marginLeft: 44, marginRight: 84, marginTop: 20, style: estiloPlot,
    x: {type: "utc", domain: dominio, label: null, tickFormat: fecha, ticks: width < 560 ? 4 : 8},
    y: {domain: [0, 100], label: "Avance o pago (% del contrato)", labelArrow: "up", grid: true},
    marks: [
      Plot.rect([0], {x1: inicioMonitoreo, x2: finVentana, y1: 0, y2: 100, fill: "var(--niebla)"}),
      Plot.text([0], {x: inicioMonitoreo, y: 100, text: () => "Período con cámara", dx: 6, dy: 10, textAnchor: "start", fill: "var(--grafito)"}),
      Plot.line(porSerie("previsto"), {x: "fecha", y: "valor_pct", stroke: "var(--trazo)", strokeWidth: 1.75, strokeDasharray: "5,4"}),
      Plot.line(porSerie("pagado"), {x: "fecha", y: "valor_pct", stroke: "var(--grafito)", strokeWidth: 1.5, curve: "step-after"}),
      Plot.line(porSerie("reportado"), {x: "fecha", y: "valor_pct", stroke: "var(--tinta)", strokeWidth: 2.25}),
      Plot.dot([...porSerie("reportado"), ...porSerie("pagado")], {x: "fecha", y: "valor_pct", r: 3.5, fill: (d) => (d.serie === "reportado" ? "var(--tinta)" : "var(--grafito)"), stroke: "var(--papel)",
        title: (d) => `${NOMBRES[d.serie]} al ${fechaLarga(d.fecha)}: ${num(d.valor_pct)}\u00a0%`, tip: true}),
      Plot.text(finales, {x: "fecha", y: "y", text: "nombre", dx: 10, textAnchor: "start", fill: "var(--tinta)", fontWeight: 600}),
      ultimo && o.atraso_pts >= 5 ? Plot.link([0], {x1: ultimo.fecha, x2: ultimo.fecha, y1: ultimo.valor_pct, y2: o.avance_previsto_pct, stroke: "var(--tinta)", strokeWidth: 1.5, markerStart: "tick", markerEnd: "tick"}) : null,
      ultimo && o.atraso_pts >= 5 ? Plot.text([0], {x: ultimo.fecha, y: (ultimo.valor_pct + o.avance_previsto_pct) / 2, text: () => `${num(o.atraso_pts)} puntos de atraso`, dx: -10, textAnchor: "end", fill: "var(--tinta)", fontWeight: 600, stroke: "var(--papel)", strokeWidth: 4, paintOrder: "stroke"}) : null
    ]
  });
}
function franjaSemanas(width) {
  const s = serie.filter((d) => d.obra_id === obraId);
  const dominio = [ficha.fecha_inicio, d3.max(s, (d) => d.fecha)];
  const datos = semanal.filter((d) => d.obra_id === obraId).map((d) => ({...d, estado: ESTADOS[d.estado_semana].label}));
  return grafico({
    width, height: 46, marginLeft: 44, marginRight: 84, marginTop: 4, marginBottom: 6, style: estiloPlot,
    x: {type: "utc", domain: dominio, axis: null}, y: {axis: null}, color: escalaEstados(),
    marks: [
      Plot.rect(datos, {x1: "semana", x2: (d) => new Date(+d.semana + 6.2 * DIA), y1: 0, y2: 1, fill: "estado", stroke: "var(--trazo)", strokeWidth: 0.6,
        title: (d) => `Semana del ${fecha(d.semana)}: ${d.estado.toLowerCase()}`, tip: true}),
      Plot.text([0], {frameAnchor: "left", text: () => "Actividad observada por semana", dx: 0, fill: "var(--grafito)"})
    ]
  });
}
const mediana = d3.median(senales.filter((d) => d.fase !== "terminada" && !d.en_cola_dispositivos && !d.historica), (d) => d.proporcion_semanas_activas);
const conSerie = serie.some((d) => d.obra_id === obraId && d.serie === "previsto");
```

<section class="pestana" id="p-avance" role="tabpanel" aria-labelledby="t-avance" hidden>
  <h2>¿Lo reportado coincide con lo que vio la cámara?</h2>
  <p>Avance previsto por el cronograma, avance reportado por la ejecutora y pagos, frente a la actividad observada cada semana.</p>
  ${conSerie ? html`<figure aria-label="Avance previsto, reportado y pagado de la obra">${resize((width) => contraste(width))}</figure>
  <figure aria-label="Actividad observada por semana">${resize((width) => franjaSemanas(width))}</figure>` : html`<p class="vacio">Esta obra no tiene contrato ni informes de avance en el registro, así que no hay con qué contrastar lo observado. Cuando el gestor de datos los registre, este contraste aparecerá solo.</p>`}
  <p>Esta obra tuvo actividad en <strong>${num(100 * o.proporcion_semanas_activas, 0)}&nbsp;%</strong> de sus semanas con datos (hasta 12). En la obra típica de la cartera, la cifra es ${num(100 * mediana, 0)}&nbsp;%.</p>
  <p class="nota-tabla">La actividad no mide el avance físico: sirve para detectar avances reportados que la cámara no respalda.</p>
</section>

```js
const evObra = evidencia.filter((d) => d.obra_id === obraId);
const diasEvidencia = [...new Set(evObra.map((d) => String(d.fecha_hora).slice(0, 10)))].sort().reverse();
const estadoPorDia = new Map(dias.map((d) => [d.fecha.toISOString().slice(0, 10), d]));
const selectorDia = Inputs.select(diasEvidencia, {
  label: "Día",
  format: (d) => `${fechaLarga(d)}, ${ESTADOS[estadoPorDia.get(d)?.estado ?? "sin_datos"].label.toLowerCase()}`
});
const diaEvidencia = Generators.input(selectorDia);
```

```js
function marco(nombre, filas) {
  const esc = 0.25, W = 1280 * esc, H = 1024 * esc;
  const dets = filas.filter((d) => d.clase);
  const personas = dets.filter((d) => d.clase === "Persona").length;
  const maquinas = dets.length - personas;
  const foto = filas[0].foto ? FOTOS[nombre] : null;
  const lienzo = d3.create("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("width", "100%").attr("role", "img")
    .attr("aria-label", `${foto ? "Foto real" : "Foto"} de las ${hora(filas[0].fecha_hora)}: ${plural(personas, "persona", "personas")} y ${plural(maquinas, "máquina", "máquinas")}`);
  if (foto) {
    lienzo.append("image").attr("href", foto.href).attr("width", W).attr("height", H);
  } else {
    lienzo.append("rect").attr("x", 0.5).attr("y", 0.5).attr("width", W - 1).attr("height", H - 1).attr("rx", 4)
      .attr("fill", "var(--niebla)").attr("stroke", "var(--trazo)");
    lienzo.append("text").attr("x", W / 2).attr("y", H / 2).attr("text-anchor", "middle").attr("fill", "var(--grafito)")
      .attr("font-size", 12).text(dets.length ? "" : "Sin detecciones");
  }
  for (const d of dets) {
    const caja = (g) => g.attr("x", d.x1 * esc).attr("y", d.y1 * esc).attr("width", (d.x2 - d.x1) * esc).attr("height", (d.y2 - d.y1) * esc)
      .attr("fill", "none").attr("stroke-dasharray", d.clase === "Persona" ? null : "4,3");
    if (foto) lienzo.append("rect").call(caja).attr("stroke", "var(--papel)").attr("stroke-width", 3.2);
    lienzo.append("rect").call(caja).attr("stroke", "var(--tinta)").attr("stroke-width", 1.6)
      .append("title").text(`${d.clase}, ${d.probabilidad == null ? "etiqueta humana" : `probabilidad ${num(d.probabilidad, 2)}`}`);
  }
  const origen = filas[0].fuente === "real" ? "etiquetado por personas" : filas[0].imagen_piloto ? `recuadros de la foto ${String(filas[0].imagen_piloto).slice(0, 15)} del piloto` : "";
  return html`<figure>${lienzo.node()}<figcaption><b>${hora(filas[0].fecha_hora)}</b>: ${plural(personas, "persona", "personas")}, ${plural(maquinas, "máquina", "máquinas")}${origen ? html`<br><span class="tenue">${origen}</span>` : ""}</figcaption></figure>`;
}
const imagenesDia = d3.groups(evObra.filter((d) => String(d.fecha_hora).startsWith(diaEvidencia)), (d) => d.nombre_imagen);
```

<section class="pestana" id="p-fotos" role="tabpanel" aria-labelledby="t-fotos" hidden>
  <h2>¿Qué muestran las fotos?</h2>
  <p>${real ? "Fotos del día elegido con los objetos que etiquetaron personas en el piloto de dIAra. El 19 de marzo incluye las fotos reales, con las personas difuminadas." : "Cuatro fotos del día elegido, cerca de las 8, 10, 13 y 15 horas, con lo que detectó el modelo."}</p>
  ${selectorDia}
  <div class="fotos">${imagenesDia.length ? imagenesDia.map(([nombre, filas]) => marco(nombre, filas)) : html`<p class="vacio">Ese día la cámara no envió fotos.</p>`}</div>
  <p class="nota-tabla">Línea continua: persona. Línea punteada: maquinaria. ${real ? "Donde no hay foto publicada, los recuadros se dibujan sobre un marco vacío de 1280 por 1024 píxeles." : "Esta obra es simulada: no tiene fotos propias. Cada foto con actividad repite los objetos de una foto real del piloto de la misma hora, como los habría detectado el modelo, y se dibuja sobre un marco vacío."}</p>
  ${real ? "" : html`<details>
    <summary>Ver una foto real de una cámara de dIAra</summary>
    <img src=${FOTOS["20240319-085919.jpg"].href} alt="Foto real de una cámara de dIAra durante el piloto: movimiento de tierras con una vagoneta, una aplanadora y un tractor; la persona visible está difuminada." style="max-width: 640px; width: 100%; border-radius: 4px; margin-top: 0.75rem;">
    <p class="nota-tabla">Foto 20240319-085919.jpg del repositorio público de dIAra (CGR, CENFOTEC y GIZ), piloto de 2024, con las personas difuminadas.</p>
  </details>`}
</section>

```js
const clave = `lupia-decision-${obraId}`;
let guardado = null;
try { guardado = JSON.parse(localStorage.getItem(clave) ?? "null"); } catch {}
const ACCIONES = ["Sin acción todavía", "Solicitar información a la ejecutora", "Programar visita de campo", "Incluir en el plan de auditoría", "Descartar"];
guardado = {accion: ACCIONES[0], motivo: "", causa: "", responsable: "", fecha_seguimiento: null, nota: "", ...(guardado ?? {})};
const formDecision = Inputs.form({
  causa: Inputs.textarea({label: "Causa", value: guardado.causa, rows: 2, width: 520, placeholder: "Por qué ocurre, según la ejecutora o la visita. Si aún no se sabe, déjelo vacío."}),
  accion: Inputs.radio(ACCIONES, {label: "Acción", value: ACCIONES.includes(guardado.accion) ? guardado.accion : ACCIONES[0]}),
  motivo: Inputs.select(["", "Feriado o lluvia", "Suspensión aprobada", "Falla de cámara", "Obra terminada", "Explicación de la ejecutora", "Otro"], {label: "Motivo, si descarta", value: guardado.motivo}),
  responsable: Inputs.text({label: "Responsable", value: guardado.responsable, placeholder: "Quién da seguimiento"}),
  fecha_seguimiento: Inputs.date({label: "Revisar de nuevo el", value: guardado.fecha_seguimiento}),
  nota: Inputs.textarea({label: "Nota", value: guardado.nota, rows: 3, width: 520, placeholder: "Qué revisó, qué pidió y qué concluyó"})
});
const decision = Generators.input(formDecision);

// Hallazgo preliminar: LupIA llena criterio, condición y efecto; la causa la determina el auditor (NGASP 204)
const CRITERIO = {
  inactividad: () => "Una obra en ejecución debería mostrar actividad en sus días hábiles. LupIA marca alerta desde 5 días hábiles seguidos sin personas ni máquinas, con la cámara funcionando.",
  atraso: () => `El cronograma vigente prevé ${num(o.avance_previsto_pct)}\u00a0% de avance al ${fechaLarga(o.fecha_ultimo_informe)}.`,
  brecha: () => "El avance que se reporta debería corresponder a semanas con actividad observada en la obra.",
  contrato: () => "Los aumentos de monto y las prórrogas deben estar respaldados por un acto aprobado y justificado.",
  ciudadania: () => "Los reportes ciudadanos deben atenderse y verificarse."
};
const alertasObra = razones(o).map((r) => r.clave);
const criterio = alertasObra.length ? alertasObra.map((k) => CRITERIO[k]()) : ["Ninguna de las cinco señales pasa su límite."];
const condicion = [
  ...razones(o).map((r) => r.texto),
  `Evidencia: ${plural(dias.filter((d) => d.estado !== "sin_datos").length, "día", "días")} con datos de la cámara${ultimoActivo ? `; último día con actividad, ${fechaLarga(ultimoActivo)}` : ""}. Fotos en la pestaña Fotos.`
];
const pagadoUltimo = serie.filter((d) => d.obra_id === obraId && d.serie === "pagado").sort((a, b) => a.fecha - b.fecha).at(-1);
const diasAlFin = o.fecha_fin_vigente ? Math.round((o.fecha_fin_vigente - corte) / DIA) : null;
const efecto = tieneDato(o.monto_vigente_crc) ? [
  `Monto vigente en riesgo: ${millones(o.monto_vigente_crc)}${pagadoUltimo ? `, de los que ya se pagó ${num(pagadoUltimo.valor_pct, 0)}\u00a0% al ${fechaLarga(pagadoUltimo.fecha)}` : ""}.`,
  diasAlFin != null ? (diasAlFin >= 0 ? `El contrato vence el ${fechaLarga(o.fecha_fin_vigente)}: faltan ${plural(diasAlFin, "día", "días")}.` : `El plazo venció el ${fechaLarga(o.fecha_fin_vigente)}.`) : null
].filter(Boolean) : ["No hay contrato registrado para estimar el efecto. Pida el monto y el plazo a la ejecutora."];
```

```js
try {
  localStorage.setItem(clave, JSON.stringify({
    ...decision, fecha_seguimiento: decision.fecha_seguimiento ? decision.fecha_seguimiento.toISOString().slice(0, 10) : null,
    actualizado: new Date().toISOString(),
    // foto de la situación al decidir, para comparar después en «Sus acciones abiertas»
    foto: {fecha_corte: resumen.fecha_corte, alertas: o.alertas ?? "", racha: o.racha_inactividad_dias, puntaje: Math.round(o.puntaje_vivo)}
  }));
} catch {}
function expedienteCSV() {
  const esc = (v) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  const filas = [
    [`Expediente de LupIA (prototipo académico; ${real ? "detecciones reales del piloto de dIAra" : "obra simulada a partir del piloto de dIAra"})`],
    ["Fecha de corte", resumen.fecha_corte], ["Generado", new Date().toISOString()], [],
    ["Obra", `${o.obra_id}. ${o.nombre}`], ["Tipo", o.tipo], ["Cantón", o.canton],
    ["Institución ejecutora", o.institucion_ejecutora], ["Contratista", o.contratista],
    ["Monto vigente (CRC)", o.monto_vigente_crc], ["Fin vigente", o.fecha_fin_vigente], [],
    ["Puntaje de atención", o.puntaje], ["Número en la lista", o.orden],
    ...SENALES.map((s) => [`Señal: ${s.label}`, o[`senal_${s.key}`], `peso ${resumen.pesos[s.key]}`]),
    ["Razones", razones(o).map((r) => r.texto).join(" | ")], [],
    ["Hallazgo preliminar (NGASP 204)"],
    ["Criterio", criterio.join(" ")], ["Condición", condicion.join(" ")],
    ["Causa", decision.causa || "Por determinar"], ["Efecto", efecto.join(" ")], [],
    ["Acción", decision.accion], ["Motivo si se descarta", decision.motivo], ["Responsable", decision.responsable],
    ["Revisar de nuevo el", decision.fecha_seguimiento ? decision.fecha_seguimiento.toISOString().slice(0, 10) : ""], ["Nota", decision.nota], [],
    ["Fecha", "Estado del día", "Cobertura de la cámara", "Fotos con actividad", "Contexto"],
    ...dias.map((d) => [d.fecha.toISOString().slice(0, 10), ESTADOS[d.estado].label, d.cobertura, d.pct_actividad, d.explicacion]),
    [], ["Metodología", "Sin datos si llega menos del 50 % de las fotos; actividad si 15 % o más de las fotos laborales tienen detecciones. Detalle en la página Metodología de LupIA."]
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

<section class="pestana registro" id="p-decision" role="tabpanel" aria-labelledby="t-decision" hidden>
  <h2>¿Qué hace con esta obra?</h2>
  <p>Este es el hallazgo preliminar, con sus cuatro atributos. LupIA llena lo que los datos permiten saber; la causa la determina usted con la ejecutora o en la visita.</p>
  <dl class="hallazgo">
    <div><dt>Criterio <span>Lo que debería ocurrir</span></dt><dd><ul>${criterio.map((t) => html`<li>${t}</li>`)}</ul></dd></div>
    <div><dt>Condición <span>Lo que se observó</span></dt><dd><ul>${condicion.map((t) => html`<li>${t}</li>`)}</ul></dd></div>
    <div><dt>Causa <span>Por qué ocurre</span></dt><dd>${decision.causa ? decision.causa : html`<span class="tenue">Por determinar. Escríbala abajo cuando la conozca.</span>`}</dd></div>
    <div><dt>Efecto <span>Lo que está en riesgo</span></dt><dd><ul>${efecto.map((t) => html`<li>${t}</li>`)}</ul></dd></div>
  </dl>
  <h3>Decisión y seguimiento</h3>
  ${formDecision}
  <p class="nota-tabla">Se guarda en este navegador. Las obras con una acción abierta aparecen en «Sus acciones abiertas», en la página de inicio.</p>
  <div class="lupia-acciones no-imprimir">
    ${html`<button class="boton" type="button" onclick=${descargar}>Descargar expediente</button>`}
    ${html`<button class="boton secundario" type="button" onclick=${() => window.print()}>Imprimir o guardar en PDF</button>`}
  </div>
  <p class="siguiente no-imprimir">${html`Siguiente en la lista: <a href=${`./obra.html?id=${siguiente.obra_id}`}>${siguiente.orden}. ${siguiente.nombre}</a>`}</p>
</section>
