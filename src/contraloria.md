---
title: Para la Contraloría
---

```js
import {fechaTexto, fechaLarga, millones, num, plural, SENALES, ESTADO_OBRA, ordenar, razonesCortas, unirFrase, leerDecision, iconoEstado, leyendaObra, mapaObras, asegurarRayado, esReal, tieneDato} from "./components/lupia.js";
asegurarRayado();
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const pais = await FileAttachment("data/costa-rica.json").json();
const resumen = await FileAttachment("data/resumen.json").json();
const base = senales;
```

<p class="cargando" id="cargando">Cargando las obras…</p>

```js
// Búsqueda libre: obra, cantón, provincia, contratista o institución
const busqueda = Inputs.text({label: "Buscar", placeholder: "Obra, cantón, provincia, contratista o institución", width: "100%"});
const texto = Generators.input(busqueda);

// Filtros (Avance 2, figura 6): por provincia y por estado
const provinciasLista = [...new Set(base.map((o) => o.provincia))].sort((a, b) => a.localeCompare(b, "es"));
const filtroProvincia = Inputs.select(["Todas", ...provinciasLista], {label: "Provincia"});
const provinciaElegida = Generators.input(filtroProvincia);
const filtroEstado = Inputs.select(["Todos", ...Object.keys(ESTADO_OBRA)], {label: "Estado", format: (k) => (k === "Todos" ? k : ESTADO_OBRA[k].label)});
const estadoElegido = Generators.input(filtroEstado);
// El orden usa siempre los mismos pesos (los del cálculo): así la prioridad no depende de quién la mire
const pesos = resumen.pesos;
```

```js
const sinTildes = (s) => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const lista = ordenar(base, pesos);
const consulta = sinTildes(texto).trim();
const coincide = (o) => (!consulta || [o.nombre, o.canton, o.provincia, o.contratista, o.institucion_ejecutora, o.tipo, o.obra_id].some((v) => sinTildes(v).includes(consulta)))
  && (provinciaElegida === "Todas" || o.provincia === provinciaElegida) && (estadoElegido === "Todos" || o.estado === estadoElegido);
const visibles = lista.filter(coincide);
const activo = visibles.length < lista.length ? new Set(visibles.map((o) => o.obra_id)) : null;
const nRevisar = lista.filter((o) => o.estado === "revisar").length;
const nVigentes = lista.filter((o) => !o.historica).length;
const nReales = lista.filter(esReal).length;
```

```js
// Encabezado: se dibuja cuando los datos están listos (sin marcadores de carga a medio llenar)
document.getElementById("cargando")?.remove();
display(html`<p class="aviso">Vista para fiscalizadores de la Contraloría. Datos al ${fechaTexto(resumen.fecha_corte)}. Prototipo académico: una obra usa datos reales del piloto de dIAra y las demás son simuladas a partir de ellos. <a href="./datos.html">Ver de dónde sale cada dato</a></p>
<section class="inicio" aria-labelledby="titulo">
  <h1 id="titulo"><span class="marca marca-trazo">${plural(nRevisar, "obra necesita", "obras necesitan")} revisión</span></h1>
  <p class="bajada">De ${plural(nVigentes, "obra", "obras")} en seguimiento. Empiece por la número 1: es la que reúne más señales de riesgo.</p>
</section>`);
```

```js
function itemObra(o) {
  const registrada = accionAbierta(o.obra_id) ? CORTO[leerDecision(o.obra_id).accion] : leerDecision(o.obra_id)?.accion === "Descartar" ? "Descartada" : null;
  // El fiscalizador va directo al análisis de la obra (desde ahí puede ver también la ficha ciudadana)
  return html`<li class=${`item ${o.estado}`} data-obra=${o.obra_id}>
    <a href=${`./obra.html?id=${o.obra_id}`}>
      ${iconoEstado(o.estado, o.orden)}
      <span class="cuerpo">
        <span class="nombre">${o.estado === "revisar" ? html`<span class="marca">${o.nombre}</span>` : o.nombre}${esReal(o) ? html` <span class="etiqueta-real">Datos reales</span>` : ""}</span>
        <span class="lugar">${[o.canton, o.contratista, tieneDato(o.monto_vigente_crc) ? millones(o.monto_vigente_crc) : null].filter(Boolean).join(". ")}.</span>
        <span class="porque">${unirFrase(razonesCortas(o))}</span>
        ${o.desempate_monto ? html`<span class="desempate">Mismo puntaje que la siguiente: va antes por tener mayor monto.</span>` : ""}
        ${o.senales_con_dato < 5 && o.estado !== "historico" ? html`<span class="faltan">Faltan datos del contrato: su lugar se calculó con ${o.senales_con_dato} de 5 señales.</span>` : ""}
      </span>
      ${registrada ? html`<span class="sello">${registrada}</span>` : ""}
    </a>
  </li>`;
}
// Acciones del auditor guardadas en este navegador (pestaña «Hallazgo y acción» de cada obra)
const ABIERTAS = ["Solicitar información a la ejecutora", "Programar visita de campo", "Incluir en el plan de auditoría"];
const CORTO = {"Solicitar información a la ejecutora": "Información solicitada", "Programar visita de campo": "Visita programada",
               "Incluir en el plan de auditoría": "En el plan de auditoría"};
const accionAbierta = (id) => ABIERTAS.includes(leerDecision(id)?.accion);
function seguimiento() {
  const abiertas = lista.filter((o) => accionAbierta(o.obra_id));
  if (!abiertas.length) return "";
  const hoy = new Date().toISOString().slice(0, 10);
  return html`<section class="seguimiento" aria-labelledby="t-seguimiento">
    <h2 id="t-seguimiento">Sus acciones abiertas <span class="tenue">${abiertas.length}</span></h2>
    <ul>${abiertas.map((o) => {
      const d = leerDecision(o.obra_id);
      const foto = d.foto ?? {};
      const estado = foto.fecha_corte === resumen.fecha_corte ? "Todavía no hay datos nuevos desde su decisión."
        : o.racha_inactividad_dias < (foto.racha ?? 0) ? "Volvió a haber actividad desde su decisión."
        : o.racha_inactividad_dias > 0 ? `Sigue sin actividad: ${plural(o.racha_inactividad_dias, "día hábil", "días hábiles")}.` : "Hay actividad.";
      const vencida = d.fecha_seguimiento && d.fecha_seguimiento <= hoy;
      return html`<li><a href=${`./obra.html?id=${o.obra_id}#decision`}>${o.orden}. ${o.nombre}</a>: ${CORTO[d.accion].toLowerCase()}${d.responsable ? `, a cargo de ${d.responsable}` : ""}.
        ${d.fecha_seguimiento ? html`<span class=${vencida ? "vencida" : ""}>${vencida ? "Revisión pendiente desde el" : "Revisar el"} ${fechaLarga(d.fecha_seguimiento)}.</span>` : ""} ${estado}</li>`;
    })}</ul>
  </section>`;
}
function listaObras() {
  if (!visibles.length) return html`<p class="vacio">Ninguna obra coincide con la búsqueda o los filtros. Borre la búsqueda o elija «Todas» para ver todas.</p>`;
  return html`${Object.keys(ESTADO_OBRA).map((k) => {
    const grupo = visibles.filter((o) => o.estado === k);
    if (!grupo.length) return "";
    return html`<section class="grupo" aria-labelledby=${`g-${k}`}>
      <h2 id=${`g-${k}`}>${ESTADO_OBRA[k].grupo} <span>${grupo.length}</span></h2>
      ${k === "sin_datos" ? html`<p class="nota-grupo">Primero hay que reparar la cámara; mientras tanto no se puede concluir nada sobre la obra.</p>` : ""}
      ${k === "historico" ? html`<p class="nota-grupo">La cámara ya no está en estas obras. Se conservan para consulta: muestran cómo se ven en LupIA los datos reales que dIAra publicó.</p>` : ""}
      <ol class="lista">${grupo.map(itemObra)}</ol>
    </section>`;
  })}`;
}
function descargarLista() {
  const esc = (v) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  const filas = [["Orden", "Obra", "Nombre", "Estado", "Por qué", "Cantón", "Institución ejecutora", "Contratista", "Monto vigente (CRC)", "Puntaje"],
    ...lista.map((o) => [o.orden, o.obra_id, o.nombre, ESTADO_OBRA[o.estado].label, unirFrase(razonesCortas(o)), o.canton, o.institucion_ejecutora, o.contratista, o.monto_vigente_crc ?? "", Math.round(o.puntaje_vivo)])];
  const blob = new Blob(["﻿" + filas.map((f) => f.map(esc).join(",")).join("\n")], {type: "text/csv;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `lupia-que-revisar-${resumen.fecha_corte}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}
```

```js
// Al pasar por una obra en la lista se resalta su punto en el mapa, y al revés
{
  const marcar = (id) => document.querySelectorAll("[data-obra]").forEach((el) => el.classList.toggle("activo", el.dataset.obra === id));
  const sobre = (e) => marcar(e.target.closest?.("[data-obra]")?.dataset.obra ?? null);
  document.addEventListener("pointerover", sobre);
  document.addEventListener("focusin", sobre);
  invalidation.then(() => {
    document.removeEventListener("pointerover", sobre);
    document.removeEventListener("focusin", sobre);
  });
}
```

<div class="tablero">
  <figure class="caja-mapa">
    ${resize((width) => mapaObras(pais, lista, {width: Math.min(width, 420), activo, enlace: (o) => `./obra.html?id=${o.obra_id}`}))}
    <figcaption>${leyendaObra()}</figcaption>
  </figure>
  <div class="caja-lista">
    <div class="herramientas">
      ${busqueda}
      <div class="filtros">${filtroProvincia}${filtroEstado}</div>
      ${html`<button class="boton secundario" type="button" onclick=${descargarLista}>Descargar lista</button>`}
    </div>
    ${seguimiento()}
    ${listaObras()}
  </div>
</div>

```js
const SENTIDO = {
  inactividad: "Muchos días hábiles seguidos sin personas ni máquinas, con la cámara funcionando.",
  atraso: "El avance reportado va por debajo de lo que dice el cronograma.",
  brecha: "La obra reporta avance, pero la cámara vio poca actividad en esas semanas.",
  contrato: "El monto aumentó o se aprobó una prórroga hace poco.",
  ciudadania: "Personas de la comunidad reportaron problemas en el último mes."
};
// Tabla para comparar las obras señal por señal: cada columna se puede ordenar (tarea del fiscalizador: comparar y priorizar)
const pctTexto = (x) => `${num(100 * x, 0)} %`;
const COLUMNAS = [
  {clave: "orden", titulo: "N.º", valor: (o) => o.orden, celda: (o) => o.orden, sube: true},
  {clave: "nombre", titulo: "Obra", valor: (o) => o.nombre, sube: true,
   celda: (o) => html`<a href=${`./obra.html?id=${o.obra_id}`}>${o.nombre}</a><br><small class="tenue">${o.canton}${o.senales_con_dato < 5 ? ` · con ${o.senales_con_dato} de 5 señales` : ""}</small>`},
  {clave: "puntaje", titulo: "Puntaje (0 a 100)", valor: (o) => o.puntaje_vivo,
   celda: (o) => html`<div class="barra"><b>${Math.round(o.puntaje_vivo)}</b><i><span class=${o.estado} style=${`width: ${o.puntaje_vivo}%`}></span></i></div>`},
  {clave: "inactividad", titulo: "Días hábiles sin actividad", valor: (o) => o.racha_inactividad_dias, celda: (o) => num(o.racha_inactividad_dias, 0)},
  {clave: "atraso", titulo: "Atraso (puntos)", valor: (o) => o.atraso_pts, celda: (o) => (tieneDato(o.atraso_pts) ? num(o.atraso_pts) : "—")},
  {clave: "brecha", titulo: "Avance reportado y semanas con trabajo", valor: (o) => o.senal_brecha,
   celda: (o) => (tieneDato(o.incremento_reportado_pts) ? html`+${num(o.incremento_reportado_pts)} puntos<br><small class="tenue">trabajo en ${pctTexto(o.proporcion_semanas_activas)} de las semanas</small>` : "—")},
  {clave: "contrato", titulo: "Cambios al contrato", valor: (o) => o.senal_contrato,
   celda: (o) => (o.aumento_monto_pct > 0 ? `Monto +${num(o.aumento_monto_pct)} %${o.prorroga_reciente ? " y prórroga" : ""}` : o.prorroga_reciente ? "Prórroga reciente" : tieneDato(o.aumento_monto_pct) ? "Sin cambios" : "—")},
  {clave: "ciudadania", titulo: "Reportes ciudadanos (30 días)", valor: (o) => o.reportes_30d, celda: (o) => num(o.reportes_30d, 0)}
];
function tablaSenales(obras) {
  const datos = obras.filter((o) => o.estado === "revisar" || o.estado === "sin_alertas");
  if (!datos.length) return html`<p class="vacio">Ninguna obra con cámara funcionando coincide con la búsqueda o los filtros.</p>`;
  let orden = {clave: "orden", sube: true};
  const cuerpo = html`<tbody></tbody>`;
  const encabezados = COLUMNAS.map((c) => {
    const boton = html`<button type="button" class="ordenar">${c.titulo}<span class="flecha" aria-hidden="true"></span></button>`;
    boton.onclick = () => {
      orden = orden.clave === c.clave ? {clave: c.clave, sube: !orden.sube} : {clave: c.clave, sube: Boolean(c.sube)};
      pintar();
    };
    return html`<th scope="col" data-clave=${c.clave}>${boton}</th>`;
  });
  function pintar() {
    const col = COLUMNAS.find((c) => c.clave === orden.clave);
    // Los datos que faltan van siempre al final
    const ordenadas = [...datos].sort((a, b) => {
      const va = col.valor(a), vb = col.valor(b);
      const faltaA = !tieneDato(va), faltaB = !tieneDato(vb);
      if (faltaA || faltaB) return faltaA - faltaB;
      const cmp = typeof va === "string" ? va.localeCompare(vb, "es") : va - vb;
      return orden.sube ? cmp : -cmp;
    });
    for (const th of encabezados) {
      const activa = th.dataset.clave === orden.clave;
      th.setAttribute("aria-sort", activa ? (orden.sube ? "ascending" : "descending") : "none");
      th.querySelector(".flecha").textContent = activa ? (orden.sube ? " ▲" : " ▼") : "";
    }
    cuerpo.replaceChildren(...ordenadas.map((o) => {
      const alertas = new Set(String(o.alertas ?? "").split(";"));
      return html`<tr class=${o.estado}>${COLUMNAS.map((c) => {
        const alerta = alertas.has(c.clave);
        return html`<td class=${alerta ? "con-alerta" : ""}>${c.celda(o)}${alerta ? html` <span class="alerta-mini" aria-hidden="true">!</span><span class="sr-only">(pasa su límite)</span>` : ""}</td>`;
      })}</tr>`;
    }));
  }
  pintar();
  return html`<div class="tabla-desliza" role="region" aria-label="Señales de cada obra" tabindex="0">
    <table class="senales-tabla">
      <caption class="sr-only">Señales de cada obra con la cámara funcionando. Use los botones del encabezado para ordenar.</caption>
      <thead><tr>${encabezados}</tr></thead>
      ${cuerpo}
    </table>
  </div>`;
}
```

<section class="comparar" aria-labelledby="t-comparar">
  <h2 id="t-comparar">Comparar las señales</h2>
  <p class="tenue">Ordene por cualquier columna tocando su nombre. El signo ! marca la señal que pasa su límite. Usa la misma búsqueda y los mismos filtros que la lista.</p>
  ${tablaSenales(visibles)}
</section>

<section class="mas" aria-label="Más detalles">
  <details class="panel">
    <summary>¿Cómo decide LupIA el orden?</summary>
    <div class="panel-cuerpo">
      <p>LupIA revisa cinco señales en cada obra. Si alguna pasa su límite, la obra entra en «Necesitan revisión». Entre esas, va primero la de mayor puntaje y, si dos obras empatan, la de mayor monto. Si a una obra le falta un dato, como el contrato, el puntaje se calcula con las señales que sí tienen dato. La importancia de cada señal es fija, para que la prioridad sea la misma para todas las personas.</p>
      <dl class="senales-texto">${SENALES.map((s) => html`<div><dt>${s.label}</dt><dd>${SENTIDO[s.key]}</dd></div>`)}</dl>
      <p><a href="./metodologia.html#para-fiscalizadores">Ver el detalle de cada cálculo</a></p>
    </div>
  </details>
</section>
