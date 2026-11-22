"""Valida los datos y comprueba que cada escenario se comporte como se diseñó.

Uso:  python scripts/validar.py   (después de construir.py)

Dos tipos de prueba:
  1. Calidad de datos: columnas, rangos, fechas completas e integridad entre tablas.
  2. Escenarios: cada obra simulada debe producir la señal para la que fue diseñada.
Termina con código 1 si algo falla, para que GitHub Actions detenga la publicación.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import config as C  # noqa: E402
from radar import lectura as L  # noqa: E402

resultados = []


def revisar(descripcion: str, condicion: bool):
    resultados.append((descripcion, bool(condicion)))


def main():
    obras, det, inv = L.cargar_obras(), L.cargar_detecciones(), L.cargar_inventario()
    diario = pd.read_csv(C.SALIDAS / "estado_diario.csv", parse_dates=["fecha"])
    sen = pd.read_csv(C.SALIDAS / "senales.csv").set_index("obra_id")
    alertas = sen["alertas"].fillna("").str.split(";")

    # 1. Calidad de datos
    revisar("obras.csv tiene 8 obras con identificador único", obras["obra_id"].is_unique and len(obras) == 8)
    revisar("Todas las clases detectadas son clases del modelo de dIAra", det["clase"].isin(C.CLASES).all())
    revisar("Todas las probabilidades superan el umbral del modelo (0,7) y no pasan de 1",
            det["probabilidad"].gt(C.UMBRAL_MODELO).all() and det["probabilidad"].le(1).all())
    revisar("Todos los recuadros caben en una imagen de 1280 x 1024",
            (det["x1"] >= 0).all() and (det["y1"] >= 0).all()
            and (det["x2"] <= C.ANCHO_IMAGEN).all() and (det["y2"] <= C.ALTO_IMAGEN).all())
    claves_inv = set(zip(inv["camara_id"], inv["nombre_imagen"]))
    revisar("Cada detección corresponde a una imagen del inventario de capturas",
            all(k in claves_inv for k in zip(det["camara_id"], det["nombre_imagen"])))
    dias = (pd.Timestamp(C.FECHA_CORTE) - pd.Timestamp(C.INICIO_MONITOREO)).days + 1
    revisar(f"Cada obra tiene sus {dias} días en el estado diario, sin huecos",
            (diario.groupby("obra_id")["fecha"].nunique() == dias).all())
    revisar("Ninguna cámara recibe más capturas de las esperadas", diario["cobertura"].le(1).all())

    # 2. Escenarios
    revisar("A (paralizada, monto alto) tiene la prioridad 1", sen.loc["A", "prioridad"] == 1)
    revisar("A tiene alerta de inactividad", "inactividad" in alertas["A"])
    revisar("B (cámara caída) está en la cola de dispositivos y no compite como obra",
            sen.loc["B", "en_cola_dispositivos"] and not sen.loc["B", "amerita_revision"])
    revisar("C tiene alerta de brecha entre lo reportado y lo observado", "brecha" in alertas["C"])
    revisar("D (atrasada, con prórroga) tiene alertas de atraso y de contrato",
            {"atraso", "contrato"} <= set(alertas["D"]))
    revisar("E tiene alerta de inactividad con explicación de suspensión",
            "inactividad" in alertas["E"] and "suspensión" in str(sen.loc["E", "explicacion_inactividad"]))
    revisar("F (activa y al día) no tiene alertas", alertas["F"] == [""])
    revisar("G (terminada) no tiene alertas", sen.loc["G", "fase"] == "terminada" and alertas["G"] == [""])
    revisar("H tiene alertas de reportes ciudadanos y de contrato", {"ciudadania", "contrato"} <= set(alertas["H"]))

    for descripcion, ok in resultados:
        print(("OK    " if ok else "FALLA ") + descripcion)
    fallas = sum(not ok for _, ok in resultados)
    print(f"\n{len(resultados) - fallas} de {len(resultados)} pruebas pasaron.")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
