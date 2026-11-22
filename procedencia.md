# Registro de procedencia

Qué dato viene de dónde, qué se le hizo y si es real o simulado. Fecha de corte de la cartera simulada: 20 de noviembre de 2026. Período de la obra real del piloto: 19 de marzo al 16 de abril de 2024.

| Datos | Fuente | Real o simulado | Transformaciones |
| --- | --- | --- | --- |
| `datos/diara/dIAra-K1/` | Repositorio público de dIAra (CGR, CENFOTEC y GIZ), commit 26a53a7 | Real: etiquetas hechas por personas en 8 días del piloto | Ninguna en los archivos. Al leerlos, `radar/diara.py` traduce las clases al español y convierte los recuadros a x1, y1, x2, y2. Detalle en `FUENTE.md` |
| `src/data/fotos-piloto/` | Las 6 fotos de ejemplo del mismo repositorio (19 de marzo de 2024) | Real | Personas difuminadas con `scripts/anonimizar_fotos.py` (Ley 8968); las originales no se guardan |
| `datos/registro/obras.csv` | Obras A a H: valores realistas con nombres y contratistas seudonimizados. Obra P: la del piloto, con lo que se sabe de ella | A a H: ejemplo. P: real, sin contrato público | Lo edita el gestor en la hoja de Google |
| `datos/registro/camaras.csv` | Asignación de cada cámara a su obra, con fechas | Simulado (A a H) y real (dIAra-K1, período con datos publicados) | Ninguna |
| `datos/registro/eventos_contrato.csv`, `avance_reportado.csv`, `pagos.csv`, `reportes_ciudadanos.csv` | Diseñados para los escenarios | Simulado | El avance previsto usa una curva en S aproximada; los pagos retienen 5 % |
| `datos/registro/feriados.csv` | Ministerio de Trabajo, feriados de pago obligatorio 2024 y 2026 | Real | El 11 de abril de 2024 se registra el lunes 15, su día de disfrute |
| `datos/registro/bitacora.csv` | `scripts/registro.py`, al comparar cada versión de la hoja con la anterior | Registro automático | Una fila por cambio: tabla, registro, campo, antes y después |
| `datos/simulados/diara/` | `scripts/generar_simulados.py`, semilla 2026 y una semilla por obra | Simulado a partir de datos reales | Cada foto con actividad repite los objetos de una foto real del piloto de la misma hora; se pierde ~15 % de los objetos (sensibilidad del modelo), los recuadros se mueven hasta 4 píxeles y las probabilidades quedan sobre 0,7, escritas como tensores, igual que `run_inference.py` |
| `datos/simulados/inventario_capturas.csv` | Mismo generador | Simulado | Es el «latido» que LupIA propone a dIAra: las fotos recibidas, con la foto real de origen de cada una |
| `datos/clima.csv` | Open-Meteo (archivo histórico; para días recientes, pronóstico con días pasados) | Real cuando hay internet | Si falla la descarga se usa la lluvia simulada, y la columna `origen` lo indica |
| `src/data/costa-rica.json` | Natural Earth 1:50 m, vía el paquete world-atlas | Real (dominio público) | Solo se extrajo el contorno de Costa Rica |

## Datos que se tomaron del repositorio de dIAra

- **Modelo:** Faster R-CNN ResNet50 (`model_1_29.pth`), 6 clases: Vagoneta, Persona, Tractor, Cargador, Mezcladora y Aplanadora. El modelo entrenado no está en el repositorio.
- **Umbral:** el modelo solo guarda detecciones con probabilidad mayor que 0,7 (`run_inference.py`).
- **Flujo de producción:** la cámara sube las fotos a una carpeta de Google Drive por día; el modelo las procesa y guarda `AAAAMMDD.csv` con `nombre_imagen, clase, probabilidad, recuadro`.
- **Cámara:** el firmware captura entre las 5:00 y las 17:59; las fotos del piloto van cada ~80 segundos (1280 × 1024).
- **Piloto:** 2.121 fotos etiquetadas; IoU promedio de 82,7 % y sensibilidad de 85,4 %, con un modelo entrenado solo con la Escuela de Pococí.

## Supuestos del equipo

Están en `radar/config.py` y se explican en la página Cómo funciona: umbrales de cobertura (50 %) y de actividad (15 %), horario laboral de 6:00 a 16:59, lluvia fuerte desde 20 mm, topes de las señales, pesos iniciales y umbrales de alerta. Para la cámara del piloto, que no trae inventario de fotos, un día con archivo se toma como día con la cámara funcionando.
