---
title: Ficha de la obra
---

```js
import {fecha as fechaDia, fechaLarga, fechaTexto, num, millones, plural, esReal, estiloPlot, estadoObra, chipEstado, razonesCortas, unirFrase} from "./components/lupia.js";
const obras = await FileAttachment("data/senales.csv").csv({typed: true});
const registro = await FileAttachment("data/obras.csv").csv({typed: true});
const diario = await FileAttachment("data/estado_diario.csv").csv({typed: true});
const semanal = await FileAttachment("data/matriz_semanal.csv").csv({typed: true});
const eventos = await FileAttachment("data/eventos.csv").csv({typed: true});
// La evidencia por foto solo se descarga para la obra con datos reales (las de prueba no la usan en la ficha)
const archivoEvidencia = FileAttachment("data/evidencia.csv");
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

<p class="cargando" id="cargando">Cargando la ficha de la obra…</p>

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
// Fecha corta («3 jul»); lleva el año cuando no es el del corte, para no confundir 2025 con 2026
const fecha = (d) => (d == null || d === "" ? "—" : new Date(d).getUTCFullYear() === new Date(corte).getUTCFullYear() ? fechaDia(d) : fechaLarga(d));
```

```js
// 1 · Qué obra es, si hay trabajo y si el dato es confiable
// La explicación es la misma que usa la lista (radar/reglas.py): solo cuenta si cubre la mitad o más de los días sin trabajo
const explicacionParada = o.explicacion_inactividad ? String(o.explicacion_inactividad).split("; ") : [];
const etiqueta = real
  ? html`<span class="fc-etiqueta fc-real">Datos reales del piloto de dIAra (${new Date(corte).getUTCFullYear()})</span>`
  : html`<span class="fc-etiqueta">Datos simulados</span>`;
// Se dice la última fecha con trabajo o con fotos («por última vez el…»): así no queda duda de qué día fue
const respuesta = terminada
  ? `La obra está terminada${recepcion ? `: se recibió el ${fechaTexto(recepcion.fecha)}` : ""}.`
  : sinCamara
  ? (ultimoConDatos ? `No sabemos si hubo trabajo: la cámara envió fotos por última vez el ${fechaTexto(ultimoConDatos)}.` : "No sabemos si hubo trabajo: la cámara no ha enviado fotos.")
  : parada
  ? (ultimoTrabajo ? `La cámara vio trabajo por última vez el ${fechaTexto(ultimoTrabajo)}.` : "La cámara no ha visto trabajo en el período con fotos.") +
    (explicacionParada.length ? ` Posible explicación: ${explicacionParada.join(" y ")}.` : "")
  : `En las últimas ${semanas.length} semanas, la cámara vio trabajo ${habilesConTrabajo} de ${plural(habiles.length, "día hábil", "días hábiles")} con fotos.`;
const confianza = sinCamara
  ? "Dato incompleto: la cámara dejó de enviar fotos."
  : conDatos >= 0.9 * diasVentana.length
  ? `Dato confiable: la cámara envió fotos ${conDatos} de ${diasVentana.length} días.`
  : `Dato con vacíos: la cámara envió fotos solo ${conDatos} de ${diasVentana.length} días.`;
// Tono de la respuesta: ámbar si hay algo que mirar, verde azulado si hay trabajo normal, gris si no hay datos
const estado = estadoObra(o);
const tono = terminada ? "neutro" : sinCamara ? "gris" : parada || o.amerita_revision ? "alerta" : "ok";
const ICONO_TONO = {neutro: "✓", gris: "?", alerta: "!", ok: "✓"};
const alertasTexto = o.amerita_revision && !sinCamara && !terminada ? unirFrase(razonesCortas(o)) : "";
const proporcionDatos = diasVentana.length ? conDatos / diasVentana.length : 0;
const nivelConfianza = sinCamara ? "Dato incompleto" : proporcionDatos >= 0.9 ? "Dato confiable" : "Dato con vacíos";
const datosAl = real ? `Datos de ${fecha(o.periodo_desde)} a ${fecha(corte)} de ${new Date(corte).getUTCFullYear()}.` : `Datos al ${fechaTexto(corte)}.`;
const sirve = reg?.necesidad_publica
  ? html`<p class="fc-sirve"><span>Sirve para</span> ${reg.necesidad_publica}</p>`
  : html`<p class="fc-sirve fc-tenue">No se ha registrado para qué sirve esta obra.</p>`;
// Título de la pestaña con el nombre de la obra (sirve al guardar o compartir el enlace)
document.title = `${o.nombre} (${o.canton}) · LupIA`;
// Compartir: por WhatsApp (el canal que la gente ya usa) o copiando el enlace
const enlaceFicha = `${location.origin}${location.pathname}?id=${obraId}`;
const textoCompartir = `${o.nombre} (${o.canton}, ${o.provincia}): ${respuesta} ${nivelConfianza}. Véalo en LupIA: ${enlaceFicha}`;
const botonWhatsapp = html`<a class="fc-boton fc-secundario" href=${`https://wa.me/?text=${encodeURIComponent(textoCompartir)}`} target="_blank" rel="noopener">Compartir por WhatsApp</a>`;
const botonCopiar = html`<button type="button" class="fc-boton fc-fantasma">Copiar enlace</button>`;
botonCopiar.onclick = async () => {
  try { await navigator.clipboard.writeText(enlaceFicha); botonCopiar.textContent = "Enlace copiado"; }
  catch { botonCopiar.textContent = "No se pudo copiar"; }
};
// Costo, entrega y avance reportado: lo que más pregunta la gente de una obra, a la vista sin bajar
const datoClave = (etq, valor, nota) => html`<div><dt>${etq}</dt><dd>${valor}${nota ? html`<small>${nota}</small>` : ""}</dd></div>`;
const cambioMonto = o.monto_vigente_crc && o.monto_original_crc && o.monto_vigente_crc !== o.monto_original_crc;
const secClave = html`<dl class="fc-clave" aria-label="Datos clave de la obra">
  ${datoClave("Costo", o.monto_vigente_crc ? millones(o.monto_vigente_crc) : "No es público", cambioMonto ? `Era ${millones(o.monto_original_crc)}` : "")}
  ${terminada && recepcion ? datoClave("Entregada", fechaLarga(recepcion.fecha)) : datoClave("Entrega prevista", o.fecha_fin_vigente ? fechaLarga(o.fecha_fin_vigente) : "No es pública", o.prorroga_reciente ? "Con prórroga reciente" : "")}
  ${datoClave("Avance reportado", tieneAvance ? `${num(o.avance_reportado_pct, 0)} %` : "Sin informes", tieneAvance ? `Informe del ${fecha(o.fecha_ultimo_informe)}` : "")}
</dl>`;
const secCabeza = html`<header class="fc-hero tarjeta">
  <div class="fc-hero-titulo">
    <div class="fc-etiquetas">${etiqueta}${chipEstado(estado)}</div>
    <h1>${o.nombre}</h1>
    <p class="fc-lugar">${o.canton}, ${o.provincia} · ${o.institucion_ejecutora}</p>
  </div>
  ${secClave}
  <section class=${`fc-respuesta fc-${tono}`} aria-label="Respuesta rápida">
    <span class="fc-respuesta-icono" aria-hidden="true">${ICONO_TONO[tono]}</span>
    <div>
      <p class="fc-frase">${respuesta}</p>
      ${alertasTexto ? html`<p class="fc-alertas"><b>Por qué LupIA la marcó:</b> ${alertasTexto}</p>` : ""}
      <div class="fc-confianza">
        <b>${nivelConfianza}</b>
        <span class="fc-medidor" role="img" aria-label=${`La cámara envió fotos ${conDatos} de ${diasVentana.length} días`}><span style=${`width: ${Math.round(100 * proporcionDatos)}%`}></span></span>
        <span>${sinCamara ? "La cámara dejó de enviar fotos." : `La cámara envió fotos ${conDatos} de ${diasVentana.length} días.`} ${datosAl}</span>
      </div>
    </div>
  </section>
  <div class="fc-hero-foto">${await marco(fotos.at(-1))}</div>
  <div class="fc-hero-detalle">
    ${sirve}
    <div class="fc-acciones"><a class="fc-boton" href="#reportar">Reportar algo que vi</a>${botonWhatsapp}${botonCopiar}</div>
  </div>
</header>`;
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
// El título dice la conclusión, no solo el tema (títulos activos)
const nActivas = semanas.filter((s) => s.estado_semana === "actividad").length;
const nSinDatosSem = semanas.filter((s) => s.estado_semana === "sin_datos").length;
const tituloSemanas = !semanas.length ? "Sin semanas con datos de la cámara"
  : semanas.every((s) => s.estado_semana === "terminada") ? `Obra terminada: en las últimas ${semanas.length} semanas ya no se espera trabajo`
  : semanas.length === 1 ? (nActivas ? "Hubo trabajo en la última semana" : "No hubo trabajo en la última semana")
  : `Hubo trabajo en ${nActivas} de las últimas ${plural(semanas.length, "semana", "semanas")}` + (nSinDatosSem ? ` (${nSinDatosSem} sin datos de la cámara)` : "");
const secSemanas = html`<section class="fc-bloque tarjeta">
  <h2>${tituloSemanas}</h2>
  ${tira}
  <div class="fc-fechas"><span>${semanas.length ? fecha(semanas[0].semana) : ""}</span><span>${fecha(corte)}</span></div>
  <p class="fc-leyenda"><span class="fc-m fc-actividad"></span> hubo trabajo <span class="fc-m fc-sin_actividad"></span> sin trabajo <span class="fc-m fc-sin_datos"></span> sin datos${semanas.some((s) => s.estado_semana === "terminada") ? html` <span class="fc-m fc-terminada"></span> terminada` : ""}</p>
  ${detalle}
</section>`;
```

```js
// 4 · Etapas de la obra
// Se comparan con la fecha de corte de los datos (no con el reloj de quien mira), igual que el resto de la ficha
const hoy = new Date(corte);
const etapas = hitos.filter((d) => d.obra_id === obraId).sort((a, b) => a.fecha_prevista - b.fecha_prevista)
  .map((h) => ({...h, estado: h.fecha_cumplido ? "cumplida" : h.fecha_prevista < hoy ? "atrasada" : "pendiente"}));
const ICONO = {cumplida: "✓", atrasada: "!", pendiente: "○"};
function lineaEtapas() {
  const fechas = etapas.flatMap((h) => [h.fecha_prevista, h.fecha_cumplido].filter(Boolean));
  const ini = d3.min([...fechas, hoy]), fin = d3.max([...fechas, hoy]);
  const posicion = (d) => (100 * (d - ini)) / (fin - ini || 1);
  const x = (d) => `${posicion(d)}%`;
  // La etiqueta del corte se alinea hacia adentro cuando cae cerca de un borde, para que no se salga
  const lado = posicion(hoy) > 80 ? " fc-hoy-der" : posicion(hoy) < 20 ? " fc-hoy-izq" : "";
  return html`<div class="fc-linea" aria-hidden="true">
    <span class="fc-linea-base"></span>
    <span class="fc-linea-hecha" style=${`width: ${x(hoy)}`}></span>
    ${etapas.map((h) => html`<span class=${`fc-hito fc-hito-${h.estado}`} style=${`left: ${x(h.fecha_cumplido ?? h.fecha_prevista)}`} title=${h.hito}>${ICONO[h.estado]}</span>`)}
    <span class=${`fc-hoy${lado}`} style=${`left: ${x(hoy)}`}><span>datos al ${fecha(hoy)}</span></span>
  </div>
  <div class="fc-linea-fechas"><span>${fecha(ini)}</span><span>${fecha(fin)}</span></div>`;
}
const secEtapas = html`<section class="fc-bloque tarjeta">
  <h2>Etapas de la obra</h2>
  ${etapas.length ? lineaEtapas() : ""}
  ${etapas.length ? html`<ul class="fc-etapas">${etapas.map((h) => html`<li class="fc-etapa-${h.estado}">
    <span class="fc-icono" aria-hidden="true">${ICONO[h.estado]}</span>
    <span><b>${h.hito}</b> · ${h.estado === "cumplida" ? `cumplida el ${fecha(h.fecha_cumplido)}` : h.estado === "atrasada" ? html`<strong>atrasada</strong> (prevista para el ${fecha(h.fecha_prevista)})` : `prevista para el ${fechaTexto(h.fecha_prevista)}`}</span>
  </li>`)}</ul>` : html`<p class="fc-tenue">No hay etapas registradas para esta obra.</p>`}
</section>`;
```

```js
// 5 · Lo que dice la ejecutora y el contrato
const cambios = contrato.filter((d) => d.tipo !== "recepcion_provisional");
const barraAvance = (etiqueta, valor, clase) => html`<div class=${`fc-barra ${clase}`}>
  <span class="fc-barra-etq">${etiqueta}</span>
  <span class="fc-barra-pista"><span style=${`width: ${Math.max(0, Math.min(100, valor))}%`}></span></span>
  <b>${num(valor, 0)}&nbsp;%</b>
</div>`;
const tieneAvance = o.avance_reportado_pct != null && !Number.isNaN(o.avance_reportado_pct);
const tienePrevisto = o.avance_previsto_pct != null && !Number.isNaN(o.avance_previsto_pct);
const secContrato = html`<section class="fc-bloque tarjeta fc-contrato">
  <h2>Lo que dice la ejecutora y el contrato</h2>
  ${tieneAvance ? html`<p class="fc-cifra-grande">${num(o.avance_reportado_pct, 0)}&nbsp;%<small>de avance, según el informe de la ejecutora del ${fecha(o.fecha_ultimo_informe)}</small></p>
    <div class="fc-barras">
      ${barraAvance("Reportado", o.avance_reportado_pct, "rep")}
      ${tienePrevisto ? barraAvance("Previsto", o.avance_previsto_pct, "prev") : ""}
    </div>
    ${tienePrevisto ? html`<p class="fc-tenue fc-nota-barras">Previsto: lo que el cronograma esperaba para la fecha de ese informe.</p>` : ""}`
  : html`<p class="fc-tenue">No hay informes de avance registrados.</p>`}
  <dl class="fc-datos">
    <div><dt>Costo</dt><dd>${o.monto_vigente_crc ? millones(o.monto_vigente_crc) : "No es público"}${o.monto_vigente_crc && o.monto_original_crc && o.monto_vigente_crc !== o.monto_original_crc ? html` <small>(era ${millones(o.monto_original_crc)})</small>` : ""}</dd></div>
    <div><dt>Fecha de entrega</dt><dd>${o.fecha_fin_vigente ? fechaTexto(o.fecha_fin_vigente) : "No es pública"}</dd></div>
    <div><dt>Cambios al contrato</dt><dd>${cambios.length ? html`<ul>${cambios.map((d) => html`<li>${d.detalle} (${fecha(d.fecha)})</li>`)}</ul>` : "Ninguno registrado"}</dd></div>
  </dl>
</section>`;
```

```js
// 3 · Fotos: las de la cámara (piloto real) o las de referencia registradas en la hoja
const fotos = real
  ? d3.groups((await archivoEvidencia.csv({typed: true})).filter((d) => d.obra_id === obraId && d.foto), (d) => d.foto).map(([foto, filas]) => ({
      clave: foto, fecha: new Date(String(filas[0].fecha_hora).replace(" ", "T") + "Z"), src: FOTOS_PILOTO[foto],
      pie: d3.rollups(filas.filter((d) => d.clase), (v) => v.length, (d) => d.clase).map(([c, n]) => `${n} ${n === 1 ? c.toLowerCase() : c.toLowerCase() + (/[aeiou]$/.test(c.toLowerCase()) ? "s" : "es")}`).join(", "),
      fuente: "camara dIAra"
    })).sort((a, b) => a.fecha - b.fecha)
  : fotosRegistro.filter((d) => d.obra_id === obraId).map((d) => ({...d, clave: d.enlace, src: d.enlace, pie: d.descripcion})).sort((a, b) => a.fecha - b.fecha);
const dosDigitos = (n) => String(n).padStart(2, "0");
const etiquetaFoto = (f) => `${fecha(f.fecha)}${real ? `, ${dosDigitos(f.fecha.getUTCHours())}:${dosDigitos(f.fecha.getUTCMinutes())}` : ""}`;
const elegirA = Inputs.select(fotos, {label: "Foto 1", format: etiquetaFoto, value: fotos[0]});
const elegirB = Inputs.select(fotos, {label: "Foto 2", format: etiquetaFoto, value: fotos.at(-1)});
async function marco(f, {conReferencia = true} = {}) {
  if (!f) return html`<figure class="fc-foto fc-foto-vacia"><div>Sin foto</div></figure>`;
  const src = typeof f.src === "string" ? f.src : await f.src.url();
  // Crédito que piden las licencias libres (autor, licencia y enlace a la fuente)
  const credito = f.autor ? html`<span class="fc-credito">Foto: ${f.pagina_fuente ? html`<a href=${f.pagina_fuente} target="_blank" rel="noopener">${f.autor}</a>` : f.autor}${f.licencia ? `, ${f.licencia}` : ""}</span>` : "";
  // Las obras de prueba usan fotos de otras obras parecidas: se dice siempre, para que nadie las tome como evidencia
  const referencia = real || !conReferencia ? "" : html`<span class="fc-ref">Foto de referencia de otra obra: no es de la cámara.</span>`;
  const alt = real ? (f.pie || `Foto de la cámara, ${fecha(f.fecha)}`) : `Foto de referencia de otra obra${f.pie ? `: ${f.pie}` : ""}`;
  return html`<figure class="fc-foto"><img src=${src} alt=${alt} loading="lazy"><figcaption><b>${etiquetaFoto(f)}</b>${f.pie ? ` · ${f.pie}` : ""}${referencia}${credito}</figcaption></figure>`;
}
const aviso = real
  ? "Fotos reales de la cámara del piloto, con las personas difuminadas. Lo que dice cada foto es lo que detectó la IA."
  : fotos.length
  ? "Obra de prueba: estas fotos son de otras obras parecidas y solo ilustran cada etapa. Lo que dice LupIA sobre el trabajo sale de los datos de la cámara, no de estas fotos."
  : "";
// Al cambiar de foto solo se reemplaza esa foto, sin redibujar la página
// En la comparación el aviso de abajo ya explica que son fotos de referencia: no se repite en cada foto
const cajaA = html`<div>${await marco(elegirA.value, {conReferencia: false})}</div>`;
const cajaB = html`<div>${await marco(elegirB.value, {conReferencia: false})}</div>`;
elegirA.addEventListener("input", async () => cajaA.replaceChildren(await marco(elegirA.value, {conReferencia: false})));
elegirB.addEventListener("input", async () => cajaB.replaceChildren(await marco(elegirB.value, {conReferencia: false})));
const secFotos = html`<section class="fc-bloque tarjeta">
  <h2>Compare dos fotos</h2>
  ${fotos.length
    ? html`<div class="fc-elegir">${elegirA}${elegirB}</div>
      <div class="fc-fotos">${cajaA}${cajaB}</div>
      <p class="fc-aviso">${aviso}</p>`
    : html`<p class="fc-tenue">Todavía no hay fotos para esta obra. Se agregan en la pestaña <em>fotos</em> de la hoja del registro.</p>`}
</section>`;
```

```js
// Lo que ha reportado la comunidad (registro, pestaña reportes_ciudadanos), como en Tracka o Sumbong sa Pangulo
const reportesOrden = [...reportes].sort((a, b) => b.fecha - a.fecha);
// Cerrar el ciclo: cada reporte muestra si la institución respondió (como en FixMyStreet) o cuántos días lleva sin respuesta
function estadoReporte(r) {
  if (r.respuesta) return html`<p class="fc-resp"><b>${r.fecha_respuesta ? `Respuesta del ${fecha(r.fecha_respuesta)}` : "Respuesta"}:</b> ${r.respuesta}</p>`;
  const dias = Math.round((new Date(corte) - r.fecha) / DIA);
  return html`<p class="fc-sinresp">Sin respuesta registrada${dias > 0 ? ` en ${plural(dias, "día", "días")}` : ""}.</p>`;
}
const secComunidad = html`<section class="fc-bloque tarjeta">
  <h2>Lo que ha reportado la comunidad</h2>
  ${reportesOrden.length
    ? html`<ul class="fc-comunidad">${reportesOrden.map((r) => html`<li><span>${fecha(r.fecha)}</span><div><q>${r.detalle}</q>${estadoReporte(r)}</div></li>`)}</ul>
      <p class="fc-tenue fc-nota-barras">Reportes anotados en el registro de LupIA, con la respuesta de la institución cuando la hay.</p>`
    : html`<p class="fc-tenue">No hay reportes de la comunidad anotados para esta obra.</p>`}
</section>`;
```

```js
// 6 · Qué no se puede concluir (cambia según la situación de la obra)
const notas = [];
if (terminada) notas.push("Que la cámara ya no vea trabajo es lo esperado en una obra terminada; no dice nada sobre la calidad de lo construido.");
else if (sinCamara) notas.push(`${ultimoConDatos ? `Después del ${fechaTexto(ultimoConDatos)} no hay fotos` : "No hay fotos"}: no se puede afirmar que la obra esté detenida ni que avance.`);
else if (parada) notas.push("Que la cámara no vea trabajo no prueba que la obra esté abandonada: puede haber lluvia, un feriado, una suspensión autorizada o trabajo fuera del ángulo de la cámara.");
else notas.push("Ver personas o máquinas no mide cuánto avanzó la obra: el avance lo informa la ejecutora.");
if (resumen.metodo?.sensibilidad_modelo) notas.push(`La IA no ve todo: en el piloto encontró unas ${Math.round(100 * resumen.metodo.sensibilidad_modelo)} de cada 100 personas y máquinas que se veían en las fotos.`);
for (const s of suspensiones) notas.push(`Hay una suspensión registrada en el contrato: ${s.detalle.toLowerCase()} (${fecha(s.fecha)}).`);
if (o.explicacion_inactividad) notas.push(`Posible explicación registrada: ${o.explicacion_inactividad}.`);
if (!real) notas.push("Esta es una obra de prueba: sus datos son simulados a partir del piloto real de dIAra.");
const secLimites = html`<section class="fc-bloque tarjeta fc-limites">
  <h2>Qué no se puede concluir</h2>
  ${notas.map((n) => html`<p>${n}</p>`)}
</section>`;
```

```js
// 7 · Reportar algo que vi: se arma el texto con la evidencia y se envía por el canal oficial de la CGR
const queVio = Inputs.textarea({label: "Escriba lo que vio (se agrega al reporte de abajo)", placeholder: "Por ejemplo: desde hace dos semanas no hay trabajadores y la zanja sigue abierta.", rows: 3});
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
const OPCIONES_VIO = ["No hay trabajadores ni máquinas", "La obra parece abandonada", "Veo daños o trabajo de mala calidad", "Está terminada pero no se usa", "Hay trabajo normal"];
const opcionesVio = html`<div class="fc-opciones" role="group" aria-label="Respuestas rápidas">${OPCIONES_VIO.map((t) => {
  const b = html`<button type="button" class="fc-opcion">${t}</button>`;
  b.onclick = () => {
    queVio.value = `${t}. `;
    queVio.dispatchEvent(new Event("input", {bubbles: true}));
    queVio.querySelector("textarea")?.focus();
  };
  return b;
})}</div>`;
const textoReporte = html`<pre class="fc-texto-reporte" aria-label="Reporte listo para enviar">${armarReporte("")}</pre>`;
queVio.addEventListener("input", () => { textoReporte.textContent = armarReporte(queVio.value); });
const copiar = html`<button type="button" class="fc-boton">Copiar el reporte</button>`;
copiar.onclick = async () => {
  try { await navigator.clipboard.writeText(textoReporte.textContent); copiar.textContent = "Reporte copiado"; }
  catch { copiar.textContent = "Selecciónelo y cópielo a mano"; }
};
const canal = resumen.canal_denuncias;
const secReporte = html`<section class="fc-bloque tarjeta fc-reportar" id="reportar">
  <h2>Reportar algo que vi</h2>
  <p>LupIA no recibe denuncias: le arma el reporte con la evidencia para que lo envíe por el canal oficial de la Contraloría. Así su reporte llega con fechas y datos, no solo con lo que vio.</p>
  <p class="fc-paso"><span class="fc-paso-num" aria-hidden="true">1</span> Toque una opción o escriba con sus palabras:</p>
  ${opcionesVio}
  ${queVio}
  <p class="fc-paso"><span class="fc-paso-num" aria-hidden="true">2</span> Así queda su reporte, con la evidencia de LupIA:</p>
  ${textoReporte}
  <p class="fc-paso"><span class="fc-paso-num" aria-hidden="true">3</span> Cópielo y péguelo en la Denuncia Digital de la Contraloría. LupIA no lo envía por usted.</p>
  <p class="fc-consejo"><b>Consejo:</b> si puede, tome fotos con la fecha visible y adjúntelas en la Denuncia Digital. Son la mejor evidencia.</p>
  <div class="fc-acciones">${copiar}<a class="fc-boton fc-secundario" href=${canal.url} target="_blank" rel="noopener">Ir a Denuncia Digital de la CGR ↗</a></div>
  <p class="fc-tenue">También puede llamar al ${canal.telefono}. Sus datos personales los maneja la Contraloría, no LupIA.</p>
</section>`;
```

```js
// Detalle para fiscalización (plegable). Plot se descarga solo al abrirlo: así la ficha carga más rápido en el celular
const serieObra = serie.filter((d) => d.obra_id === obraId);
const ultimoPagado = serieObra.filter((d) => d.serie === "pagado").at(-1);
const NOMBRES_SERIE = {previsto: "Previsto", reportado: "Reportado", pagado: "Pagado"};
const porSerie = (k) => serieObra.filter((d) => d.serie === k).sort((a, b) => a.fecha - b.fecha);
// Nombre al final de cada línea, separados para que no se encimen
const finalesSerie = ["previsto", "reportado", "pagado"].map((k) => ({...porSerie(k).at(-1), nombre: NOMBRES_SERIE[k]}))
  .filter((d) => d.fecha).sort((a, b) => b.valor_pct - a.valor_pct);
for (let i = 0; i < finalesSerie.length; i++) finalesSerie[i].y = i ? Math.min(finalesSerie[i].valor_pct, finalesSerie[i - 1].y - 8) : finalesSerie[i].valor_pct;
const anchoGrafico = Math.min(width, 760);
const cajaGrafico = html`<div class="fc-fisc-grafico">${serieObra.length
  ? html`<p class="fc-tenue">Cargando el gráfico…</p>`
  : html`<p class="fc-tenue">Sin cronograma, informes ni pagos registrados.</p>`}</div>`;
async function dibujarGrafico() {
  try {
    const Plot = await import("npm:@observablehq/plot");
    cajaGrafico.replaceChildren(Plot.plot({
      style: estiloPlot, height: 230, marginLeft: 40, marginRight: 80, width: anchoGrafico,
      y: {domain: [0, 100], label: "% de avance o del monto", labelArrow: "up", grid: true},
      x: {type: "utc", label: null, tickFormat: fecha, ticks: anchoGrafico < 560 ? 4 : 6},
      marks: [
        Plot.line(porSerie("previsto"), {x: "fecha", y: "valor_pct", stroke: "var(--trazo)", strokeWidth: 1.75, strokeDasharray: "5,4"}),
        Plot.line(porSerie("pagado"), {x: "fecha", y: "valor_pct", stroke: "var(--grafito)", strokeWidth: 1.5, curve: "step-after"}),
        Plot.line(porSerie("reportado"), {x: "fecha", y: "valor_pct", stroke: "var(--tinta)", strokeWidth: 2.25}),
        Plot.text(finalesSerie, {x: "fecha", y: "y", text: "nombre", dx: 8, textAnchor: "start", fill: "var(--tinta)", fontWeight: 600})
      ]
    }));
  } catch {
    cajaGrafico.replaceChildren(html`<p class="fc-tenue">No se pudo cargar el gráfico. Revise la conexión y vuelva a abrir este detalle.</p>`);
    delete secFisc.dataset.dibujado;
  }
}
const secFisc = html`<details class="fc-fiscalizacion tarjeta">
  <summary>Detalle para fiscalización</summary>
  <div class="fc-fisc-cuerpo">
    ${cajaGrafico}
    <dl class="fc-datos">
      <div><dt>Pagado</dt><dd>${ultimoPagado ? `${num(ultimoPagado.valor_pct, 0)} % del monto al ${fecha(ultimoPagado.fecha)}` : "Sin pagos registrados"}</dd></div>
      <div><dt>Contratista</dt><dd>${o.contratista || "No es público"}</dd></div>
      <div><dt>Institución ejecutora</dt><dd>${o.institucion_ejecutora}</dd></div>
      <div><dt>Reportes ciudadanos registrados</dt><dd>${reportes.length ? html`<ul>${reportes.map((r) => html`<li>${fecha(r.fecha)}: ${r.detalle}</li>`)}</ul>` : "Ninguno"}</dd></div>
    </dl>
    <p><a href="./obra.html?id=${obraId}">Abrir el análisis completo para fiscalización →</a></p>
  </div>
</details>`;
secFisc.addEventListener("toggle", () => {
  if (secFisc.open && serieObra.length && !secFisc.dataset.dibujado) { secFisc.dataset.dibujado = "si"; dibujarGrafico(); }
});
```

```js
document.getElementById("cargando")?.remove();
display(html`<div class="ficha-c">
  <div class="fc-arriba"><a class="fc-volver" href="./index.html">← Todas las obras</a>${selector}</div>
  ${secCabeza}
  <div class="fc-columnas">
    <div class="fc-principal">${secSemanas}${secFotos}${secEtapas}${secComunidad}</div>
    <aside class="fc-lateral" aria-label="Contrato y límites">${secContrato}${secLimites}</aside>
  </div>
  ${secReporte}
  ${secFisc}
</div>`);
```
