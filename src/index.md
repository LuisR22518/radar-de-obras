---
title: Qué revisar
---

```js
import {Plot, grafico, fechaTexto, fechaLarga, millones, num, plural, SENALES, ESTADO_OBRA, ordenar, razonesCortas, unirFrase, leerDecision, iconoEstado, leyendaObra, mapaObras, asegurarRayado, estiloPlot, esReal, tieneDato} from "./components/lupia.js";
asegurarRayado();
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const pais = await FileAttachment("data/costa-rica.json").json();
const resumen = await FileAttachment("data/resumen.json").json();
const base = senales;
```

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

<p class="aviso">Datos al ${fechaTexto(resumen.fecha_corte)}. Prototipo académico: una obra usa datos reales del piloto de dIAra y las demás son simuladas a partir de ellos. <a href="./datos.html">Ver de dónde sale cada dato</a></p>

<section class="inicio" aria-labelledby="titulo">
  <h1 id="titulo"><span class="marca marca-trazo">${plural(nRevisar, "obra necesita", "obras necesitan")} revisión</span></h1>
  <p class="bajada">De ${plural(nVigentes, "obra", "obras")} en seguimiento. Empiece por la número 1: es la que reúne más señales de riesgo.</p>
</section>

```js
function itemObra(o) {
  const registrada = accionAbierta(o.obra_id) ? CORTO[leerDecision(o.obra_id).accion] : leerDecision(o.obra_id)?.accion === "Descartar" ? "Descartada" : null;
  return html`<li class=${`item ${o.estado}`} data-obra=${o.obra_id}>
    <a href=${`./ficha.html?id=${o.obra_id}`}>
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
    ${resize((width) => mapaObras(pais, lista, {width: Math.min(width, 420), activo}))}
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
function puntajes() {
  const datos = lista.filter((o) => o.estado !== "sin_datos" && o.estado !== "historico");
  return html`<table class="puntajes">
    <caption class="sr-only">Puntaje de atención de cada obra</caption>
    <thead><tr><th scope="col">Obra</th><th scope="col">Puntaje de 0 a 100</th></tr></thead>
    <tbody>${datos.map((o) => html`<tr><td>${o.orden}. ${o.nombre}${o.senales_con_dato < 5 ? html`<br><small class="tenue">con ${o.senales_con_dato} de 5 señales; faltan datos del contrato</small>` : ""}</td>
      <td><div class="barra"><b>${Math.round(o.puntaje_vivo)}</b><i><span class=${o.estado} style=${`width: ${o.puntaje_vivo}%`}></span></i></div></td></tr>`)}</tbody>
  </table>`;
}
```

<section class="mas" aria-label="Más detalles">
  <details class="panel">
    <summary>¿Cómo decide LupIA el orden?</summary>
    <div class="panel-cuerpo dos-columnas">
      <div>
        <p>LupIA revisa cinco señales en cada obra. Si alguna pasa su límite, la obra entra en «Necesitan revisión». Entre esas, va primero la de mayor puntaje y, si dos obras empatan, la de mayor monto. Si a una obra le falta un dato, como el contrato, el puntaje se calcula con las señales que sí tienen dato. La importancia de cada señal es fija, para que la prioridad sea la misma para todas las personas.</p>
        <dl class="senales-texto">${SENALES.map((s) => html`<div><dt>${s.label}</dt><dd>${SENTIDO[s.key]}</dd></div>`)}</dl>
        <p><a href="./metodologia.html">Ver el detalle de cada cálculo</a></p>
      </div>
      <div>
        <h3>Puntaje de cada obra</h3>
        ${puntajes()}
      </div>
    </div>
  </details>
</section>
