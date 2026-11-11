#!/usr/bin/env python3
"""Escribe reportes/estructura_anexos.md con la forma de cada Excel descargado.

Sirve para revisar rápido si el DANE cambió el formato de un anexo (títulos, filas de encabezado, hojas).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
# En Windows la consola a veces no usa UTF-8: así las tildes y los símbolos se ven bien.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pobreza.config import CRUDOS, REPORTES  # noqa: E402
from pobreza.lectura import describir_libro  # noqa: E402


def main() -> int:
    partes = ["# Estructura de los anexos descargados\n",
              "Generado por `scripts/02_inspeccionar.py`. Muestra las primeras filas de cada hoja.\n"]
    for ruta in sorted(CRUDOS.glob("*.xls*")):
        try:
            partes.append(describir_libro(ruta))
        except Exception as e:  # noqa: BLE001
            partes.append(f"## {ruta.name}\n\nNo se pudo leer: {e}\n")
    salida = REPORTES / "estructura_anexos.md"
    salida.write_text("\n".join(partes), encoding="utf-8")
    print(salida.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
