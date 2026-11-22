---
title: Orden de revisión
---

```js
import {Plot, grafico, fechaTexto, millones, num, plural, SENALES, puntaje, razones, lamina, pulso, senalesMini, leyendaEstados, asegurarRayado, estiloPlot} from "./components/lupia.js";
asegurarRayado();
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const semanal = await FileAttachment("data/matriz_semanal.csv").csv({typed: true});
const resumen = await FileAttachment("data/resumen.json").json();
const UMBRAL_PUNTAJE_ALTO = 30; // desde aquí, el puntaje se considera alto en la dispersión
const semanasDe = (id) => semanal.filter((d) => d.obra_id === id).sort((a, b) => a.semana - b.semana).slice(-12);
```

```js
const opciones = (campo) => ["Todas", ...new Set(senales.map((d) => d[campo]).sort())];
const filtroInstitucion = Inputs.select(opciones("institucion_ejecutora"), {label: "Institución"});
const filtroContratista = Inputs.select(opciones("contratista"), {label: "Contratista"});
const filtroTipo = Inputs.select(opciones("tipo"), {label: "Tipo de obra"});
const institucion = Generators.input(filtroInstitucion);
const contratista = Generators.input(filtroContratista);
const tipo = Generators.input(filtroTipo);

const formPesos = Inputs.form(Object.fromEntries(SENALES.map((s) =>
  [s.key, Inputs.range([0, 50], {step: 5, value: resumen.pesos[s.key], label: s.corto, width: 200})])));
formPesos.querySelectorAll('input[type="range"]').forEach((el, i) => el.setAttribute("aria-label", `Peso de ${SENALES[i].label}`));
const pesos = Generators.input(formPesos);
function restablecerPesos() {
  formPesos.value = {...resumen.pesos};
  formPesos.dispatchEvent(new Event("input", {bubbles: true}));
}
```

```js
const filas = senales
  .filter((d) => (institucion === "Todas" || d.institucion_ejecutora === institucion)
    && (contratista === "Todas" || d.contratista === contratista)
    && (tipo === "Todas" || d.tipo === tipo))
  .map((d) => ({...d, puntaje_vivo: d.en_cola_dispositivos ? 0 : puntaje(d, pesos)}))
  .sort((a, b) => (b.amerita_revision - a.amerita_revision) || (a.en_cola_dispositivos - b.en_cola_dispositivos) || (b.puntaje_vivo - a.puntaje_vivo));
const primero = filas.find((d) => d.amerita_revision);
const cuantas = filas.filter((d) => d.amerita_revision).length;
const camaras = filas.filter((d) => d.en_cola_dispositivos);
```

<p class="aviso">Datos al ${fechaTexto(resumen.fecha_corte)}. Prototipo académico: las detecciones son simuladas con el formato real de dIAra.</p>

<section class="portada" aria-labelledby="revise-primero">
  <div>
    <p class="rotulo" id="revise-primero">Revise primero</p>
    ${primero ? html`<h1>${lamina(primero.obra_id)}<span class="marca marca-trazo">${primero.nombre}</span></h1>
      <p class="donde">${primero.canton}. ${primero.institucion_ejecutora}, ${primero.contratista}. ${millones(primero.monto_vigente_crc)}.</p>
      <ul class="razones">${razones(primero).map((r) => html`<li class=${r.explicada ? "explicada" : ""}>${r.texto}</li>`)}</ul>
      <a class="boton" href="./obra.html?id=${primero.obra_id}">Analizar esta obra</a>`
    : html`<h1>Ninguna obra amerita revisión</h1><p class="donde">Con los filtros y pesos actuales, ninguna señal supera su umbral.</p>`}
  </div>
  <div class="balance">
    <p class="grande">${cuantas === 1 ? "1 obra amerita revisión" : `${cuantas} obras ameritan revisión`}</p>
    ${camaras.length ? html`<p>${camaras.length === 1
      ? `Una cámara lleva ${camaras[0].dias_sin_datos} días sin datos (obra ${camaras[0].obra_id}). Va a mantenimiento, no a fiscalización.`
      : `${camaras.length} cámaras sin datos van a mantenimiento.`}</p>` : ""}
    <p class="tenue">El orden cambia si ajusta los pesos del puntaje, al final de la página.</p>
  </div>
</section>

```js
function fila(d, rango) {
  const nombre = d.amerita_revision ? html`<span class="marca">${d.nombre}</span>` : d.nombre;
  const detalle = d.fase === "terminada" ? "Obra terminada." : `${d.institucion_ejecutora}.`;
  return html`<tr class="fila">
    <td class="rango">${rango}</td>
    <td class="obra"><div class="obra-nombre">${lamina(d.obra_id)}<a href="./obra.html?id=${d.obra_id}">${nombre}</a></div><small>${d.canton}. ${detalle}</small></td>
    <td class="pulso">${pulso(semanasDe(d.obra_id))}</td>
    <td class="senales">${d.en_cola_dispositivos ? html`<small>Cámara sin datos hace ${d.dias_sin_datos} días</small>` : senalesMini(d)}</td>
    <td class="puntaje">${d.en_cola_dispositivos ? html`<small>No aplica</small>` : html`<div class="barra"><b>${Math.round(d.puntaje_vivo)}</b><i><span style="width: ${d.puntaje_vivo}%"></span></i></div>`}</td>
    <td class="monto">${millones(d.monto_vigente_crc)}</td>
  </tr>`;
}
function tablaOrden() {
  if (!filas.length) return html`<p class="vacio">Ninguna obra coincide con estos filtros. Elija «Todas» en algún filtro para ver más obras.</p>`;
  const grupos = [
    {titulo: "Ameritan revisión", filas: filas.filter((d) => d.amerita_revision)},
    {titulo: "Sin alertas", filas: filas.filter((d) => !d.amerita_revision && !d.en_cola_dispositivos)},
    {titulo: "Cámaras sin datos", detalle: "van a mantenimiento", filas: filas.filter((d) => d.en_cola_dispositivos)}
  ].filter((g) => g.filas.length);
  let rango = 0;
  return html`<table class="orden">
    <caption class="sr-only">Obras ordenadas por puntaje de atención</caption>
    <thead><tr><th scope="col">#</th><th scope="col">Obra</th><th scope="col">Últimas 12 semanas</th><th scope="col">Señales</th><th scope="col">Puntaje</th><th scope="col" class="monto">Monto vigente</th></tr></thead>
    ${grupos.map((g) => html`<tbody>
      <tr><th class="grupo" colspan="6" scope="colgroup">${g.titulo} <span>${g.detalle ? `(${g.filas.length}, ${g.detalle})` : `(${g.filas.length})`}</span></th></tr>
      ${g.filas.map((d) => fila(d, ++rango))}
    </tbody>`)}
  </table>`;
}
```

<section aria-labelledby="orden">
  <div class="encabezado-seccion">
    <h2 id="orden">Orden de revisión</h2>
    <p>${plural(filas.length, "obra", "obras")} con cámara, de mayor a menor puntaje de atención</p>
  </div>
  <div class="filtros">${filtroInstitucion}${filtroContratista}${filtroTipo}</div>
  ${leyendaEstados()}
  ${tablaOrden()}
  <p class="nota-tabla">Los cinco cuadros de señales son, en orden: inactividad, atraso, brecha entre lo reportado y lo observado, cambios contractuales y reportes ciudadanos. Más oscuro indica una señal más fuerte; el borde grueso, una alerta. Un punto en el pulso marca una semana sin actividad con explicación posible.</p>
</section>

```js
function dispersion(width) {
  const datos = filas.filter((d) => d.fase !== "terminada" && !d.en_cola_dispositivos);
  const medianaMonto = d3.median(senales, (d) => d.monto_vigente_crc);
  return grafico({
    width, height: 340, marginLeft: 56, marginTop: 20, marginBottom: 44, style: estiloPlot,
    x: {domain: [0, 100], label: "Puntaje de atención", labelAnchor: "right", labelArrow: "right", grid: true},
    y: {type: "log", domain: [1.5e8, 4e9], label: "Monto vigente (₡ millones)", labelArrow: "up", grid: true,
        ticks: [2e8, 5e8, 1e9, 2e9], tickFormat: (d) => num(d / 1e6, 0)},
    marks: [
      Plot.rect([0], {x1: UMBRAL_PUNTAJE_ALTO, x2: 100, y1: medianaMonto, y2: 4e9, fill: "var(--resaltador)", fillOpacity: 0.45}),
      Plot.text([0], {x: 98, y: 3.5e9, text: () => "Revisar primero", textAnchor: "end", fill: "var(--tinta)", fontWeight: 600}),
      Plot.dot(datos, {
        x: "puntaje_vivo", y: "monto_vigente_crc", r: 6.5,
        fill: (d) => (d.amerita_revision ? "var(--tinta)" : "var(--papel)"), stroke: (d) => (d.amerita_revision ? "var(--papel)" : "var(--trazo)"),
        strokeWidth: 1.5, title: (d) => `${d.obra_id}. ${d.nombre}\nPuntaje ${Math.round(d.puntaje_vivo)}, ${millones(d.monto_vigente_crc)}`, tip: true
      }),
      Plot.text(datos, {x: "puntaje_vivo", y: "monto_vigente_crc", text: "obra_id", dx: -13, fontWeight: 700, fill: "var(--tinta)"})
    ]
  });
}
const decisiones = (() => {
  const cuenta = {Remitida: 0, Descartada: 0};
  try {
    for (const d of senales) {
      const g = JSON.parse(localStorage.getItem(`lupia-decision-${d.obra_id}`) ?? "null");
      if (g && g.estado in cuenta) cuenta[g.estado]++;
    }
  } catch {}
  return cuenta;
})();
```

<div class="dos-columnas">
  <section class="bloque" aria-labelledby="riesgo">
    <h2 id="riesgo">Riesgo frente a monto</h2>
    <p>Las obras de la zona resaltada combinan un puntaje alto con un monto mayor que la mediana. El monto no entra en el puntaje: así se separa la probabilidad de la importancia.</p>
    <figure aria-label="Dispersión del puntaje de atención frente al monto vigente de cada obra">${resize((width) => dispersion(width))}</figure>
  </section>
  <section class="bloque pesos" aria-labelledby="pesos">
    <h2 id="pesos">Pesos del puntaje</h2>
    <p>El puntaje va de 0 a 100 y suma las cinco señales con estos pesos. Los iniciales son una propuesta del equipo, no de la CGR; muévalos y el orden se actualiza.</p>
    ${formPesos}
    <p>${html`<button class="boton secundario" type="button" onclick=${restablecerPesos}>Restablecer pesos</button>`}</p>
    <p class="tenue">Decisiones registradas en este navegador: ${plural(decisiones.Remitida, "alerta remitida", "alertas remitidas")} y ${plural(decisiones.Descartada, "descartada", "descartadas")}.</p>
    <p><a href="./metodologia.html">Cómo se calcula cada señal</a></p>
  </section>
</div>
