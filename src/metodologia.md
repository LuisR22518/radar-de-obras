---
title: Metodología y datos
---

```js
import {SENALES} from "./components/radar.js";
const resumen = await FileAttachment("data/resumen.json").json();
```

# Metodología y datos

El Radar convierte lo que produce dIAra en decisiones para el auditor: **identificar, priorizar, filtrar, separar, analizar, contrastar, verificar y documentar**. Señala situaciones que ameritan revisión; nunca afirma que haya irregularidades.

## De la foto al estado del día

1. **Captura.** Cada cámara toma fotos de 5:00 a 17:59, según su firmware. La muestra real del repositorio va cada 80 segundos; el prototipo usa una foto cada 10 minutos para que los archivos sean manejables.
2. **Detección.** El modelo de dIAra (Faster R-CNN) busca 6 clases (Persona, Vagoneta, Tractor, Cargador, Mezcladora y Aplanadora) y solo guarda las detecciones con probabilidad mayor que 0,7. Escribe un CSV por día con las columnas `nombre_imagen`, `clase`, `probabilidad` y `recuadro`.
3. **Limpieza.** En producción, la probabilidad y el recuadro quedan escritos como tensores de PyTorch, por ejemplo `tensor(0.9761)`. El Radar los convierte en números, une los CSV diarios y agrega la cámara y la hora a partir del nombre de la imagen.
4. **Inventario de capturas.** El CSV de dIAra solo registra fotos con detecciones, así que, por sí solo, no distingue un día sin datos de un día sin actividad. Por eso el Radar propone un inventario de las fotos recibidas: el «latido» de cada cámara.
5. **Estado del día.**
    - **Sin datos:** llegó menos del 50 % de las fotos esperadas.
    - **Actividad:** el 15 % o más de las fotos en horario laboral (6:00 a 16:59) tiene al menos una detección.
    - **Sin actividad:** el resto.
6. **Contexto.** Cada día sin actividad se cruza con los feriados oficiales, las suspensiones aprobadas y la lluvia diaria (fuerte desde 20 mm).

## Señales y puntaje de atención

Cada señal va de 0 a 1. El puntaje (0 a 100) es la suma ponderada de las cinco señales. El auditor puede mover los pesos en la cartera. Una señal es **alerta** cuando supera su umbral.

```js
const umbral = resumen.umbrales_alerta;
const regla = {
  inactividad: "Días hábiles seguidos sin actividad con la cámara funcionando; 10 días = 1. Fines de semana, feriados y días sin datos no suman ni cortan la racha.",
  atraso: "Avance previsto por el cronograma vigente menos el avance reportado; 20 puntos = 1.",
  brecha: "Proporción del avance típico de 12 semanas que la ejecutora reportó, menos la proporción de semanas con actividad observada.",
  contrato: "Aumento del monto (20 % = 1) o prórroga aprobada en los últimos 90 días (0,5).",
  ciudadania: "Reportes ciudadanos en los últimos 30 días; 3 reportes = 1."
};
display(Inputs.table(SENALES.map((s) => ({
  "Señal": s.label, "Cómo se calcula": regla[s.key], "Peso inicial": resumen.pesos[s.key], "Alerta desde": umbral[s.key]
})), {select: false, layout: "auto", rows: 6}));
```

- **Cola de dispositivos:** una cámara con 3 días seguidos sin datos va a mantenimiento. Su obra no compite por la atención del auditor, porque no se puede concluir nada sobre ella.
- **Obra terminada:** después de la recepción provisional, la obra no genera alertas.
- **Monto:** no entra en el puntaje. Va en el otro eje de la dispersión, para separar la probabilidad de la importancia, como en una matriz de riesgo.

Todos los umbrales y pesos son **supuestos del equipo, no de la CGR**, y están en `radar/config.py`. Las necesidades que atienden salen de las Normas Generales de Auditoría para el Sector Público (R-DC-064-2014): la valoración del riesgo para seleccionar qué examinar (norma 203.04), la evidencia suficiente, competente y pertinente (207.01) y los papeles de trabajo (208.02 y 208.04).

## Procedencia de los datos

| Dato | Origen | Estado |
| --- | --- | --- |
| Obras (tipo, cantón, monto, plazo) | Valores realistas, inspirados en obras públicas; nombres y contratistas seudonimizados | Ejemplo, a reemplazar por datos de SICOP o PROERI |
| Formato del CSV, clases, umbral y horario de captura | Repositorio público de dIAra (CGR y Universidad CENFOTEC) | Real |
| Detecciones e inventario de capturas | Generados con semilla fija según 8 escenarios | Simulado |
| Avance reportado, pagos y eventos de contrato | Generados según los escenarios | Simulado |
| Reportes ciudadanos | Redactados para los escenarios | Simulado |
| Feriados | Calendario 2026 del Ministerio de Trabajo | Real |
| Lluvia diaria | Open-Meteo (CC BY 4.0) cuando hay conexión; si no, simulada | Origen actual: ${resumen.origen_clima.join(", ")} |

Las obras se seudonimizan a propósito: las señales son simuladas, y ponerlas sobre obras y contratistas reales podría exponer injustamente a alguien.

## Limitaciones

- La cámara mide presencia de personas y máquinas, no avance físico.
- El modelo de dIAra detecta unas 85 de cada 100 personas visibles (sensibilidad de 85,4 %) y se entrenó solo con imágenes de la Escuela de Pocosí; puede funcionar peor en otras obras.
- El avance previsto usa una curva en S aproximada mientras no se tenga el cronograma real de cada obra.
- Los pesos y umbrales no están validados con la CGR: se ajustan con las pruebas de usabilidad.

## Escenarios simulados

| Obra | Escenario | Qué debe ver el auditor |
| --- | --- | --- |
| A | Paralizada desde el 19 de octubre; monto alto | Prioridad 1: inactividad, atraso y reportes ciudadanos |
| B | Cámara caída desde el 12 de noviembre | Cola de dispositivos, no de obras |
| C | Actividad en 3 de 12 semanas, pero reporta avance normal | Brecha entre lo reportado y lo observado |
| D | Atrasada, con prórroga aprobada | Atraso y cambio contractual |
| E | Sin actividad del 16 al 20 de noviembre por una suspensión aprobada | Alerta con explicación: se descarta con motivo |
| F | Activa y al día | Control: sin alertas |
| G | Recibida el 25 de septiembre | Terminada: sin alertas |
| H | Aumento de monto y reportes ciudadanos repetidos | Contrato y ciudadanía |
