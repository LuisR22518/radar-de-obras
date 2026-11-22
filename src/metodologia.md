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
const tablaSenales = html`<table>
  <thead><tr><th scope="col">Señal</th><th scope="col">Cómo se calcula</th><th scope="col">Peso inicial</th><th scope="col">Alerta desde</th></tr></thead>
  <tbody>${SENALES.map((s) => html`<tr><td><strong>${s.label}</strong></td><td>${regla[s.key]}</td><td>${resumen.pesos[s.key]}</td><td>${String(resumen.umbrales_alerta[s.key]).replace(".", ",")}</td></tr>`)}</tbody>
</table>`;
```

<div class="lectura">

# Cómo funciona LupIA

LupIA ayuda a los auditores de la Contraloría a decidir qué obras públicas revisar primero. Convierte lo que ven las cámaras de dIAra en señales explicables y respaldadas con evidencia. Indica dónde conviene revisar; nunca afirma que haya una irregularidad.

<p class="tenue">Datos al ${fechaTexto(resumen.fecha_corte)}.</p>

## En cuatro pasos

1. **La cámara toma fotos** de la obra durante el día.
2. **dIAra reconoce** personas y máquinas en cada foto.
3. **LupIA resume cada día** como actividad, sin actividad o sin datos de la cámara, y lo cruza con feriados, suspensiones y lluvia.
4. **LupIA compara** esa actividad con el contrato, el avance reportado y los reportes ciudadanos, y ordena las obras.

## Las cinco señales

Cada señal va de 0 a 1. Si una pasa su límite, la obra necesita revisión. El puntaje, de 0 a 100, suma las señales según su importancia y decide el orden.

${tablaSenales}

## Datos y actualización

LupIA solo lee datos: no permite agregar ni modificar obras. Cada dato debe venir de su fuente oficial para que la evidencia sea competente; cambiarlo a mano dentro de la herramienta la debilitaría.

| Dato | Fuente esperada | Quién lo mantiene | Cada cuánto | En este prototipo |
| --- | --- | --- | --- | --- |
| Lista de obras y contratos | SICOP | Institución ejecutora | Al firmar o modificar el contrato | Ejemplo seudonimizado |
| Detecciones e inventario de fotos | dIAra | Contraloría (equipo de dIAra) | Diario | Simulado con el formato real |
| Avance reportado y pagos | Informes de la ejecutora | Institución ejecutora | Quincenal o mensual | Simulado |
| Reportes ciudadanos | Canal de denuncias | Contraloría | Al recibirse | Simulado |
| Feriados | Ministerio de Trabajo | Equipo de LupIA | Anual | Real |
| Lluvia | Open-Meteo | Automático | Diario | ${(([s]) => s.charAt(0).toUpperCase() + s.slice(1))([resumen.origen_clima.join(", ")])} |

Quién mantiene cada dato dentro de la Contraloría está por confirmar con la institución. La página se reconstruye sola cada día a las 6:00 (hora de Costa Rica) y cada vez que cambian los datos.

## Límites

- La cámara ve personas y máquinas, no avance físico.
- El modelo de dIAra detecta unas 85 de cada 100 personas visibles y se entrenó solo con imágenes de la Escuela de Pocosí; en otras obras puede funcionar peor.
- Los límites y la importancia de cada señal son propuestas del equipo, no de la Contraloría; se ajustan con las pruebas de usabilidad.

<details class="panel">
<summary>Detalle técnico</summary>

### De la foto al estado del día

1. **Captura.** Cada cámara toma fotos de 5:00 a 17:59, según su firmware. La muestra real del repositorio de dIAra va cada 80 segundos; el prototipo usa una foto cada 10 minutos para que los archivos sean manejables.
2. **Detección.** El modelo de dIAra (Faster R-CNN) busca seis clases: persona, vagoneta, tractor, cargador, mezcladora y aplanadora. Solo guarda las detecciones con probabilidad mayor que 0,7, en un CSV por día con las columnas `nombre_imagen`, `clase`, `probabilidad` y `recuadro`.
3. **Limpieza.** En producción, la probabilidad y el recuadro quedan escritos como tensores de PyTorch, por ejemplo `tensor(0.9761)`. LupIA los convierte en números, une los archivos diarios y obtiene la cámara y la hora del nombre de cada imagen.
4. **Inventario de capturas.** El CSV de dIAra solo registra fotos con detecciones; por sí solo no distingue un día sin datos de un día sin actividad. Por eso LupIA usa un inventario de las fotos recibidas: el latido de cada cámara.
5. **Estado del día.** Sin datos, si llegó menos del 50 % de las fotos esperadas. Actividad, si el 15 % o más de las fotos en horario laboral (6:00 a 16:59) tiene alguna detección. Sin actividad, en el resto.
6. **Contexto.** Cada día sin actividad se cruza con los feriados oficiales, las suspensiones aprobadas y la lluvia diaria; desde 20 mm cuenta como lluvia fuerte.

Una cámara con 3 días seguidos sin datos pasa a mantenimiento: su obra no compite por la atención del auditor, porque no se puede concluir nada sobre ella. Después de la recepción provisional, una obra no genera alertas. El monto no entra en el puntaje; va en el otro eje de la dispersión, como en una matriz de riesgo.

Todos los umbrales y pesos son supuestos del equipo, no de la CGR, y están en `radar/config.py`. Las necesidades que atienden vienen de las Normas Generales de Auditoría para el Sector Público (R-DC-064-2014): valorar el riesgo para elegir qué examinar (norma 203.04), contar con evidencia suficiente, competente y pertinente (207.01) y documentar en papeles de trabajo (208.02 y 208.04).

### Origen de cada dato

| Dato | Origen | Estado |
| --- | --- | --- |
| Obras: tipo, cantón, monto y plazo | Valores realistas inspirados en obras públicas, con nombres y contratistas seudonimizados | Ejemplo, a reemplazar por datos de SICOP o PROERI |
| Formato del CSV, clases, umbral y horario | Repositorio público de dIAra (CGR y Universidad CENFOTEC) | Real |
| Detecciones e inventario de capturas | Generados con semilla fija según 8 escenarios | Simulado |
| Avance reportado, pagos y eventos del contrato | Generados según los escenarios | Simulado |
| Reportes ciudadanos | Redactados para los escenarios | Simulado |
| Feriados | Calendario 2026 del Ministerio de Trabajo | Real |
| Lluvia diaria | Open-Meteo (CC BY 4.0) cuando hay conexión; si no, simulada | ${resumen.origen_clima.join(", ")} |

Las obras están seudonimizadas a propósito: las señales son simuladas, y ponerlas sobre obras y contratistas reales podría exponer injustamente a alguien.

### Escenarios simulados

| Obra | Qué ocurre | Qué debe ver el auditor |
| --- | --- | --- |
| A | Paralizada desde el 19 de octubre; monto alto | Prioridad 1: inactividad, atraso y reportes ciudadanos |
| B | Cámara caída desde el 12 de noviembre | Cola de dispositivos, no de obras |
| C | Actividad en 3 de 12 semanas, aunque reporta avance normal | Brecha entre lo reportado y lo observado |
| D | Atrasada, con prórroga aprobada | Atraso y cambio contractual |
| E | Sin actividad del 16 al 20 de noviembre por una suspensión aprobada | Alerta con explicación: se descarta con motivo |
| F | Activa y al día | Control: sin alertas |
| G | Recibida el 25 de septiembre | Terminada: sin alertas |
| H | Aumento de monto y reportes ciudadanos repetidos | Contrato y ciudadanía |


</details>

</div>
