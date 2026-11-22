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
    return int((C.HORA_ULTIMA_CAPTURA - C.HORA_PRIMERA_CAPTURA + 1) * 3600 / C.INTERVALO_SEG)


def capturas_laborales_esperadas() -> int:
    ini, fin = C.HORARIO_LABORAL
    return int((fin - ini + 1) * 3600 / C.INTERVALO_SEG)


def periodos(camaras: pd.DataFrame) -> pd.DataFrame:
    """Una fila por obra, cámara y día en que esa cámara estuvo asignada a esa obra (hasta la fecha de corte)."""
    corte = pd.Timestamp(C.FECHA_CORTE)
    filas = []
    for _, c in camaras.iterrows():
        fin = min(c["hasta"], corte) if pd.notna(c["hasta"]) else corte
        for dia in pd.date_range(c["desde"], fin, freq="D"):
            filas.append([c["obra_id"], c["camara_id"], dia, c["inventario_fotos"] == "si"])
    return pd.DataFrame(filas, columns=["obra_id", "camara_id", "fecha", "con_inventario"])


# --- 1. Estado de cada obra en cada día -------------------------------------------------
def estado_diario(obras, camaras, eventos, feriados, inventario, lectura, clima) -> pd.DataFrame:
    """Una fila por obra y día con cámara: cobertura, actividad observada, estado y contexto.

    Si la cámara reporta su inventario de fotos, la cobertura es fotos recibidas / esperadas.
    Si no lo reporta (como en los datos públicos del piloto), LupIA solo sabe si ese día hay archivo:
    con archivo supone que la cámara funcionó todo el día (cobertura_supuesta) y sin archivo
    lo marca como sin datos.
    """
    base = periodos(camaras[camaras["obra_id"].isin(obras.index)])
    ini, fin = C.HORARIO_LABORAL
    claves = ["camara_id", "fecha"]

    inv = inventario.assign(fecha=inventario["fecha_hora"].dt.normalize(), hora=inventario["fecha_hora"].dt.hour)
    det = lectura.detecciones
    det = det.assign(fecha=det["fecha_hora"].dt.normalize(), hora=det["fecha_hora"].dt.hour)
    det_lab = det[det["hora"].between(ini, fin)]
    tablas = [
        inv.groupby(claves).size().rename("capturas_recibidas"),
        inv[inv["hora"].between(ini, fin)].groupby(claves).size().rename("capturas_laborales"),
        det_lab.groupby(claves)["nombre_imagen"].nunique().rename("imagenes_con_deteccion"),
        det_lab[det_lab["clase"] == "Persona"].groupby(claves).size().rename("personas_detectadas"),
        det_lab[det_lab["clase"].isin(C.MAQUINARIA)].groupby(claves)["nombre_imagen"].nunique()
        .rename("imagenes_con_maquinaria"),
    ]
    d = base.merge(pd.concat(tablas, axis=1).reset_index(), on=claves, how="left")
    conteos = ["capturas_recibidas", "capturas_laborales", "imagenes_con_deteccion",
               "personas_detectadas", "imagenes_con_maquinaria"]
    d[conteos] = d[conteos].fillna(0).astype(int)
    archivos = set(zip(lectura.dias_con_archivo["camara_id"], lectura.dias_con_archivo["fecha"]))
    d["con_archivo"] = [(c, f) in archivos for c, f in zip(d["camara_id"], d["fecha"])]

    sin_inv = ~d["con_inventario"]
    d["cobertura_supuesta"] = sin_inv & d["con_archivo"]
    d.loc[d["cobertura_supuesta"], "capturas_laborales"] = capturas_laborales_esperadas()
    d["cobertura"] = np.where(sin_inv, np.where(d["con_archivo"], np.nan, 0.0),
                              d["capturas_recibidas"] / capturas_esperadas_por_dia()).round(3)
    d["pct_actividad"] = np.where(d["capturas_laborales"] > 0,
                                  d["imagenes_con_deteccion"] / d["capturas_laborales"].clip(lower=1), 0.0).round(3)
    sin_datos = np.where(sin_inv, ~d["con_archivo"], d["cobertura"] < C.UMBRAL_COBERTURA)
    d["estado"] = np.select([sin_datos, d["pct_actividad"] >= C.UMBRAL_ACTIVIDAD],
                            ["sin_datos", "actividad"], default="sin_actividad")

    # Contexto que puede explicar un día sin actividad
    nombres_feriado = dict(zip(feriados["fecha"], feriados["nombre"]))
    d["feriado"] = d["fecha"].map(nombres_feriado).fillna("")
    d["es_habil"] = (d["fecha"].dt.weekday < 5) & (d["feriado"] == "")
    d = d.merge(clima[["obra_id", "fecha", "lluvia_mm"]], on=["obra_id", "fecha"], how="left")
    suspendidos = {(oid, dia) for oid in obras.index for dia in dias_suspendidos(oid, eventos)}
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
    return d.drop(columns=["con_inventario"])


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
         # En semanas incompletas (inicio o fin del período con cámara) basta con los días hábiles que haya
         s["dias_actividad"] >= np.minimum(C.DIAS_ACTIVOS_SEMANA, s["dias_habiles"].clip(lower=1))],
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


def puntaje(valores: dict, pesos: dict) -> float:
    """Puntaje de 0 a 100 con las señales que tienen dato.

    Si a una obra le faltan datos (por ejemplo, no hay contrato registrado), el puntaje se calcula
    con las señales disponibles y se reparte su peso: así no se castiga ni se premia la falta de datos.
    """
    disponibles = {k: v for k, v in valores.items() if pd.notna(v)}
    peso_total = sum(pesos[k] for k in disponibles)
    if not peso_total:
        return np.nan
    return round(100 * sum(pesos[k] * v for k, v in disponibles.items()) / peso_total, 1)


def senales(obras, camaras, eventos, diario, semanal, avance, pagos, reportes, inventario, pesos=None) -> pd.DataFrame:
    """Calcula las cinco señales (de 0 a 1, o vacía si falta el dato), el puntaje (0 a 100) y las alertas."""
    pesos = pesos or C.PESOS
    corte_cartera = pd.Timestamp(C.FECHA_CORTE)
    filas = []
    for oid, obra in obras.iterrows():
        d = diario[diario["obra_id"] == oid]
        cams = camaras[camaras["obra_id"] == oid]
        # Cada obra se analiza a su propia fecha de corte: el último día con cámara asignada
        corte = min(d["fecha"].max(), corte_cartera) if len(d) else corte_cartera
        historica = len(d) > 0 and corte < corte_cartera  # la cámara ya se retiró de esta obra
        inicio_ventana = max(corte - pd.Timedelta(weeks=12) + pd.Timedelta(days=1), d["fecha"].min()) if len(d) else corte
        semanas_ventana = max((corte - inicio_ventana).days / 7, 1)
        rec = fecha_recepcion(obra, eventos)
        terminada = rec is not None and rec <= corte
        con_contrato = pd.notna(obra["fecha_inicio"]) and pd.notna(obra["fecha_fin_original"])
        fin_vig = fin_vigente(obra, eventos, corte) if con_contrato else pd.NaT
        monto = monto_vigente(obra, eventos, corte)

        # Cola de dispositivos: la cámara lleva días sin enviar datos
        sin_datos_corte = _dias_sin_datos_al_corte(d)
        en_dispositivos = not historica and sin_datos_corte >= C.DIAS_SIN_DATOS_DISPOSITIVO
        con_datos = d[d["estado"] != "sin_datos"]
        ultima_captura = con_datos["fecha"].max() if len(con_datos) else pd.NaT
        inv = inventario[inventario["camara_id"].isin(cams["camara_id"])]["fecha_hora"]
        if len(inv):
            ultima_captura = inv.max()

        # Señal 1: inactividad con la cámara funcionando
        racha = pd.DataFrame() if terminada else _racha_inactividad(d)
        s_inactividad = 0.0 if (terminada or en_dispositivos) else min(1.0, len(racha) / C.DIAS_INACTIVIDAD_TOPE)

        # Señal 2: atraso del avance reportado frente al cronograma vigente
        rep = avance[(avance["obra_id"] == oid) & (avance["fecha"] <= corte)].sort_values("fecha")
        ultimo = rep.iloc[-1] if len(rep) else None
        if ultimo is not None and con_contrato:
            previsto = avance_previsto(obra["fecha_inicio"], fin_vigente(obra, eventos, ultimo["fecha"]), ultimo["fecha"])
            atraso = max(0.0, previsto - ultimo["avance_reportado_pct"])
            s_atraso = 0.0 if terminada else min(1.0, atraso / C.ATRASO_TOPE_PTS)
        else:
            previsto, atraso, s_atraso = np.nan, np.nan, np.nan

        # Señal 3: lo reportado avanza más de lo que la actividad observada permite suponer
        sem = semanal[(semanal["obra_id"] == oid) & semanal["estado_semana"].isin(["actividad", "sin_actividad"])]
        proporcion_activa = float((sem["estado_semana"] == "actividad").mean()) if len(sem) else np.nan
        en_ventana = rep[rep["fecha"] >= inicio_ventana]
        if len(en_ventana) >= 2 and con_contrato and len(sem):
            incremento = float(en_ventana["avance_reportado_pct"].iloc[-1] - en_ventana["avance_reportado_pct"].iloc[0])
            duracion_sem = max((fin_vig - obra["fecha_inicio"]).days / 7, 1)
            incremento_tipico = 100 / duracion_sem * semanas_ventana
            proporcion_reportada = min(1.0, max(incremento, 0) / incremento_tipico)
            s_brecha = 0.0 if terminada else float(np.clip(proporcion_reportada - proporcion_activa, 0, 1))
        else:
            incremento, s_brecha = np.nan, np.nan

        # Señal 4: cambios contractuales (aumento de monto o prórroga reciente)
        prorrogas = eventos[(eventos["obra_id"] == oid) & (eventos["tipo"] == "prorroga")
                            & (eventos["fecha"] > corte - pd.Timedelta(days=C.VENTANA_PRORROGA_DIAS))
                            & (eventos["fecha"] <= corte)]
        if pd.notna(obra["monto_original_crc"]):
            aumento = monto / obra["monto_original_crc"] - 1
            s_contrato = 0.0 if terminada else max(min(1.0, max(aumento, 0) / C.AUMENTO_TOPE),
                                                     C.VALOR_PRORROGA if len(prorrogas) else 0.0)
        else:
            aumento, s_contrato = np.nan, np.nan

        # Señal 5: reportes ciudadanos recientes
        recientes = reportes[(reportes["obra_id"] == oid)
                             & (reportes["fecha"] > corte - pd.Timedelta(days=C.VENTANA_REPORTES_DIAS))
                             & (reportes["fecha"] <= corte)]
        s_ciudadania = 0.0 if terminada else min(1.0, len(recientes) / C.REPORTES_TOPE)

        valores = {"inactividad": s_inactividad, "atraso": s_atraso, "brecha": s_brecha,
                   "contrato": s_contrato, "ciudadania": s_ciudadania}
        peso_disponible = sum(pesos[k] for k, v in valores.items() if pd.notna(v))
        aportes = {k: (round(100 * pesos[k] * v / peso_disponible, 1) if pd.notna(v) else np.nan)
                   for k, v in valores.items()}
        alertas = [k for k, v in valores.items() if pd.notna(v) and v >= C.UMBRALES_ALERTA[k]]
        filas.append({
            "obra_id": oid, "nombre": obra["nombre"], "tipo": obra["tipo"], "provincia": obra["provincia"],
            "canton": obra["canton"], "lat": obra["lat"], "lon": obra["lon"],
            "institucion_ejecutora": obra["institucion_ejecutora"], "contratista": obra["contratista"] or "",
            "fuente_datos": obra["fuente_datos"], "nota": obra["nota"],
            "monto_original_crc": obra["monto_original_crc"], "monto_vigente_crc": monto,
            "fecha_inicio": obra["fecha_inicio"].date() if pd.notna(obra["fecha_inicio"]) else None,
            "fecha_fin_vigente": fin_vig.date() if pd.notna(fin_vig) else None,
            "fase": "terminada" if terminada else "en ejecucion",
            "historica": historica, "periodo_desde": d["fecha"].min().date() if len(d) else None,
            "fecha_corte_obra": corte.date(),
            "camaras": ", ".join(cams["camara_id"]),
            "inventario_fotos": bool((cams["inventario_fotos"] == "si").all()) if len(cams) else False,
            "dias_con_datos": int((d["estado"] != "sin_datos").sum()), "dias_periodo": len(d),
            "en_cola_dispositivos": en_dispositivos, "dias_sin_datos": sin_datos_corte,
            "ultima_captura": ultima_captura,
            "racha_inactividad_dias": len(racha), "explicacion_inactividad": _explicar_racha(racha),
            "avance_previsto_pct": previsto,
            "avance_reportado_pct": ultimo["avance_reportado_pct"] if ultimo is not None else np.nan,
            "fecha_ultimo_informe": ultimo["fecha"].date() if ultimo is not None else None,
            "atraso_pts": round(atraso, 1) if pd.notna(atraso) else np.nan,
            "incremento_reportado_pts": round(incremento, 1) if pd.notna(incremento) else np.nan,
            "proporcion_semanas_activas": round(proporcion_activa, 2) if pd.notna(proporcion_activa) else np.nan,
            "aumento_monto_pct": round(100 * aumento, 1) if pd.notna(aumento) else np.nan,
            "prorroga_reciente": bool(len(prorrogas)),
            "reportes_30d": len(recientes),
            **{f"senal_{k}": (round(v, 3) if pd.notna(v) else np.nan) for k, v in valores.items()},
            **{f"aporte_{k}": v for k, v in aportes.items()},
            "senales_con_dato": sum(pd.notna(v) for v in valores.values()),
            "puntaje": puntaje(valores, pesos),
            "alertas": ";".join(alertas),
            "amerita_revision": bool(alertas) and not terminada and not en_dispositivos and not historica,
        })
    out = pd.DataFrame(filas)
    out["_orden"] = np.select([out["amerita_revision"], ~out["en_cola_dispositivos"] & ~out["historica"],
                               out["en_cola_dispositivos"]], [0, 1, 2], default=3)
    out = out.sort_values(["_orden", "puntaje"], ascending=[True, False]).drop(columns="_orden")
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
        "obras_historicas": sen.loc[sen["historica"], "obra_id"].tolist(),
        "frase": " · ".join(partes),
        "obras_que_ameritan_revision": sen.loc[sen["amerita_revision"], "obra_id"].tolist(),
        "cola_dispositivos": disp["obra_id"].tolist(),
        "pesos": C.PESOS,
        "umbrales_alerta": C.UMBRALES_ALERTA,
    }
