"""Aviso semanal a los auditores por Telegram: qué obras necesitan revisión esta semana.

Uso:  python scripts/avisos.py            solo muestra el mensaje
      python scripts/avisos.py --enviar   lo envía por Telegram

GitHub Actions lo envía los lunes a las 7:05 (hora de Costa Rica) y cuando se pide a mano
(Actions > Recalcular y publicar LupIA > Run workflow > Enviar el aviso semanal).

Para enviarlo hacen falta dos secretos del repositorio (Settings > Secrets and variables > Actions):
  TELEGRAM_TOKEN    el token del bot, que da @BotFather al crearlo
  TELEGRAM_CHAT_ID  el chat o grupo de auditores donde está el bot
Sin ellos, el script solo muestra el mensaje: nunca detiene la publicación.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import config as C  # noqa: E402

SITIO = "https://luisr22518.github.io/radar-de-obras"


def razon(o) -> str:
    alertas = str(o["alertas"]).split(";") if isinstance(o["alertas"], str) else []
    partes = []
    if "inactividad" in alertas:
        partes.append(f"{int(o['racha_inactividad_dias'])} días hábiles sin actividad")
    if "atraso" in alertas:
        partes.append(f"{o['atraso_pts']:.1f} puntos de atraso".replace(".", ","))
    if "brecha" in alertas:
        partes.append("reporta avance que la cámara no respalda")
    if "contrato" in alertas:
        partes.append(f"monto aumentado {o['aumento_monto_pct']:.0f} %" if o["aumento_monto_pct"] > 0 else "prórroga reciente")
    if "ciudadania" in alertas:
        partes.append(f"{int(o['reportes_30d'])} reportes ciudadanos")
    return ", ".join(partes)


def mensaje() -> str:
    sen = pd.read_csv(C.SALIDAS / "senales.csv")
    res = json.loads((C.SALIDAS / "resumen.json").read_text(encoding="utf-8"))
    revisar = sen[sen["amerita_revision"]].sort_values("prioridad")
    camaras = sen[sen["en_cola_dispositivos"]]
    lineas = [f"LupIA: {len(revisar)} obras necesitan revisión (datos al {res['fecha_corte']})", ""]
    for i, (_, o) in enumerate(revisar.iterrows(), start=1):
        lineas.append(f"{i}. {o['nombre']} ({o['canton']}): {razon(o)}.")
        lineas.append(f"   {SITIO}/obra.html?id={o['obra_id']}")
    if len(camaras):
        lineas += ["", "Cámaras sin datos (van a mantenimiento): " + ", ".join(camaras["nombre"]) + "."]
    lineas += ["", f"Lista completa: {SITIO}/"]
    return "\n".join(lineas)


def enviar(texto: str) -> bool:
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("No hay TELEGRAM_TOKEN ni TELEGRAM_CHAT_ID: el aviso no se envía.")
        return False
    datos = urllib.parse.urlencode({"chat_id": chat, "text": texto, "disable_web_page_preview": "true"}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=datos, timeout=30) as r:
        ok = json.load(r).get("ok", False)
    print("Aviso enviado por Telegram." if ok else "Telegram no aceptó el aviso.")
    return ok


def main():
    texto = mensaje()
    print(texto)
    if "--enviar" in sys.argv:
        try:
            enviar(texto)
        except Exception as error:  # Telegram caído o token inválido: no se detiene la publicación
            print(f"No se pudo enviar el aviso ({error}).")


if __name__ == "__main__":
    main()
