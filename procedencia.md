# Registro de procedencia

Qué dato viene de dónde, qué se le hizo y si es real o simulado. Fecha de corte de los datos: 20 de noviembre de 2026.

| Archivo | Fuente | Real o simulado | Transformaciones |
| --- | --- | --- | --- |
| `datos/obras.csv` | Valores realistas inspirados en obras públicas costarricenses; ubicación aproximada en el centro de cada cantón | Ejemplo seudonimizado | Ninguna. Reemplazar por datos de SICOP o PROERI, sin poner señales simuladas sobre nombres reales |
| `datos/eventos_contrato.csv` | Diseñados para los escenarios D, E, G y H | Simulado | Se aplican por fecha en `radar/contrato.py` |
| `datos/feriados.csv` | Calendario de feriados 2026 del MTSS, según la prensa nacional | Real | Ninguna |
| `datos/simulados/dIAra_crudo/` | `scripts/generar_simulados.py`, semilla 2026 | Simulado con el formato real | Imitan `run_inference.py` del repositorio de dIAra: columnas `nombre_imagen, clase, probabilidad, recuadro`, valores como tensores de PyTorch, solo detecciones mayores que 0,7 y sin archivo los días sin fotos |
| `datos/simulados/inventario_capturas.csv` | Mismo generador | Simulado | Es el «latido» que proponemos: lista las fotos recibidas, porque el CSV de dIAra omite las fotos sin detecciones |
| `datos/simulados/avance_reportado.csv` y `pagos.csv` | Mismo generador | Simulado | El avance previsto usa una curva en S aproximada; los pagos retienen 5 % |
| `datos/simulados/reportes_ciudadanos.csv` | Redactados para los escenarios A, C y H | Simulado | Ninguna |
| `datos/clima.csv` | Open-Meteo (archivo histórico y, para días recientes, pronóstico con días pasados) | Real cuando hay internet | Si falla la descarga se usa `clima_simulado.csv`, y la columna `origen` lo indica |
| `src/data/ejemplo-camara-diara.jpg` | Repositorio público de dIAra, imagen 20240319-085919.jpg | Real | Ninguna; persona de espaldas, sin rostro visible |

## Datos que se tomaron del repositorio de dIAra

- **Modelo:** Faster R-CNN ResNet50 (`model_1_29.pth`), 6 clases: Vagoneta, Persona, Tractor, Cargador, Mezcladora y Aplanadora.
- **Umbral:** el modelo solo guarda detecciones con probabilidad mayor que 0,7.
- **Salida:** un CSV por día llamado `AAAAMMDD.csv`, con imágenes llamadas `AAAAMMDD-HHMMSS.jpg` de 1280 × 1024.
- **Horario:** el firmware de la cámara solo captura entre las 5:00 y las 17:59; la muestra real va cada 80 segundos.
- **Métricas publicadas:** IoU promedio de 82,7 % y sensibilidad de 85,4 %, con un modelo entrenado solo con la Escuela de Pocosí.

## Supuestos del equipo

Están en `radar/config.py` y se explican en la página Metodología y datos: intervalo de 10 minutos, umbrales de cobertura (50 %) y de actividad (15 %), horario laboral de 6:00 a 16:59, lluvia fuerte desde 20 mm, topes de las señales, pesos iniciales y umbrales de alerta.
