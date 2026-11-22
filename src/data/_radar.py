"""Puente entre el sitio y el cálculo en Python: lo usan todos los cargadores de src/data."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")  # en Windows evita que se dañen las tildes

from scripts.construir import calcular  # noqa: E402


def imprimir(nombre: str):
    tabla = calcular()[nombre]
    if nombre == "resumen":
        sys.stdout.write(json.dumps(tabla, ensure_ascii=False))
        return
    for col in tabla.columns:  # true/false en minúscula para que JavaScript los lea como booleanos
        if tabla[col].dtype == bool:
            tabla[col] = tabla[col].map({True: "true", False: "false"})
    sys.stdout.write(tabla.to_csv(index=False))
