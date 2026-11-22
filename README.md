# LupIA

LupIA (lupa + IA) es un prototipo de visualización para priorizar la fiscalización de obra pública con los datos de **dIAra** (CGR y Universidad CENFOTEC). Proyecto integrador del curso BCD 8215 Visualización de datos, LEAD University, 2026.

> Prototipo académico. No es una herramienta oficial de la Contraloría General de la República. Las detecciones son simuladas con el formato real de dIAra, y las obras y los contratistas están seudonimizados.

LupIA le permite a un auditor **identificar, priorizar, filtrar, separar, analizar, contrastar, verificar y documentar** las obras que ameritan revisión. Tiene tres páginas:

- **Orden de revisión:** la obra que conviene revisar primero y por qué, el orden de todas las obras con su pulso de 12 semanas y sus señales, riesgo frente a monto y pesos ajustables.
- **Análisis de obra:** alertas explicadas, línea de tiempo con contexto (feriados, suspensiones, lluvia y reportes ciudadanos), contraste entre lo reportado y lo observado, visor de evidencia, comparación y registro con expediente descargable.
- **Metodología:** reglas, umbrales, procedencia y limitaciones.

## Cómo correrlo en tu computadora

Necesitas [Python 3.10 o más reciente](https://www.python.org/downloads/) y [Node.js 18 o más reciente](https://nodejs.org/).

```bash
pip install -r requirements.txt   # pandas y numpy
npm install                       # Observable Framework

python scripts/generar_simulados.py   # datos simulados (siempre los mismos: semilla fija)
python scripts/clima.py               # lluvia real de Open-Meteo (opcional; sin internet usa la simulada)
python scripts/construir.py           # calcula estados, señales y puntaje en salidas/
python scripts/validar.py             # 16 pruebas de calidad y de escenarios

npm run dev    # abre el sitio en http://127.0.0.1:3000 y se actualiza al guardar
npm run build  # genera el sitio estático en dist/
```

En Windows, si `python` no funciona, prueba con `py`.

## Cómo publicarlo en GitHub Pages

1. Crea un repositorio en GitHub y sube esta carpeta completa.
2. En el repositorio, ve a **Settings → Pages** y en **Source** elige **GitHub Actions**.
3. Cada vez que subas cambios a `main`, y todos los días a las 6:00, el flujo `.github/workflows/publicar.yml` recalcula los datos, corre las pruebas y publica el sitio. Si una prueba falla, no se publica.

Con la cuenta gratuita, GitHub Pages solo publica desde repositorios públicos. Con GitHub Pro, gratis para estudiantes con el Student Developer Pack, el código puede quedar privado y el sitio seguir siendo visible.

## Estructura

```
datos/
  obras.csv              8 obras seudonimizadas (editable: reemplázalas por datos reales)
  eventos_contrato.csv   prórrogas, cambios de monto, suspensiones y recepciones
  feriados.csv           feriados oficiales de 2026
  simulados/             generados por scripts/generar_simulados.py
    dIAra_crudo/CAM-X/   un CSV por cámara y día, en el formato de producción de dIAra
radar/
  config.py              todos los parámetros y umbrales en un solo lugar
  lectura.py             lectura y limpieza (convierte los tensores de PyTorch en números)
  contrato.py            plazo y monto vigentes, suspensiones y avance previsto
  reglas.py              estado diario, matriz semanal, señales, puntaje y alertas
scripts/                 generar_simulados, clima, construir y validar
src/                     el sitio (Observable Framework)
  data/*.py              cargadores: el sitio usa el mismo cálculo de Python
salidas/                 resultados de construir.py (para revisar en Excel si quieres)
```

## Cambiar las reglas

Todos los umbrales y pesos están en `radar/config.py`. Después de cambiarlos, corre `python scripts/construir.py` y `python scripts/validar.py`. Si una prueba de escenario falla, el cambio alteró lo que el auditor debería ver.

## Fuentes

- Repositorio de dIAra: https://github.com/cgrcostarica/dIAra (formato del CSV, clases, umbral, horario de captura y foto de muestra).
- Normas Generales de Auditoría para el Sector Público, R-DC-064-2014 (CGR).
- Feriados 2026: calendario del Ministerio de Trabajo y Seguridad Social.
- Lluvia: Open-Meteo, https://open-meteo.com/ (CC BY 4.0).
- Observable Framework: https://observablehq.com/framework/

Detalle de qué es real y qué es simulado: `procedencia.md`.
