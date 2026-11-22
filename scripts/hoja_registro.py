"""Arma la hoja de cálculo del registro de obras (LupIA · Registro de obras) a partir de datos/registro/.

Uso:  python scripts/hoja_registro.py salida.xlsx

El archivo se sube a Google Drive, que lo convierte en una hoja de Google. Sirve para crear la hoja
la primera vez o para restaurarla desde la copia del repositorio. Trae una pestaña LEEME con las
instrucciones para el gestor de datos, una pestaña por tabla, listas desplegables y validación de
fechas y números, para que los errores más comunes no lleguen a LupIA.
"""
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import registro as R  # noqa: E402

TINTA, NIEBLA = "13263A", "F3F5F7"
FILAS = 1000  # hasta dónde llegan las validaciones


def leeme(ws):
    ws.title = "LEEME"
    filas = [
        ["LupIA · Registro de obras"],
        ["Esta hoja es la base de datos que LupIA usa además de las cámaras de dIAra. La mantiene el gestor de datos; el auditor no la edita."],
        ["LupIA la lee sola cada hora. Si encuentra errores, conserva la última versión buena y los muestra en la página Datos."],
        [],
        ["Reglas"],
        ["1. No cambie los nombres de las pestañas ni de las columnas (fila 1)."],
        ["2. Una fila por registro. No deje filas vacías en medio de los datos."],
        ["3. Escriba las fechas como fechas. Los montos, en colones y sin símbolo."],
        ["4. Use las listas desplegables donde las haya."],
        ["5. Cada cambio de contrato, informe o pago debe tener su documento de respaldo."],
        ["6. Para quitar una obra, cambie estado_registro a archivada; no borre la fila."],
        [],
        ["Pestaña", "Columna", "Obligatoria", "Qué poner"],
    ]
    for tabla, cols in R.TABLAS.items():
        for col, _tipo, oblig in cols:
            filas.append([tabla, col, "sí" if oblig else "no", R.DESCRIPCIONES[tabla][col]])
    for f in filas:
        ws.append(f)
    ws["A1"].font = Font(bold=True, size=16, color=TINTA)
    ws["A5"].font = Font(bold=True, size=12, color=TINTA)
    for c in ws[13]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=TINTA)
    for col, ancho in zip("ABCD", (22, 24, 12, 90)):
        ws.column_dimensions[col].width = ancho
    for fila in ws.iter_rows(min_row=14):
        fila[3].alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A14"


def pestana(wb, tabla: str, df: pd.DataFrame):
    ws = wb.create_sheet(tabla)
    cols = R.TABLAS[tabla]
    ws.append([c for c, _, _ in cols])
    for _, fila in df.iterrows():
        valores = []
        for col, tipo, _ in cols:
            v = fila[col]
            if pd.isna(v) or v == "":
                valores.append(None)
            elif tipo == "fecha":
                valores.append(v.to_pydatetime().date())
            elif tipo == "numero":
                valores.append(int(v) if float(v).is_integer() else float(v))
            else:
                valores.append(str(v))
        ws.append(valores)
    for j, (col, tipo, oblig) in enumerate(cols, start=1):
        letra = get_column_letter(j)
        celda = ws.cell(row=1, column=j)
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor=TINTA)
        celda.comment = Comment(("Obligatoria. " if oblig else "") + R.DESCRIPCIONES[tabla][col], "LupIA")
        ws.column_dimensions[letra].width = max(12, min(40, len(col) + 4))
        rango = f"{letra}2:{letra}{FILAS}"
        if tipo == "fecha":
            for fila in ws.iter_rows(min_row=2, min_col=j, max_col=j):
                fila[0].number_format = "yyyy-mm-dd"
            dv = DataValidation(type="date", operator="greaterThan", formula1="36526", allow_blank=True,
                                showErrorMessage=True, error="Escriba una fecha válida.")
        elif tipo == "numero":
            dv = DataValidation(type="decimal", operator="between", formula1="-1000000000000", formula2="1000000000000",
                                allow_blank=True, showErrorMessage=True, error="Escriba un número, sin símbolos.")
            if col == "avance_reportado_pct":
                dv = DataValidation(type="decimal", operator="between", formula1="0", formula2="100",
                                    allow_blank=True, showErrorMessage=True, error="El avance va de 0 a 100.")
        elif tipo.startswith("opcion:"):
            opciones = [o for o in tipo.split(":", 1)[1].split("|") if o]
            dv = DataValidation(type="list", formula1='"' + ",".join(opciones) + '"', allow_blank=True,
                                showErrorMessage=True, error="Elija una opción de la lista.")
        elif col == "obra_id" and tabla != "obras":
            dv = DataValidation(type="list", formula1=f"obras!$A$2:$A${FILAS}", allow_blank=False,
                                showErrorMessage=True, error="La obra debe existir en la pestaña obras.")
        else:
            continue
        dv.add(rango)
        ws.add_data_validation(dv)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{max(2, len(df) + 1)}"


def main(salida: Path):
    reg = R.validar(R.leer_crudo())
    wb = Workbook()
    leeme(wb.active)
    for tabla in R.TABLAS:
        pestana(wb, tabla, reg[tabla])
    wb.save(salida)
    print(f"Hoja lista en {salida}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
