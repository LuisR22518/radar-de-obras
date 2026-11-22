"""Reglas del Radar: estado diario, matriz semanal, señales, puntaje y alertas.

Todo es explicable: cada número sale de una regla escrita aquí y de un parámetro
de config.py. El Radar señala situaciones que ameritan revisión; no afirma
irregularidades.
"""
import numpy as np
import pandas as pd

from . import config as C
from .contrato import avance_previsto, dias_suspendidos, fecha_recepcion, fin_vigente, monto_vigente

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_corta(fecha) -> str:
    fecha = pd.Timestamp(fecha)
    return f"{fecha.day} {MESES[fecha.month - 1]}"


def capturas_esperadas_por_dia() -> int:
    return (C.HORA_ULTIMA_CAPTURA - C.HORA_PRIMERA_CAPTURA + 1) * (60 // C.INTERVALO_MIN)


# --- 1. Estado de cada obra en cada día -------------------------------------------------
def estado_diario(obras, eventos, feriados, inventario, detecciones, clima) -> pd.DataFrame:
    """Una fila por obra y día: cobertura de la cámara, actividad observada, estado y contexto."""
    camara_a_obra = dict(zip(obras["camara_id"], obras["obra_id"]))
    dias = pd.date_range(C.INICIO_MONITOREO, C.FECHA_CORTE, freq="D")
    base = pd.MultiIndex.from_product([obras["obra_id"], dias], names=["obra_id", "fecha"]).to_frame(index=False)

    inv = inventario.assign(obra_id=inventario["camara_id"].map(camara_a_obra),
                            fecha=inventario["fecha_hora"].dt.normalize(),
                            hora=inventario["fecha_hora"].dt.hour)
    ini, fin = C.HORARIO_LABORAL
    inv_lab = inv[inv["hora"].between(ini, fin)]

    det = detecciones.assign(obra_id=detecciones["camara_id"].map(camara_a_obra),
                             fecha=detecciones["fecha_hora"].dt.normalize(),
                             hora=detecciones["fecha_hora"].dt.hour)
    det_lab = det[det["hora"].between(ini, fin)]

    claves = ["obra_id", "fecha"]
    tablas = [
        inv.groupby(claves).size().rename("capturas_recibidas"),
        inv_lab.groupby(claves).size().rename("capturas_laborales"),
        det_lab.groupby(claves)["nombre_imagen"].nunique().rename("imagenes_con_deteccion"),
        det_lab[det_lab["clase"] == "Persona"].groupby(claves).size().rename("personas_detectadas"),
        det_lab[det_lab["clase"].isin(C.MAQUINARIA)].groupby(claves)["nombre_imagen"].nunique()
        .rename("imagenes_con_maquinaria"),
    ]
    d = base.merge(pd.concat(tablas, axis=1).reset_index(), on=claves, how="left")
    conteos = ["capturas_recibidas", "capturas_laborales", "imagenes_con_deteccion",
               "personas_detectadas", "imagenes_con_maquinaria"]
    d[conteos] = d[conteos].fillna(0).astype(int)

    d["cobertura"] = (d["capturas_recibidas"] / capturas_esperadas_por_dia()).round(3)
    d["pct_actividad"] = np.where(d["capturas_laborales"] > 0,
                                  d["imagenes_con_deteccion"] / d["capturas_laborales"].clip(lower=1), 0.0).round(3)
    d["estado"] = np.select(
        [d["cobertura"] < C.UMBRAL_COBERTURA, d["pct_actividad"] >= C.UMBRAL_ACTIVIDAD],
        ["sin_datos", "actividad"], default="sin_actividad")

    # Contexto que puede explicar un día sin actividad
    nombres_feriado = dict(zip(feriados["fecha"], feriados["nombre"]))
    d["feriado"] = d["fecha"].map(nombres_feriado).fillna("")
    d["es_habil"] = (d["fecha"].dt.weekday < 5) & (d["feriado"] == "")
    d = d.merge(clima[["obra_id", "fecha", "lluvia_mm"]], on=claves, how="left")
    suspendidos = {(oid, dia) for oid in obras["obra_id"] for dia in dias_suspendidos(oid, eventos)}
    d["suspendido"] = [(o, f) in suspendidos for o, f in zip(d["obra_id"], d["fecha"])]
    recepcion = {oid: fecha_recepcion(obra, eventos) for oid, obra in obras.iterrows()}
    d["fase"] = [("terminada" if recepcion[o] is not None and f > recepcion[o] else "en ejecucion")
                 for o, f in zip(d["obra_id"], d["fecha"])]

    def explicar(fila) -> str:
        if fila["estado"] != "sin_actividad":
            return ""
        motivos = []
        if fila["fase"] == "terminada":
            motivos.append("obra terminada")
        if fila["suspendido"]:
            motivos.append("suspensión aprobada")
        if fila["feriado"]:
            motivos.append(f"feriado: {fila['feriado']}")
        if fila["lluvia_mm"] >= C.LLUVIA_FUERTE_MM:
            motivos.append(f"lluvia fuerte ({fila['lluvia_mm']:.0f} mm)")
        return "; ".join(motivos)

    d["explicacion"] = d.apply(explicar, axis=1)
    return d


# --- 2. Matriz de cartera: una celda por obra y semana -----------------------------------------
def matriz_semanal(diario: pd.DataFrame) -> pd.DataFrame:
    d = diario.assign(semana=diario["fecha"] - pd.to_timedelta(diario["fecha"].dt.weekday, unit="D"))
    d["habil_con_datos"] = d["es_habil"] & (d["estado"] != "sin_datos")
    d["habil_inactivo"] = d["es_habil"] & (d["estado"] == "sin_actividad")
    d["habil_inactivo_explicado"] = d["habil_inactivo"] & (d["explicacion"] != "")
    s = d.groupby(["obra_id", "semana"]).agg(
        dias_habiles=("es_habil", "sum"),
        habiles_con_datos=("habil_con_datos", "sum"),
        dias_actividad=("estado", lambda e: int((e == "actividad").sum())),
        dias_sin_datos=("estado", lambda e: int((e == "sin_datos").sum())),
        habiles_inactivos=("habil_inactivo", "sum"),
        habiles_inactivos_explicados=("habil_inactivo_explicado", "sum"),
        terminada=("fase", lambda f: bool((f == "terminada").all())),
    ).reset_index()
    s["estado_semana"] = np.select(
        [s["terminada"],
         s["habiles_con_datos"] < 0.5 * s["dias_habiles"],
         s["dias_actividad"] >= C.DIAS_ACTIVOS_SEMANA],
        ["terminada", "sin_datos", "actividad"], default="sin_actividad")
    s["con_explicacion"] = (s["estado_semana"] == "sin_actividad") & (
        s["habiles_inactivos_explicados"] >= 0.5 * s["habiles_inactivos"].clip(lower=1))
    return s


# --- 3. Señales, puntaje y alertas a la fecha de corte ------------------------------------------
def _racha_inactividad(d: pd.DataFrame):
    """Días hábiles seguidos sin actividad, contando hacia atrás desde la fecha de corte.

    Los fines de semana, feriados y días sin datos no suman ni cortan la racha:
    se saltan. La racha termina en el primer día con actividad.
    """
    dias = []
    for _, fila in d.sort_values("fecha", ascending=False).iterrows():
        if not fila["es_habil"] or fila["estado"] == "sin_datos":
            continue
        if fila["estado"] == "actividad":
            break
        dias.append(fila)
    return pd.DataFrame(dias)


def _dias_sin_datos_al_corte(d: pd.DataFrame) -> int:
    n = 0
    for estado in d.sort_values("fecha", ascending=False)["estado"]:
        if estado != "sin_datos":
            break
        n += 1
    return n


def _explicar_racha(racha: pd.DataFrame) -> str:
    if racha.empty:
        return ""
    n = len(racha)
    motivos = []
    susp = racha[racha["suspendido"]]
    if len(susp) >= n / 2:
        motivos.append(f"suspensión aprobada ({fecha_corta(susp['fecha'].min())} a {fecha_corta(susp['fecha'].max())})")
    lluvia = int((racha["lluvia_mm"] >= C.LLUVIA_FUERTE_MM).sum())
    if lluvia >= n / 2:
        motivos.append(f"lluvia fuerte en {lluvia} de {n} días")
    return "; ".join(motivos)


def senales(obras, eventos, diario, semanal, avance, reportes, inventario, pesos=None) -> pd.DataFrame:
    """Calcula las cinco señales (de 0 a 1), el puntaje de atención (de 0 a 100) y las alertas."""
    pesos = pesos or C.PESOS
    corte = pd.Timestamp(C.FECHA_CORTE)
    inicio_ventana = pd.Timestamp(C.INICIO_MONITOREO)
    semanas_ventana = (corte - inicio_ventana).days / 7
    filas = []
    for oid, obra in obras.iterrows():
        d = diario[diario["obra_id"] == oid]
        rec = fecha_recepcion(obra, eventos)
        terminada = rec is not None and rec <= corte
        fin_vig = fin_vigente(obra, eventos, corte)
        monto = monto_vigente(obra, eventos, corte)

        # Cola de dispositivos: la cámara lleva días sin enviar datos
        sin_datos_corte = _dias_sin_datos_al_corte(d)
        en_dispositivos = sin_datos_corte >= C.DIAS_SIN_DATOS_DISPOSITIVO
        capturas = inventario[inventario["camara_id"] == obra["camara_id"]]["fecha_hora"]
        ultima_captura = capturas.max() if len(capturas) else pd.NaT

        # Señal 1: inactividad con la cámara funcionando
        racha = pd.DataFrame() if terminada else _racha_inactividad(d)
        s_inactividad = 0.0 if (terminada or en_dispositivos) else min(1.0, len(racha) / C.DIAS_INACTIVIDAD_TOPE)

        # Señal 2: atraso del avance reportado frente al cronograma vigente
        rep = avance[(avance["obra_id"] == oid) & (avance["fecha"] <= corte)].sort_values("fecha")
        ultimo = rep.iloc[-1]
        previsto = avance_previsto(obra["fecha_inicio"], fin_vigente(obra, eventos, ultimo["fecha"]), ultimo["fecha"])
        atraso = max(0.0, previsto - ultimo["avance_reportado_pct"])
        s_atraso = 0.0 if terminada else min(1.0, atraso / C.ATRASO_TOPE_PTS)

        # Señal 3: lo reportado avanza más de lo que la actividad observada permite suponer
        en_ventana = rep[rep["fecha"] >= inicio_ventana]
        incremento = float(en_ventana["avance_reportado_pct"].iloc[-1] - en_ventana["avance_reportado_pct"].iloc[0])
        duracion_sem = max((fin_vig - obra["fecha_inicio"]).days / 7, 1)
        incremento_tipico = 100 / duracion_sem * semanas_ventana
        proporcion_reportada = min(1.0, max(incremento, 0) / incremento_tipico)
        sem = semanal[(semanal["obra_id"] == oid) & semanal["estado_semana"].isin(["actividad", "sin_actividad"])]
        proporcion_activa = float((sem["estado_semana"] == "actividad").mean()) if len(sem) else 1.0
        s_brecha = 0.0 if terminada else float(np.clip(proporcion_reportada - proporcion_activa, 0, 1))

        # Señal 4: cambios contractuales (aumento de monto o prórroga reciente)
        aumento = monto / obra["monto_original_crc"] - 1
        prorrogas = eventos[(eventos["obra_id"] == oid) & (eventos["tipo"] == "prorroga")
                            & (eventos["fecha"] > corte - pd.Timedelta(days=C.VENTANA_PRORROGA_DIAS))
                            & (eventos["fecha"] <= corte)]
        s_contrato = 0.0 if terminada else max(min(1.0, max(aumento, 0) / C.AUMENTO_TOPE),
                                                 C.VALOR_PRORROGA if len(prorrogas) else 0.0)

        # Señal 5: reportes ciudadanos recientes
        recientes = reportes[(reportes["obra_id"] == oid)
                             & (reportes["fecha"] > corte - pd.Timedelta(days=C.VENTANA_REPORTES_DIAS))
                             & (reportes["fecha"] <= corte)]
        s_ciudadania = 0.0 if terminada else min(1.0, len(recientes) / C.REPORTES_TOPE)

        valores = {"inactividad": s_inactividad, "atraso": s_atraso, "brecha": s_brecha,
                   "contrato": s_contrato, "ciudadania": s_ciudadania}
        aportes = {k: round(pesos[k] * v, 1) for k, v in valores.items()}
        alertas = [k for k, v in valores.items() if v >= C.UMBRALES_ALERTA[k]]
        filas.append({
            "obra_id": oid, "nombre": obra["nombre"], "tipo": obra["tipo"], "canton": obra["canton"],
            "institucion_ejecutora": obra["institucion_ejecutora"], "contratista": obra["contratista"],
            "monto_original_crc": obra["monto_original_crc"], "monto_vigente_crc": monto,
            "fecha_fin_vigente": fin_vig.date(), "fase": "terminada" if terminada else "en ejecucion",
            "en_cola_dispositivos": en_dispositivos, "dias_sin_datos": sin_datos_corte,
            "ultima_captura": ultima_captura,
            "racha_inactividad_dias": len(racha), "explicacion_inactividad": _explicar_racha(racha),
            "avance_previsto_pct": previsto, "avance_reportado_pct": ultimo["avance_reportado_pct"],
            "fecha_ultimo_informe": ultimo["fecha"].date(), "atraso_pts": round(atraso, 1),
            "incremento_reportado_pts": round(incremento, 1),
            "proporcion_semanas_activas": round(proporcion_activa, 2),
            "aumento_monto_pct": round(100 * aumento, 1), "prorroga_reciente": bool(len(prorrogas)),
            "reportes_30d": len(recientes),
            **{f"senal_{k}": round(v, 3) for k, v in valores.items()},
            **{f"aporte_{k}": v for k, v in aportes.items()},
            "puntaje": round(sum(aportes.values()), 1),
            "alertas": ";".join(alertas),
            "amerita_revision": bool(alertas) and not terminada and not en_dispositivos,
        })
    out = pd.DataFrame(filas).sort_values(["amerita_revision", "puntaje"], ascending=[False, False])
    out["prioridad"] = range(1, len(out) + 1)
    return out.reset_index(drop=True)


# --- 4. Resumen de cartera en una frase -------------------------------------------------------
def resumen(sen: pd.DataFrame) -> dict:
    n = int(sen["amerita_revision"].sum())
    disp = sen[sen["en_cola_dispositivos"]]
    partes = [f"{n} obra amerita revisión" if n == 1 else f"{n} obras ameritan revisión"]
    if len(disp) == 1:
        partes.append(f"1 cámara lleva {int(disp['dias_sin_datos'].iloc[0])} días sin datos")
    elif len(disp) > 1:
        partes.append(f"{len(disp)} cámaras sin datos")
    return {
        "fecha_corte": str(C.FECHA_CORTE),
        "frase": " · ".join(partes),
        "obras_que_ameritan_revision": sen.loc[sen["amerita_revision"], "obra_id"].tolist(),
        "cola_dispositivos": disp["obra_id"].tolist(),
        "pesos": C.PESOS,
        "umbrales_alerta": C.UMBRALES_ALERTA,
    }
