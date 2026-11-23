---
title: Mantenimiento del registro
---

```js
import {fecha, fechaLarga, fechaTexto, plural} from "./components/lupia.js";
const mantenimiento = await FileAttachment("data/mantenimiento.csv").csv({typed: true});
const calidad = await FileAttachment("data/calidad.csv").csv({typed: true});
const bitacora = await FileAttachment("data/bitacora.csv").csv({typed: true});
const responsables = await FileAttachment("data/responsables.csv").csv({typed: true});
const resumen = await FileAttachment("data/resumen.json").json();

const GERENCIA = "Gerencia";
const ENCARGADO = "Encargado de actualización de obra";
const DE_GERENCIA = new Set(["Obras", "Cámaras", "Feriados", "Responsables", "Simulación"]);
const receptores = responsables.filter((d) => d.activo === "si" && d.correo);
const SIN_RECEPTOR = "Los reportes de datos que hacen los auditores no tienen a quién llegar.";
const hace = (n) => (n === 0 ? "hoy" : `hace ${plural(n, "día", "días")}`);
const hora = (t) => `${fechaTexto(String(t).slice(0, 10))}, a las ${String(t).slice(11, 16)}`;
const corte = new Date(resumen.fecha_corte);

// Bandeja: primero lo que bloquea (errores), luego lo vencido y al final los avisos
const errores = calidad.filter((d) => d.nivel === "error");
const avisos = calidad.filter((d) => d.nivel === "aviso");
const enHoja = (d) => `Pestaña ${d.tabla}${d.fila ? `, fila ${d.fila}` : ""}`;
const aCargo = (tabla) => (DE_GERENCIA.has(tabla) ? GERENCIA : ENCARGADO);
const pendientes = [
  ...errores.map((d) => ({nivel: "Error", que: d.mensaje, donde: enHoja(d), quien: aCargo(d.tabla)})),
  ...mantenimiento.flatMap((o) => [
    o.camara_a_mantenimiento && {nivel: "Cámara", donde: o.nombre, quien: `${GERENCIA}, que avisa al equipo de dIAra`,
      que: `La cámara no envía fotos desde el ${fechaLarga(o.ultima_foto)} (${plural(o.dias_sin_datos, "día", "días")}). Hay que repararla.`},
    o.informe_vencido && {nivel: "Vencido", donde: o.nombre, quien: ENCARGADO,
      que: o.ultimo_informe ? `El último informe de avance es del ${fechaLarga(o.ultimo_informe)} (${hace(o.dias_informe)}). Pida el informe a la ejecutora y regístrelo.` : "No hay informes de avance registrados."},
    o.pago_vencido && {nivel: "Vencido", donde: o.nombre, quien: ENCARGADO,
      que: o.ultimo_pago ? `El último pago registrado es del ${fechaLarga(o.ultimo_pago)} (${hace(o.dias_pago)}). Confirme si falta registrar alguno.` : "No hay pagos registrados."}
  ].filter(Boolean)),
  ...avisos.map((d) => ({nivel: "Aviso", donde: enHoja(d), quien: aCargo(d.tabla),
    que: d.tabla === "Responsables" && d.mensaje.includes("«correo»") ? `${SIN_RECEPTOR} Agregue la columna «correo» en la pestaña responsables y escriba el correo de quien debe recibirlos.` : d.mensaje})),
  ...(!receptores.length && !avisos.some((d) => d.mensaje.includes("«correo»"))
    ? [{nivel: "Aviso", que: `${SIN_RECEPTOR} Escriba en la pestaña responsables el correo de quien debe recibirlos.`, donde: "Pestaña Responsables", quien: GERENCIA}] : [])
];
const alDia = mantenimiento.filter((d) => d.al_dia).length;
const cambios30 = bitacora.filter((d) => (corte - new Date(d.fecha_hora)) / 864e5 <= 30).length;
```

<div class="lectura ancha">

# Mantenimiento del registro

<p class="bajada">Para la gerencia y los encargados de actualización de obra: qué hay que corregir o poner al día para que el auditor trabaje con datos confiables.</p>

```js
function estadoGeneral() {
  if (resumen.registro_rechazado) return html`<p class="estado-registro"><strong>El último cambio de la hoja no se aplicó porque tiene ${plural(errores.length, "error", "errores")}.</strong> El auditor sigue viendo la última versión correcta hasta que se corrijan.</p>`;
  if (!pendientes.length) return html`<p class="estado-registro">Todo al día: no hay errores, avisos ni datos vencidos.</p>`;
  return html`<p class="estado-registro"><strong>${plural(pendientes.length, "pendiente", "pendientes")}.</strong> Están ordenados de lo más urgente a lo menos urgente.</p>`;
}
```

${estadoGeneral()}

<p>${resumen.registro_hoja ? html`<a class="boton" href=${resumen.registro_hoja} target="_blank" rel="noopener">Abrir el registro</a>` : ""}</p>
<p class="tenue">${resumen.registro_actualizado ? `Último cambio aplicado: ${hora(resumen.registro_actualizado)}. ` : ""}Los cambios de la hoja aparecen en LupIA unos 15 minutos después.</p>

<dl class="datos-clave">
  <div><dt>Obras al día</dt><dd>${alDia} de ${mantenimiento.length}<small>Informes, pagos, cámara y contrato</small></dd></div>
  <div><dt>Errores en la hoja</dt><dd>${errores.length}<small>Impiden aplicar los cambios</small></dd></div>
  <div><dt>Avisos</dt><dd>${avisos.length}<small>Se pueden usar, pero conviene revisarlos</small></dd></div>
  <div><dt>Cambios en los últimos 30 días</dt><dd>${cambios30}<small>Hechos desde la hoja</small></dd></div>
</dl>

## Por hacer

```js
function tablaPendientes() {
  if (!pendientes.length) return html`<p class="tenue">No hay nada pendiente.</p>`;
  return html`<table class="tabla-datos apilada" tabindex="0">
    <thead><tr><th scope="col">Tipo</th><th scope="col">Qué hay que hacer</th><th scope="col">Dónde</th><th scope="col">A cargo de</th></tr></thead>
    <tbody>${pendientes.map((d) => html`<tr><td data-et="Tipo"><strong>${d.nivel}</strong></td><td data-et="Qué hacer">${d.que}</td><td data-et="Dónde">${d.donde}</td><td data-et="A cargo de">${d.quien}</td></tr>`)}</tbody>
  </table>`;
}
```

${tablaPendientes()}

## Estado de cada obra

```js
function celda(dia, dias, vencido, documento, terminada) {
  if (terminada) return html`<span class="tenue">No aplica: obra terminada</span>`;
  if (!dia) return html`<strong>Sin registros</strong>`;
  return html`${fecha(dia)}, ${hace(dias)}${vencido ? html`<br><strong>Vencido</strong>` : ""}${documento ? "" : html`<br><strong>Sin documento de respaldo</strong>`}`;
}
function tablaObras() {
  return html`<table class="tabla-datos apilada" tabindex="0">
    <thead><tr><th scope="col">Obra</th><th scope="col">Informe de avance</th><th scope="col">Pago</th><th scope="col">Cámara</th><th scope="col">Contrato</th></tr></thead>
    <tbody>${mantenimiento.map((o) => html`<tr>
      <td data-et="Obra"><a href=${`./obra.html?id=${o.obra_id}`}>${o.nombre}</a></td>
      <td data-et="Informe de avance">${celda(o.ultimo_informe, o.dias_informe, o.informe_vencido, o.documento_informe, o.fase === "terminada")}</td>
      <td data-et="Pago">${celda(o.ultimo_pago, o.dias_pago, o.pago_vencido, o.documento_pago, o.fase === "terminada")}</td>
      <td data-et="Cámara">${o.camara_a_mantenimiento ? html`<strong>A mantenimiento</strong><br><span class="tenue">Última foto: ${fecha(o.ultima_foto)}</span>` : "Envía fotos"}</td>
      <td data-et="Contrato">${o.contrato_faltante ? html`<strong>Faltan:</strong> ${o.contrato_faltante}` : "Completo"}</td>
    </tr>`)}</tbody>
  </table>`;
}
```

${tablaObras()}

<p class="nota-tabla">Cada informe y cada pago deben indicar el documento que los respalda; si falta, aparece aquí. Un informe de avance se vence a los ${resumen.vence_informe_dias} días y un pago a los ${resumen.vence_pago_dias}. Una cámara va a mantenimiento después de ${resumen.dias_sin_datos_camara} días seguidos sin enviar fotos. Las obras con monitoreo terminado no aparecen aquí.</p>

## Quién hace qué

```js
function personas(rol) {
  const lista = responsables.filter((d) => d.rol === rol);
  return lista.length ? lista.map((d) => `${d.nombre}${d.activo === "si" ? "" : " (inactivo)"}`).join("; ") : "—";
}
function tablaRoles() {
  const filas = [
    [GERENCIA, "Obras, cámaras, feriados, responsables y la simulación de las obras de prueba. Decide qué obras se vigilan y avisa al equipo de dIAra cuando una cámara deja de enviar fotos.", personas(GERENCIA)],
    [ENCARGADO, "Etapas de la obra (hitos), cambios de contrato, avance reportado, pagos y reportes ciudadanos, cada fila con el documento que la respalda.", personas(ENCARGADO)],
    ["Equipo de dIAra", "Repara las cámaras. No edita la hoja.", "—"],
    ["Auditor", "Consulta LupIA. No edita la hoja: si un dato no cuadra, lo reporta desde el análisis completo de la obra y el reporte llega por correo a las personas con correo registrado.", "—"]
  ];
  return html`<table class="tabla-datos apilada" tabindex="0">
    <thead><tr><th scope="col">Rol</th><th scope="col">Qué mantiene</th><th scope="col">Personas</th></tr></thead>
    <tbody>${filas.map(([r, q, p]) => html`<tr><td data-et="Rol"><strong>${r}</strong></td><td data-et="Qué mantiene">${q}</td><td data-et="Personas">${p}</td></tr>`)}</tbody>
  </table>`;
}
```

${tablaRoles()}

<p class="nota-tabla">${receptores.length ? `Reciben los reportes de los auditores: ${receptores.map((d) => d.nombre).join(", ")}.` : "Nadie recibe todavía los reportes de los auditores: falta registrar un correo en la pestaña responsables."} Como LupIA es un sitio público, use un buzón institucional y no un correo personal.</p>

<p class="nota-tabla">Cada fila de la hoja lleva el nombre de quien la cambió en la columna <em>actualizado_por</em>, y ese nombre debe estar en la pestaña de responsables.</p>

## Últimos cambios

```js
function tablaBitacora() {
  if (!bitacora.length) return html`<p class="tenue">Todavía no hay cambios desde la hoja. Cada cambio quedará aquí, con la fecha, quién lo hizo y el valor anterior.</p>`;
  return html`<table class="tabla-datos" tabindex="0">
    <thead><tr><th scope="col">Cuándo</th><th scope="col">Quién</th><th scope="col">Pestaña</th><th scope="col">Registro</th><th scope="col">Campo</th><th scope="col">Antes</th><th scope="col">Después</th></tr></thead>
    <tbody>${bitacora.map((d) => html`<tr><td>${String(d.fecha_hora).slice(0, 16).replace("T", ", ")}</td><td>${d.responsable ?? "—"}</td><td>${d.tabla}</td><td>${d.clave}</td><td>${d.campo}</td><td>${d.antes ?? "—"}</td><td>${d.despues ?? "—"}</td></tr>`)}</tbody>
  </table>`;
}
```

${tablaBitacora()}

## Cómo agregar o cambiar una obra

1. **Gerencia:** agregue la obra en la pestaña **obras**, con una frase sobre para qué sirve en *necesidad_publica*. Si es una obra de prueba, ponga `simulado` en *fuente_datos* y elija su escenario en la pestaña **simulacion**.
2. **Gerencia:** asígnele una cámara en la pestaña **camaras**, con la fecha desde la que está instalada.
3. **Encargado de actualización:** registre las etapas de la obra en la pestaña **hitos** (fecha prevista y, cuando se cumpla, la fecha en que se cumplió), los cambios de contrato, el avance reportado, los pagos y los reportes ciudadanos, cada uno en su pestaña y con su documento de respaldo.
4. En cada fila, ponga su nombre en *actualizado_por*.
5. Espere unos 15 minutos. LupIA lee la hoja, revisa los datos y, si no hay errores, actualiza la lista, el mapa y la ficha de la obra. Si hay errores, aparecen arriba en «Por hacer» y no se aplica nada hasta corregirlos.

Para conectar una cámara real de dIAra no hay que cambiar código: se copian sus archivos diarios a `datos/diara/<cámara>/` en el repositorio y se registra la cámara en la pestaña **camaras**.

</div>
