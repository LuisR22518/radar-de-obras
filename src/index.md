---
title: Cartera
---

<div class="banner">Prototipo académico · detecciones simuladas con el formato real de dIAra · obras y contratistas seudonimizados</div>

```js
import {Plot, fecha, fechaLarga, hora, millones, ESTADOS, escalaEstados, leyendaEstados, SENALES, nombreSenal, nombreCorto, puntaje, asegurarRayado} from "./components/radar.js";
asegurarRayado();
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const semanal = await FileAttachment("data/matriz_semanal.csv").csv({typed: true});
const resumen = await FileAttachment("data/resumen.json").json();
const UMBRAL_PUNTAJE_ALTO = 30; // desde aquí, el puntaje se considera alto en la dispersión
const etiqueta = (d) => `${d.obra_id} · ${d.nombre}`;
```

# Radar de Obras

<div class="frase">${resumen.frase}</div>
<div class="corte">Datos al ${fechaLarga(resumen.fecha_corte)} · ${senales.length} obras con cámara · tareas 1 a 4: identificar, priorizar, filtrar y separar</div>

```js
const opciones = (campo) => ["Todas", ...new Set(senales.map((d) => d[campo]).sort())];
const filtroInstitucion = Inputs.select(opciones("institucion_ejecutora"), {label: "Institución"});
const filtroContratista = Inputs.select(opciones("contratista"), {label: "Contratista"});
const filtroTipo = Inputs.select(opciones("tipo"), {label: "Tipo de obra"});
const institucion = Generators.input(filtroInstitucion);
const contratista = Generators.input(filtroContratista);
const tipo = Generators.input(filtroTipo);
display(html`<div style="display: flex; gap: 0 1.5rem; flex-wrap: wrap;">${filtroInstitucion}${filtroContratista}${filtroTipo}</div>`);
```

<details class="pesos no-imprimir">
<summary><strong>Pesos del puntaje</strong> · muévelos para ver cómo cambia la prioridad</summary>

```js
const formPesos = Inputs.form(
  Object.fromEntries(SENALES.map((s) => [s.key, Inputs.range([0, 50], {step: 5, value: resumen.pesos[s.key], label: s.label, width: 260})]))
);
const pesos = Generators.input(formPesos);
display(formPesos);
```

<p class="nota">El puntaje se recalcula de 0 a 100 con estos pesos. Los pesos iniciales (30, 20, 20, 15 y 15) son una propuesta del equipo, no de la CGR.</p>
</details>

```js
const filas = senales
  .filter((d) => (institucion === "Todas" || d.institucion_ejecutora === institucion)
    && (contratista === "Todas" || d.contratista === contratista)
    && (tipo === "Todas" || d.tipo === tipo))
  .map((d) => ({...d, puntaje_vivo: puntaje(d, pesos)}))
  .sort((a, b) => (b.amerita_revision - a.amerita_revision) || (b.puntaje_vivo - a.puntaje_vivo));
const orden = filas.map(etiqueta);
const sumaPesos = SENALES.reduce((a, s) => a + pesos[s.key], 0) || 1;
```

```js
function matriz(width) {
  const porId = new Map(filas.map((d) => [d.obra_id, d]));
  const datos = semanal
    .filter((d) => porId.has(d.obra_id))
    .map((d) => ({...d, obra: etiqueta(porId.get(d.obra_id)), estado: ESTADOS[d.estado_semana].label}));
  return Plot.plot({
    width,
    height: 40 + 32 * filas.length,
    marginLeft: 190,
    marginBottom: 30,
    marginTop: 8,
    x: {type: "band", label: null, tickFormat: (d, i) => (i % 3 === 0 ? fecha(d) : ""), tickSize: 0, padding: 0.12},
    y: {domain: orden, label: null, padding: 0.12},
    color: escalaEstados(),
    marks: [
      Plot.cell(datos, {
        x: "semana", y: "obra", fill: "estado", stroke: "var(--vacio-borde)", strokeWidth: 0.75, rx: 3,
        title: (d) => `${d.obra}\nSemana del ${fecha(d.semana)}\n${d.estado} · ${d.dias_actividad} días con actividad` +
          (d.con_explicacion ? "\nTiene explicación: feriado, suspensión o lluvia" : ""),
        tip: true
      }),
      Plot.dot(datos.filter((d) => d.con_explicacion), {x: "semana", y: "obra", r: 3.5, fill: "var(--theme-foreground-muted)"})
    ]
  });
}

function dispersion(width) {
  const datos = filas.filter((d) => d.fase !== "terminada" && !d.en_cola_dispositivos);
  const medianaMonto = d3.median(senales, (d) => d.monto_vigente_crc);
  return Plot.plot({
    width,
    height: 320,
    marginLeft: 56,
    marginTop: 26,
    x: {domain: [0, 100], label: "Puntaje de atención →", grid: true},
    y: {type: "log", domain: [1.5e8, 4e9], label: "↑ Monto vigente (₡ millones)", grid: true,
        tickFormat: (d) => (d / 1e6).toLocaleString("es-CR"), ticks: [2e8, 5e8, 1e9, 2e9]},
    color: {domain: ["Amerita revisión", "Sin alertas"], range: ["var(--s1)", "var(--theme-foreground-faint)"], legend: true},
    marks: [
      Plot.rect([0], {x1: UMBRAL_PUNTAJE_ALTO, x2: 100, y1: medianaMonto, y2: 4e9, fill: "var(--tinte)"}),
      Plot.text([0], {x: 99, y: 3.6e9, text: () => "revisar primero", textAnchor: "end", fill: "var(--theme-foreground-muted)"}),
      Plot.dot(datos, {
        x: "puntaje_vivo", y: "monto_vigente_crc", r: 7, stroke: "var(--theme-background)", strokeWidth: 2,
        fill: (d) => (d.amerita_revision ? "Amerita revisión" : "Sin alertas"),
        title: (d) => `${etiqueta(d)}\nPuntaje ${Math.round(d.puntaje_vivo)} · ${millones(d.monto_vigente_crc)}`, tip: true
      }),
      Plot.text(datos, {x: "puntaje_vivo", y: "monto_vigente_crc", text: "obra_id", dx: -13, fontWeight: 600})
    ]
  });
}
```

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Matriz de cartera</h2>
    <h3>Una celda por semana: ¿hubo actividad, no la hubo o faltaron datos?</h3>
    ${leyendaEstados(html)}
    ${resize((width) => matriz(width))}
    <p class="nota">● = la semana sin actividad tiene una explicación posible (feriado, suspensión aprobada o lluvia fuerte). Pasa el cursor por una celda para ver el detalle.</p>
  </div>
  <div class="card">
    <h2>Riesgo frente a monto</h2>
    <h3>Arriba a la derecha: puntaje alto y monto mayor que la mediana</h3>
    ${resize((width) => dispersion(width))}
    <p class="nota">El monto no entra en el puntaje: va en el otro eje, para separar la probabilidad de la importancia, como en una matriz de riesgo.</p>
  </div>
</div>

```js
function desglose(width) {
  const datos = filas.flatMap((d) => SENALES.map((s) => ({
    obra: etiqueta(d), senal: s.label, aporte: (100 * pesos[s.key] * d[`senal_${s.key}`]) / sumaPesos
  }))).filter((d) => d.aporte > 0);
  return Plot.plot({
    width,
    height: 70 + 30 * filas.length,
    marginLeft: 190,
    x: {domain: [0, 100], label: "Aporte al puntaje →", grid: true},
    y: {domain: orden, label: null},
    color: {domain: SENALES.map((s) => s.label), range: SENALES.map((s) => s.color), legend: true},
    marks: [
      Plot.barX(datos, Plot.stackX({
        x: "aporte", y: "obra", fill: "senal", order: SENALES.map((s) => s.label), inset: 1, rx: 2,
        title: (d) => `${d.obra}\n${d.senal}: ${d.aporte.toFixed(1)} puntos`, tip: true
      })),
      Plot.ruleX([0], {stroke: "var(--theme-foreground-faint)"})
    ]
  });
}
```

<div class="card">
  <h2>Por qué cada obra tiene ese puntaje</h2>
  <h3>Cuánto aporta cada señal, con los pesos actuales</h3>
  ${resize((width) => desglose(width))}
</div>

```js
const cola = senales.filter((d) => d.en_cola_dispositivos);
const decisiones = (() => {
  const cuenta = {Remitida: 0, Descartada: 0};
  try {
    for (const d of senales) {
      const g = JSON.parse(localStorage.getItem(`radar-decision-${d.obra_id}`) ?? "null");
      if (g && g.estado in cuenta) cuenta[g.estado]++;
    }
  } catch {}
  return cuenta;
})();
```

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Cola de dispositivos</h2>
    <h3>Cámaras sin datos: van a mantenimiento, no a fiscalización</h3>
    ${cola.length ? cola.map((d) => html`<p><span class="chip disp">${d.obra_id} · ${d.nombre}</span><br>La cámara lleva <strong>${d.dias_sin_datos} días</strong> sin enviar datos (última captura: ${fecha(d.ultima_captura)}, ${hora(d.ultima_captura)}). No se puede concluir nada sobre la obra hasta repararla.</p>`) : html`<p>Todas las cámaras están enviando datos.</p>`}
  </div>
  <div class="card">
    <h2>Decisiones registradas</h2>
    <h3>En este navegador, desde el análisis de cada obra</h3>
    <p><strong>${decisiones.Remitida}</strong> alertas remitidas · <strong>${decisiones.Descartada}</strong> descartadas con motivo</p>
    <p class="nota">Con el tiempo, esta proporción indica qué tan útiles son las alertas y sirve para ajustar los pesos.</p>
  </div>
</div>

```js
const tabla = filas.map((d) => ({
  Prioridad: d.prioridad, Obra: d.obra_id, Nombre: d.nombre, Puntaje: Math.round(d.puntaje_vivo),
  Alertas: d.en_cola_dispositivos ? "Cámara sin datos" : (d.alertas ? String(d.alertas).split(";").map((a) => nombreCorto[a]).join(" · ") : "—"),
  Monto: d.monto_vigente_crc, Analizar: d.obra_id
}));
display(Inputs.table(tabla, {
  select: false, rows: 10, layout: "auto",
  format: {Monto: millones, Analizar: (id) => html`<a href="./obra?id=${id}">Analizar →</a>`}
}));
```
