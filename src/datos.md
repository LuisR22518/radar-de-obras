---
title: Datos
---

```js
import {fecha, fechaLarga, fechaTexto, num, plural, esReal} from "./components/lupia.js";
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const fuentes = await FileAttachment("data/fuentes.csv").csv({typed: true});
const calidad = await FileAttachment("data/calidad.csv").csv({typed: true});
const bitacora = await FileAttachment("data/bitacora.csv").csv({typed: true});
const responsables = await FileAttachment("data/responsables.csv").csv({typed: true});
const resumen = await FileAttachment("data/resumen.json").json();
const archivoPublico = FileAttachment("data/estado_publico.csv");
const publico = await archivoPublico.csv({typed: true});
const nombre = new Map(senales.map((d) => [d.obra_id, d.nombre]));
const reales = fuentes.filter((d) => d.fuente_datos === "dIAra real");
const simuladas = fuentes.filter((d) => d.fuente_datos === "simulado");
const errores = calidad.filter((d) => d.nivel === "error");
const avisos = calidad.filter((d) => d.nivel === "aviso");
```

<div class="lectura">

# De dónde sale cada dato

LupIA junta tres capas. Cada una tiene un responsable distinto, y el auditor solo lee: no puede cambiar ningún dato desde aquí.

<ol class="capas">
  <li>
    <h2>Lo que ve dIAra</h2>
    <p>Las detecciones de personas y máquinas que produce cada cámara. Nadie las edita a mano: llegan tal cual de dIAra.</p>
    <p class="cifras">${plural(reales.length, "cámara real", "cámaras reales")} con ${plural(d3.sum(reales, (d) => d.dias_con_archivo), "día publicado", "días publicados")} del piloto. ${plural(simuladas.length, "cámara simulada", "cámaras simuladas")} a partir de ese piloto.</p>
  </li>
  <li>
    <h2>El registro de obras</h2>
    <p>La base de datos propia de LupIA: obras, cámaras asignadas, contratos, avance reportado, pagos, reportes ciudadanos y feriados. La mantienen la gerencia y los encargados de actualización de obra en una hoja de Google; LupIA la lee sola cada 15 minutos.</p>
    <p class="cifras">${resumen.registro_leido ? `Última lectura de la hoja: ${resumen.registro_leido.replace("T", ", ")}.` : "En esta versión no se leyó la hoja: se usa la copia guardada en el repositorio."} ${resumen.registro_actualizado ? `Último cambio aplicado: ${resumen.registro_actualizado.replace("T", ", ")}.` : ""}</p>
    ${resumen.registro_hoja ? html`<p><a class="boton secundario" href=${resumen.registro_hoja} target="_blank" rel="noopener">Abrir el registro (gerencia y encargados)</a></p>` : ""}
  </li>
  <li>
    <h2>El contexto</h2>
    <p>Feriados (del registro) y lluvia diaria de cada obra (${resumen.origen_clima.join(", ")}).</p>
  </li>
</ol>

## Fuente de cada obra

```js
const filas = fuentes.map((d) => ({...d, nombre: nombre.get(d.obra_id)}));
function tablaPublica() {
  return html`<table class="tabla-datos" tabindex="0">
    <thead><tr><th scope="col">Obra</th><th scope="col">Cantón</th><th scope="col">Esta semana</th><th scope="col">Semanas con actividad</th><th scope="col">Último día con actividad</th></tr></thead>
    <tbody>${publico.map((d) => html`<tr><td>${d.nombre}</td><td>${d.canton}</td><td>${d.estado_esta_semana}</td><td>${d.semanas_con_actividad}</td><td>${d.ultimo_dia_con_actividad ? fechaLarga(d.ultimo_dia_con_actividad) : "—"}</td></tr>`)}</tbody>
  </table>`;
}
function tablaResponsables() {
  return html`<table class="tabla-datos" tabindex="0">
    <thead><tr><th scope="col">Nombre</th><th scope="col">Cargo</th><th scope="col">Rol</th><th scope="col">Activo</th></tr></thead>
    <tbody>${responsables.map((d) => html`<tr><td>${d.nombre}</td><td>${d.cargo}</td><td>${d.rol}</td><td>${d.activo === "si" ? "Sí" : "No"}</td></tr>`)}</tbody>
  </table>`;
}
function tablaCalidad() {
  if (!calidad.length) return "";
  return html`<table class="tabla-datos" tabindex="0">
    <thead><tr><th scope="col">Nivel</th><th scope="col">Tabla</th><th scope="col">Fila</th><th scope="col">Qué revisar</th></tr></thead>
    <tbody>${calidad.map((d) => html`<tr><td>${d.nivel === "error" ? "Error" : "Aviso"}</td><td>${d.tabla}</td><td>${d.fila || "—"}</td><td>${d.mensaje}</td></tr>`)}</tbody>
  </table>`;
}
function tablaBitacora() {
  if (!bitacora.length) return html`<p class="tenue">Todavía no hay cambios desde la hoja. Cada cambio quedará aquí, con la fecha, quién lo hizo y el valor anterior.</p>`;
  return html`<table class="tabla-datos" tabindex="0">
    <thead><tr><th scope="col">Cuándo</th><th scope="col">Quién</th><th scope="col">Tabla</th><th scope="col">Registro</th><th scope="col">Campo</th><th scope="col">Antes</th><th scope="col">Después</th></tr></thead>
    <tbody>${bitacora.map((d) => html`<tr><td>${String(d.fecha_hora).slice(0, 16).replace("T", " ")}</td><td>${d.responsable ?? "—"}</td><td>${d.tabla}</td><td>${d.clave}</td><td>${d.campo}</td><td>${d.antes ?? "—"}</td><td>${d.despues ?? "—"}</td></tr>`)}</tbody>
  </table>`;
}
```

<table class="tabla-datos" tabindex="0">
  <thead><tr><th scope="col">Obra</th><th scope="col">Cámara</th><th scope="col">Origen</th><th scope="col">Días con archivo</th><th scope="col">Inventario de fotos</th><th scope="col">Período</th></tr></thead>
  <tbody>${filas.map((d) => html`<tr>
    <td><a href=${`./obra.html?id=${d.obra_id}`}>${d.obra_id}. ${d.nombre}</a></td>
    <td>${d.camara_id}</td>
    <td>${d.fuente_datos === "dIAra real" ? html`<span class="etiqueta-real">Real</span> ${d.formato}` : html`<span class="etiqueta-simulada">Simulada</span>`}</td>
    <td>${d.dias_con_archivo}</td>
    <td>${d.inventario_fotos === "si" ? "Sí" : "No"}</td>
    <td>${d.hasta ? `${fechaLarga(d.desde)} al ${fechaLarga(d.hasta)}` : `Desde ${fechaLarga(d.desde)}`}</td>
  </tr>`)}</tbody>
</table>

<p class="nota-tabla">El inventario de fotos dice cuántas fotos tomó la cámara cada día. Sin él, un día sin detecciones no se distingue de un día con la cámara apagada. Los datos públicos del piloto no lo traen; LupIA propone que dIAra lo publique, y las cámaras simuladas muestran cómo se usaría.</p>

## Calidad del registro

${errores.length ? html`<p><strong>La hoja tiene ${plural(errores.length, "error", "errores")}.</strong> LupIA no aplicó el último cambio y sigue usando la última versión buena hasta que se corrijan.</p>` : html`<p>El registro no tiene errores.${avisos.length ? ` Tiene ${plural(avisos.length, "aviso", "avisos")}: datos que se pueden usar pero conviene revisar.` : ""}</p>`}

${tablaCalidad()}

## Quién mantiene el registro

${tablaResponsables()}

## Últimos cambios

${tablaBitacora()}

## Para la ciudadanía

LupIA es una herramienta interna de fiscalización, pero parte de lo que calcula sirve al público: si cada obra tuvo actividad, desde cuándo y con qué datos. Este archivo lo resume sin puntajes, alertas ni decisiones del auditor, para que obrapublica.info u otra página pública pueda mostrarlo.

${tablaPublica()}

<p>${html`<a class="boton secundario" href=${archivoPublico.href} download="lupia-estado-publico.csv">Descargar el estado público (CSV)</a>`}</p>

## Cómo agregar o cambiar una obra

El auditor no cambia datos. La gerencia crea y cambia obras, cámaras y feriados; los encargados de actualización de obra cargan el seguimiento:

1. **Gerencia:** agregue la obra en la pestaña **obras**. Si es una obra de prueba, ponga `simulado` en *fuente_datos* y elija un escenario.
2. **Gerencia:** asígnele una cámara en la pestaña **camaras**, con la fecha desde la que está instalada.
3. **Encargado de actualización:** registre los cambios de contrato, el avance reportado, los pagos y los reportes ciudadanos, cada uno en su pestaña y con su documento de respaldo.
4. En cada fila, ponga su nombre en *actualizado_por* (debe estar en la pestaña **responsables**).
5. Espere unos 15 minutos. LupIA lee la hoja, revisa la calidad de los datos y, si no hay errores, recalcula todo y publica los cambios en el mapa, la lista y la ficha de la obra.

Para conectar una cámara real de dIAra no hay que cambiar código: se copian sus archivos diarios a `datos/diara/<cámara>/` en el repositorio y se registra la cámara.

</div>
