"""Miniatura de la foto real del piloto para la tarjeta de la portada.

La tarjeta mide unos 100 px, así que basta una foto de 330 px de ancho (el mismo tamaño que se pide
a Wikimedia para las fotos de referencia). La foto completa, con las personas ya difuminadas, sigue en
fotos-piloto/ para la ficha y el análisis de la obra.
"""
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

FOTO = Path(__file__).resolve().parent / "fotos-piloto" / "20240319-090439.jpg"
ANCHO = 330

img = Image.open(FOTO).convert("RGB")
img = img.resize((ANCHO, round(img.height * ANCHO / img.width)), Image.LANCZOS)
salida = BytesIO()
img.save(salida, "JPEG", quality=80, optimize=True, progressive=True)
sys.stdout.buffer.write(salida.getvalue())
