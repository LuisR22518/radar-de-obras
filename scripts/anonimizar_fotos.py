"""Difumina a las personas en las fotos reales del piloto de dIAra antes de publicarlas.

Uso:  python scripts/anonimizar_fotos.py <carpeta con las fotos originales>

Las fotos originales vienen del repositorio público de dIAra (ver datos/diara/dIAra-K1/FUENTE.md).
LupIA no las guarda: solo publica estas versiones, en las que cada recuadro etiquetado como persona
se difumina con un margen, por la Ley 8968 de protección de datos personales. Las máquinas quedan
visibles porque son la evidencia que interesa al auditor.
"""
import sys
from pathlib import Path

from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import diara  # noqa: E402
from radar import config as C  # noqa: E402

DESTINO = C.RAIZ / "src" / "data" / "fotos-piloto"
MARGEN = 12  # píxeles alrededor de cada persona


def main(origen: Path):
    det = diara.leer_camara(C.DIARA_REAL / "dIAra-K1", "dIAra-K1").detecciones
    DESTINO.mkdir(parents=True, exist_ok=True)
    for foto in sorted(origen.glob("*.jpg")):
        img = Image.open(foto).convert("RGB")
        personas = det[(det["nombre_imagen"] == foto.name) & (det["clase"] == "Persona")]
        for _, p in personas.iterrows():
            caja = (max(0, int(p["x1"]) - MARGEN), max(0, int(p["y1"]) - MARGEN),
                    min(img.width, int(p["x2"]) + MARGEN), min(img.height, int(p["y2"]) + MARGEN))
            img.paste(img.crop(caja).filter(ImageFilter.GaussianBlur(10)), caja[:2])
        img.save(DESTINO / foto.name, quality=82, optimize=True)
        print(f"{foto.name}: {len(personas)} persona(s) difuminada(s)")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
