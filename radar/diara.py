"""Adaptador de dIAra: lee lo que dIAra produce, en sus formatos reales, y lo deja en una sola tabla.

dIAra guarda una carpeta por cámara. LupIA acepta tres formatos y los reconoce solos:

1. Producción (`run_inference.py`): un `AAAAMMDD.csv` por día con
   `nombre_imagen, clase, probabilidad, recuadro`, donde los números vienen escritos como tensores
   de PyTorch (`tensor(0.9761)`, `tensor([x1, y1, x2, y2])`). Un archivo con solo el encabezado
   significa que ese día hubo fotos pero ninguna detección.
2. Etiquetas en CSV (las del piloto): `label_name, bbox_x, bbox_y, bbox_width, bbox_height, image_name`.
3. Etiquetas en JSON (las del piloto): `images[].objects[]` con `class` y `bbox`.

Para conectar LupIA a datos nuevos de dIAra basta con poner la carpeta de la cámara en datos/diara/
y registrarla en datos/registro/camaras.csv: no hay que cambiar código.
"""
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C

COLUMNAS = ["camara_id", "nombre_imagen", "fecha_hora", "clase", "probabilidad",
            "x1", "y1", "x2", "y2", "origen", "fuente"]
_NUMERO = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"


@dataclass
class LecturaCamara:
    """Lo que se sabe de una cámara: sus detecciones y los días en que hubo archivo."""
    detecciones: pd.DataFrame
    dias_con_archivo: pd.DataFrame  # camara_id, fecha, formato


def _fecha_hora(nombres: pd.Series) -> pd.Series:
    return pd.to_datetime(nombres.str.slice(0, 15), format="%Y%m%d-%H%M%S", errors="coerce")


def _produccion(archivo: Path) -> pd.DataFrame:
    df = pd.read_csv(archivo, dtype=str)
    if df.empty:
        return pd.DataFrame(columns=["nombre_imagen", "clase", "probabilidad", "x1", "y1", "x2", "y2"])
    df["probabilidad"] = df["probabilidad"].str.extract(f"({_NUMERO})")[0].astype(float)
    cajas = df["recuadro"].str.findall(_NUMERO).map(lambda v: [float(n) for n in v[:4]])
    df[["x1", "y1", "x2", "y2"]] = pd.DataFrame(cajas.tolist(), index=df.index)
    df["origen"] = "modelo dIAra"
    return df.drop(columns=["recuadro"])


def _etiquetas_csv(archivo: Path) -> pd.DataFrame:
    df = pd.read_csv(archivo)
    return pd.DataFrame({
        "nombre_imagen": df["image_name"], "clase": df["label_name"].map(C.CLASES_ETIQUETADO),
        "probabilidad": np.nan,
        "x1": df["bbox_x"].astype(float), "y1": df["bbox_y"].astype(float),
        "x2": (df["bbox_x"] + df["bbox_width"]).astype(float), "y2": (df["bbox_y"] + df["bbox_height"]).astype(float),
        "origen": "etiqueta humana",
    })


def _etiquetas_json(archivo: Path) -> pd.DataFrame:
    filas = []
    for img in json.loads(archivo.read_text(encoding="utf-8"))["images"]:
        nombre = Path(img.get("image_id") or img.get("image_path")).name
        for obj in img.get("objects", []):
            b = obj["bbox"]
            filas.append([nombre, C.CLASES_ETIQUETADO.get(obj["class"]), np.nan,
                          b["x_min"], b["y_min"], b["x_max"], b["y_max"], "etiqueta humana"])
    return pd.DataFrame(filas, columns=["nombre_imagen", "clase", "probabilidad", "x1", "y1", "x2", "y2", "origen"])


def _leer_archivo(archivo: Path) -> tuple[pd.DataFrame, str]:
    if archivo.suffix == ".json":
        return _etiquetas_json(archivo), "etiquetas JSON"
    encabezado = archivo.open(encoding="utf-8").readline()
    if "label_name" in encabezado:
        return _etiquetas_csv(archivo), "etiquetas CSV"
    return _produccion(archivo), "producción"


def leer_camara(carpeta: Path, camara_id: str, fuente: str = "real") -> LecturaCamara:
    """Lee todos los archivos de una cámara, sin importar su formato."""
    partes, dias = [], []
    for archivo in sorted(Path(carpeta).glob("*")):
        if archivo.suffix not in (".csv", ".json") or archivo.stem.startswith("inventario"):
            continue
        df, formato = _leer_archivo(archivo)
        df["fecha_hora"] = _fecha_hora(df["nombre_imagen"].astype(str))
        if formato == "producción":
            # El nombre del archivo dice el día, aunque no traiga detecciones
            dias.append([camara_id, pd.Timestamp(archivo.stem), formato])
        else:
            dias += [[camara_id, f, formato] for f in df["fecha_hora"].dt.normalize().dropna().unique()]
        partes.append(df)
    det = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLUMNAS)
    det["camara_id"], det["fuente"] = camara_id, fuente
    det = det.dropna(subset=["fecha_hora", "clase"])
    dias = pd.DataFrame(dias, columns=["camara_id", "fecha", "formato"]).drop_duplicates(["camara_id", "fecha"])
    return LecturaCamara(det[COLUMNAS], dias)


def leer_todas(camaras: pd.DataFrame) -> LecturaCamara:
    """Lee cada cámara del registro desde su carpeta: datos reales primero, simulados si no hay reales."""
    partes_det, partes_dias = [], []
    for camara_id in camaras["camara_id"].unique():
        real = C.DIARA_REAL / camara_id
        simulada = C.DIARA_SIMULADO / camara_id
        if real.exists():
            lectura = leer_camara(real, camara_id, "real")
        elif simulada.exists():
            lectura = leer_camara(simulada, camara_id, "simulado")
        else:
            continue
        partes_det.append(lectura.detecciones)
        partes_dias.append(lectura.dias_con_archivo)
    det = pd.concat(partes_det, ignore_index=True) if partes_det else pd.DataFrame(columns=COLUMNAS)
    dias = (pd.concat(partes_dias, ignore_index=True) if partes_dias
            else pd.DataFrame(columns=["camara_id", "fecha", "formato"]))
    return LecturaCamara(det, dias)
