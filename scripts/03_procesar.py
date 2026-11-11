#!/usr/bin/env python3
"""Convierte los archivos de datos/crudos en tablas limpias en datos/procesados."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pobreza.procesar import procesar_todo  # noqa: E402

if __name__ == "__main__":
    procesar_todo()
