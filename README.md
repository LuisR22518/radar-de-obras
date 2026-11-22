# LupIA

LupIA (lupa + IA) es un prototipo de visualización para priorizar la fiscalización de obra pública con los datos de **dIAra** (CGR y Universidad CENFOTEC). Proyecto integrador del curso BCD 8215 Visualización de datos, LEAD University, 2026.

> Prototipo académico. No es una herramienta oficial de la Contraloría General de la República. Usa los datos reales que dIAra publicó de su piloto (2024) y, a partir de ellos, obras simuladas con nombres y contratistas seudonimizados.

## Cómo está armado: tres capas de datos

| Capa | Qué es | Quién la mantiene | Dónde vive |
| --- | --- | --- | --- |
| 1. dIAra | Detecciones de personas y máquinas por foto. Hoy: 8 días reales del piloto en la Escuela de Pococí (2024) | La Contraloría; nadie las edita a mano | `datos/diara/<cámara>/` |
| 2. Simulado | Obras ficticias cuya cámara "ve" fotos reales del piloto recombinadas por hora, con la sensibilidad del modelo | Se regenera en cada corrida (semilla fija) | `datos/simulados/` (no se guarda en el repositorio) |
| 3. Registro de obras | Base de datos propia: obras, cámaras, contratos, avance, pagos, reportes ciudadanos y feriados | La gerencia y los encargados de actualización de obra, en una [hoja de Google](https://docs.google.com/spreadsheets/d/1JKpAcmlTYHDmC1i9EuHFKIsWvBkFza8MNm9PfhiWP4Q/edit) | `datos/registro/` (copia que GitHub actualiza cada 15 minutos) |

El auditor solo lee. La gerencia y los encargados de actualización editan la hoja; cada 15 minutos GitHub la descarga, revisa su calidad y, si no hay errores, guarda los cambios con su bitácora (quién, cuándo, antes y después), recalcula y publica. Si la hoja trae errores, se conserva la última versión buena y la página **Mantenimiento del registro** dice qué corregir.

Para conectar datos nuevos de dIAra no hay que cambiar código: se copia la carpeta de la cámara en `datos/diara/` (el adaptador `radar/diara.py` reconoce el CSV de producción y las etiquetas del piloto) y se registra la cámara en la hoja.

LupIA le permite a un auditor **identificar, priorizar, filtrar, separar, analizar, contrastar, verificar y documentar** las obras que ameritan revisión. Tiene cinco páginas:

- **Qué revisar:** cuántas obras necesitan revisión, un mapa de Costa Rica y la lista en orden con la razón en palabras; búsqueda, descarga de la lista y, en paneles plegables, cómo se decide el orden, la importancia de cada señal y el cruce de riesgo y monto.
- **Ficha de cada obra:** por qué necesita revisión, datos clave y cinco pestañas: resumen (qué sabemos y qué no), actividad diaria, avance y pagos, fotos con detecciones (reales en la obra del piloto) y hallazgo y acción: criterio, condición, causa y efecto (NGASP 204), la acción elegida y su seguimiento, con expediente descargable.
- **Datos:** para el auditor. De dónde sale cada dato, qué tan al día está cada obra y qué no se puede afirmar con estos datos.
- **Mantenimiento del registro:** para la gerencia y los encargados de actualización (enlace al pie de cada página). Lo que hay que corregir o poner al día, el estado de cada obra, quién hace qué y los últimos cambios.
- **Cómo funciona:** los pasos, las cinco señales, de dónde salen los datos y quién los mantiene, y los límites; el detalle técnico va plegado.

## Cómo correrlo en tu computadora

Necesitas [Python 3.10 o más reciente](https://www.python.org/downloads/) y [Node.js 18 o más reciente](https://nodejs.org/).

```bash
pip install -r requirements.txt   # pandas, numpy, openpyxl y pillow
npm install                       # Observable Framework

python scripts/registro.py            # lee la hoja del registro (sin internet, usa la copia del repositorio)
python scripts/generar_simulados.py   # obras simuladas a partir del piloto real (siempre las mismas: semilla fija)
python scripts/clima.py               # lluvia real de Open-Meteo (sin internet usa la simulada)
python scripts/construir.py           # calcula estados, señales y puntaje en salidas/
python scripts/validar.py             # pruebas de calidad, de escenarios y de la obra real

npm run dev    # abre el sitio en http://127.0.0.1:3000 y se actualiza al guardar
npm run build  # genera el sitio estático en dist/
```

En Windows, si `python` no funciona, prueba con `py`.

## Cómo publicarlo en GitHub Pages

1. Crea un repositorio en GitHub y sube esta carpeta completa.
2. En el repositorio, ve a **Settings → Pages** y en **Source** elige **GitHub Actions**.
3. Cada vez que subas cambios a `main`, y cada 15 minutos, el flujo `.github/workflows/publicar.yml` lee la hoja del registro, recalcula los datos, corre las pruebas y publica el sitio. Si una prueba de calidad falla, no se publica.

Con la cuenta gratuita, GitHub Pages solo publica desde repositorios públicos. Con GitHub Pro, gratis para estudiantes con el Student Developer Pack, el código puede quedar privado y el sitio seguir siendo visible.

## Estructura

```
datos/
  diara/dIAra-K1/        datos reales del piloto de dIAra, sin modificar (ver FUENTE.md)
  registro/              copia de la hoja del registro: obras, camaras, eventos_contrato,
                         avance_reportado, pagos, reportes_ciudadanos, feriados y bitacora
  simulados/             generados por scripts/generar_simulados.py (no se guardan en git)
radar/
  config.py              todos los parámetros y umbrales en un solo lugar
  diara.py               adaptador: lee los formatos reales de dIAra
  registro.py            columnas, lectura y revisiones de calidad del registro
  lectura.py             junta las tres capas
  contrato.py            plazo y monto vigentes, suspensiones y avance previsto
  reglas.py              estado diario, matriz semanal, señales, puntaje y alertas
scripts/
  registro.py            lee la hoja de Google y guarda los cambios con su bitácora
  hoja_registro.py       arma la hoja (con instrucciones y validaciones) desde datos/registro/
  anonimizar_fotos.py    difumina a las personas en las fotos reales del piloto
  generar_simulados.py, clima.py, construir.py, validar.py
src/                     el sitio (Observable Framework)
  data/                  cargadores, mapa de Costa Rica y fotos del piloto anonimizadas
salidas/                 resultados de construir.py (para revisar en Excel si quieres)
```

## Cambiar las reglas

Todos los umbrales y pesos están en `radar/config.py`. Después de cambiarlos, corre `python scripts/construir.py` y `python scripts/validar.py`. Si una prueba de escenario falla, el cambio alteró lo que el auditor debería ver.

## Fuentes

- Repositorio de dIAra: https://github.com/cgrcostarica/dIAra (etiquetas y fotos del piloto, código de producción, firmware, clases, umbral y métricas).
- Normas Generales de Auditoría para el Sector Público, R-DC-064-2014 (CGR).
- Feriados 2024 y 2026: Ministerio de Trabajo y Seguridad Social (incluye el traslado del 11 al 15 de abril de 2024, comunicado CP-018-2024).
- Contorno de Costa Rica: Natural Earth (dominio público), vía world-atlas.
- Lluvia: Open-Meteo, https://open-meteo.com/ (CC BY 4.0).
- Observable Framework: https://observablehq.com/framework/

Detalle de qué es real y qué es simulado: `procedencia.md`.
