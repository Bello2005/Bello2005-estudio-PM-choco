#!/usr/bin/env python3
"""Descarga las fuentes del estudio a datos/crudos.

    python scripts/01_descargar.py                 # todas
    python scripts/01_descargar.py ipm_municipal_2018 nbi_2018
    python scripts/01_descargar.py --forzar        # vuelve a bajar aunque ya existan
    python scripts/01_descargar.py --lista         # muestra el catálogo
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pobreza.descarga import descargar_todo  # noqa: E402
from pobreza.fuentes import FUENTES  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("claves", nargs="*", help="claves del catálogo (por defecto, todas)")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--lista", action="store_true")
    a = ap.parse_args()

    if a.lista:
        for f in FUENTES:
            print(f"{f.clave:<28} {'obligatoria' if f.obligatoria else 'opcional':<12} {f.nombre}")
        return 0

    res = descargar_todo(a.claves or None, forzar=a.forzar)
    fallas = [r for r in res if r["estado"] == "error"]
    graves = [r for r in fallas if r["obligatoria"]]
    print(f"\nListo: {len(res) - len(fallas)} bien, {len(fallas)} con error ({len(graves)} obligatorias).")
    return 1 if graves else 0


if __name__ == "__main__":
    sys.exit(main())
