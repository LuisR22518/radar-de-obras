"""Datos de contrato: plazo y monto vigentes, suspensiones y avance previsto.

Los eventos de contrato (prórrogas, cambios de monto, suspensiones, recepción)
vienen de datos/eventos_contrato.csv. Aquí se aplican a una fecha dada.
"""
import pandas as pd


def avance_previsto(inicio, fin, fecha) -> float:
    """Avance previsto (%) con una curva en S: lenta al inicio, rápida en el medio y lenta al final.

    Es una aproximación declarada: si se consigue el cronograma real, se reemplaza esta función.
    """
    inicio, fin, fecha = pd.Timestamp(inicio), pd.Timestamp(fin), pd.Timestamp(fecha)
    if pd.isna(inicio) or pd.isna(fin):
        return float("nan")
    x = (fecha - inicio).days / max((fin - inicio).days, 1)
    x = min(max(x, 0.0), 1.0)
    return round(100 * (3 * x**2 - 2 * x**3), 1)


def _eventos_de(eventos: pd.DataFrame, obra_id: str, tipo: str, hasta=None) -> pd.DataFrame:
    sel = eventos[(eventos["obra_id"] == obra_id) & (eventos["tipo"] == tipo)]
    if hasta is not None:
        sel = sel[sel["fecha"] <= pd.Timestamp(hasta)]
    return sel.sort_values("fecha")


def fin_vigente(obra, eventos: pd.DataFrame, fecha) -> pd.Timestamp:
    """Fecha de fin del contrato a una fecha dada, sumando las prórrogas aprobadas hasta ese día."""
    prorrogas = _eventos_de(eventos, obra["obra_id"], "prorroga", hasta=fecha)
    return obra["fecha_fin_original"] + pd.Timedelta(days=int(prorrogas["dias_prorroga"].fillna(0).sum()))


def monto_vigente(obra, eventos: pd.DataFrame, fecha) -> float:
    """Monto del contrato a una fecha dada: el último monto modificado, o el original."""
    cambios = _eventos_de(eventos, obra["obra_id"], "modificacion_monto", hasta=fecha)
    if len(cambios):
        return float(cambios["monto_nuevo_crc"].iloc[-1])
    return float(obra["monto_original_crc"]) if pd.notna(obra["monto_original_crc"]) else float("nan")


def fecha_recepcion(obra, eventos: pd.DataFrame):
    """Fecha de recepción provisional, o None si la obra sigue en ejecución."""
    rec = _eventos_de(eventos, obra["obra_id"], "recepcion_provisional")
    return rec["fecha"].iloc[0] if len(rec) else None


def dias_suspendidos(obra_id: str, eventos: pd.DataFrame) -> set:
    """Días cubiertos por una orden de suspensión de la administración."""
    dias = set()
    for _, ev in _eventos_de(eventos, obra_id, "suspension").iterrows():
        dias.update(pd.date_range(ev["suspension_desde"], ev["suspension_hasta"], freq="D"))
    return dias
