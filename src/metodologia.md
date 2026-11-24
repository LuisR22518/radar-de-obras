---
title: Cómo funciona
---

```js
import {SENALES, fechaTexto} from "./components/lupia.js";
const resumen = await FileAttachment("data/resumen.json").json();
const regla = {
  inactividad: "Días hábiles seguidos sin actividad con la cámara funcionando; 10 días equivalen a 1. Fines de semana, feriados y días sin datos no suman ni cortan la racha.",
  atraso: "Avance previsto por el cronograma vigente menos el avance reportado; 20 puntos equivalen a 1.",
  brecha: "Parte del avance típico de 12 semanas que la ejecutora reportó, menos la parte de esas semanas con actividad observada.",
  contrato: "Aumento del monto (20 % equivale a 1) o una prórroga aprobada en los últimos 90 días (0,5).",
  ciudadania: "Reportes ciudadanos en los últimos 30 días; 3 reportes equivalen a 1."
};
// Desde cuántos días hábiles sin actividad hay alerta (sale de radar/config.py a través de resumen.json)
const diasAlerta = resumen.metodo?.dias_alerta_inactividad ?? Math.round(10 * resumen.umbrales_alerta.inactividad);
const tablaSenales = html`<table>
  <thead><tr><th scope="col">Señal</th><th scope="col">Cómo se calcula</th><th scope="col">Peso inicial</th><th scope="col">Alerta desde</th></tr></thead>
  <tbody>${SENALES.map((s) => html`<tr><td><strong>${s.label}</strong></td><td>${regla[s.key]}</td><td>${resumen.pesos[s.key]}</td><td>${String(resumen.umbrales_alerta[s.key]).replace(".", ",")}</td></tr>`)}</tbody>
</table>`;
```

```js
// En celular las tablas anchas se deslizan hacia los lados: las que se deslizan se pueden enfocar para moverlas con el teclado
{
  const ajustar = () => {
    for (const t of document.querySelectorAll(".lectura table")) {
      if (t.scrollWidth > t.clientWidth + 1) { t.tabIndex = 0; if (!t.hasAttribute("aria-label")) t.setAttribute("aria-label", "Tabla que se desliza hacia los lados"); }
      else { t.removeAttribute("tabindex"); }
    }
  };
  const espera = setTimeout(ajustar, 300);
  addEventListener("resize", ajustar);
  invalidation.then(() => { clearTimeout(espera); removeEventListener("resize", ajustar); });
}
```

<div class="lectura">

# Cómo funciona LupIA

LupIA usa las cámaras de dIAra para mostrar si hubo trabajo en una obra pública. Sirve a dos públicos: a las personas que quieren saber cómo va la obra de su comunidad y a los fiscalizadores de la Contraloría, que deciden qué obras revisar primero. Indica dónde conviene mirar; nunca afirma que haya una irregularidad.

<p class="tenue">Datos al ${fechaTexto(resumen.fecha_corte)}.</p>

<p class="indice">En esta página: <a href="#para-la-ciudadania">Para la ciudadanía</a> · <a href="#para-fiscalizadores">Para fiscalizadores</a> · <a href="#datos-y-actualizacion">Datos y actualización</a> · <a href="#limites">Límites</a></p>

<h2 id="para-la-ciudadania">Para la ciudadanía: cómo leer la ficha de una obra</h2>

1. **La respuesta rápida** dice si la cámara vio trabajo. En verde azulado, hubo trabajo normal; en ámbar, hay algo que conviene revisar; en gris, la cámara no envió fotos y no se puede concluir nada.
2. **Qué tan confiable es el dato:** cuántos días envió fotos la cámara. Si hay vacíos, el dato vale menos.
3. **Las semanas:** un cuadro por semana. Lleno, si hubo trabajo; con borde ámbar, si no lo hubo; rayado, si no llegaron fotos. Toque una semana para ver cada día.
4. **Costo, entrega y avance:** lo que dicen el contrato y la ejecutora. La cámara no mide el avance: ve personas y máquinas.
5. **Qué no se puede concluir:** lluvia, feriados, suspensiones o trabajo fuera del ángulo de la cámara pueden explicar un día sin actividad.
6. **Qué puede hacer:** compartir la ficha por WhatsApp o armar un reporte con la evidencia para la Denuncia Digital de la Contraloría. LupIA no recibe denuncias.

<h2 id="para-fiscalizadores">Para fiscalizadores: cómo se ordenan las obras</h2>

### En cuatro pasos

1. **La cámara toma fotos** de la obra durante el día.
2. **dIAra reconoce** personas y máquinas en cada foto.
3. **LupIA resume cada día** como actividad, sin actividad o sin datos de la cámara, y lo cruza con feriados, suspensiones y lluvia.
4. **LupIA compara** esa actividad con el contrato, el avance reportado y los reportes ciudadanos, y ordena las obras.

### Las cinco señales

Cada señal va de 0 a 1. Si una pasa su límite, la obra necesita revisión. El puntaje, de 0 a 100, suma las señales según su importancia y decide el orden.

${tablaSenales}

### Alerta temprana, no declaratoria de paralización

LupIA marca alerta desde ${diasAlerta} días hábiles seguidos sin personas ni máquinas, con la cámara funcionando. Es un aviso para revisar, no una declaratoria. Como referencia, la Contraloría de Perú considera paralizada una obra que no reporta avance físico durante seis meses o más (<a href="https://www.gob.pe/institucion/contraloria/noticias/896326-en-peru-existen-cerca-de-2300-obras-publicas-paralizadas-por-mas-de-s-26-mil-millones-a-diciembre-del-2023" target="_blank" rel="noopener">nota de la Contraloría de Perú</a>). Las dos medidas no son iguales, porque LupIA mide actividad observada y no avance físico, pero muestran la ventaja de la cámara: avisar meses antes.

<h2 id="datos-y-actualizacion">Datos y actualización</h2>

LupIA trabaja con tres capas. El auditor solo lee; los datos los mantiene quien corresponde y cada cambio queda registrado. Detalle por obra en <a href="./datos.html">Datos</a>.

| Capa | Qué contiene | Quién la mantiene | En este prototipo |
| --- | --- | --- | --- |
| dIAra | Detecciones de personas y máquinas por foto | La Contraloría (equipo de dIAra); nadie las edita | 8 días reales del piloto (2024) y 8 obras simuladas a partir de ellos |
| Registro de obras | Obras, cámaras, contratos, avance, pagos, reportes y feriados | La gerencia y los encargados de actualización de obra, en una hoja de Google | Obras ficticias y seudonimizadas; feriados reales |
| Contexto | Lluvia diaria | Automático (Open-Meteo) | ${(([s]) => s.charAt(0).toUpperCase() + s.slice(1))([resumen.origen_clima.join(", ")])} |

Varias veces al día (o al momento, con «Publicar ahora» en Mantenimiento), LupIA lee la hoja del registro y revisa su calidad. Si encuentra errores, conserva la última versión buena y lo avisa; si no, recalcula todo y publica. Qué cargos cumplen esos roles dentro de la Contraloría está por confirmar con la institución.

<h2 id="limites">Límites</h2>

- La cámara ve personas y máquinas, no avance físico.
- El modelo de dIAra encuentra unos 85 de cada 100 objetos visibles y se entrenó solo con fotos de la Escuela de Pococí; en otras obras puede funcionar peor.
- Los datos públicos del piloto cubren 8 días y no traen el inventario de fotos: un día sin archivo puede ser un día sin trabajo o con la cámara apagada.
- Las obras simuladas recombinan fotos reales del piloto: su actividad es realista, pero su contrato, sus informes y sus reportes son ficticios.
- Los límites y la importancia de cada señal son propuestas del equipo, no de la Contraloría; se ajustan con las pruebas de usabilidad.

<details class="panel">
<summary>Detalle técnico</summary>

### De la foto al estado del día

1. **Captura.** Cada cámara toma fotos de 5:00 a 17:59, según su firmware, una cada 80 segundos aproximadamente (585 por día), como en las fotos del piloto.
2. **Detección.** El modelo de dIAra (Faster R-CNN) busca seis clases: persona, vagoneta, tractor, cargador, mezcladora y aplanadora. Solo guarda las detecciones con probabilidad mayor que 0,7, en un CSV por día con las columnas `nombre_imagen`, `clase`, `probabilidad` y `recuadro`.
3. **Lectura.** Un adaptador (`radar/diara.py`) reconoce solo tres formatos de dIAra: el CSV de producción, donde la probabilidad y el recuadro vienen escritos como tensores de PyTorch (`tensor(0.9761)`), y las etiquetas del piloto en CSV y en JSON. Traduce las clases al español, convierte los números y obtiene la cámara y la hora del nombre de cada foto.
4. **Inventario de capturas.** El CSV de dIAra solo registra fotos con detecciones; por sí solo no distingue un día sin datos de un día sin actividad. Por eso LupIA propone un inventario de las fotos recibidas, el latido de cada cámara. Las cámaras simuladas lo tienen; la del piloto no: para ella, un día con archivo se toma como día con cámara funcionando y un día sin archivo, como sin datos.
5. **Estado del día.** Sin datos, si llegó menos del 50 % de las fotos esperadas (o, sin inventario, si no hay archivo). Actividad, si el 15 % o más de las fotos en horario laboral (6:00 a 16:59) tiene alguna detección. Sin actividad, en el resto.
6. **Contexto.** Cada día sin actividad se cruza con los feriados oficiales, las suspensiones aprobadas y la lluvia diaria; desde 20 mm cuenta como lluvia fuerte.

Una cámara con 3 días seguidos sin datos pasa a mantenimiento: su obra no compite por la atención del auditor, porque no se puede concluir nada sobre ella. Después de la recepción provisional, una obra no genera alertas. El monto no entra en el puntaje: solo desempata. Si dos obras tienen el mismo puntaje, va antes la de mayor monto.

Todos los umbrales y pesos son supuestos del equipo, no de la CGR, y están en `radar/config.py`. Las necesidades que atienden vienen de las Normas Generales de Auditoría para el Sector Público (R-DC-064-2014): valorar el riesgo para elegir qué examinar (norma 203.04), contar con evidencia suficiente, competente y pertinente (207.01) y documentar en papeles de trabajo (208.02 y 208.04).

### Origen de cada dato

| Dato | Origen | Estado |
| --- | --- | --- |
| Detecciones del piloto (8 días de 2024) y 6 fotos | Repositorio público de dIAra (CGR, CENFOTEC y GIZ), etiquetas hechas por personas; fotos con las personas difuminadas | Real |
| Formato del CSV, clases, umbral, horario e intervalo de captura | Código de producción y firmware del repositorio de dIAra | Real |
| Detecciones de las obras simuladas | Fotos reales del piloto recombinadas por hora, con la sensibilidad del modelo (85,4 %) y semilla fija por obra | Simulado a partir de datos reales |
| Obras: tipo, cantón, monto y plazo | Valores realistas, con nombres y contratistas seudonimizados, en el registro | Ejemplo, a reemplazar por datos de SICOP o PROERI |
| Avance reportado, pagos, eventos del contrato y reportes ciudadanos | Registro de obras | Simulado |
| Feriados 2024 y 2026 | Ministerio de Trabajo (incluye el traslado del 11 al 15 de abril de 2024) | Real |
| Lluvia diaria | Open-Meteo (CC BY 4.0) cuando hay conexión; si no, simulada | ${resumen.origen_clima.join(", ")} |

Las obras simuladas están seudonimizadas a propósito: sus señales son ficticias, y ponerlas sobre obras y contratistas reales podría exponer injustamente a alguien.

### Escenarios simulados

| Obra | Qué ocurre | Qué debe ver el auditor |
| --- | --- | --- |
| A | Paralizada desde el 19 de octubre; monto alto | Prioridad 1: inactividad, atraso y reportes ciudadanos |
| B | Cámara caída desde el 12 de noviembre | Cola de dispositivos, no de obras |
| C | Trabaja una semana de cada cuatro, aunque reporta avance normal | Brecha entre lo reportado y lo observado |
| D | Atrasada, con prórroga aprobada | Atraso y cambio contractual |
| E | Sin actividad del 16 al 20 de noviembre por una suspensión aprobada | Alerta con explicación: se descarta con motivo |
| F | Activa y al día | Control: sin alertas |
| G | Recibida el 25 de septiembre | Terminada: sin alertas |
| H | Aumento de monto y reportes ciudadanos repetidos | Contrato y ciudadanía |
| P | Obra real del piloto de dIAra (2024), sin contrato público | Monitoreo terminado; solo las señales con dato |


</details>

</div>
