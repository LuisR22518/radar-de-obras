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
  calidad.csv          problemas de calidad encontrados en el registro
  bitacora.csv         últimos cambios hechos al registro por el gestor de datos
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
    fotos = fotos[recientes | fotos["fecha"].isin(dias_con_foto)]
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
    res["registro_actualizado"] = (C.REGISTRO / "actualizado.txt").read_text(encoding="utf-8").strip() \
        if (C.REGISTRO / "actualizado.txt").exists() else ""
    res["registro_hoja"] = json.loads((C.REGISTRO / "fuente.json").read_text(encoding="utf-8")).get("url", "") \
        if (C.REGISTRO / "fuente.json").exists() else ""
    calidad = pd.DataFrame([[REG.NOMBRES[p.tabla], p.fila, p.nivel, p.mensaje] for p in reg.problemas],
                           columns=["tabla", "fila", "nivel", "mensaje"])
    bitacora = pd.read_csv(C.REGISTRO / "bitacora.csv").tail(50).iloc[::-1]
    return {
        "obras": obras.reset_index(drop=True), "estado_diario": diario, "matriz_semanal": semanal,
        "senales": sen, "serie_avance": serie_avance(obras, eventos, avance, pagos),
        "eventos": eventos_linea_tiempo(eventos, feriados, reportes),
        "evidencia": evidencia(diario, inventario, lectura), "fuentes": fuentes(obras, camaras, lectura),
        "calidad": calidad, "bitacora": bitacora, "resumen": res,
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
