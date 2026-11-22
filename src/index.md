---
title: Qué revisar
---

```js
import {Plot, grafico, fechaTexto, millones, num, plural, SENALES, ESTADO_OBRA, ordenar, razonesCortas, unirFrase, leerDecision, iconoEstado, leyendaObra, mapaObras, asegurarRayado, estiloPlot, esReal, tieneDato} from "./components/lupia.js";
asegurarRayado();
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const pais = await FileAttachment("data/costa-rica.json").json();
const resumen = await FileAttachment("data/resumen.json").json();
const base = senales;
```

```js
// Búsqueda libre: obra, cantón, contratista o institución
const busqueda = Inputs.text({label: "Buscar", placeholder: "Obra, cantón, contratista o institución", width: "100%"});
const texto = Generators.input(busqueda);

// Importancia de cada señal (solo cambia el orden dentro de «Necesitan revisión»)
const formPesos = Inputs.form(Object.fromEntries(SENALES.map((s) =>
  [s.key, Inputs.range([0, 50], {step: 5, value: resumen.pesos[s.key], label: s.corto, width: 180})])));
formPesos.querySelectorAll('input[type="range"]').forEach((el, i) => el.setAttribute("aria-label", `Importancia de ${SENALES[i].label}`));
const pesos = Generators.input(formPesos);
function restablecerPesos() {
  formPesos.value = {...resumen.pesos};
  formPesos.dispatchEvent(new Event("input", {bubbles: true}));
}
```

```js
const sinTildes = (s) => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const lista = ordenar(base, pesos);
const consulta = sinTildes(texto).trim();
const coincide = (o) => !consulta || [o.nombre, o.canton, o.contratista, o.institucion_ejecutora, o.tipo, o.obra_id].some((v) => sinTildes(v).includes(consulta));
const visibles = lista.filter(coincide);
const activo = consulta ? new Set(visibles.map((o) => o.obra_id)) : null;
const nRevisar = lista.filter((o) => o.estado === "revisar").length;
const nVigentes = lista.filter((o) => !o.historica).length;
const nReales = lista.filter(esReal).length;
```

<p class="aviso">Datos al ${fechaTexto(resumen.fecha_corte)}. Prototipo académico: una obra usa datos reales del piloto de dIAra y las demás son simuladas a partir de ellos. <a href="./datos.html">Ver de dónde sale cada dato</a></p>

<section class="inicio" aria-labelledby="titulo">
  <h1 id="titulo"><span class="marca marca-trazo">${plural(nRevisar, "obra necesita", "obras necesitan")} revisión</span></h1>
  <p class="bajada">De ${plural(nVigentes, "obra", "obras")} con cámara de dIAra. Empiece por la número 1: es la que reúne más señales de riesgo.</p>
</section>

```js
function itemObra(o) {
  const decision = leerDecision(o.obra_id);
  const registrada = decision && decision.estado !== "Nueva" ? decision.estado : null;
  return html`<li class=${`item ${o.estado}`} data-obra=${o.obra_id}>
    <a href=${`./obra.html?id=${o.obra_id}`}>
      ${iconoEstado(o.estado, o.orden)}
      <span class="cuerpo">
        <span class="nombre">${o.estado === "revisar" ? html`<span class="marca">${o.nombre}</span>` : o.nombre}${esReal(o) ? html` <span class="etiqueta-real">Datos reales</span>` : ""}</span>
        <span class="lugar">${[o.canton, o.contratista, tieneDato(o.monto_vigente_crc) ? millones(o.monto_vigente_crc) : null].filter(Boolean).join(". ")}.</span>
        <span class="porque">${unirFrase(razonesCortas(o))}</span>
      </span>
      ${registrada ? html`<span class="sello">${registrada}</span>` : ""}
    </a>
  </li>`;
}
function listaObras() {
  if (!visibles.length) return html`<p class="vacio">Ninguna obra coincide con «${texto}». Revise la ortografía o borre la búsqueda para ver todas.</p>`;
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
    ${resize((width) => mapaObras(pais, lista, {width: Math.min(width, 560), activo}))}
    <figcaption>${leyendaObra()}Cada punto lleva el número de la lista. Haga clic en una obra para ver su análisis.</figcaption>
  </figure>
  <div class="caja-lista">
    <div class="herramientas">
      ${busqueda}
      ${html`<button class="boton secundario" type="button" onclick=${descargarLista}>Descargar lista</button>`}
    </div>
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
function dispersion(width) {
  const datos = lista.filter((d) => d.fase !== "terminada" && d.estado !== "sin_datos" && d.estado !== "historico" && tieneDato(d.monto_vigente_crc));
  const medianaMonto = d3.median(senales, (d) => d.monto_vigente_crc);
  return grafico({
    width, height: 300, marginLeft: 56, marginTop: 20, marginBottom: 44, style: estiloPlot,
    x: {domain: [0, 100], label: "Puntaje de atención", labelAnchor: "right", labelArrow: "right", grid: true},
    y: {type: "log", domain: [1.5e8, 4e9], label: "Monto vigente (₡ millones)", labelArrow: "up", grid: true, ticks: [2e8, 5e8, 1e9, 2e9], tickFormat: (d) => num(d / 1e6, 0)},
    marks: [
      Plot.rect([0], {x1: 30, x2: 100, y1: medianaMonto, y2: 4e9, fill: "var(--niebla)"}),
      Plot.text([0], {x: 98, y: 3.4e9, text: () => "Riesgo y monto altos", textAnchor: "end", fill: "var(--tinta)", fontWeight: 600}),
      Plot.dot(datos, {x: "puntaje_vivo", y: "monto_vigente_crc", r: 11, fill: (d) => (d.estado === "revisar" ? "var(--resaltador)" : "var(--papel)"), stroke: (d) => (d.estado === "revisar" ? "var(--tinta)" : "var(--trazo)"), strokeWidth: 1.5}),
      Plot.text(datos, {x: "puntaje_vivo", y: "monto_vigente_crc", text: "orden", fontWeight: 700, fill: "var(--tinta)"})
    ]
  });
}
```

<section class="mas" aria-label="Más detalles">
  <details class="panel">
    <summary>¿Cómo decide LupIA el orden?</summary>
    <div class="panel-cuerpo dos-columnas">
      <div>
        <p>LupIA revisa cinco señales en cada obra. Si alguna pasa su límite, la obra entra en «Necesitan revisión». Entre esas, va primero la de mayor puntaje. Si a una obra le falta un dato, como el contrato, el puntaje se calcula con las señales que sí tienen dato.</p>
        <dl class="senales-texto">${SENALES.map((s) => html`<div><dt>${s.label}</dt><dd>${SENTIDO[s.key]}</dd></div>`)}</dl>
        <p><a href="./metodologia.html">Ver el detalle de cada cálculo</a></p>
      </div>
      <div>
        <h3>Puntaje de cada obra</h3>
        ${puntajes()}
      </div>
    </div>
  </details>
  <details class="panel">
    <summary>Ajustar la importancia de cada señal</summary>
    <div class="panel-cuerpo pesos">
      <p>Los valores iniciales son una propuesta del equipo, no de la Contraloría. Al moverlos cambia el orden dentro de «Necesitan revisión»; qué obras entran en ese grupo no cambia.</p>
      ${formPesos}
      <p>${html`<button class="boton secundario" type="button" onclick=${restablecerPesos}>Volver a los valores iniciales</button>`}</p>
    </div>
  </details>
  <details class="panel">
    <summary>Comparar riesgo y monto</summary>
    <div class="panel-cuerpo">
      <p>El monto no entra en el puntaje. Este gráfico los cruza para distinguir qué tan probable es un problema y qué tan grande sería. Cada círculo lleva el número de la lista.</p>
      <figure aria-label="Puntaje de atención frente al monto vigente de cada obra">${resize((width) => dispersion(Math.min(width, 720)))}</figure>
    </div>
  </details>
</section>
