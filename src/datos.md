---
title: Datos
---

```js
import {fechaLarga, fechaTexto, plural} from "./components/lupia.js";
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const fuentes = await FileAttachment("data/fuentes.csv").csv({typed: true});
const mantenimiento = await FileAttachment("data/mantenimiento.csv").csv({typed: true});
const resumen = await FileAttachment("data/resumen.json").json();
const reales = fuentes.filter((d) => d.fuente_datos === "dIAra real");
const simuladas = fuentes.filter((d) => d.fuente_datos === "simulado");
const registro = new Map(mantenimiento.map((d) => [d.obra_id, d]));
const camara = new Map(fuentes.map((d) => [d.obra_id, d]));
const hora = (t) => `${fechaTexto(String(t).slice(0, 10))}, a las ${String(t).slice(11, 16)}`;
```

<div class="lectura">

# De dónde salen los datos

<p class="bajada">Datos al ${fechaTexto(resumen.fecha_corte)}. El auditor solo consulta: ningún dato se cambia desde LupIA.</p>

<ol class="capas">
  <li>
    <h2>Lo que ve dIAra</h2>
    <p>Las personas y máquinas que detecta cada cámara. Llegan tal cual de dIAra; nadie las edita.</p>
    <p class="cifras">${plural(reales.length, "cámara real", "cámaras reales")} del piloto, con ${plural(d3.sum(reales, (d) => d.dias_con_archivo), "día publicado", "días publicados")}. ${plural(simuladas.length, "cámara simulada", "cámaras simuladas")} a partir de ese piloto.</p>
  </li>
  <li>
    <h2>El registro de obras</h2>
    <p>Obras, cámaras asignadas, contratos, avance reportado, pagos, reportes ciudadanos y feriados. Lo mantienen la gerencia y los encargados de actualización de obra, a partir de los documentos de cada obra.</p>
    <p class="cifras">${resumen.registro_actualizado ? `Último cambio aplicado: ${hora(resumen.registro_actualizado)}.` : resumen.registro_leido ? `Revisado por última vez: ${hora(resumen.registro_leido)}.` : "Se usa la copia guardada del registro."}</p>
  </li>
  <li>
    <h2>El contexto</h2>
    <p>Feriados, suspensiones aprobadas y lluvia diaria en cada obra (lluvia: ${resumen.origen_clima.join(", ")}). Sirven para no confundir un día de lluvia o un feriado con una obra abandonada.</p>
  </li>
</ol>

## Qué tan al día está cada obra

```js
function celdaFecha(dia, extra) {
  return dia ? html`${fechaLarga(dia)}${extra ? html`<br><span class="tenue">${extra}</span>` : ""}` : "—";
}
function tablaObras() {
  const filas = senales.map((s) => ({s, r: registro.get(s.obra_id), c: camara.get(s.obra_id)}));
  return html`<table class="tabla-datos apilada" tabindex="0">
    <thead><tr><th scope="col">Obra</th><th scope="col">Origen</th><th scope="col">Última foto</th><th scope="col">Último informe de avance</th><th scope="col">Último pago registrado</th></tr></thead>
    <tbody>${filas.map(({s, r, c}) => html`<tr>
      <td data-et="Obra"><a href=${`./ficha.html?id=${s.obra_id}`}>${s.nombre}</a><br><span class="tenue">${s.canton}</span></td>
      <td data-et="Origen">${s.fuente_datos === "dIAra real" ? html`<span class="etiqueta-real">Real</span>` : html`<span class="etiqueta-simulada">Simulada</span>`}</td>
      <td data-et="Última foto">${celdaFecha(s.ultima_captura, s.historica ? "Monitoreo terminado" : s.en_cola_dispositivos ? `Sin fotos hace ${plural(s.dias_sin_datos, "día", "días")}` : "")}</td>
      <td data-et="Último informe">${r ? celdaFecha(r.ultimo_informe, r.informe_vencido ? "Vencido" : "") : "—"}</td>
      <td data-et="Último pago">${r ? celdaFecha(r.ultimo_pago, r.pago_vencido ? "Vencido" : "") : "—"}</td>
    </tr>`)}</tbody>
  </table>`;
}
```

${tablaObras()}

<p class="nota-tabla">«Vencido» quiere decir que no se registró un informe de avance en ${resumen.vence_informe_dias} días o un pago en ${resumen.vence_pago_dias}. Antes de usar ese dato como evidencia, confírmelo con la ejecutora.</p>

## Lo que estos datos no permiten afirmar

- **El avance físico.** La cámara cuenta personas y máquinas; no mide cuánto se construyó.
- **Lo que pasó fuera de cámara.** Un día sin detecciones puede ser trabajo en otra parte de la obra.
- **Un día apagado frente a un día sin trabajo**, en las cámaras reales. El piloto no publica cuántas fotos tomó la cámara cada día, así que esos dos casos se ven igual. Las cámaras simuladas sí traen ese dato, para mostrar cómo se usaría.
- **Que el avance y los pagos sean ciertos.** Son lo que reporta la ejecutora; LupIA los compara con lo que vio la cámara, pero no revisa los documentos.
- **Nada de las obras simuladas.** Sus contratos, informes y pagos son ficticios; solo la escuela del piloto en Pococí usa datos reales de dIAra.

<p class="nota-tabla">¿Vio un dato que no cuadra? Abra la obra desde <a href="./contraloria.html">Para la Contraloría</a> y use «Reportar un dato que no cuadra», al final de la página. La gerencia y los encargados de actualización lo corrigen desde <a href="./mantenimiento.html">Mantenimiento del registro</a>.</p>

## Listos para un estándar abierto

Los datos del registro corresponden a OC4IDS, el estándar abierto de datos de infraestructura (<a href="https://standard.open-contracting.org/infrastructure/latest/es/reference/schema" target="_blank" rel="noopener">referencia del esquema</a>). CoST Costa Rica lo usa en la plataforma nacional de datos abiertos de infraestructura que presentó en noviembre de 2025 (<a href="https://delfino.cr/2025/11/cost-costa-rica-presenta-indice-de-transparencia-2025-y-plataforma-nacional-de-datos-abiertos-en-infraestructura" target="_blank" rel="noopener">nota de prensa</a>). Con esta correspondencia, LupIA podría tomar los datos de las obras de esa plataforma en lugar de cargarlos a mano.

| Dato en LupIA | Campo en OC4IDS |
| --- | --- |
| Código y nombre de la obra | `id`, `title` |
| Para qué sirve | `purpose` |
| Tipo de obra | `sector` |
| Provincia, cantón y coordenadas | `locations` (`address`, `geometry`) |
| Institución ejecutora | `publicAuthority` |
| Contratista | `contractingProcesses` → `summary.suppliers` |
| Monto original del contrato | `contractingProcesses` → `summary.contractValue` |
| Inicio y fin según el contrato | `period` (`startDate`, `endDate`) |
| Cambios de monto, prórrogas y suspensiones | `contractingProcesses` → `summary.modifications` |
| Etapas de la obra | `milestones` (`dueDate`, `dateMet`, `status`) |
| Avance previsto y avance reportado | `forecasts` y `metrics` |
| Pagos | `transactions` |
| Recepción de la obra | `completion.endDate` |
| Fotos | `documents` |
| Lo que ve la cámara y los reportes ciudadanos | No tienen campo en OC4IDS: son el aporte propio de LupIA |

<p class="nota-tabla">Correspondencia propuesta por el equipo con la versión vigente del estándar; no es una publicación certificada.</p>

</div>
