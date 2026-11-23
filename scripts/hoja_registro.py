"""Arma la hoja de cálculo del registro de obras (LupIA · Registro de obras) a partir de datos/registro/.

Uso:  python scripts/hoja_registro.py salida.xlsx

El archivo se sube a Google Drive, que lo convierte en una hoja de Google. Sirve para crear la hoja
la primera vez o para restaurarla desde la copia del repositorio. Trae una pestaña LEEME con las
instrucciones por rol (gerencia y encargados de actualización de obra), una pestaña por tabla, listas
desplegables, formato de montos y fechas y validación, para que los errores más comunes no lleguen a LupIA.
"""
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import registro as R  # noqa: E402

TINTA, NIEBLA, GRIS = "13263A", "F3F5F7", "9AA5B1"
FILAS = 1000  # hasta dónde llegan las validaciones


ANCHOS = {"obra_id": 9, "nombre": 30, "tipo": 20, "necesidad_publica": 50, "hito": 34, "fecha_prevista": 15,
          "fecha_cumplido": 15, "escenario": 14, "provincia": 13, "canton": 16, "lat": 10, "lon": 11,
          "institucion_ejecutora": 30, "contratista": 18, "monto_original_crc": 18, "fecha_inicio": 13,
          "fecha_fin_original": 15, "fuente_datos": 13, "escenario_simulado": 17, "escenario_desde": 15,
          "estado_registro": 15, "nota": 45, "camara_id": 12, "desde": 12, "hasta": 12, "inventario_fotos": 15,
          "fecha": 12, "detalle": 45, "dias_prorroga": 13, "monto_nuevo_crc": 17, "suspension_desde": 16,
          "suspension_hasta": 16, "documento": 38, "avance_reportado_pct": 19, "pagado_acumulado_crc": 21,
          "descripcion": 50, "con_foto": 10, "canal": 28, "fuente": 45, "actualizado_por": 30, "cargo": 34,
          "rol": 24, "activo": 9, "correo": 34}
FORMATOS = {"monto_original_crc": "#,##0", "monto_nuevo_crc": "#,##0", "pagado_acumulado_crc": "#,##0",
            "avance_reportado_pct": "0.0", "lat": "0.0000", "lon": "0.0000", "dias_prorroga": "0"}
LARGOS = {"necesidad_publica", "hito", "nombre", "institucion_ejecutora", "nota", "detalle", "documento", "descripcion", "canal", "fuente", "cargo"}
BORDE = Side(style="thin", color="DCE1E5")


def leeme(ws):
    ws.title = "LEEME"
    dia = [t for t in R.TABLAS if t not in R.CONFIGURACION]
    filas = [
        ["LupIA · Registro de obras"],
        ["Aquí se cargan los datos de cada obra que no vienen de las cámaras de dIAra. Los cambios aparecen en LupIA en unos 15 minutos."],
        ["Si un cambio tiene un error, LupIA no lo aplica: sigue con la última versión buena y explica qué corregir en su página Mantenimiento del registro."],
        [],
        ["Quién actualiza qué"],
        ["Rol", "Pestañas", "Qué hace"],
        ["Gerencia", "obras, camaras, feriados, responsables y simulacion",
         "Agrega obras, asigna cámaras, mantiene los feriados y define quién puede actualizar."],
        ["Encargado de actualización", ", ".join(t for t in dia if t != "obras"),
         "Carga lo que va pasando en cada obra: etapas, cambios de contrato, avance, pagos y reportes ciudadanos."],
        [],
        ["Reglas"],
        ["1. No cambie los nombres de las pestañas ni de la fila 1."],
        ["2. Una fila por registro, sin filas vacías en medio. En cada fila que cree o cambie, elija su nombre en actualizado_por."],
        ["3. Fechas como fechas; montos en colones, sin símbolo; use las listas desplegables donde las haya."],
        ["4. No borre filas: para quitar una obra, ponga estado_registro = archivada; para quitar a un responsable, activo = no."],
        [],
        ["¿Qué va en cada columna? Pase el mouse sobre el encabezado: cada columna tiene una nota que lo explica."],
        ["Las pestañas grises (camaras, feriados, responsables y simulacion) son de configuración y casi nunca se tocan."],
        ["Google guarda cada versión de esta hoja (Archivo > Historial de versiones) y LupIA anota cada cambio con su valor anterior."],
        [],
        ["Qué parte de la ficha de la obra usa cada pestaña"],
        ["Pestaña", "Qué muestra en la ficha"],
    ] + [[t, R.ALIMENTA[t]] for t in R.TABLAS]
    for f in filas:
        ws.append(f)
    ws["A1"].font = Font(bold=True, size=16, color=TINTA)
    for celda in ("A5", "A10", "A20"):
        ws[celda].font = Font(bold=True, size=12, color=TINTA)
    for fila in (6, 21):
        for c in ws[fila][:3 if fila == 6 else 2]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor=TINTA)
    for col, ancho in zip("ABC", (28, 52, 80)):
        ws.column_dimensions[col].width = ancho
    for fila in ws.iter_rows(min_row=6, max_row=8):
        for c in fila:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    ws.sheet_view.showGridLines = False


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
        celda.alignment = Alignment(vertical="center")
        ws.column_dimensions[letra].width = ANCHOS.get(col, max(12, len(col) + 4))
        for fila in ws.iter_rows(min_row=2, max_row=max(2, len(df) + 1), min_col=j, max_col=j):
            fila[0].border = Border(bottom=BORDE)
            fila[0].alignment = Alignment(wrap_text=col in LARGOS, vertical="top")
            if col in FORMATOS:
                fila[0].number_format = FORMATOS[col]
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
        elif col == "actualizado_por":
            dv = DataValidation(type="list", formula1=f"responsables!$A$2:$A${FILAS}", allow_blank=True,
                                showErrorMessage=True, error="Elija su nombre de la pestaña responsables.")
        else:
            continue
        dv.add(rango)
        ws.add_data_validation(dv)
    ws.sheet_properties.tabColor = GRIS if tabla in R.CONFIGURACION else TINTA
    ws.row_dimensions[1].height = 24
    ws.freeze_panes = "B2" if tabla in ("obras", "camaras") else "A2"
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
