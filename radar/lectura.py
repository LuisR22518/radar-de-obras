"""Lectura de las tres capas de datos de LupIA.

  1. dIAra (datos/diara/ y datos/simulados/diara/): lo lee el adaptador radar/diara.py.
  2. Registro (datos/registro/): la base de datos propia que mantiene el gestor; la lee radar/registro.py.
  3. Contexto externo: lluvia (Open-Meteo o simulada).
"""
import pandas as pd

from . import config as C
from . import diara, registro


def cargar_registro() -> registro.Registro:
    return registro.cargar()


def cargar_dIAra(camaras: pd.DataFrame) -> diara.LecturaCamara:
    return diara.leer_todas(camaras)


def cargar_inventario(camaras: pd.DataFrame) -> pd.DataFrame:
    """Fotos recibidas por cámara (el "latido"), solo para las cámaras que lo reportan.

    Las cámaras simuladas lo traen en datos/simulados/; una cámara real que lo reporte debe dejarlo
    en datos/diara/<camara>/inventario_capturas.csv con las columnas camara_id y nombre_imagen.
    """
    partes = []
    simulado = C.SIMULADOS / "inventario_capturas.csv"
    if simulado.exists():
        partes.append(pd.read_csv(simulado, dtype=str, keep_default_na=False))
    for cam in camaras.loc[camaras["inventario_fotos"] == "si", "camara_id"]:
        real = C.DIARA_REAL / cam / "inventario_capturas.csv"
        if real.exists():
            partes.append(pd.read_csv(real, dtype=str, keep_default_na=False).assign(camara_id=cam))
    if not partes:
        return pd.DataFrame(columns=["camara_id", "nombre_imagen", "imagen_piloto", "fecha_hora"])
    inv = pd.concat(partes, ignore_index=True)
    if "imagen_piloto" not in inv.columns:
        inv["imagen_piloto"] = ""
    inv = inv[inv["camara_id"].isin(set(camaras.loc[camaras["inventario_fotos"] == "si", "camara_id"]))]
    inv["fecha_hora"] = pd.to_datetime(inv["nombre_imagen"].str.slice(0, 15), format="%Y%m%d-%H%M%S")
    return inv.reset_index(drop=True)


def cargar_clima() -> pd.DataFrame:
    """Lluvia diaria por obra. Usa la real (Open-Meteo) si existe; si no, la simulada."""
    real = C.DATOS / "clima.csv"
    archivo = real if real.exists() else C.SIMULADOS / "clima_simulado.csv"
    return pd.read_csv(archivo, parse_dates=["fecha"])
