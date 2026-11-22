# Procedencia: cámara dIAra-K1 (piloto de dIAra, 2024)

Estos archivos son **datos reales** del piloto de dIAra en la construcción de la Escuela de Pococí
(Limón), copiados sin modificar desde el repositorio público de la Contraloría General de la
República y la Universidad CENFOTEC.

| Dato | Valor |
| --- | --- |
| Repositorio | https://github.com/cgrcostarica/dIAra |
| Archivo de origen | `IA/Imagenes y Etiquetas/Etiquetas e Imagenes Ejemplo.zip`, carpeta `Labels/` |
| Versión del repositorio | commit `26a53a7fe89032e56dde014674ac0b830034692d` (10 de mayo de 2024) |
| Copiado el | 22 de noviembre de 2026 |
| Licencia | El repositorio no incluye un archivo de licencia; su README declara que permite la reproducción abierta de los resultados. |

## Qué contienen

Son las **etiquetas hechas por personas** que se usaron para entrenar y evaluar el modelo de dIAra:
para cada foto, qué objetos aparecen y dónde (recuadro en píxeles de una imagen de 1280 × 1024).
No son la salida del modelo: por eso no traen probabilidad.

| Archivo | Días | Formato |
| --- | --- | --- |
| `mar_19_20.json` | 19 y 20 de marzo de 2024 | JSON: `images[].objects[].class` y `bbox` |
| `test_dataset.json` | 3 de abril de 2024 | JSON (mismo formato) |
| `20240401.csv`, `20240402.csv`, `20240411.csv`, `20240415.csv`, `20240416.csv` | 1, 2, 11, 15 y 16 de abril de 2024 | CSV: `label_name, bbox_x, bbox_y, bbox_width, bbox_height, image_name` |

Se omitieron `Train_dataset.json` (duplica a `mar_19_20.json`), `Json_gabo.json` (duplica los CSV de
abril), las etiquetas XML (son un subconjunto del 16 de abril) y los `.xlsx` (duplican los CSV).

## Limitaciones que LupIA declara

- Solo aparecen las fotos con al menos un objeto etiquetado. No hay inventario de las fotos tomadas,
  así que un día sin archivo no se puede distinguir de un día con la cámara apagada.
- No se sabe si se etiquetaron todas las fotos de cada día. Los días con pocas fotos (1, 11 y 15 de
  abril) pueden reflejar poca actividad o un etiquetado parcial.
- Las clases están en inglés; LupIA las traduce a los nombres que usa el modelo en producción
  (`run_inference.py`): dump_truck → Vagoneta, person → Persona, excavator → Tractor,
  loader → Cargador, mixer_truck → Mezcladora, steamroller → Aplanadora.
- El 15 de abril de 2024 fue feriado: el de Juan Santamaría se trasladó del jueves 11 al lunes 15
  (MTSS, comunicado CP-018-2024).

## Fotos

El mismo archivo trae 6 fotos reales del 19 de marzo de 2024 (8:57 a 9:04). LupIA no guarda las
originales: publica versiones con las personas difuminadas (`src/data/fotos-piloto/`), generadas
con `scripts/anonimizar_fotos.py`, por la Ley 8968 de protección de datos personales.
