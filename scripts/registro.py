"""Lee el registro de obras desde la hoja de Google y actualiza datos/registro/.

La hoja la mantienen la gerencia (obras, cámaras, feriados y responsables) y los encargados de
actualización de obra (cambios de contrato, avance, pagos y reportes). Cada fila dice quién la
actualizó; ese nombre queda en la bitácora junto con el valor anterior y el nuevo.

Uso:  python scripts/registro.py                    descarga la hoja indicada en datos/registro/fuente.json
      python scripts/registro.py --archivo hoja.xlsx  usa un archivo descargado a mano (para probar)

Pasos:
  1. Descarga la hoja completa como .xlsx (cualquiera con el enlace puede verla).
  2. Revisa su calidad con las reglas de radar/registro.py.
  3. Si hay errores, NO toca datos/registro/: LupIA sigue con la última versión buena y la página
     Datos muestra qué corregir (queda en datos/registro/intento.json).
  4. Si no hay errores, guarda las tablas, anota cada cambio en datos/registro/bitacora.csv
     (qué tabla, qué registro, qué campo, valor anterior y nuevo) y la hora de lectura.

Nunca detiene la publicación: si la hoja no responde, se usa la copia del repositorio.
"""
import json
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import config as C  # noqa: E402
from radar import registro as R  # noqa: E402

FUENTE = C.REGISTRO / "fuente.json"
INTENTO = C.REGISTRO / "intento.json"
BITACORA = C.REGISTRO / "bitacora.csv"


def descargar(hoja_id: str) -> Path:
    url = f"https://docs.google.com/spreadsheets/d/{hoja_id}/export?format=xlsx"
    destino = Path(tempfile.mkdtemp()) / "registro.xlsx"
    with urllib.request.urlopen(url, timeout=60) as r:
        destino.write_bytes(r.read())
    return destino


def cambios(antes: dict, despues: dict, cuando: str) -> list:
    """Compara dos versiones del registro tabla por tabla y devuelve las filas de la bitácora."""
    filas = []
    for tabla, cols in R.TABLAS.items():
        claves = R.CLAVES[tabla]
        nombres = [c for c, _, _ in cols if c != "actualizado_por"]
        a = {tuple(f[k] for k in claves): f for f in antes[tabla].to_dict("records")}
        d = {tuple(f[k] for k in claves): f for f in despues[tabla].to_dict("records")}
        quien = lambda f: f.get("actualizado_por", "")  # noqa: E731
        for clave in d.keys() - a.keys():
            filas.append([cuando, tabla, " / ".join(clave), "(fila nueva)", "", "", quien(d[clave])])
        for clave in a.keys() - d.keys():
            filas.append([cuando, tabla, " / ".join(clave), "(fila eliminada)", "", "", quien(a[clave])])
        for clave in d.keys() & a.keys():
            for col in nombres:
                va, vd = a[clave].get(col, ""), d[clave].get(col, "")
                if va != vd:
                    filas.append([cuando, tabla, " / ".join(clave), col, va, vd, quien(d[clave])])
    return sorted(filas, key=lambda f: (f[1], f[2], f[3]))


def main():
    cuando = datetime.now(ZoneInfo("America/Costa_Rica")).strftime("%Y-%m-%dT%H:%M")
    if "--archivo" in sys.argv:
        archivo = Path(sys.argv[sys.argv.index("--archivo") + 1])
    else:
        if not FUENTE.exists():
            print("No hay datos/registro/fuente.json: se usa la copia del repositorio.")
            return
        try:
            archivo = descargar(json.loads(FUENTE.read_text(encoding="utf-8"))["hoja_id"])
        except Exception as error:  # sin internet o la hoja dejó de estar compartida
            print(f"No se pudo leer la hoja ({error}); se usa la copia del repositorio.")
            return

    nuevo = R.canonico(R.leer_hoja(archivo))
    revision = R.validar(nuevo)
    problemas = [{"nivel": p.nivel, "tabla": R.NOMBRES[p.tabla], "fila": p.fila, "mensaje": p.mensaje}
                 for p in revision.problemas]
    if revision.errores:
        INTENTO.write_text(json.dumps({"fecha_hora": cuando, "aceptado": False, "problemas": problemas},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"La hoja tiene {len(revision.errores)} error(es); se conserva la última versión buena:")
        for p in revision.errores:
            print(f"  {R.NOMBRES[p.tabla]}, fila {p.fila}: {p.mensaje}")
        return

    anterior = R.canonico(R.leer_crudo())
    nuevas = cambios(anterior, nuevo, cuando)
    R.guardar(nuevo)
    if nuevas:
        bitacora = pd.read_csv(BITACORA, dtype=str, keep_default_na=False)
        if "responsable" not in bitacora.columns:
            bitacora["responsable"] = ""
        pd.concat([bitacora, pd.DataFrame(nuevas, columns=bitacora.columns)]).to_csv(BITACORA, index=False)
        (C.REGISTRO / "actualizado.txt").write_text(cuando + "\n", encoding="utf-8")
    INTENTO.write_text(json.dumps({"fecha_hora": cuando, "aceptado": True, "problemas": problemas},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Registro leído a las {cuando}: {len(nuevas)} cambio(s).")


if __name__ == "__main__":
    main()
