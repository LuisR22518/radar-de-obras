"""Corre todo el cálculo del Radar y escribe los resultados en salidas/.

Uso:  python scripts/construir.py

Salidas:
  estado_diario.csv    una fila por obra y día
  matriz_semanal.csv   una celda por obra y semana (matriz de cartera)
  senales.csv          señales, puntaje, alertas y prioridad por obra
  serie_avance.csv     avance previsto, reportado y pagado, por obra (para contrastar)
  evidencia.csv        imágenes de los últimos 21 días con sus detecciones (visor de evidencia)
  eventos.csv          contexto en la línea de tiempo: contrato, feriados y reportes
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
from radar.contrato import avance_previsto, fin_vigente, monto_vigente  # noqa: E402


def serie_avance(obras, eventos, avance, pagos) -> pd.DataFrame:
    filas = []
    corte = pd.Timestamp(C.FECHA_CORTE)
    for oid, obra in obras.iterrows():
        fin = fin_vigente(obra, eventos, corte)
        for fecha in pd.date_range(obra["fecha_inicio"], max(fin, corte), freq="7D"):
            filas.append([oid, fecha, "previsto",
                          avance_previsto(obra["fecha_inicio"], fin_vigente(obra, eventos, fecha), fecha)])
    for _, a in avance.iterrows():
        filas.append([a["obra_id"], a["fecha"], "reportado", a["avance_reportado_pct"]])
    for _, p in pagos.iterrows():
        obra = obras.loc[p["obra_id"]]
        pct = 100 * p["pagado_acumulado_crc"] / monto_vigente(obra, eventos, p["fecha"])
        filas.append([p["obra_id"], p["fecha"], "pagado", round(pct, 1)])
    return pd.DataFrame(filas, columns=["obra_id", "fecha", "serie", "valor_pct"])


def eventos_linea_tiempo(eventos, feriados, reportes) -> pd.DataFrame:
    inicio, corte = pd.Timestamp(C.INICIO_MONITOREO), pd.Timestamp(C.FECHA_CORTE)
    filas = [[e["obra_id"], e["fecha"], "contrato", e["tipo"], e["detalle"]] for _, e in eventos.iterrows()]
    filas += [[r["obra_id"], r["fecha"], "ciudadania", r["tipo"], r["descripcion"]] for _, r in reportes.iterrows()]
    for _, f in feriados[(feriados["fecha"] >= inicio) & (feriados["fecha"] <= corte)].iterrows():
        filas.append(["*", f["fecha"], "feriado", "feriado", f["nombre"]])
    return pd.DataFrame(filas, columns=["obra_id", "fecha", "categoria", "tipo", "detalle"]).sort_values("fecha")


def evidencia(obras, inventario, detecciones, dias=21) -> pd.DataFrame:
    """Para el visor: hasta 4 imágenes por día (cerca de las 8, 10, 13 y 15 h) de los últimos días, con sus recuadros."""
    corte = pd.Timestamp(C.FECHA_CORTE)
    inv = inventario[inventario["fecha_hora"] > corte - pd.Timedelta(days=dias)].copy()
    inv["fecha"] = inv["fecha_hora"].dt.normalize()
    elegidas = []
    for _, grupo in inv.groupby(["camara_id", "fecha"]):
        for hora in (8, 10, 13, 15):
            objetivo = grupo["fecha"].iloc[0] + pd.Timedelta(hours=hora)
            elegidas.append(grupo.loc[(grupo["fecha_hora"] - objetivo).abs().idxmin()])
    sel = pd.DataFrame(elegidas)[["camara_id", "nombre_imagen", "fecha_hora"]].drop_duplicates()
    out = sel.merge(detecciones.drop(columns=["fecha_hora"]), on=["camara_id", "nombre_imagen"], how="left")
    out["obra_id"] = out["camara_id"].map(dict(zip(obras["camara_id"], obras["obra_id"])))
    return out.sort_values(["obra_id", "fecha_hora"]).reset_index(drop=True)


def calcular() -> dict:
    """Corre todo el cálculo y devuelve las tablas. La usan este script y los cargadores del sitio."""
    obras, eventos, feriados = L.cargar_obras(), L.cargar_eventos(), L.cargar_feriados()
    inventario, detecciones = L.cargar_inventario(), L.cargar_detecciones()
    clima, avance, pagos, reportes = L.cargar_clima(), L.cargar_avance(), L.cargar_pagos(), L.cargar_reportes()

    diario = R.estado_diario(obras, eventos, feriados, inventario, detecciones, clima)
    semanal = R.matriz_semanal(diario)
    sen = R.senales(obras, eventos, diario, semanal, avance, reportes, inventario)
    res = R.resumen(sen)
    res["origen_clima"] = sorted(clima["origen"].unique().tolist())
    return {
        "obras": obras.reset_index(drop=True), "estado_diario": diario, "matriz_semanal": semanal,
        "senales": sen, "serie_avance": serie_avance(obras, eventos, avance, pagos),
        "eventos": eventos_linea_tiempo(eventos, feriados, reportes),
        "evidencia": evidencia(obras, inventario, detecciones), "resumen": res,
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
    cols = ["prioridad", "obra_id", "nombre", "puntaje", "alertas", "en_cola_dispositivos", "racha_inactividad_dias"]
    print(sen[cols].to_string(index=False))


if __name__ == "__main__":
    main()
