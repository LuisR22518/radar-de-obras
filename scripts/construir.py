"""Corre todo el cálculo de LupIA y escribe los resultados en salidas/.

Uso:  python scripts/construir.py

Salidas:
  estado_diario.csv    una fila por obra y día con cámara
  matriz_semanal.csv   una celda por obra y semana
  senales.csv          señales, puntaje, alertas y prioridad por obra
  serie_avance.csv     avance previsto, reportado y pagado, por obra (para contrastar)
  evidencia.csv        fotos de los últimos 21 días de cada obra con sus detecciones (visor de evidencia)
  eventos.csv          contexto en la línea de tiempo: contrato, feriados y reportes
  fuentes.csv          de dónde viene cada dato de cada obra (real, simulado o registro)
  mantenimiento.csv    qué tan al día está el registro de cada obra (informes, pagos, cámara, contrato)
  calidad.csv          problemas de calidad encontrados en el registro
  bitacora.csv         últimos cambios hechos al registro, con quién los hizo
  responsables.csv     quién mantiene el registro y con qué rol
  resumen.json         la frase de cartera y los parámetros usados
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import config as C  # noqa: E402
from radar import lectura as L  # noqa: E402
from radar import reglas as R  # noqa: E402
from radar import registro as REG  # noqa: E402
from radar.contrato import avance_previsto, fin_vigente, monto_vigente  # noqa: E402

FOTOS_PILOTO = C.RAIZ / "src" / "data" / "fotos-piloto"


def serie_avance(obras, eventos, avance, pagos) -> pd.DataFrame:
    filas = []
    corte = pd.Timestamp(C.FECHA_CORTE)
    for oid, obra in obras.iterrows():
        if pd.isna(obra["fecha_inicio"]) or pd.isna(obra["fecha_fin_original"]):
            continue
        fin = fin_vigente(obra, eventos, corte)
        for fecha in pd.date_range(obra["fecha_inicio"], max(fin, corte), freq="7D"):
            filas.append([oid, fecha, "previsto",
                          avance_previsto(obra["fecha_inicio"], fin_vigente(obra, eventos, fecha), fecha)])
    for _, a in avance[avance["obra_id"].isin(obras.index)].iterrows():
        filas.append([a["obra_id"], a["fecha"], "reportado", a["avance_reportado_pct"]])
    for _, p in pagos[pagos["obra_id"].isin(obras.index)].iterrows():
        monto = monto_vigente(obras.loc[p["obra_id"]], eventos, p["fecha"])
        if pd.notna(monto) and monto > 0:
            filas.append([p["obra_id"], p["fecha"], "pagado", round(100 * p["pagado_acumulado_crc"] / monto, 1)])
    return pd.DataFrame(filas, columns=["obra_id", "fecha", "serie", "valor_pct"])


def eventos_linea_tiempo(eventos, feriados, reportes) -> pd.DataFrame:
    filas = [[e["obra_id"], e["fecha"], "contrato", e["tipo"], e["detalle"]] for _, e in eventos.iterrows()]
    filas += [[r["obra_id"], r["fecha"], "ciudadania", r["tipo"], r["descripcion"]] for _, r in reportes.iterrows()]
    filas += [["*", f["fecha"], "feriado", "feriado", f["nombre"]] for _, f in feriados.iterrows()]
    return pd.DataFrame(filas, columns=["obra_id", "fecha", "categoria", "tipo", "detalle"]).sort_values("fecha")


def evidencia(diario, inventario, lectura, dias=21) -> pd.DataFrame:
    """Para el visor: hasta 4 fotos por día (cerca de las 8, 10, 13 y 15 h) de los últimos días con datos de cada obra.

    Si la cámara no reporta inventario (datos reales del piloto), las fotos salen de las detecciones.
    Si existe la foto real anonimizada, se indica en `foto`.
    """
    det = lectura.detecciones
    fotos = pd.concat([
        inventario[["camara_id", "nombre_imagen", "fecha_hora", "imagen_piloto"]],
        det[~det["camara_id"].isin(inventario["camara_id"])][["camara_id", "nombre_imagen", "fecha_hora"]]
        .drop_duplicates().assign(imagen_piloto=""),
    ], ignore_index=True)
    fotos["fecha"] = fotos["fecha_hora"].dt.normalize()
    asignacion = diario[["obra_id", "camara_id", "fecha"]]
    fotos = fotos.merge(asignacion, on=["camara_id", "fecha"])
    ultimos = diario[diario["estado"] != "sin_datos"].groupby("obra_id")["fecha"].max()
    reales = {f.name for f in FOTOS_PILOTO.glob("*.jpg")} if FOTOS_PILOTO.exists() else set()
    dias_con_foto = set(fotos.loc[fotos["nombre_imagen"].isin(reales), "fecha"])
    recientes = fotos["fecha"] > fotos["obra_id"].map(ultimos) - pd.Timedelta(days=dias)
    # Para comparar "antes y después": el último día con actividad y el primer día con datos de cada obra
    activos = diario[diario["estado"] == "actividad"].groupby("obra_id")["fecha"].max()
    primeros = diario[diario["estado"] != "sin_datos"].groupby("obra_id")["fecha"].min()
    clave = list(zip(fotos["obra_id"], fotos["fecha"]))
    referencia = {(o, f) for o, f in activos.items()} | {(o, f) for o, f in primeros.items()}
    fotos = fotos[recientes | fotos["fecha"].isin(dias_con_foto) | pd.Series([k in referencia for k in clave], index=fotos.index)]
    elegidas = []
    for (_, fecha), grupo in fotos.groupby(["camara_id", "fecha"]):
        con_foto = grupo[grupo["nombre_imagen"].isin(reales)]
        if len(con_foto):  # si hay fotos reales ese día, se muestran esas
            elegidas += [fila for _, fila in con_foto.head(6).iterrows()]
            continue
        for hora in (8, 10, 13, 15):
            objetivo = fecha + pd.Timedelta(hours=hora)
            elegidas.append(grupo.loc[(grupo["fecha_hora"] - objetivo).abs().idxmin()])
    sel = pd.DataFrame(elegidas).drop_duplicates(["camara_id", "nombre_imagen"])
    out = sel.merge(det.drop(columns=["fecha_hora"]), on=["camara_id", "nombre_imagen"], how="left")
    out["foto"] = out["nombre_imagen"].map(lambda n: f"fotos-piloto/{n}" if n in reales else "")
    cols = ["obra_id", "camara_id", "nombre_imagen", "fecha_hora", "clase", "probabilidad",
            "x1", "y1", "x2", "y2", "origen", "fuente", "imagen_piloto", "foto"]
    return out[cols].sort_values(["obra_id", "fecha_hora"]).reset_index(drop=True)


def mantenimiento(obras, sen, avance, pagos) -> pd.DataFrame:
    """Qué tan al día está el registro de cada obra en seguimiento: último informe de avance, último pago,
    última foto de la cámara y datos del contrato. Lo usa la página de Mantenimiento."""
    corte = pd.Timestamp(C.FECHA_CORTE)
    campos_contrato = {"monto_original_crc": "monto", "fecha_inicio": "fecha de inicio",
                       "fecha_fin_original": "fecha de fin", "contratista": "contratista"}

    def ultimo(tabla, oid):
        filas = tabla[tabla["obra_id"] == oid].sort_values("fecha")
        return filas.iloc[-1] if len(filas) else None

    filas = []
    for _, s in sen[~sen["historica"]].iterrows():
        oid, obra = s["obra_id"], obras.loc[s["obra_id"]]
        terminada = s["fase"] == "terminada"
        inf, pag = ultimo(avance, oid), ultimo(pagos, oid)
        dias_inf = (corte - inf["fecha"]).days if inf is not None else None
        dias_pag = (corte - pag["fecha"]).days if pag is not None else None
        faltan = [n for c, n in campos_contrato.items() if pd.isna(obra.get(c))]
        inf_vencido = not terminada and (dias_inf is None or dias_inf > C.VENCE_INFORME_DIAS)
        pag_vencido = not terminada and (dias_pag is None or dias_pag > C.VENCE_PAGO_DIAS)
        camara = bool(s["en_cola_dispositivos"])
        filas.append([oid, s["nombre"], s["fase"],
                      inf["fecha"].date() if inf is not None else None, inf.get("documento") if inf is not None else None,
                      dias_inf, inf_vencido,
                      pag["fecha"].date() if pag is not None else None, pag.get("documento") if pag is not None else None,
                      dias_pag, pag_vencido,
                      str(s["ultima_captura"])[:10] if pd.notna(s["ultima_captura"]) else None, int(s["dias_sin_datos"]),
                      camara, ", ".join(faltan),
                      not (inf_vencido or pag_vencido or camara or faltan)])
    return pd.DataFrame(filas, columns=["obra_id", "nombre", "fase", "ultimo_informe", "documento_informe",
                                        "dias_informe", "informe_vencido", "ultimo_pago", "documento_pago", "dias_pago",
                                        "pago_vencido", "ultima_foto", "dias_sin_datos", "camara_a_mantenimiento",
                                        "contrato_faltante", "al_dia"])


def fuentes(obras, camaras, lectura) -> pd.DataFrame:
    filas = []
    dias = lectura.dias_con_archivo
    for oid, obra in obras.iterrows():
        for _, cam in camaras[camaras["obra_id"] == oid].iterrows():
            d = dias[dias["camara_id"] == cam["camara_id"]]
            formatos = ", ".join(sorted(d["formato"].unique())) if len(d) else "sin archivos"
            filas.append([oid, cam["camara_id"], obra["fuente_datos"], formatos, len(d),
                          cam["inventario_fotos"], cam["desde"].date(),
                          cam["hasta"].date() if pd.notna(cam["hasta"]) else None])
    return pd.DataFrame(filas, columns=["obra_id", "camara_id", "fuente_datos", "formato", "dias_con_archivo",
                                        "inventario_fotos", "desde", "hasta"])


def calcular() -> dict:
    """Corre todo el cálculo y devuelve las tablas. La usan este script y los cargadores del sitio."""
    reg = L.cargar_registro()
    obras, camaras, eventos = reg["obras"], reg["camaras"], reg["eventos_contrato"]
    feriados, avance, pagos, reportes = reg["feriados"], reg["avance_reportado"], reg["pagos"], reg["reportes_ciudadanos"]
    camaras = camaras[camaras["obra_id"].isin(obras.index)]
    lectura = L.cargar_dIAra(camaras)
    inventario = L.cargar_inventario(camaras)
    clima = L.cargar_clima()

    diario = R.estado_diario(obras, camaras, eventos, feriados, inventario, lectura, clima)
    semanal = R.matriz_semanal(diario)
    sen = R.senales(obras, camaras, eventos, diario, semanal, avance, pagos, reportes, inventario)
    res = R.resumen(sen)
    res["origen_clima"] = sorted(clima["origen"].unique().tolist())
    res["vence_informe_dias"], res["vence_pago_dias"] = C.VENCE_INFORME_DIAS, C.VENCE_PAGO_DIAS
    res["dias_sin_datos_camara"] = C.DIAS_SIN_DATOS_DISPOSITIVO
    res["canal_denuncias"] = C.CANAL_DENUNCIAS
    leer = lambda nombre: (C.REGISTRO / nombre).read_text(encoding="utf-8") if (C.REGISTRO / nombre).exists() else ""  # noqa: E731
    res["registro_actualizado"] = leer("actualizado.txt").strip()
    res["registro_hoja"] = json.loads(leer("fuente.json")).get("url", "") if leer("fuente.json") else ""
    intento = json.loads(leer("intento.json")) if leer("intento.json") else {}
    res["registro_leido"] = intento.get("fecha_hora", "")
    res["registro_rechazado"] = intento.get("aceptado") is False
    filas = [[REG.NOMBRES[p.tabla], p.fila, p.nivel, p.mensaje] for p in reg.problemas]
    if res["registro_rechazado"]:  # errores de la versión de la hoja que no se aceptó
        filas = [[p["tabla"], p["fila"], p["nivel"], p["mensaje"]] for p in intento["problemas"] if p["nivel"] == "error"] + filas
    calidad = pd.DataFrame(filas, columns=["tabla", "fila", "nivel", "mensaje"])
    bitacora = pd.read_csv(C.REGISTRO / "bitacora.csv").tail(50).iloc[::-1]
    responsables = reg["responsables"].assign(rol=lambda d: d["rol"].map(REG.ROLES))[["nombre", "cargo", "rol", "activo", "correo"]]
    return {
        "obras": obras.reset_index(drop=True), "estado_diario": diario, "matriz_semanal": semanal,
        "senales": sen, "serie_avance": serie_avance(obras, eventos, avance, pagos),
        "eventos": eventos_linea_tiempo(eventos, feriados, reportes),
        "evidencia": evidencia(diario, inventario, lectura), "fuentes": fuentes(obras, camaras, lectura),
        "mantenimiento": mantenimiento(obras, sen, avance, pagos),
        "calidad": calidad, "bitacora": bitacora, "responsables": responsables, "resumen": res,
        "hitos": reg["hitos"][reg["hitos"]["obra_id"].isin(obras.index)], "fotos": reg["fotos"][reg["fotos"]["obra_id"].isin(obras.index)],
    }


def main():
    C.SALIDAS.mkdir(exist_ok=True)
    tablas = calcular()
    for nombre, tabla in tablas.items():
        if nombre != "resumen":
            tabla.to_csv(C.SALIDAS / f"{nombre}.csv", index=False)
    res, sen = tablas["resumen"], tablas["senales"]
    (C.SALIDAS / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(res["frase"])
    cols = ["prioridad", "obra_id", "nombre", "puntaje", "senales_con_dato", "alertas", "en_cola_dispositivos",
            "historica", "racha_inactividad_dias"]
    print(sen[cols].to_string(index=False))


if __name__ == "__main__":
    main()
