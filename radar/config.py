"""Parámetros de LupIA.

Todo lo que cambia el resultado está aquí, en un solo lugar. Los umbrales son
supuestos del equipo (no de la CGR) y se declaran en la metodología del informe.
Si cambias un valor, vuelve a correr `python scripts/construir.py`.
"""
from datetime import date
from pathlib import Path

# --- Rutas -----------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
DIARA_REAL = DATOS / "diara"          # capa 1: lo que entrega dIAra, tal cual (una carpeta por cámara)
REGISTRO = DATOS / "registro"         # capa 3: base de datos propia (gerencia y encargados de actualización)
SIMULADOS = DATOS / "simulados"       # capa 2: generado a partir del piloto real (se regenera en cada corrida)
DIARA_SIMULADO = SIMULADOS / "diara"  # mismo formato que producción: una carpeta por cámara, un CSV por día
SALIDAS = RAIZ / "salidas"

# --- Período de monitoreo ----------------------------------------------------
# Cada cámara tiene su propio período en datos/registro/camaras.csv. FECHA_CORTE es "hoy" para
# la cartera simulada; INICIO_MONITOREO es el inicio de la ventana de análisis (12 semanas).
INICIO_MONITOREO = date(2026, 8, 31)  # lunes
FECHA_CORTE = date(2026, 11, 20)      # viernes: último día con datos

# --- Cámara (firmware ESP32CAM_Timer_CGR_Day.ino y fotos del piloto) ---------------
HORA_PRIMERA_CAPTURA = 5    # el firmware descarta horas antes de las 5:00 ...
HORA_ULTIMA_CAPTURA = 17    # ... y desde las 18:00
INTERVALO_SEG = 80          # el temporizador TPL5110 despierta la cámara cada ~80 s (fotos del piloto)
ANCHO_IMAGEN, ALTO_IMAGEN = 1280, 1024

# --- Modelo de dIAra (run_inference.py del repositorio) -------------------------
CLASES = ["Vagoneta", "Persona", "Tractor", "Cargador", "Mezcladora", "Aplanadora"]
# Las etiquetas del piloto usan los nombres en inglés; run_inference.py los traduce así:
CLASES_ETIQUETADO = {"dump_truck": "Vagoneta", "person": "Persona", "excavator": "Tractor",
                     "loader": "Cargador", "mixer_truck": "Mezcladora", "steamroller": "Aplanadora"}
SENSIBILIDAD_MODELO = 0.854  # el modelo encuentra ~85 de cada 100 objetos (resultados del piloto)
MAQUINARIA = [c for c in CLASES if c != "Persona"]
UMBRAL_MODELO = 0.7         # el modelo solo guarda detecciones con probabilidad > 0,7

# --- Reglas del estado diario (supuestos del equipo) ----------------------------
HORARIO_LABORAL = (6, 16)   # de 6:00 a 16:59
UMBRAL_COBERTURA = 0.5      # menos del 50 % de las capturas esperadas -> "sin datos"
UMBRAL_ACTIVIDAD = 0.15     # 15 % o más de las imágenes laborales con alguna detección -> "actividad"
DIAS_ACTIVOS_SEMANA = 2     # una semana es activa si tiene al menos 2 días con actividad
LLUVIA_FUERTE_MM = 20       # lluvia diaria que puede explicar un día sin actividad

# --- Señales y puntaje de atención --------------------------------------------------
DIAS_INACTIVIDAD_TOPE = 10  # 10 días hábiles seguidos sin actividad = señal completa
ATRASO_TOPE_PTS = 20        # 20 puntos de atraso frente al cronograma vigente = señal completa
AUMENTO_TOPE = 0.20         # 20 % de aumento de monto = señal completa
VALOR_PRORROGA = 0.5        # una prórroga reciente vale media señal
VENTANA_PRORROGA_DIAS = 90
REPORTES_TOPE = 3           # 3 reportes ciudadanos en la ventana = señal completa
VENTANA_REPORTES_DIAS = 30

PESOS = {  # pesos iniciales propuestos; suman 100 y el auditor puede moverlos
    "inactividad": 30,
    "atraso": 20,
    "brecha": 20,
    "contrato": 15,
    "ciudadania": 15,
}
UMBRALES_ALERTA = {  # desde qué valor (0 a 1) una señal se considera alerta
    "inactividad": 0.5,   # 5 días hábiles seguidos
    "atraso": 0.5,        # 10 puntos de atraso
    "brecha": 0.4,
    "contrato": 0.5,      # 10 % de aumento o una prórroga reciente
    "ciudadania": 0.6,    # 2 reportes en 30 días
}
NOMBRES_SENALES = {
    "inactividad": "Inactividad con cámara funcionando",
    "atraso": "Atraso frente al cronograma",
    "brecha": "Brecha entre lo reportado y lo observado",
    "contrato": "Cambios contractuales",
    "ciudadania": "Reportes ciudadanos",
}
DIAS_SIN_DATOS_DISPOSITIVO = 3  # días seguidos sin datos que mandan la cámara a mantenimiento
# Mantenimiento del registro: cuándo un dato se considera vencido
VENCE_INFORME_DIAS = 30  # días desde el último informe de avance registrado
VENCE_PAGO_DIAS = 45     # días desde el último pago registrado

SEMILLA = 2026  # misma semilla = mismos datos simulados en cualquier computadora

# --- Generador a partir del piloto -----------------------------------------------------------
ESCENARIOS = ["normal", "paralizada", "esporadica", "lenta", "falla_camara", "terminada"]

# Canal oficial al que la ficha ciudadana envía los reportes (no se guardan en LupIA)
CANAL_DENUNCIAS = {
    "nombre": "Denuncia electrónica de la Contraloría General de la República",
    "url": "https://www.cgr.go.cr/",
    "telefono": "2501-8000",
}
