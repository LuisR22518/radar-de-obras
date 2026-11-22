---
title: Datos
---

```js
import {fecha, fechaLarga, fechaTexto, num, plural, esReal} from "./components/lupia.js";
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const fuentes = await FileAttachment("data/fuentes.csv").csv({typed: true});
const calidad = await FileAttachment("data/calidad.csv").csv({typed: true});
const bitacora = await FileAttachment("data/bitacora.csv").csv({typed: true});
const resumen = await FileAttachment("data/resumen.json").json();
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
    <p>La base de datos propia de LupIA: obras, cámaras asignadas, contratos, avance reportado, pagos, reportes ciudadanos y feriados. La mantiene el gestor de datos en una hoja de Google; LupIA la lee sola cada hora.</p>
    <p class="cifras">${resumen.registro_actualizado ? `Última lectura de la hoja: ${resumen.registro_actualizado}.` : "Todavía no se ha leído desde la hoja: se usa la copia guardada en el repositorio."}</p>
    ${resumen.registro_hoja ? html`<p><a class="boton secundario" href=${resumen.registro_hoja} target="_blank" rel="noopener">Abrir el registro (solo gestores)</a></p>` : ""}
  </li>
  <li>
    <h2>El contexto</h2>
    <p>Feriados (del registro) y lluvia diaria de cada obra (${resumen.origen_clima.join(", ")}).</p>
  </li>
</ol>

## Fuente de cada obra

```js
const filas = fuentes.map((d) => ({...d, nombre: nombre.get(d.obra_id)}));
function tablaCalidad() {
  if (!calidad.length) return "";
  return html`<table class="tabla-datos">
    <thead><tr><th scope="col">Nivel</th><th scope="col">Tabla</th><th scope="col">Fila</th><th scope="col">Qué revisar</th></tr></thead>
    <tbody>${calidad.map((d) => html`<tr><td>${d.nivel === "error" ? "Error" : "Aviso"}</td><td>${d.tabla}</td><td>${d.fila || "—"}</td><td>${d.mensaje}</td></tr>`)}</tbody>
  </table>`;
}
function tablaBitacora() {
  if (!bitacora.length) return html`<p class="tenue">Todavía no hay cambios desde la hoja. Cada cambio que haga el gestor quedará aquí, con la fecha y el valor anterior.</p>`;
  return html`<table class="tabla-datos">
    <thead><tr><th scope="col">Cuándo</th><th scope="col">Tabla</th><th scope="col">Registro</th><th scope="col">Campo</th><th scope="col">Antes</th><th scope="col">Después</th></tr></thead>
    <tbody>${bitacora.map((d) => html`<tr><td>${String(d.fecha_hora).slice(0, 16).replace("T", " ")}</td><td>${d.tabla}</td><td>${d.clave}</td><td>${d.campo}</td><td>${d.antes ?? "—"}</td><td>${d.despues ?? "—"}</td></tr>`)}</tbody>
  </table>`;
}
```

<table class="tabla-datos">
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

${errores.length ? html`<p><strong>El registro tiene ${plural(errores.length, "error", "errores")}.</strong> LupIA sigue usando la última versión buena hasta que se corrijan.</p>` : html`<p>El registro no tiene errores.</p>`}

${tablaCalidad()}

## Últimos cambios del gestor

${tablaBitacora()}

## Cómo agregar o cambiar una obra

Esto lo hace el gestor de datos, no el auditor:

1. Abra el registro y agregue la obra en la pestaña **obras**. Si es una obra de prueba, ponga `simulado` en *fuente_datos* y elija un escenario.
2. Asígnele una cámara en la pestaña **camaras**, con la fecha desde la que está instalada.
3. Registre el contrato y los informes: cambios de contrato, avance reportado y pagos, cada uno en su pestaña.
4. Espere hasta una hora. LupIA lee la hoja, revisa la calidad de los datos y, si no hay errores, recalcula todo y publica la obra en el mapa y en la lista.

Para conectar una cámara real de dIAra no hay que cambiar código: se copian sus archivos diarios a `datos/diara/<cámara>/` en el repositorio y se registra la cámara.

</div>
