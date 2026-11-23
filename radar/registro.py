"""Registro de obras: la base de datos propia de LupIA.

La mantienen la gerencia y los encargados de actualización de obra (no el auditor) en una hoja de
Google con una pestaña por tabla; GitHub la descarga cada 15 minutos a datos/registro/ (ver scripts/registro.py). Aquí se define qué columnas
lleva cada tabla, cómo se leen y qué revisiones de calidad se le aplican.

Dos niveles de problema:
  - error: el dato no se puede usar (por ejemplo, una fecha que no es fecha). Si la hoja trae errores,
    LupIA conserva la última versión buena del registro y lo avisa en la página «Mantenimiento del registro».
  - aviso: el dato se puede usar pero merece revisión (por ejemplo, un avance que retrocede).
"""
from dataclasses import dataclass, field

import re

import pandas as pd

from . import config as C

# Columnas de cada tabla: (nombre, tipo, obligatoria). Tipos: texto, numero, fecha, opcion:<a|b|c>
TABLAS = {
    "obras": [
        ("obra_id", "texto", True), ("nombre", "texto", True), ("tipo", "texto", True),
        ("necesidad_publica", "texto", False), ("provincia", "texto", True), ("canton", "texto", True), ("lat", "numero", True), ("lon", "numero", True),
        ("institucion_ejecutora", "texto", True), ("contratista", "texto", False),
        ("monto_original_crc", "numero", False), ("fecha_inicio", "fecha", False), ("fecha_fin_original", "fecha", False),
        ("fuente_datos", "opcion:dIAra real|simulado", True),
        ("estado_registro", "opcion:activa|archivada", True), ("nota", "texto", False), ("actualizado_por", "texto", False),
    ],
    "hitos": [
        ("obra_id", "texto", True), ("hito", "texto", True), ("fecha_prevista", "fecha", True),
        ("fecha_cumplido", "fecha", False), ("documento", "texto", False), ("actualizado_por", "texto", False),
    ],
    "avance_reportado": [
        ("obra_id", "texto", True), ("fecha", "fecha", True), ("avance_reportado_pct", "numero", True),
        ("documento", "texto", False), ("actualizado_por", "texto", False),
    ],
    "eventos_contrato": [
        ("obra_id", "texto", True), ("fecha", "fecha", True),
        ("tipo", "opcion:modificacion_monto|prorroga|suspension|recepcion_provisional", True),
        ("detalle", "texto", True), ("dias_prorroga", "numero", False), ("monto_nuevo_crc", "numero", False),
        ("suspension_desde", "fecha", False), ("suspension_hasta", "fecha", False), ("documento", "texto", False), ("actualizado_por", "texto", False),
    ],
    "pagos": [
        ("obra_id", "texto", True), ("fecha", "fecha", True), ("pagado_acumulado_crc", "numero", True),
        ("documento", "texto", False), ("actualizado_por", "texto", False),
    ],
    "reportes_ciudadanos": [
        ("obra_id", "texto", True), ("fecha", "fecha", True), ("tipo", "texto", True), ("descripcion", "texto", True),
        ("con_foto", "opcion:si|no", False), ("canal", "texto", False), ("actualizado_por", "texto", False),
    ],
    # Configuración: se tocan poco
    "camaras": [
        ("camara_id", "texto", True), ("obra_id", "texto", True), ("desde", "fecha", True), ("hasta", "fecha", False),
        ("inventario_fotos", "opcion:si|no", True), ("nota", "texto", False), ("actualizado_por", "texto", False),
    ],
    "feriados": [("fecha", "fecha", True), ("nombre", "texto", True), ("fuente", "texto", False),
                 ("actualizado_por", "texto", False)],
    "responsables": [("nombre", "texto", True), ("cargo", "texto", True),
                     ("rol", "opcion:gerencia|encargado_actualizacion", True), ("activo", "opcion:si|no", True), ("correo", "texto", False)],
    # Solo para las obras de prueba: cómo se fabrican sus datos. No describe la obra.
    "simulacion": [("obra_id", "texto", True), ("escenario", "opcion:" + "|".join(C.ESCENARIOS), True),
                   ("desde", "fecha", False), ("actualizado_por", "texto", False)],
}
# Qué parte de la ficha de la obra usa cada pestaña (lo muestra la pestaña LEEME de la hoja)
ALIMENTA = {
    "obras": "Qué obra es, dónde está y para qué sirve",
    "hitos": "Etapas de la obra: cumplidas, pendientes y atrasadas",
    "avance_reportado": "Lo que reporta la ejecutora (avance en %)",
    "eventos_contrato": "Costo, fecha de entrega y cambios al contrato",
    "pagos": "Detalle para fiscalización: cuánto se ha pagado",
    "reportes_ciudadanos": "Lo que reporta la gente",
    "camaras": "Las 8 semanas de actividad (qué cámara es de cada obra)",
    "feriados": "Que un feriado no cuente como día sin trabajo",
    "responsables": "Quién puede editar esta hoja",
    "simulacion": "Cómo se fabrican los datos de las obras de prueba",
}
# Pestañas de configuración (se tocan poco): van al final de la hoja y con otro color
CONFIGURACION = {"camaras", "feriados", "responsables", "simulacion"}
# Quién puede cambiar cada tabla: la gerencia (cargos sobre el auditor) mantiene la estructura del registro;
# los encargados de actualización de obra cargan el seguimiento. El auditor solo lee, desde LupIA.
PERMISOS = {"obras": {"gerencia"}, "camaras": {"gerencia"}, "feriados": {"gerencia"}, "responsables": {"gerencia"},
            "simulacion": {"gerencia"}, "hitos": {"gerencia", "encargado_actualizacion"},
            "eventos_contrato": {"gerencia", "encargado_actualizacion"},
            "avance_reportado": {"gerencia", "encargado_actualizacion"},
            "pagos": {"gerencia", "encargado_actualizacion"},
            "reportes_ciudadanos": {"gerencia", "encargado_actualizacion"}}
ROLES = {"gerencia": "Gerencia", "encargado_actualizacion": "Encargado de actualización de obra"}
CLAVES = {"obras": ["obra_id"], "camaras": ["camara_id", "desde"], "eventos_contrato": ["obra_id", "fecha", "tipo"],
          "avance_reportado": ["obra_id", "fecha"], "pagos": ["obra_id", "fecha"],
          "reportes_ciudadanos": ["obra_id", "fecha", "descripcion"], "feriados": ["fecha"], "responsables": ["nombre"],
          "hitos": ["obra_id", "hito"], "simulacion": ["obra_id"]}
NOMBRES = {"obras": "Obras", "camaras": "Cámaras", "eventos_contrato": "Cambios de contrato",
           "avance_reportado": "Avance reportado", "pagos": "Pagos", "reportes_ciudadanos": "Reportes ciudadanos",
           "feriados": "Feriados", "responsables": "Responsables", "hitos": "Hitos", "simulacion": "Simulación"}
# Qué poner en cada columna (lo usan la pestaña LEEME de la hoja y la documentación)
DESCRIPCIONES = {
    "obras": {
        "obra_id": "Código corto y único de la obra (por ejemplo, A o P). No se cambia una vez creado.",
        "nombre": "Nombre de la obra como lo verá el auditor.",
        "tipo": "Puente, Camino, Acueducto, Alcantarillado, Edificio educativo, Edificio de salud, etc.",
        "necesidad_publica": "Para qué sirve la obra, en una frase que entienda cualquier vecino (por ejemplo, «Aulas nuevas para 300 estudiantes»).",
        "provincia": "Provincia donde está la obra.", "canton": "Cantón donde está la obra.",
        "lat": "Latitud en grados decimales (por ejemplo, 9.3745).", "lon": "Longitud en grados decimales (por ejemplo, -83.7037).",
        "institucion_ejecutora": "Institución que contrata y supervisa la obra.",
        "contratista": "Empresa contratista. Vacío si no se conoce.",
        "monto_original_crc": "Monto original del contrato en colones, sin separadores. Vacío si no se conoce.",
        "fecha_inicio": "Fecha de la orden de inicio. Vacío si no se conoce.",
        "fecha_fin_original": "Fecha de fin según el contrato original. Las prórrogas van en cambios de contrato.",
        "fuente_datos": "dIAra real, si la cámara es real; simulado, si es una obra de prueba (sus datos se fabrican según la pestaña simulacion).",
        "estado_registro": "activa: aparece en LupIA. archivada: se conserva pero no aparece.",
        "nota": "Comentario libre.",
    },
    "camaras": {
        "camara_id": "Código de la cámara (por ejemplo, CAM-A). Debe coincidir con su carpeta de datos.",
        "obra_id": "Obra donde está instalada (código de la pestaña obras).",
        "desde": "Fecha de instalación en esta obra.", "hasta": "Fecha de retiro. Vacío si sigue instalada.",
        "inventario_fotos": "si, si la cámara informa cuántas fotos tomó cada día; no, si solo hay detecciones.",
        "nota": "Comentario libre.",
    },
    "hitos": {
        "obra_id": "Código de la obra.", "hito": "Etapa de la obra, en pocas palabras (por ejemplo, «Cimientos» o «Techo»).",
        "fecha_prevista": "Cuándo debía cumplirse, según el cronograma.",
        "fecha_cumplido": "Cuándo se cumplió. Vacío si todavía no se cumple.",
        "documento": "Cronograma o informe que lo respalda.",
    },
    "eventos_contrato": {
        "obra_id": "Código de la obra.", "fecha": "Fecha de aprobación del cambio.",
        "tipo": "modificacion_monto, prorroga, suspension o recepcion_provisional.",
        "detalle": "Descripción corta del cambio.", "dias_prorroga": "Solo prórrogas: días que se suman al plazo.",
        "monto_nuevo_crc": "Solo modificaciones de monto: el nuevo monto total.",
        "suspension_desde": "Solo suspensiones: primer día.", "suspension_hasta": "Solo suspensiones: último día.",
        "documento": "Número de adenda, oficio o resolución que lo respalda.",
    },
    "avance_reportado": {
        "obra_id": "Código de la obra.", "fecha": "Fecha del informe.",
        "avance_reportado_pct": "Avance físico que reporta la ejecutora, de 0 a 100.",
        "documento": "Informe que lo respalda.",
    },
    "pagos": {
        "obra_id": "Código de la obra.", "fecha": "Fecha de corte del pago.",
        "pagado_acumulado_crc": "Total pagado hasta esa fecha, en colones.", "documento": "Orden de pago que lo respalda.",
    },
    "reportes_ciudadanos": {
        "obra_id": "Código de la obra.", "fecha": "Fecha del reporte.", "tipo": "obra detenida, seguridad, calidad u otro.",
        "descripcion": "Lo que reporta la persona, en pocas palabras.", "con_foto": "si o no.",
        "canal": "Por dónde llegó (denuncia CGR, inspector ciudadano, etc.).",
    },
    "feriados": {"fecha": "Fecha del feriado (la de su disfrute, si se trasladó).", "nombre": "Nombre del feriado.",
                 "fuente": "De dónde sale (por ejemplo, comunicado del MTSS)."},
    "responsables": {"nombre": "Nombre de la persona que mantiene el registro.", "cargo": "Su cargo.",
                     "rol": "gerencia: crea y cambia obras, cámaras y feriados. encargado_actualizacion: carga avance, pagos, cambios de contrato y reportes.",
                     "activo": "si, mientras la persona tenga ese rol; no, cuando deje de tenerlo (no se borra, para conservar el historial).",
                     "correo": "Correo donde recibe los reportes de datos que hacen los auditores; de preferencia un buzón institucional. Vacío si no los recibe."},
    "simulacion": {"obra_id": "Código de una obra con fuente_datos = simulado.",
                   "escenario": "Cómo se comporta su cámara simulada: " + ", ".join(C.ESCENARIOS) + ".",
                   "desde": "Solo para paralizada, falla_camara y terminada: desde qué fecha."},
}
for _tabla in DESCRIPCIONES:
    if _tabla != "responsables":
        DESCRIPCIONES[_tabla]["actualizado_por"] = "Quién hizo el último cambio en esta fila (de la pestaña responsables)."
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


def _texto(v, tipo: str) -> str:
    """Valor de una celda de la hoja como texto canónico: fechas AAAA-MM-DD y números sin separadores."""
    if v is None or (isinstance(v, float) and pd.isna(v)) or (not isinstance(v, str) and pd.isna(v)):
        return ""
    if tipo == "fecha" and hasattr(v, "strftime"):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, bool):
        return "si" if v else "no"
    if isinstance(v, (int, float)):
        return str(int(v)) if float(v).is_integer() else repr(float(v))
    texto = str(v).strip()
    if tipo == "fecha" and len(texto) > 10 and texto[4] == "-":
        texto = texto[:10]  # "2026-08-31 00:00:00" -> "2026-08-31"
    if tipo == "numero":
        try:
            n = float(texto)
            return str(int(n)) if n.is_integer() else repr(n)
        except ValueError:
            pass  # se deja como está: la validación lo marcará como error
    return texto


def canonico(crudo: dict) -> dict:
    """Pasa cada valor a su forma canónica, para comparar versiones sin diferencias falsas."""
    out = {}
    for tabla, cols in TABLAS.items():
        df = crudo[tabla].copy()
        for col, tipo, _ in cols:
            if col in df.columns:
                df[col] = [_texto(v, tipo) for v in df[col]]
        out[tabla] = df
    return out


def guardar(crudo: dict, carpeta=C.REGISTRO):
    for tabla, cols in TABLAS.items():
        df = crudo[tabla]
        df[[c for c, _, _ in cols if c in df.columns]].to_csv(carpeta / f"{tabla}.csv", index=False)


def leer_hoja(archivo_xlsx) -> dict:
    """Lee la hoja de Google descargada como .xlsx y devuelve cada tabla como texto canónico.

    Se usa .xlsx y no CSV porque el CSV de Google escribe números y fechas según el idioma de la hoja
    (por ejemplo, 67,7 en vez de 67.7); el .xlsx trae los valores tal cual.
    """
    libro = pd.read_excel(archivo_xlsx, sheet_name=None, dtype=object)
    crudo = {}
    for tabla, cols in TABLAS.items():
        if tabla not in libro:
            crudo[tabla] = pd.DataFrame(columns=[c for c, _, _ in cols])
            continue
        df = libro[tabla]
        df.columns = [str(c).strip() for c in df.columns]
        # Una fila cuenta si tiene algún dato en las columnas del registro. Las columnas calculadas
        # de la hoja (por ejemplo, el estado de los hitos) se ignoran y no crean filas vacías.
        propias = [c for c, _, _ in cols if c in df.columns]
        df = df.replace(r"^\s*$", pd.NA, regex=True)
        df = df.dropna(how="all", subset=propias or None)
        out = pd.DataFrame(index=range(len(df)))
        tipos = {c: tipo for c, tipo, _ in cols}
        for col in df.columns:
            if col.startswith("Unnamed"):
                continue
            out[col] = [_texto(v, tipos.get(col, "texto")) for v in df[col]]
        crudo[tabla] = out
    return crudo


def leer_crudo(carpeta=C.REGISTRO) -> dict:
    """Lee las tablas como texto, tal como están en la hoja (sin convertir tipos)."""
    return {t: pd.read_csv(carpeta / f"{t}.csv", dtype=str, keep_default_na=False) for t in TABLAS}


def _convertir(df: pd.DataFrame, tabla: str, problemas: list) -> pd.DataFrame:
    out = df.copy()
    for col, tipo, obligatoria in TABLAS[tabla]:
        if col not in out.columns:
            if obligatoria:
                problemas.append(Problema("error", tabla, 0, f"Falta la columna «{col}»."))
            else:
                problemas.append(Problema("aviso", tabla, 0, f"Falta la columna «{col}». Agréguela en la fila 1 de la pestaña; "
                                          "mientras tanto se toma como vacía."))
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
        if o["fuente_datos"] == "simulado" and o["obra_id"] not in set(t["simulacion"]["obra_id"]):
            problemas.append(Problema("error", "obras", f, f"La obra simulada {o['obra_id']} necesita su fila en la pestaña simulacion."))
        if o["estado_registro"] == "activa" and not o["necesidad_publica"]:
            problemas.append(Problema("aviso", "obras", f, f"Obra {o['obra_id']}: falta «necesidad_publica» (para qué sirve la obra)."))
        faltan = [c for c in ("monto_original_crc", "fecha_inicio", "fecha_fin_original", "contratista")
                  if pd.isna(o[c]) or o[c] == ""]
        if faltan and o["estado_registro"] == "activa":
            legibles = {"monto_original_crc": "monto original", "fecha_inicio": "fecha de inicio",
                        "fecha_fin_original": "fecha de fin", "contratista": "contratista"}
            lista = [legibles[c] for c in faltan]
            texto = lista[0] if len(lista) == 1 else ", ".join(lista[:-1]) + " y " + lista[-1]
            problemas.append(Problema("aviso", "obras", f, f"Obra {o['obra_id']}: faltan datos del contrato ({texto}). "
                                      "Sin ellos no se calculan las señales del contrato."))
        if o["estado_registro"] == "activa" and o["obra_id"] not in set(camaras["obra_id"]):
            problemas.append(Problema("aviso", "obras", f, f"Obra {o['obra_id']}: no tiene cámara asignada."))
    sim = t["simulacion"]
    reales = set(obras.loc[obras["fuente_datos"] != "simulado", "obra_id"])
    for i, s in sim.iterrows():
        if s["obra_id"] in reales:
            problemas.append(Problema("error", "simulacion", i + 2, f"La obra {s['obra_id']} no es simulada: quite esta fila."))
        if s["escenario"] in ("paralizada", "falla_camara", "terminada") and pd.isna(s["desde"]):
            problemas.append(Problema("error", "simulacion", i + 2, f"El escenario «{s['escenario']}» necesita «desde»."))
    hoy = pd.Timestamp.now(tz="America/Costa_Rica").tz_localize(None).normalize()
    for i, h in t["hitos"].iterrows():
        if pd.notna(h["fecha_cumplido"]) and h["fecha_cumplido"] > hoy:
            problemas.append(Problema("aviso", "hitos", i + 2, "«fecha_cumplido» está en el futuro."))
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
    resp = t["responsables"]
    for i, correo in resp["correo"].items():
        if correo and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(correo)):
            problemas.append(Problema("aviso", "responsables", i + 2, f"«{correo}» no parece un correo válido."))
    rol = dict(zip(resp["nombre"], resp["rol"]))
    activos = set(resp.loc[resp["activo"] == "si", "nombre"])
    for tabla in TABLAS:
        if tabla == "responsables" or "actualizado_por" not in t[tabla].columns:
            continue
        for i, quien in t[tabla]["actualizado_por"].items():
            if not quien:
                problemas.append(Problema("aviso", tabla, i + 2, "Falta «actualizado_por»: no se sabe quién hizo el cambio."))
            elif quien not in rol:
                problemas.append(Problema("error", tabla, i + 2, f"«{quien}» no está en la pestaña responsables."))
            elif rol[quien] not in PERMISOS[tabla]:
                problemas.append(Problema("aviso", tabla, i + 2,
                                          f"{quien} ({ROLES[rol[quien]].lower()}) cambió una tabla que corresponde a la gerencia."))
            elif quien not in activos:
                problemas.append(Problema("aviso", tabla, i + 2, f"{quien} ya no está activo como responsable."))
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
    # El cálculo sigue usando escenario_simulado y escenario_desde por obra: se traen de la pestaña simulacion
    sim = reg["simulacion"].rename(columns={"escenario": "escenario_simulado", "desde": "escenario_desde"})
    obras = obras.merge(sim[["obra_id", "escenario_simulado", "escenario_desde"]], on="obra_id", how="left")
    obras["escenario_simulado"] = obras["escenario_simulado"].fillna("")
    reg.tablas["obras"] = obras[obras["estado_registro"] == "activa"].set_index("obra_id", drop=False)
    return reg
