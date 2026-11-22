"""Lectura y limpieza de datos.

Cada función devuelve una tabla limpia y con tipos correctos. La limpieza más
importante es la del CSV de dIAra: en producción el modelo escribe sus valores
como tensores de PyTorch (por ejemplo `tensor(0.9876)`), y aquí se convierten
en números.
"""
import re
from pathlib import Path

import pandas as pd

from . import config as C

_NUMERO = re.compile(r"-?\d+(?:\.\d+)?(?:[eE]-?\d+)?")


def _numeros(texto) -> list:
    """Extrae los números de un valor crudo: 'tensor([1., 2.])', '[1, 2]' o '0.93'."""
    return [float(n) for n in _NUMERO.findall(str(texto))]


def cargar_obras() -> pd.DataFrame:
    obras = pd.read_csv(C.DATOS / "obras.csv", parse_dates=["fecha_inicio", "fecha_fin_original"])
    return obras.set_index("obra_id", drop=False)


def cargar_eventos() -> pd.DataFrame:
    return pd.read_csv(
        C.DATOS / "eventos_contrato.csv",
        parse_dates=["fecha", "suspension_desde", "suspension_hasta"],
    )


def cargar_feriados() -> pd.DataFrame:
    return pd.read_csv(C.DATOS / "feriados.csv", parse_dates=["fecha"])


def cargar_inventario() -> pd.DataFrame:
    """Imágenes recibidas por cámara (el 'latido'). Agrega fecha y hora a partir del nombre."""
    inv = pd.read_csv(C.SIMULADOS / "inventario_capturas.csv")
    inv["fecha_hora"] = pd.to_datetime(inv["nombre_imagen"].str.slice(0, 15), format="%Y%m%d-%H%M%S")
    return inv


def cargar_detecciones() -> pd.DataFrame:
    """Une los CSV diarios de dIAra (uno por cámara y por día) en una sola tabla limpia.

    Formato de producción (run_inference.py): nombre_imagen, clase, probabilidad, recuadro.
    Se agregan camara_id (sale de la carpeta) y fecha_hora (sale del nombre de la imagen),
    y el recuadro se separa en x1, y1, x2, y2 (píxeles en una imagen de 1280 x 1024).
    """
    partes = []
    for archivo in sorted(Path(C.CRUDO_DIARA).glob("*/*.csv")):
        df = pd.read_csv(archivo, dtype=str)
        if df.empty:
            continue  # día con imágenes pero sin detecciones sobre el umbral: solo trae encabezado
        df["camara_id"] = archivo.parent.name
        partes.append(df)
    columnas = ["camara_id", "nombre_imagen", "fecha_hora", "clase", "probabilidad", "x1", "y1", "x2", "y2"]
    if not partes:
        return pd.DataFrame(columns=columnas)
    det = pd.concat(partes, ignore_index=True)
    det["probabilidad"] = det["probabilidad"].map(lambda v: _numeros(v)[0])
    cajas = det["recuadro"].map(_numeros)
    det[["x1", "y1", "x2", "y2"]] = pd.DataFrame(cajas.tolist(), index=det.index)
    det["fecha_hora"] = pd.to_datetime(det["nombre_imagen"].str.slice(0, 15), format="%Y%m%d-%H%M%S")
    return det[columnas]


def cargar_clima() -> pd.DataFrame:
    """Lluvia diaria por obra. Usa la real (Open-Meteo) si existe; si no, la simulada."""
    real = C.DATOS / "clima.csv"
    archivo = real if real.exists() else C.SIMULADOS / "clima_simulado.csv"
    return pd.read_csv(archivo, parse_dates=["fecha"])


def cargar_avance() -> pd.DataFrame:
    return pd.read_csv(C.SIMULADOS / "avance_reportado.csv", parse_dates=["fecha"])


def cargar_pagos() -> pd.DataFrame:
    return pd.read_csv(C.SIMULADOS / "pagos.csv", parse_dates=["fecha"])


def cargar_reportes() -> pd.DataFrame:
    return pd.read_csv(C.SIMULADOS / "reportes_ciudadanos.csv", parse_dates=["fecha"])
