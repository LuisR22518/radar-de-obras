"""Valida los datos y comprueba que cada escenario se comporte como se diseñó.

Uso:  python scripts/validar.py   (después de construir.py)

Tres tipos de prueba:
  1. Registro: la base de datos propia no tiene errores.
  2. Calidad de los datos de dIAra: clases, probabilidades, recuadros e integridad con el inventario.
  3. Escenarios: cada obra simulada produce la señal para la que fue diseñada, y la obra real del
     piloto se trata como histórica y con datos incompletos.
Termina con código 1 si algo falla, para que GitHub Actions detenga la publicación.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import config as C  # noqa: E402
from radar import lectura as L  # noqa: E402
from radar import reglas as R  # noqa: E402

resultados = []
omitidas = []


def revisar(descripcion: str, condicion: bool):
    resultados.append((descripcion, bool(condicion)))


def main():
    reg = L.cargar_registro()
    for p in reg.errores:
        print(f"Registro, {p.tabla}, fila {p.fila}: {p.mensaje}")
    revisar("El registro de obras no tiene errores", not reg.errores)
    camaras = reg["camaras"]
    lectura = L.cargar_dIAra(camaras)
    det, inv = lectura.detecciones, L.cargar_inventario(camaras)
    diario = pd.read_csv(C.SALIDAS / "estado_diario.csv", parse_dates=["fecha"])
    sen = pd.read_csv(C.SALIDAS / "senales.csv").set_index("obra_id")
    alertas = sen["alertas"].fillna("").str.split(";")

    # 2. Calidad de los datos de dIAra
    revisar("Todas las clases detectadas son clases del modelo de dIAra", det["clase"].isin(C.CLASES).all())
    modelo = det[det["origen"] == "modelo dIAra"]
    revisar("Las detecciones del modelo superan el umbral de 0,7 y no pasan de 1",
            modelo["probabilidad"].gt(C.UMBRAL_MODELO).all() and modelo["probabilidad"].le(1).all())
    revisar("Las etiquetas humanas no traen probabilidad", det.loc[det["origen"] == "etiqueta humana", "probabilidad"].isna().all())
    revisar("Todos los recuadros caben en una imagen de 1280 x 1024",
            (det["x1"] >= 0).all() and (det["y1"] >= 0).all()
            and (det["x2"] <= C.ANCHO_IMAGEN).all() and (det["y2"] <= C.ALTO_IMAGEN).all())
    claves_inv = set(zip(inv["camara_id"], inv["nombre_imagen"]))
    sim = det[det["fuente"] == "simulado"]
    revisar("Cada detección simulada corresponde a una foto del inventario",
            all(k in claves_inv for k in zip(sim["camara_id"], sim["nombre_imagen"])))
    con_origen = inv[inv["imagen_piloto"] != ""]
    reales = set(det.loc[det["fuente"] == "real", "nombre_imagen"])
    revisar("Cada foto simulada con actividad sale de una foto real del piloto", con_origen["imagen_piloto"].isin(reales).all())
    esperados = R.periodos(camaras).groupby("obra_id").size()
    revisar("Cada obra tiene un estado para cada día con cámara, sin huecos",
            diario.groupby("obra_id").size().reindex(esperados.index).eq(esperados).all())
    revisar("Ninguna cámara recibe más fotos de las esperadas", diario["cobertura"].dropna().le(1).all())

    # 3. Escenarios simulados. El gestor puede cambiar el registro: cada prueba corre solo si la obra
    #    sigue con el escenario para el que se diseñó; si no, se omite (no bloquea la publicación).
    obras = reg["obras"]

    def escenario(oid, esperado):
        if oid in obras.index and oid in sen.index and obras.loc[oid, "escenario_simulado"] == esperado:
            return True
        omitidas.append(oid)
        return False

    if escenario("A", "paralizada"):
        revisar("A (paralizada) necesita revisión con alerta de inactividad",
                sen.loc["A", "amerita_revision"] and "inactividad" in alertas["A"])
        originales = [o for o in "ABCDEFGH" if o in sen.index]
        revisar("A (paralizada, monto alto) va primero entre las obras de ejemplo",
                sen.loc["A", "prioridad"] == sen.loc[originales, "prioridad"].min())
    if escenario("B", "falla_camara"):
        revisar("B (cámara caída) está en la cola de dispositivos y no compite como obra",
                sen.loc["B", "en_cola_dispositivos"] and not sen.loc["B", "amerita_revision"])
    if escenario("C", "esporadica"):
        revisar("C tiene alerta de brecha entre lo reportado y lo observado", "brecha" in alertas["C"])
    if escenario("D", "lenta"):
        revisar("D (atrasada, con prórroga) tiene alertas de atraso y de contrato", {"atraso", "contrato"} <= set(alertas["D"]))
    if escenario("E", "normal"):
        revisar("E tiene alerta de inactividad con explicación de suspensión",
                "inactividad" in alertas["E"] and "suspensión" in str(sen.loc["E", "explicacion_inactividad"]))
    if escenario("F", "normal"):
        revisar("F (activa y al día) no tiene alertas", alertas["F"] == [""])
    if escenario("G", "terminada"):
        revisar("G (terminada) no tiene alertas", sen.loc["G", "fase"] == "terminada" and alertas["G"] == [""])
    if escenario("H", "normal"):
        revisar("H tiene alertas de reportes ciudadanos y de contrato", {"ciudadania", "contrato"} <= set(alertas["H"]))

    # 4. Obra real del piloto
    if "P" in sen.index:
        p = diario[diario["obra_id"] == "P"]
        revisar("P (piloto real) usa los 8 días publicados por dIAra", int((p["estado"] != "sin_datos").sum()) == 8)
        revisar("P es histórica: no compite en la lista de revisión", sen.loc["P", "historica"] and not sen.loc["P", "amerita_revision"])
        revisar("P no calcula las señales de contrato porque no hay contrato registrado",
                sen.loc["P", ["senal_atraso", "senal_brecha", "senal_contrato"]].isna().all())
    else:
        omitidas.append("P")

    # 5. Mantenimiento del registro
    man = pd.read_csv(C.SALIDAS / "mantenimiento.csv").set_index("obra_id")
    activas = sen[~sen["historica"].astype(bool)]
    revisar("Mantenimiento: incluye todas las obras en seguimiento y ninguna con monitoreo terminado",
            set(man.index) == set(activas.index))
    revisar("Mantenimiento: cada cámara sin datos aparece para enviar a mantenimiento",
            set(man.index[man["camara_a_mantenimiento"]]) == set(activas.index[activas["en_cola_dispositivos"].astype(bool)]))
    terminadas = man[man["fase"] == "terminada"]
    revisar("Mantenimiento: una obra terminada no tiene informes ni pagos vencidos",
            not (terminadas["informe_vencido"] | terminadas["pago_vencido"]).any())
    # Cerrar el ciclo: la ficha muestra la respuesta a cada reporte ciudadano, o los días que lleva sin respuesta
    ev = pd.read_csv(C.SALIDAS / "eventos.csv", parse_dates=["fecha", "fecha_respuesta"])
    rep = ev[ev["categoria"] == "ciudadania"]
    revisar("Los reportes ciudadanos llevan su respuesta, y ninguna respuesta es anterior a su reporte",
            {"respuesta", "fecha_respuesta"} <= set(ev.columns) and not (rep["fecha_respuesta"] < rep["fecha"]).any())

    for descripcion, ok in resultados:
        print(("OK    " if ok else "FALLA ") + descripcion)
    if omitidas:
        print(f"OMITIDA pruebas de escenario de {', '.join(omitidas)}: esas obras cambiaron en el registro.")
    fallas = sum(not ok for _, ok in resultados)
    print(f"\n{len(resultados) - fallas} de {len(resultados)} pruebas pasaron.")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
