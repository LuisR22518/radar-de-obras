"""Genera los datos simulados del Radar de Obras.

Simula lo que dIAra produciría en 8 obras durante 12 semanas. Cada obra sigue un
escenario pensado para probar una tarea visual del auditor. La semilla es fija:
en cualquier computadora salen exactamente los mismos archivos.

Salidas en datos/simulados/:
  dIAra_crudo/CAM-X/AAAAMMDD.csv  detecciones con el formato real de producción de dIAra
  inventario_capturas.csv          imágenes recibidas por cámara (el "latido" que proponemos)
  avance_reportado.csv             avance que reporta la unidad ejecutora, cada quincena
  pagos.csv                        pagos acumulados al cierre de cada mes
  reportes_ciudadanos.csv          reportes de inspectores ciudadanos
  clima_simulado.csv               lluvia diaria simulada (respaldo si Open-Meteo no responde)

Uso:  python scripts/generar_simulados.py
"""
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import config as C  # noqa: E402
from radar.contrato import avance_previsto, dias_suspendidos, fin_vigente, monto_vigente  # noqa: E402
from radar.lectura import cargar_eventos, cargar_feriados, cargar_obras  # noqa: E402

rng = np.random.default_rng(C.SEMILLA)
T = pd.Timestamp

# --- Escenarios: cómo trabaja cada cuadrilla durante el período ------------------------
# p_dia: probabilidad de trabajar un día hábil; p_sabado: de trabajar medio día el sábado;
# intensidad: proporción de imágenes laborales con gente o máquinas cuando sí trabajan.
ESCENARIOS = {
    "A": {"patron": "paralizada", "desde": T("2026-10-19"), "p_dia": 0.95, "p_sabado": 0.5, "intensidad": 0.85},
    "B": {"patron": "normal", "p_dia": 0.95, "p_sabado": 0.4, "intensidad": 0.75, "falla_camara": T("2026-11-12")},
    "C": {"patron": "esporadica", "semanas": [T("2026-09-07"), T("2026-10-05"), T("2026-11-02")],
          "p_dia": 0.9, "intensidad": 0.6},
    "D": {"patron": "lenta", "dias": [0, 1, 3], "p_dia": 0.9, "intensidad": 0.55},
    "E": {"patron": "normal", "p_dia": 0.95, "p_sabado": 0.3, "intensidad": 0.7},
    "F": {"patron": "normal", "p_dia": 0.97, "p_sabado": 0.6, "intensidad": 0.8},
    "G": {"patron": "terminada", "hasta": T("2026-09-25"), "p_dia": 0.9, "intensidad": 0.5},
    "H": {"patron": "normal", "p_dia": 0.8, "p_sabado": 0.2, "intensidad": 0.65},
}
# Probabilidad de ver cada máquina en una imagen con actividad, según el tipo de obra.
MAQUINAS = {
    "Puente": {"Tractor": 0.35, "Vagoneta": 0.30, "Mezcladora": 0.25, "Cargador": 0.10},
    "Camino": {"Aplanadora": 0.35, "Vagoneta": 0.40, "Cargador": 0.30, "Tractor": 0.20},
    "Acueducto": {"Tractor": 0.40, "Vagoneta": 0.25},
    "Alcantarillado": {"Tractor": 0.35, "Vagoneta": 0.30, "Cargador": 0.15},
}
MAQUINAS_EDIFICIO = {"Mezcladora": 0.30, "Vagoneta": 0.15}
# Probabilidad diaria de lluvia por región y mes (setiembre, octubre, noviembre).
REGION = {"A": "pacifico_sur", "B": "caribe", "C": "norte", "D": "pacifico_norte",
          "E": "caribe", "F": "central", "G": "central", "H": "pacifico_norte"}
P_LLUVIA = {"pacifico_sur": {9: .70, 10: .75, 11: .55}, "caribe": {8: .45, 9: .45, 10: .50, 11: .65},
            "norte": {9: .60, 10: .60, 11: .55}, "pacifico_norte": {9: .60, 10: .65, 11: .30},
            "central": {9: .60, 10: .65, 11: .35}}
FECHAS_INFORME = [T(f) for f in ["2026-08-31", "2026-09-15", "2026-09-30", "2026-10-15", "2026-10-31", "2026-11-15"]]
CIERRES_MES = [T("2026-08-31"), T("2026-09-30"), T("2026-10-31")]


def jornada(dia, esc, feriado: bool, suspendido: bool) -> float:
    """Fracción de jornada trabajada ese día: 1 = día completo, 0.5 = medio día, 0 = no se trabajó."""
    dow = dia.weekday()
    if suspendido or dow == 6:
        return 0.0
    patron = esc["patron"]
    if patron == "paralizada" and dia >= esc["desde"]:
        return 0.0
    if patron == "terminada" and dia > esc["hasta"]:
        return 0.0
    if patron == "esporadica" and ((dia - pd.Timedelta(days=dow)) not in esc["semanas"] or dow > 2):
        return 0.0
    if patron == "lenta" and dow not in esc["dias"]:
        return 0.0
    if feriado:
        return 1.0 if rng.random() < 0.15 else 0.0
    if dow == 5:
        return 0.5 if rng.random() < esc.get("p_sabado", 0) else 0.0
    return 1.0 if rng.random() < esc["p_dia"] else 0.0


def recuadro(clase: str) -> str:
    """Caja de detección en el formato de producción: tensor([x1, y1, x2, y2])."""
    if clase == "Persona":
        w, h = rng.uniform(25, 60), rng.uniform(60, 130)
    else:
        w, h = rng.uniform(120, 380), rng.uniform(90, 260)
    x1 = rng.uniform(0, C.ANCHO_IMAGEN - w)
    y1 = rng.uniform(300, C.ALTO_IMAGEN - h)
    return f"tensor([{x1:.4f}, {y1:.4f}, {x1 + w:.4f}, {y1 + h:.4f}])"


def probabilidad() -> str:
    """Probabilidad sobre el umbral del modelo, en el formato de producción: tensor(0.9876)."""
    return f"tensor({C.UMBRAL_MODELO + 0.0001 + (0.9999 - C.UMBRAL_MODELO) * rng.beta(6, 1.6):.4f})"


def detecciones_de_imagen(nombre: str, hora: int, jorn: float, esc, tipo: str) -> list:
    filas = []
    fin_laboral = 11 if jorn == 0.5 else C.HORARIO_LABORAL[1]
    laboral = C.HORARIO_LABORAL[0] <= hora <= fin_laboral
    if jorn > 0 and laboral:
        borde = hora in (C.HORARIO_LABORAL[0], fin_laboral)
        if rng.random() < esc["intensidad"] * (0.6 if borde else 1.0):
            for _ in range(1 + rng.poisson(1.4)):
                filas.append([nombre, "Persona", probabilidad(), recuadro("Persona")])
            for clase, p in MAQUINAS.get(tipo, MAQUINAS_EDIFICIO).items():
                if rng.random() < p:
                    filas.append([nombre, clase, probabilidad(), recuadro(clase)])
    else:
        # Fuera de jornada solo aparece, a veces, el guarda o alguien que llega temprano.
        p_persona = 0.15 if (jorn > 0 and hora in (5, 17)) else 0.03
        if rng.random() < p_persona:
            filas.append([nombre, "Persona", probabilidad(), recuadro("Persona")])
    return filas


def simular_camaras(obras, eventos, feriados_set):
    dias = pd.date_range(C.INICIO_MONITOREO, C.FECHA_CORTE, freq="D")
    slots = [(h, m) for h in range(C.HORA_PRIMERA_CAPTURA, C.HORA_ULTIMA_CAPTURA + 1)
             for m in range(0, 60, C.INTERVALO_MIN)]
    inventario = []
    for oid, obra in obras.iterrows():
        esc = ESCENARIOS[oid]
        suspendidos = dias_suspendidos(oid, eventos)
        carpeta = C.CRUDO_DIARA / obra["camara_id"]
        carpeta.mkdir(parents=True, exist_ok=True)
        for dia in dias:
            jorn = jornada(dia, esc, dia in feriados_set, dia in suspendidos)
            if "falla_camara" in esc and dia >= esc["falla_camara"]:
                continue  # la cámara no envía nada: en producción no se genera el CSV del día
            p_recibir = rng.uniform(0.2, 0.45) if rng.random() < 0.02 else 0.965  # baja energía o señal
            filas = []
            for hora, minuto in slots:
                if rng.random() > p_recibir:
                    continue
                nombre = f"{dia:%Y%m%d}-{hora:02d}{minuto:02d}{rng.integers(0, 60):02d}.jpg"
                inventario.append([obra["camara_id"], nombre])
                filas += detecciones_de_imagen(nombre, hora, jorn, esc, obra["tipo"])
            pd.DataFrame(filas, columns=["nombre_imagen", "clase", "probabilidad", "recuadro"]).to_csv(
                carpeta / f"{dia:%Y%m%d}.csv", index=False)
    pd.DataFrame(inventario, columns=["camara_id", "nombre_imagen"]).to_csv(
        C.SIMULADOS / "inventario_capturas.csv", index=False)


def reportado(obra, eventos, fecha) -> float:
    """Avance que reportaría la unidad ejecutora en cada escenario."""
    oid = obra["obra_id"]
    prev = avance_previsto(obra["fecha_inicio"], fin_vigente(obra, eventos, fecha), fecha)
    if oid == "A":  # deja de avanzar cuando se paraliza, y lo reporta con honestidad
        congelado = avance_previsto(obra["fecha_inicio"], obra["fecha_fin_original"], T("2026-10-15"))
        valor = min(prev, congelado) - 1 + (0.5 if fecha >= T("2026-10-31") else 0)
    elif oid == "C":  # reporta como si fuera al día, aunque casi no se observa actividad
        valor = prev - 1
    elif oid == "D":  # atrasada frente al plan original
        valor = 0.8 * avance_previsto(obra["fecha_inicio"], obra["fecha_fin_original"], fecha)
    elif oid == "G":
        valor = min(100, prev + 2)
    elif oid == "H":  # se va quedando atrás
        inicio = T(C.INICIO_MONITOREO)
        avance_ventana = (fecha - inicio).days / (T("2026-11-15") - inicio).days
        valor = prev - 4 - 6 * max(avance_ventana, 0)
    elif oid == "B":
        valor = prev - 2
    else:
        valor = prev - 1
    return round(min(max(valor, 0), 100), 1)


def simular_contrato(obras, eventos):
    avance, pagos = [], []
    for oid, obra in obras.iterrows():
        for fecha in FECHAS_INFORME:
            avance.append([oid, fecha.date(), reportado(obra, eventos, fecha), "simulado"])
        for fecha in CIERRES_MES:
            monto = monto_vigente(obra, eventos, fecha)
            pagado = round(reportado(obra, eventos, fecha) / 100 * monto * 0.95, -5)  # 5 % de retención
            pagos.append([oid, fecha.date(), int(pagado), "simulado"])
    pd.DataFrame(avance, columns=["obra_id", "fecha", "avance_reportado_pct", "origen"]).to_csv(
        C.SIMULADOS / "avance_reportado.csv", index=False)
    pd.DataFrame(pagos, columns=["obra_id", "fecha", "pagado_acumulado_crc", "origen"]).to_csv(
        C.SIMULADOS / "pagos.csv", index=False)


def simular_reportes():
    reportes = [
        ["2026-10-22", "H", "seguridad", "Zanja abierta sin señalización frente a la escuela.", True],
        ["2026-10-28", "C", "obra detenida", "Pasan días sin maquinaria en el camino.", False],
        ["2026-11-03", "H", "calidad", "El agua se empoza donde ya trabajaron.", True],
        ["2026-11-06", "A", "obra detenida", "Desde hace semanas no se ve maquinaria en el puente.", True],
        ["2026-11-10", "H", "obra detenida", "La zanja sigue abierta y no hay trabajadores desde el lunes.", True],
        ["2026-11-17", "A", "obra detenida", "La obra sigue sin trabajadores; solo hay un guarda.", False],
        ["2026-11-18", "H", "seguridad", "Material acumulado sobre la vía.", True],
    ]
    df = pd.DataFrame(reportes, columns=["fecha", "obra_id", "tipo", "descripcion", "con_foto"])
    df["origen"] = "simulado"
    df.to_csv(C.SIMULADOS / "reportes_ciudadanos.csv", index=False)


def simular_clima(obras):
    filas = []
    for oid in obras.index:
        for dia in pd.date_range(C.INICIO_MONITOREO, C.FECHA_CORTE, freq="D"):
            p = P_LLUVIA[REGION[oid]].get(dia.month, 0.5)
            mm = rng.gamma(0.8, 14) if rng.random() < p else 0.0
            if oid == "E" and T("2026-11-16") <= dia <= T("2026-11-20"):
                mm = rng.uniform(35, 80)  # coherente con la suspensión por lluvias de la obra E
            filas.append([oid, dia.date(), round(mm, 1), "simulado"])
    pd.DataFrame(filas, columns=["obra_id", "fecha", "lluvia_mm", "origen"]).to_csv(
        C.SIMULADOS / "clima_simulado.csv", index=False)


def main():
    if C.SIMULADOS.exists():
        shutil.rmtree(C.SIMULADOS)  # se regenera todo desde cero
    C.SIMULADOS.mkdir(parents=True)
    obras, eventos = cargar_obras(), cargar_eventos()
    feriados_set = set(cargar_feriados()["fecha"])
    simular_camaras(obras, eventos, feriados_set)
    simular_contrato(obras, eventos)
    simular_reportes()
    simular_clima(obras)
    print(f"Datos simulados listos en {C.SIMULADOS.relative_to(C.RAIZ)} (semilla {C.SEMILLA}).")


if __name__ == "__main__":
    main()
