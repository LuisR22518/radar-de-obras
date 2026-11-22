"""Descarga la lluvia diaria real de cada obra desde Open-Meteo (gratis, sin clave).

Uso:  python scripts/clima.py

Escribe datos/clima.csv. Si una obra no se puede descargar (sin internet, por
ejemplo), usa la lluvia simulada y lo marca en la columna `origen`, para que el
resto del cálculo nunca se detenga. Datos de Open-Meteo con licencia CC BY 4.0:
hay que citarlos en el sitio y en el informe.
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import config as C  # noqa: E402
from radar import registro  # noqa: E402

ARCHIVO = "https://archive-api.open-meteo.com/v1/archive"
PRONOSTICO = "https://api.open-meteo.com/v1/forecast"


def pedir(url: str, params: dict) -> pd.Series:
    with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=30) as r:
        datos = json.load(r)["daily"]
    return pd.Series(datos["precipitation_sum"], index=pd.to_datetime(datos["time"]), dtype="float")


def lluvia_real(lat: float, lon: float, desde, hasta) -> pd.Series:
    """El archivo histórico tiene unos días de rezago; los días recientes salen del pronóstico."""
    comun = {"latitude": lat, "longitude": lon, "daily": "precipitation_sum", "timezone": "America/Costa_Rica"}
    serie = pedir(ARCHIVO, {**comun, "start_date": str(desde.date()), "end_date": str(hasta.date())})
    if serie.isna().any() and hasta > pd.Timestamp.now() - pd.Timedelta(days=90):
        reciente = pedir(PRONOSTICO, {**comun, "past_days": 92, "forecast_days": 1})
        serie = serie.fillna(reciente)
    return serie


def main():
    simulado = pd.read_csv(C.SIMULADOS / "clima_simulado.csv", parse_dates=["fecha"])
    reg = registro.cargar()
    camaras = reg["camaras"]
    partes = []
    for oid, obra in reg["obras"].iterrows():
        cams = camaras[camaras["obra_id"] == oid]
        if cams.empty:
            continue
        desde = cams["desde"].min()
        hasta = min(cams["hasta"].max() if cams["hasta"].notna().all() else pd.Timestamp(C.FECHA_CORTE),
                    pd.Timestamp(C.FECHA_CORTE))
        try:
            serie = lluvia_real(obra["lat"], obra["lon"], desde, hasta)
            df = serie.rename("lluvia_mm").rename_axis("fecha").reset_index()
            df = df[(df["fecha"] >= desde) & (df["fecha"] <= hasta)]
            df = df.assign(obra_id=oid, origen="Open-Meteo").dropna()
            print(f"{oid}: lluvia real descargada ({len(df)} días)")
        except Exception as error:  # sin internet o servicio caído: se usa el respaldo
            df = simulado[simulado["obra_id"] == oid]
            print(f"{oid}: no se pudo descargar ({error}); se usa lluvia simulada")
        partes.append(df[["obra_id", "fecha", "lluvia_mm", "origen"]])
    pd.concat(partes).to_csv(C.DATOS / "clima.csv", index=False)


if __name__ == "__main__":
    main()
