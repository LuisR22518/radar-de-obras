"""Genera las cámaras simuladas de LupIA a partir de los datos reales del piloto de dIAra.

Cada foto simulada con actividad es una foto real del piloto (de la misma hora del día) con sus
mismos objetos y recuadros, a la que se le aplica el comportamiento del modelo en producción: se
pierde ~15 % de los objetos (sensibilidad de 85,4 %), los recuadros se mueven unos píxeles y cada
detección recibe una probabilidad sobre el umbral de 0,7. Así, las obras son ficticias, pero lo que
"ve" cada cámara viene de una obra real.

Qué obras y cámaras se simulan lo decide el registro (datos/registro/): toda obra con
fuente_datos = simulado y su escenario. Cada obra tiene su propia semilla, de modo que agregar
una obra nueva no cambia los datos de las demás.

Salidas en datos/simulados/ (se regeneran en cada corrida; no se guardan en el repositorio):
  diara/CAM-X/AAAAMMDD.csv  detecciones con el formato de producción de dIAra (run_inference.py)
  inventario_capturas.csv   fotos recibidas por cámara (el "latido" que LupIA propone a dIAra)
                            y, para cada foto con actividad, la foto real del piloto de la que sale
  clima_simulado.csv        lluvia diaria simulada (respaldo si Open-Meteo no responde)

Uso:  python scripts/generar_simulados.py
"""
import shutil
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import config as C  # noqa: E402
from radar import diara, registro  # noqa: E402
from radar.contrato import dias_suspendidos  # noqa: E402

T = pd.Timestamp
DIAS_ACTIVOS_PILOTO = ["2024-03-19", "2024-03-20", "2024-04-02", "2024-04-03"]  # días completos y con obra
FOTOS_POR_HORA = 3600 / C.INTERVALO_SEG

# Cuánto trabaja la cuadrilla en cada escenario
P_DIA = {"normal": 0.93, "paralizada": 0.93, "esporadica": 0.9, "lenta": 0.9, "falla_camara": 0.93, "terminada": 0.9}
INTENSIDAD = {"lenta": 0.75, "esporadica": 0.8}  # proporción de la actividad típica del piloto
# Qué fotos del piloto se parecen más a cada tipo de obra (peso extra a las que tienen esa máquina)
AFINIDAD = {"Camino": "Aplanadora", "Puente": "Tractor", "Acueducto": "Tractor", "Alcantarillado": "Tractor",
            "Edificio educativo": "Mezcladora"}
# Probabilidad diaria de lluvia por región y mes
REGION_PROVINCIA = {"Limón": "caribe", "Guanacaste": "pacifico_norte", "Puntarenas": "pacifico_sur",
                    "Alajuela": "norte", "San José": "central", "Cartago": "central", "Heredia": "central"}
REGION_CANTON = {"Pérez Zeledón": "pacifico_sur", "Upala": "norte"}
P_LLUVIA = {"caribe": [.55, .45, .40, .45, .60, .60, .65, .60, .45, .50, .65, .70],
            "pacifico_norte": [.05, .05, .05, .15, .55, .60, .45, .55, .65, .70, .30, .10],
            "pacifico_sur": [.25, .20, .30, .50, .75, .70, .65, .70, .75, .80, .55, .35],
            "norte": [.45, .35, .30, .40, .60, .65, .65, .65, .60, .60, .55, .55],
            "central": [.10, .05, .10, .30, .60, .55, .45, .55, .65, .70, .40, .15]}


def semilla(obra_id: str) -> np.random.Generator:
    return np.random.default_rng([C.SEMILLA, zlib.crc32(obra_id.encode())])


# --- Lo que se aprende del piloto real --------------------------------------------------------
class Piloto:
    """Fotos reales del piloto agrupadas por hora, listas para recombinarse."""

    def __init__(self):
        det = diara.leer_camara(C.DIARA_REAL / "dIAra-K1", "dIAra-K1").detecciones
        det = det.sort_values(["nombre_imagen", "clase"]).reset_index(drop=True)
        self.objetos = det[["nombre_imagen", "clase", "x1", "y1", "x2", "y2"]]
        fotos = det.groupby("nombre_imagen").agg(hora=("fecha_hora", lambda s: s.iloc[0].hour),
                                                 inicio=("clase", lambda s: s.index[0]),
                                                 n=("clase", "size"),
                                                 clases=("clase", lambda s: set(s)))
        self.fotos = fotos.reset_index()
        # Actividad típica por hora: proporción de fotos con algún objeto en los días completos de obra
        completos = det[det["fecha_hora"].dt.strftime("%Y-%m-%d").isin(DIAS_ACTIVOS_PILOTO)]
        por_hora = completos.groupby(completos["fecha_hora"].dt.hour)["nombre_imagen"].nunique()
        self.actividad_hora = (por_hora / (FOTOS_POR_HORA * len(DIAS_ACTIVOS_PILOTO))).clip(upper=0.97)
        self.solo_personas = self.fotos.index[self.fotos["clases"].map(lambda c: c == {"Persona"})].to_numpy()

        # Arreglos de numpy para recombinar rápido
        self.nombre = self.fotos["nombre_imagen"].to_numpy()
        self.inicio = self.fotos["inicio"].to_numpy()
        self.n = self.fotos["n"].to_numpy()
        self.hora = self.fotos["hora"].to_numpy()
        self.o_clase = self.objetos["clase"].to_numpy()
        self.o_caja = self.objetos[["x1", "y1", "x2", "y2"]].to_numpy(dtype=float)

    def candidatas(self, tipo: str) -> dict:
        """Para cada hora: fotos reales de esa hora (o de la más cercana) y su probabilidad de salir."""
        clave = AFINIDAD.get(tipo)
        w = np.ones(len(self.fotos))
        if clave:
            w[self.fotos["clases"].map(lambda c: clave in c).to_numpy()] = 2.0
        out = {}
        for hora in range(24):
            for delta in range(0, 24):
                cand = np.flatnonzero((self.hora == hora - delta) | (self.hora == hora + delta))
                if len(cand):
                    out[hora] = (cand, w[cand] / w[cand].sum())
                    break
        return out


# --- Escenarios ---------------------------------------------------------------------------------
def jornada(rng, dia, obra, feriado: bool, suspendido: bool) -> float:
    """Fracción de jornada trabajada ese día: 1 = día completo, 0,5 = medio día, 0 = no se trabajó."""
    esc, desde, dow = obra["escenario_simulado"], obra["escenario_desde"], dia.weekday()
    if suspendido or dow == 6:
        return 0.0
    if esc in ("paralizada", "terminada") and pd.notna(desde) and dia >= desde:
        return 0.0
    if esc == "esporadica":
        semana = (dia - T(C.INICIO_MONITOREO)).days // 7
        if semana % 4 != zlib.crc32(obra["obra_id"].encode()) % 4 or dow > 2:
            return 0.0
    if esc == "lenta" and dow not in (0, 1, 3):
        return 0.0
    if feriado:
        return 1.0 if rng.random() < 0.15 else 0.0
    if dow == 5:
        return 0.5 if rng.random() < 0.4 else 0.0
    return 1.0 if rng.random() < P_DIA[esc] else 0.0


def probabilidades(rng, n: int) -> np.ndarray:
    return C.UMBRAL_MODELO + 0.0001 + (0.9999 - C.UMBRAL_MODELO) * rng.beta(6, 1.6, n)


def simular_camara(piloto: Piloto, obra, cam, feriados: set, suspendidos: set, inventario: list):
    rng = semilla(obra["obra_id"])
    candidatas = piloto.candidatas(obra["tipo"])
    intensidad = INTENSIDAD.get(obra["escenario_simulado"], 1.0)
    carpeta = C.DIARA_SIMULADO / cam["camara_id"]
    carpeta.mkdir(parents=True, exist_ok=True)
    fin = min(cam["hasta"], T(C.FECHA_CORTE)) if pd.notna(cam["hasta"]) else T(C.FECHA_CORTE)
    segundos = np.arange(C.HORA_PRIMERA_CAPTURA * 3600, (C.HORA_ULTIMA_CAPTURA + 1) * 3600, C.INTERVALO_SEG)
    vacio = np.empty(0, dtype=int)
    for dia in pd.date_range(cam["desde"], fin, freq="D"):
        if (obra["escenario_simulado"] == "falla_camara" and pd.notna(obra["escenario_desde"])
                and dia >= obra["escenario_desde"]):
            continue  # la cámara no envía nada: en producción no se genera el CSV del día
        jorn = jornada(rng, dia, obra, dia in feriados, dia in suspendidos)
        p_recibir = rng.uniform(0.2, 0.45) if rng.random() < 0.02 else 0.965  # baja energía o señal
        filas = []
        for s in segundos:
            if rng.random() > p_recibir:
                continue
            s_real = int(s + rng.integers(0, 4))
            hora = s_real // 3600
            nombre = f"{dia:%Y%m%d}-{hora:02d}{(s_real % 3600) // 60:02d}{s_real % 60:02d}.jpg"
            fin_laboral = 11 if jorn == 0.5 else C.HORARIO_LABORAL[1]
            laboral = jorn > 0 and C.HORARIO_LABORAL[0] <= hora <= fin_laboral
            origen, quedan = "", vacio
            if laboral and rng.random() < intensidad * piloto.actividad_hora.get(hora, 0.0):
                cand, p = candidatas[hora]
                f = int(rng.choice(cand, p=p))
                origen = piloto.nombre[f]
                idx = np.arange(piloto.inicio[f], piloto.inicio[f] + piloto.n[f])
                quedan = idx[rng.random(len(idx)) < C.SENSIBILIDAD_MODELO]  # el modelo no ve ~15 %
            elif not laboral and rng.random() < (0.15 if jorn > 0 and hora in (5, 17) else 0.02):
                f = int(rng.choice(piloto.solo_personas))  # el guarda, o alguien que llega temprano
                origen = piloto.nombre[f]
                quedan = np.arange(piloto.inicio[f], piloto.inicio[f] + 1)
            inventario.append([cam["camara_id"], nombre, origen])
            if len(quedan):
                caja = piloto.o_caja[quedan] + np.tile(rng.integers(-4, 5, size=(len(quedan), 2)), (1, 2))
                caja[:, [0, 2]] = np.clip(caja[:, [0, 2]], 0, C.ANCHO_IMAGEN)
                caja[:, [1, 3]] = np.clip(caja[:, [1, 3]], 0, C.ALTO_IMAGEN)
                for clase, p_det, (a, b, c, d) in zip(piloto.o_clase[quedan], probabilidades(rng, len(quedan)), caja):
                    filas.append([nombre, clase, f"tensor({p_det:.4f})", f"tensor([{a:.4f}, {b:.4f}, {c:.4f}, {d:.4f}])"])
        pd.DataFrame(filas, columns=["nombre_imagen", "clase", "probabilidad", "recuadro"]).to_csv(
            carpeta / f"{dia:%Y%m%d}.csv", index=False)


def simular_clima(obras, camaras, eventos):
    filas = []
    for oid, obra in obras.iterrows():
        rng = np.random.default_rng([C.SEMILLA, zlib.crc32(oid.encode()), 7])
        region = REGION_CANTON.get(obra["canton"], REGION_PROVINCIA.get(obra["provincia"], "central"))
        suspendidos = dias_suspendidos(oid, eventos)
        for _, cam in camaras[camaras["obra_id"] == oid].iterrows():
            fin = cam["hasta"] if pd.notna(cam["hasta"]) else T(C.FECHA_CORTE)
            for dia in pd.date_range(cam["desde"], fin, freq="D"):
                mm = rng.gamma(0.8, 14) if rng.random() < P_LLUVIA[region][dia.month - 1] else 0.0
                if dia in suspendidos:
                    mm = rng.uniform(35, 80)  # las suspensiones simuladas son por lluvias
                filas.append([oid, dia.date(), round(mm, 1), "simulado"])
    pd.DataFrame(filas, columns=["obra_id", "fecha", "lluvia_mm", "origen"]).to_csv(
        C.SIMULADOS / "clima_simulado.csv", index=False)


def main():
    if C.SIMULADOS.exists():
        shutil.rmtree(C.SIMULADOS)
    C.SIMULADOS.mkdir(parents=True)
    reg = registro.cargar()
    if reg.errores:
        sys.exit("El registro tiene errores; corra scripts/registro.py para verlos.")
    obras, camaras, eventos = reg["obras"], reg["camaras"], reg["eventos_contrato"]
    feriados = set(reg["feriados"]["fecha"])
    piloto = Piloto()
    inventario = []
    simuladas = obras[obras["fuente_datos"] == "simulado"]
    for _, cam in camaras[camaras["obra_id"].isin(simuladas.index)].iterrows():
        obra = simuladas.loc[cam["obra_id"]]
        simular_camara(piloto, obra, cam, feriados, dias_suspendidos(obra["obra_id"], eventos), inventario)
    pd.DataFrame(inventario, columns=["camara_id", "nombre_imagen", "imagen_piloto"]).to_csv(
        C.SIMULADOS / "inventario_capturas.csv", index=False)
    simular_clima(obras, camaras, eventos)
    print(f"{len(simuladas)} obras simuladas a partir de {len(piloto.fotos)} fotos reales del piloto "
          f"({len(inventario):,} fotos generadas, semilla {C.SEMILLA}).")


if __name__ == "__main__":
    main()
