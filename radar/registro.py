"""Registro de obras: la base de datos propia de LupIA.

La mantiene el gestor de datos (no el auditor) en una hoja de Google con una pestaña por tabla;
GitHub la descarga cada hora a datos/registro/ (ver scripts/registro.py). Aquí se define qué columnas
lleva cada tabla, cómo se leen y qué revisiones de calidad se le aplican.

Dos niveles de problema:
  - error: el dato no se puede usar (por ejemplo, una fecha que no es fecha). Si la hoja trae errores,
    LupIA conserva la última versión buena del registro y lo avisa en la página «Datos».
  - aviso: el dato se puede usar pero merece revisión (por ejemplo, un avance que retrocede).
"""
from dataclasses import dataclass, field

import pandas as pd

from . import config as C

# Columnas de cada tabla: (nombre, tipo, obligatoria). Tipos: texto, numero, fecha, opcion:<a|b|c>
TABLAS = {
    "obras": [
        ("obra_id", "texto", True), ("nombre", "texto", True), ("tipo", "texto", True),
        ("provincia", "texto", True), ("canton", "texto", True), ("lat", "numero", True), ("lon", "numero", True),
        ("institucion_ejecutora", "texto", True), ("contratista", "texto", False),
        ("monto_original_crc", "numero", False), ("fecha_inicio", "fecha", False), ("fecha_fin_original", "fecha", False),
        ("fuente_datos", "opcion:dIAra real|simulado", True),
        ("escenario_simulado", "opcion:|" + "|".join(C.ESCENARIOS), False), ("escenario_desde", "fecha", False),
        ("estado_registro", "opcion:activa|archivada", True), ("nota", "texto", False),
    ],
    "camaras": [
        ("camara_id", "texto", True), ("obra_id", "texto", True), ("desde", "fecha", True), ("hasta", "fecha", False),
        ("inventario_fotos", "opcion:si|no", True), ("nota", "texto", False),
    ],
    "eventos_contrato": [
        ("obra_id", "texto", True), ("fecha", "fecha", True),
        ("tipo", "opcion:modificacion_monto|prorroga|suspension|recepcion_provisional", True),
        ("detalle", "texto", True), ("dias_prorroga", "numero", False), ("monto_nuevo_crc", "numero", False),
        ("suspension_desde", "fecha", False), ("suspension_hasta", "fecha", False), ("documento", "texto", False),
    ],
    "avance_reportado": [
        ("obra_id", "texto", True), ("fecha", "fecha", True), ("avance_reportado_pct", "numero", True),
        ("documento", "texto", False),
    ],
    "pagos": [
        ("obra_id", "texto", True), ("fecha", "fecha", True), ("pagado_acumulado_crc", "numero", True),
        ("documento", "texto", False),
    ],
    "reportes_ciudadanos": [
        ("obra_id", "texto", True), ("fecha", "fecha", True), ("tipo", "texto", True), ("descripcion", "texto", True),
        ("con_foto", "opcion:si|no", False), ("canal", "texto", False),
    ],
    "feriados": [("fecha", "fecha", True), ("nombre", "texto", True), ("fuente", "texto", False)],
}
CLAVES = {"obras": ["obra_id"], "camaras": ["camara_id", "desde"], "eventos_contrato": ["obra_id", "fecha", "tipo"],
          "avance_reportado": ["obra_id", "fecha"], "pagos": ["obra_id", "fecha"],
          "reportes_ciudadanos": ["obra_id", "fecha", "descripcion"], "feriados": ["fecha"]}
NOMBRES = {"obras": "Obras", "camaras": "Cámaras", "eventos_contrato": "Cambios de contrato",
           "avance_reportado": "Avance reportado", "pagos": "Pagos", "reportes_ciudadanos": "Reportes ciudadanos",
           "feriados": "Feriados"}
# Rectángulo que contiene a Costa Rica (con un margen): un punto fuera es casi seguro un error de digitación
LAT_CR, LON_CR = (8.0, 11.3), (-86.0, -82.5)


@dataclass
class Problema:
    nivel: str      # "error" o "aviso"
    tabla: str
    fila: int       # fila en la hoja (la 1 es el encabezado), o 0 si es de toda la tabla
    mensaje: str


@dataclass
class Registro:
    tablas: dict
    problemas: list = field(default_factory=list)

    def __getitem__(self, nombre):
        return self.tablas[nombre]

    @property
    def errores(self):
        return [p for p in self.problemas if p.nivel == "error"]


def leer_crudo(carpeta=C.REGISTRO) -> dict:
    """Lee las tablas como texto, tal como están en la hoja (sin convertir tipos)."""
    return {t: pd.read_csv(carpeta / f"{t}.csv", dtype=str, keep_default_na=False) for t in TABLAS}


def _convertir(df: pd.DataFrame, tabla: str, problemas: list) -> pd.DataFrame:
    out = df.copy()
    for col, tipo, obligatoria in TABLAS[tabla]:
        if col not in out.columns:
            problemas.append(Problema("error", tabla, 0, f"Falta la columna «{col}»."))
            out[col] = ""
        valores = out[col].astype(str).str.strip()
        vacios = valores == ""
        for i in out.index[vacios & obligatoria]:
            problemas.append(Problema("error", tabla, i + 2, f"«{col}» es obligatorio y está vacío."))
        if tipo == "numero":
            conv = pd.to_numeric(valores.str.replace(",", "", regex=False), errors="coerce")
            for i in out.index[conv.isna() & ~vacios]:
                problemas.append(Problema("error", tabla, i + 2, f"«{col}» debe ser un número y dice «{valores[i]}»."))
            out[col] = conv
        elif tipo == "fecha":
            conv = pd.to_datetime(valores, format="%Y-%m-%d", errors="coerce")
            for i in out.index[conv.isna() & ~vacios]:
                problemas.append(Problema("error", tabla, i + 2,
                                          f"«{col}» debe ser una fecha AAAA-MM-DD y dice «{valores[i]}»."))
            out[col] = conv
        elif tipo.startswith("opcion:"):
            validas = tipo.split(":", 1)[1].split("|")
            for i in out.index[~valores.isin(validas) & ~vacios]:
                problemas.append(Problema("error", tabla, i + 2,
                                          f"«{col}» no admite «{valores[i]}»; use: {', '.join(v for v in validas if v)}."))
            out[col] = valores
        else:
            out[col] = valores
    return out[[c for c, _, _ in TABLAS[tabla]]]


def _revisar(t: dict, problemas: list):
    obras, camaras = t["obras"], t["camaras"]
    ids = set(obras["obra_id"])
    for tabla in TABLAS:
        claves = CLAVES[tabla]
        dup = t[tabla][t[tabla].duplicated(claves, keep="first")]
        for i in dup.index:
            problemas.append(Problema("error", tabla, i + 2, f"Fila repetida ({', '.join(claves)})."))
        if "obra_id" in t[tabla].columns and tabla != "obras":
            for i in t[tabla].index[~t[tabla]["obra_id"].isin(ids)]:
                problemas.append(Problema("error", tabla, i + 2,
                                          f"La obra «{t[tabla].loc[i, 'obra_id']}» no existe en la tabla Obras."))
    for i, o in obras.iterrows():
        f = i + 2
        if pd.notna(o["lat"]) and not (LAT_CR[0] <= o["lat"] <= LAT_CR[1] and LON_CR[0] <= o["lon"] <= LON_CR[1]):
            problemas.append(Problema("error", "obras", f, "La ubicación (lat, lon) cae fuera de Costa Rica."))
        if pd.notna(o["fecha_inicio"]) and pd.notna(o["fecha_fin_original"]) and o["fecha_fin_original"] <= o["fecha_inicio"]:
            problemas.append(Problema("error", "obras", f, "La fecha de fin es anterior a la de inicio."))
        if o["fuente_datos"] == "simulado" and not o["escenario_simulado"]:
            problemas.append(Problema("error", "obras", f, "Una obra simulada necesita «escenario_simulado»."))
        if o["escenario_simulado"] in ("paralizada", "falla_camara", "terminada") and pd.isna(o["escenario_desde"]):
            problemas.append(Problema("error", "obras", f,
                                      f"El escenario «{o['escenario_simulado']}» necesita «escenario_desde»."))
        faltan = [c for c in ("monto_original_crc", "fecha_inicio", "fecha_fin_original", "contratista")
                  if pd.isna(o[c]) or o[c] == ""]
        if faltan and o["estado_registro"] == "activa":
            problemas.append(Problema("aviso", "obras", f, f"Obra {o['obra_id']}: sin {', '.join(faltan)}. "
                                      "Las señales que dependen del contrato no se calculan."))
        if o["estado_registro"] == "activa" and o["obra_id"] not in set(camaras["obra_id"]):
            problemas.append(Problema("aviso", "obras", f, f"Obra {o['obra_id']}: no tiene cámara asignada."))
    # Una cámara no puede estar en dos obras a la vez
    for cam, g in camaras.groupby("camara_id"):
        g = g.sort_values("desde")
        fin_anterior = None
        for i, c in g.iterrows():
            if fin_anterior is not None and (pd.isna(fin_anterior) or c["desde"] <= fin_anterior):
                problemas.append(Problema("error", "camaras", i + 2,
                                          f"La cámara {cam} queda asignada a dos obras al mismo tiempo."))
            fin_anterior = c["hasta"]
        if pd.notna(c["hasta"]) and c["hasta"] < c["desde"]:
            problemas.append(Problema("error", "camaras", i + 2, "«hasta» es anterior a «desde»."))
    av = t["avance_reportado"]
    for i in av.index[(av["avance_reportado_pct"] < 0) | (av["avance_reportado_pct"] > 100)]:
        problemas.append(Problema("error", "avance_reportado", i + 2, "El avance debe estar entre 0 y 100."))
    for oid, g in av.sort_values("fecha").groupby("obra_id"):
        baja = g["avance_reportado_pct"].diff() < 0
        for i in g.index[baja]:
            problemas.append(Problema("aviso", "avance_reportado", i + 2,
                                      f"Obra {oid}: el avance reportado baja respecto al informe anterior."))
    ev = t["eventos_contrato"]
    for i, e in ev.iterrows():
        if e["tipo"] == "prorroga" and pd.isna(e["dias_prorroga"]):
            problemas.append(Problema("error", "eventos_contrato", i + 2, "Una prórroga necesita «dias_prorroga»."))
        if e["tipo"] == "modificacion_monto" and pd.isna(e["monto_nuevo_crc"]):
            problemas.append(Problema("error", "eventos_contrato", i + 2,
                                      "Una modificación de monto necesita «monto_nuevo_crc»."))
        if e["tipo"] == "suspension" and (pd.isna(e["suspension_desde"]) or pd.isna(e["suspension_hasta"])):
            problemas.append(Problema("error", "eventos_contrato", i + 2,
                                      "Una suspensión necesita «suspension_desde» y «suspension_hasta»."))


def validar(crudo: dict) -> Registro:
    problemas = []
    tablas = {t: _convertir(df, t, problemas) for t, df in crudo.items()}
    if not any(p.nivel == "error" and p.fila == 0 for p in problemas):
        _revisar(tablas, problemas)
    return Registro(tablas, problemas)


def cargar() -> Registro:
    """Registro listo para el cálculo: solo obras activas y tipos convertidos."""
    reg = validar(leer_crudo())
    obras = reg["obras"]
    reg.tablas["obras"] = obras[obras["estado_registro"] == "activa"].set_index("obra_id", drop=False)
    return reg
