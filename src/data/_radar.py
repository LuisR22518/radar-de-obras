"""Puente entre el sitio y el cálculo en Python: lo usan todos los cargadores de src/data."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")  # en Windows evita que se dañen las tildes

import pandas as pd  # noqa: E402

SALIDAS = RAIZ / "salidas"


def imprimir(nombre: str):
    """Lee el resultado ya calculado por scripts/construir.py; si no existe, lo calcula."""
    archivo = SALIDAS / (f"{nombre}.json" if nombre == "resumen" else f"{nombre}.csv")
    if not archivo.exists():
        import contextlib
        from scripts.construir import main
        with contextlib.redirect_stdout(sys.stderr):  # lo que imprime el cálculo no debe mezclarse con los datos
            main()
    if nombre == "resumen":
        sys.stdout.write(archivo.read_text(encoding="utf-8"))
        return
    tabla = pd.read_csv(archivo)
    for col in tabla.columns:  # true/false en minúscula para que JavaScript los lea como booleanos
        if tabla[col].dtype == bool:
            tabla[col] = tabla[col].map({True: "true", False: "false"})
    sys.stdout.write(tabla.to_csv(index=False))
