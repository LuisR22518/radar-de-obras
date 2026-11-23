---
title: Ficha de la obra
---

```js
import {Plot, fecha, fechaTexto, num, millones, plural, esReal, estiloPlot} from "./components/lupia.js";
const obras = await FileAttachment("data/senales.csv").csv({typed: true});
const registro = await FileAttachment("data/obras.csv").csv({typed: true});
const diario = await FileAttachment("data/estado_diario.csv").csv({typed: true});
const semanal = await FileAttachment("data/matriz_semanal.csv").csv({typed: true});
const eventos = await FileAttachment("data/eventos.csv").csv({typed: true});
const evidencia = await FileAttachment("data/evidencia.csv").csv({typed: true});
const serie = await FileAttachment("data/serie_avance.csv").csv({typed: true});
const hitos = await FileAttachment("data/hitos.csv").csv({typed: true});
const fotosRegistro = await FileAttachment("data/fotos.csv").csv({typed: true});
const resumen = await FileAttachment("data/resumen.json").json();
// Fotos reales del piloto (personas difuminadas): se declaran una por una para que se publiquen
const FOTOS_PILOTO = {
  "fotos-piloto/20240319-085758.jpg": FileAttachment("data/fotos-piloto/20240319-085758.jpg"),
  "fotos-piloto/20240319-085919.jpg": FileAttachment("data/fotos-piloto/20240319-085919.jpg"),
  "fotos-piloto/20240319-090039.jpg": FileAttachment("data/fotos-piloto/20240319-090039.jpg"),
  "fotos-piloto/20240319-090159.jpg": FileAttachment("data/fotos-piloto/20240319-090159.jpg"),
  "fotos-piloto/20240319-090319.jpg": FileAttachment("data/fotos-piloto/20240319-090319.jpg"),
  "fotos-piloto/20240319-090439.jpg": FileAttachment("data/fotos-piloto/20240319-090439.jpg")
};
const DIA = 864e5;
const SEMANAS = 8;
const porNombre = [...obras].sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
```

```js
const pedida = new URLSearchParams(location.search).get("id");
const selector = Inputs.select(porNombre.map((d) => d.obra_id), {
  label: "Ver otra obra",
  value: porNombre.some((d) => d.obra_id === pedida) ? pedida : porNombre[0].obra_id,
  format: (id) => {
    const o = obras.find((d) => d.obra_id === id);
    return `${o.nombre} · ${o.canton}`;
  }
});
const obraId = Generators.input(selector);
```

```js
history.replaceState(null, "", `?id=${obraId}`);
const o = obras.find((d) => d.obra_id === obraId);
const reg = registro.find((d) => d.obra_id === obraId);
const real = esReal(o);
const dias = diario.filter((d) => d.obra_id === obraId).sort((a, b) => a.fecha - b.fecha);
const corte = o.fecha_corte_obra;
const semanas = semanal.filter((d) => d.obra_id === obraId).sort((a, b) => a.semana - b.semana).slice(-SEMANAS);
const inicioVentana = semanas.length ? semanas[0].semana : corte;
const diasVentana = dias.filter((d) => d.fecha >= inicioVentana);
const conDatos = diasVentana.filter((d) => d.estado !== "sin_datos").length;
const ultimoTrabajo = d3.max(dias.filter((d) => d.estado === "actividad"), (d) => d.fecha);
const ultimoConDatos = d3.max(dias.filter((d) => d.estado !== "sin_datos"), (d) => d.fecha);
const eventosObra = eventos.filter((d) => d.obra_id === obraId);
const contrato = eventosObra.filter((d) => d.categoria === "contrato");
const reportes = eventosObra.filter((d) => d.categoria === "ciudadania");
const suspensiones = contrato.filter((d) => d.tipo === "suspension");
const recepcion = contrato.find((d) => d.tipo === "recepcion_provisional");
const sinCamara = o.en_cola_dispositivos || o.dias_sin_datos >= resumen.dias_sin_datos_camara;
const terminada = o.fase === "terminada";
const parada = !terminada && !sinCamara && o.racha_inactividad_dias >= 5;
const habiles = diasVentana.filter((d) => d.es_habil && d.estado !== "sin_datos");
const habilesConTrabajo = habiles.filter((d) => d.estado === "actividad").length;
const siguienteDia = (f) => new Date(+f + DIA);
```

```js
// 1 · Qué obra es, si hay trabajo y si el dato es confiable
const etiqueta = real
  ? html`<span class="fc-etiqueta fc-real">Datos reales del piloto de dIAra (${new Date(corte).getUTCFullYear()})</span>`
  : html`<span class="fc-etiqueta">Datos simulados</span>`;
const respuesta = terminada
  ? `La obra está terminada${recepcion ? `: se recibió el ${fechaTexto(recepcion.fecha)}` : ""}.`
  : sinCamara
  ? `No sabemos si hubo trabajo: la cámara no envía fotos desde el ${fechaTexto(siguienteDia(ultimoConDatos))}.`
  : parada
  ? `La cámara no ha visto trabajo desde el ${fechaTexto(siguienteDia(ultimoTrabajo))}.`
  : `La cámara vio trabajo ${habilesConTrabajo} de los últimos ${plural(habiles.length, "día hábil", "días hábiles")}.`;
const confianza = sinCamara
  ? "Dato incompleto: la cámara dejó de enviar fotos."
  : conDatos >= 0.9 * diasVentana.length
  ? `Dato confiable: la cámara envió fotos ${conDatos} de ${diasVentana.length} días.`
  : `Dato con vacíos: la cámara envió fotos solo ${conDatos} de ${diasVentana.length} días.`;
const botonReporte = html`<a class="fc-boton" href="#reportar">Reportar algo que vi</a>`;
const secCabeza = html`<header class="fc-cabeza">
  <div>
    ${etiqueta}
    <h1>${o.nombre}</h1>
    <p class="fc-lugar">${o.canton}, ${o.provincia}</p>
    ${reg?.necesidad_publica ? html`<p class="fc-sirve"><b>Sirve para:</b> ${reg.necesidad_publica}</p>` : html`<p class="fc-sirve fc-tenue">No se ha registrado para qué sirve esta obra.</p>`}
  </div>
  <div class="fc-boton-arriba">${botonReporte}</div>
</header>
<section class="fc-respuesta" aria-label="Respuesta rápida">
  <p class="fc-frase">${respuesta}</p>
  <p class="fc-confianza">${confianza}${real ? ` Datos de ${fecha(o.periodo_desde)} a ${fecha(corte)} de ${new Date(corte).getUTCFullYear()}.` : ` Datos al ${fechaTexto(corte)}.`}</p>
</section>`;
```

```js
// 2 · Las últimas 8 semanas
const NOMBRE_SEMANA = {actividad: "hubo trabajo", sin_actividad: "sin trabajo", sin_datos: "sin datos de la cámara", terminada: "obra terminada"};
const detalle = html`<div class="fc-detalle" aria-live="polite"><p class="fc-tenue">Toque una semana para ver cada día.</p></div>`;
function verSemana(s, boton) {
  for (const b of boton.parentElement.children) b.setAttribute("aria-pressed", "false");
  boton.setAttribute("aria-pressed", "true");
  const fin = new Date(+s.semana + 7 * DIA);
  const sus = dias.filter((d) => d.fecha >= s.semana && d.fecha < fin);
  const ESTADO_DIA = {actividad: "hubo trabajo", sin_actividad: "sin trabajo", sin_datos: "sin datos"};
  detalle.replaceChildren(html`<p class="fc-detalle-titulo">Semana del ${fecha(s.semana)}: ${NOMBRE_SEMANA[s.estado_semana]}</p>
    <ul class="fc-dias">${sus.map((d) => html`<li class="fc-dia-${d.estado}"><span>${["dom", "lun", "mar", "mié", "jue", "vie", "sáb"][d.fecha.getUTCDay()]} ${fecha(d.fecha)}</span> ${ESTADO_DIA[d.estado]}${d.explicacion ? ` (${d.explicacion})` : ""}</li>`)}</ul>`);
}
const tira = html`<div class="fc-semanas" role="group" aria-label="Actividad por semana">${semanas.map((s) => {
  const b = html`<button type="button" class="fc-semana fc-${s.estado_semana}" aria-pressed="false" title="Semana del ${fecha(s.semana)}: ${NOMBRE_SEMANA[s.estado_semana]}" aria-label="Semana del ${fecha(s.semana)}: ${NOMBRE_SEMANA[s.estado_semana]}"></button>`;
  b.onclick = () => verSemana(s, b);
  return b;
})}</div>`;
const secSemanas = html`<section class="fc-bloque">
  <h2>Últimas ${semanas.length} semanas</h2>
  ${tira}
  <div class="fc-fechas"><span>${semanas.length ? fecha(semanas[0].semana) : ""}</span><span>${fecha(corte)}</span></div>
  <p class="fc-leyenda"><span class="fc-m fc-actividad"></span> hubo trabajo <span class="fc-m fc-sin_actividad"></span> sin trabajo <span class="fc-m fc-sin_datos"></span> sin datos${semanas.some((s) => s.estado_semana === "terminada") ? html` <span class="fc-m fc-terminada"></span> terminada` : ""}</p>
  ${detalle}
</section>`;
```

```js
// 4 · Etapas de la obra
const hoy = new Date();
const etapas = hitos.filter((d) => d.obra_id === obraId).sort((a, b) => a.fecha_prevista - b.fecha_prevista)
  .map((h) => ({...h, estado: h.fecha_cumplido ? "cumplida" : h.fecha_prevista < hoy ? "atrasada" : "pendiente"}));
const ICONO = {cumplida: "✓", atrasada: "!", pendiente: "○"};
const secEtapas = html`<section class="fc-bloque">
  <h2>Etapas de la obra</h2>
  ${etapas.length ? html`<ul class="fc-etapas">${etapas.map((h) => html`<li class="fc-etapa-${h.estado}">
    <span class="fc-icono" aria-hidden="true">${ICONO[h.estado]}</span>
    <span><b>${h.hito}</b> · ${h.estado === "cumplida" ? `cumplida el ${fecha(h.fecha_cumplido)}` : h.estado === "atrasada" ? html`<strong>atrasada</strong> (prevista para el ${fecha(h.fecha_prevista)})` : `prevista para el ${fechaTexto(h.fecha_prevista)}`}</span>
  </li>`)}</ul>` : html`<p class="fc-tenue">No hay etapas registradas para esta obra.</p>`}
</section>`;
```

```js
// 5 · Lo que dice la ejecutora y el contrato
const cambios = contrato.filter((d) => d.tipo !== "recepcion_provisional");
const secContrato = html`<section class="fc-bloque">
  <h2>Lo que dice la ejecutora y el contrato</h2>
  <dl class="fc-datos">
    <div><dt>Avance reportado por la ejecutora</dt><dd>${o.avance_reportado_pct != null ? html`${num(o.avance_reportado_pct, 0)}&nbsp;% <small>(informe del ${fecha(o.fecha_ultimo_informe)})</small>` : "No hay informes registrados"}</dd></div>
    <div><dt>Costo</dt><dd>${o.monto_vigente_crc ? millones(o.monto_vigente_crc) : "No es público"}${o.monto_vigente_crc && o.monto_original_crc && o.monto_vigente_crc !== o.monto_original_crc ? html` <small>(era ${millones(o.monto_original_crc)})</small>` : ""}</dd></div>
    <div><dt>Fecha de entrega</dt><dd>${o.fecha_fin_vigente ? fechaTexto(o.fecha_fin_vigente) : "No es pública"}</dd></div>
    <div><dt>Cambios al contrato</dt><dd>${cambios.length ? html`<ul>${cambios.map((d) => html`<li>${d.detalle} (${fecha(d.fecha)})</li>`)}</ul>` : "Ninguno registrado"}</dd></div>
  </dl>
</section>`;
```

```js
// 3 · Fotos: las de la cámara (piloto real) o las de referencia registradas en la hoja
const fotos = real
  ? d3.groups(evidencia.filter((d) => d.obra_id === obraId && d.foto), (d) => d.foto).map(([foto, filas]) => ({
      clave: foto, fecha: new Date(String(filas[0].fecha_hora).replace(" ", "T") + "Z"), src: FOTOS_PILOTO[foto],
      pie: d3.rollups(filas.filter((d) => d.clase), (v) => v.length, (d) => d.clase).map(([c, n]) => `${n} ${c.toLowerCase()}`).join(", "),
      fuente: "camara dIAra"
    })).sort((a, b) => a.fecha - b.fecha)
  : fotosRegistro.filter((d) => d.obra_id === obraId).map((d) => ({...d, clave: d.enlace, src: d.enlace, pie: d.descripcion})).sort((a, b) => a.fecha - b.fecha);
const dosDigitos = (n) => String(n).padStart(2, "0");
const etiquetaFoto = (f) => `${fecha(f.fecha)}${real ? `, ${dosDigitos(f.fecha.getUTCHours())}:${dosDigitos(f.fecha.getUTCMinutes())}` : ""}`;
const elegirA = Inputs.select(fotos, {label: "Foto 1", format: etiquetaFoto, value: fotos[0]});
const elegirB = Inputs.select(fotos, {label: "Foto 2", format: etiquetaFoto, value: fotos.at(-1)});
async function marco(f) {
  if (!f) return html`<figure class="fc-foto fc-foto-vacia"><div>Sin foto</div></figure>`;
  const src = typeof f.src === "string" ? f.src : await f.src.url();
  const credito = f.autor ? html`<span class="fc-credito">${f.pagina_fuente ? html`<a href=${f.pagina_fuente} target="_blank" rel="noopener">${f.autor}</a>` : f.autor}${f.licencia ? `, ${f.licencia}` : ""}</span>` : "";
  return html`<figure class="fc-foto"><img src=${src} alt=${f.pie || `Foto de la obra, ${fecha(f.fecha)}`} loading="lazy"><figcaption><b>${etiquetaFoto(f)}</b>${f.pie ? ` · ${f.pie}` : ""}${credito}</figcaption></figure>`;
}
const aviso = real
  ? "Fotos reales de la cámara del piloto, con las personas difuminadas. Lo que dice cada foto es lo que detectó la IA."
  : fotos.length
  ? html`<b>Fotos de referencia: no son de esta obra.</b> Muestran cómo se ve una obra parecida en esa etapa. Cuando la obra tenga cámara de dIAra, aquí irán sus fotos reales.`
  : "";
// Al cambiar de foto solo se reemplaza esa foto, sin redibujar la página
const cajaA = html`<div>${await marco(elegirA.value)}</div>`;
const cajaB = html`<div>${await marco(elegirB.value)}</div>`;
elegirA.addEventListener("input", async () => cajaA.replaceChildren(await marco(elegirA.value)));
elegirB.addEventListener("input", async () => cajaB.replaceChildren(await marco(elegirB.value)));
const secFotos = html`<section class="fc-bloque">
  <h2>Compare dos fotos</h2>
  ${fotos.length
    ? html`<div class="fc-elegir">${elegirA}${elegirB}</div>
      <div class="fc-fotos">${cajaA}${cajaB}</div>
      <p class="fc-aviso">${aviso}</p>`
    : html`<p class="fc-tenue">Todavía no hay fotos para esta obra. Se agregan en la pestaña <em>fotos</em> de la hoja del registro.</p>`}
</section>`;
```

```js
// 6 · Qué no se puede concluir (cambia según la situación de la obra)
const notas = [];
if (terminada) notas.push("Que la cámara ya no vea trabajo es lo esperado en una obra terminada; no dice nada sobre la calidad de lo construido.");
else if (sinCamara) notas.push(`No sabemos si hubo trabajo desde el ${fechaTexto(siguienteDia(ultimoConDatos))}: sin fotos no se puede afirmar que la obra esté detenida ni que avance.`);
else if (parada) notas.push("Que la cámara no vea trabajo no prueba que la obra esté abandonada: puede haber lluvia, un feriado, una suspensión autorizada o trabajo fuera del ángulo de la cámara.");
else notas.push("Ver personas o máquinas no mide cuánto avanzó la obra: el avance lo informa la ejecutora.");
for (const s of suspensiones) notas.push(`Hay una suspensión registrada en el contrato: ${s.detalle.toLowerCase()} (${fecha(s.fecha)}).`);
if (o.explicacion_inactividad) notas.push(`Posible explicación registrada: ${o.explicacion_inactividad}.`);
if (!real) notas.push("Esta es una obra de prueba: sus datos son simulados a partir del piloto real de dIAra.");
const secLimites = html`<section class="fc-bloque fc-limites">
  <h2>Qué no se puede concluir</h2>
  ${notas.map((n) => html`<p>${n}</p>`)}
</section>`;
```

```js
// 7 · Reportar algo que vi: se arma el texto con la evidencia y se envía por el canal oficial de la CGR
const queVio = Inputs.textarea({label: "¿Qué vio en la obra?", placeholder: "Por ejemplo: desde hace dos semanas no hay trabajadores y la zanja sigue abierta.", rows: 3});
const enlaceFicha = `${location.origin}${location.pathname}?id=${obraId}`;
const atrasadas = etapas.filter((h) => h.estado === "atrasada");
const armarReporte = (vio) => [
  `Reporte sobre: ${o.nombre}, ${o.canton} (${o.provincia})`,
  `Lo que vi: ${vio.trim() || "(escriba aquí lo que vio)"}`,
  `Lo que muestra LupIA al ${fechaTexto(corte)}: ${respuesta} ${confianza}` +
    (atrasadas.length ? ` Etapas atrasadas: ${atrasadas.map((h) => `${h.hito} (prevista ${fecha(h.fecha_prevista)})`).join("; ")}.` : "") +
    (o.avance_reportado_pct != null ? ` La ejecutora reporta ${num(o.avance_reportado_pct, 0)} % de avance.` : ""),
  `Evidencia: ${enlaceFicha}`,
  real ? "" : "Nota: obra de prueba de un prototipo académico; datos simulados."
].filter(Boolean).join("\n");
const textoReporte = html`<pre class="fc-texto-reporte" aria-label="Reporte listo para enviar">${armarReporte("")}</pre>`;
queVio.addEventListener("input", () => { textoReporte.textContent = armarReporte(queVio.value); });
const copiar = html`<button type="button" class="fc-boton">Copiar el reporte</button>`;
copiar.onclick = async () => {
  try { await navigator.clipboard.writeText(textoReporte.textContent); copiar.textContent = "Reporte copiado"; }
  catch { copiar.textContent = "Selecciónelo y cópielo a mano"; }
};
const canal = resumen.canal_denuncias;
const secReporte = html`<section class="fc-bloque fc-reportar" id="reportar">
  <h2>Reportar algo que vi</h2>
  <p>LupIA no recibe denuncias: le arma el reporte con la evidencia para que lo envíe por el canal oficial de la Contraloría. Así su reporte llega con fechas y datos, no solo con lo que vio.</p>
  ${queVio}
  ${textoReporte}
  <div class="fc-acciones">${copiar}<a class="fc-boton fc-secundario" href=${canal.url} target="_blank" rel="noopener">Ir a Denuncia Digital de la CGR ↗</a></div>
  <p class="fc-tenue">También puede llamar al ${canal.telefono}. Sus datos personales los maneja la Contraloría, no LupIA.</p>
</section>`;
```

```js
// Detalle para fiscalización (plegable)
const serieObra = serie.filter((d) => d.obra_id === obraId);
const ultimoPagado = serieObra.filter((d) => d.serie === "pagado").at(-1);
const NOMBRES_SERIE = {previsto: "Previsto por cronograma", reportado: "Reportado por la ejecutora", pagado: "Pagado"};
const secFisc = html`<details class="fc-fiscalizacion">
  <summary>Detalle para fiscalización</summary>
  <div class="fc-fisc-cuerpo">
    ${serieObra.length ? Plot.plot({
      ...estiloPlot, height: 220, marginLeft: 40, width: Math.min(width, 760),
      y: {domain: [0, 100], label: "% de avance o del monto", grid: true},
      x: {type: "utc", label: null},
      color: {domain: Object.values(NOMBRES_SERIE), range: ["var(--trazo)", "var(--tinta)", "var(--grafito)"], legend: true},
      marks: [Plot.line(serieObra, {x: "fecha", y: "valor_pct", stroke: (d) => NOMBRES_SERIE[d.serie], strokeWidth: 2, strokeDasharray: (d) => (d.serie === "previsto" ? "4,3" : null)})]
    }) : html`<p class="fc-tenue">Sin cronograma, informes ni pagos registrados.</p>`}
    <dl class="fc-datos">
      <div><dt>Pagado</dt><dd>${ultimoPagado ? `${num(ultimoPagado.valor_pct, 0)} % del monto al ${fecha(ultimoPagado.fecha)}` : "Sin pagos registrados"}</dd></div>
      <div><dt>Contratista</dt><dd>${o.contratista || "No es público"}</dd></div>
      <div><dt>Institución ejecutora</dt><dd>${o.institucion_ejecutora}</dd></div>
      <div><dt>Reportes ciudadanos registrados</dt><dd>${reportes.length ? html`<ul>${reportes.map((r) => html`<li>${fecha(r.fecha)}: ${r.detalle}</li>`)}</ul>` : "Ninguno"}</dd></div>
    </dl>
    <p><a href="./obra.html?id=${obraId}">Abrir el análisis completo para fiscalización →</a></p>
  </div>
</details>`;
```

```js
display(html`<div class="ficha-c">
  <div class="fc-arriba">${selector}</div>
  ${secCabeza}
  <div class="fc-columnas">
    <div class="fc-col">${secSemanas}${secEtapas}${secContrato}</div>
    <div class="fc-col">${secFotos}${secLimites}</div>
  </div>
  ${secReporte}
  ${secFisc}
</div>`);
```
