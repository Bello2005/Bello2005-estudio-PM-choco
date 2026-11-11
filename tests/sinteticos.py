"""Genera datos falsos con la misma forma que los procesados, para probar los notebooks sin internet.

    POBREZA_DATOS=/tmp/prueba python tests/sinteticos.py ruta/al/municipios.geojson

Los valores son inventados (solo sirven para comprobar que el código corre). Nunca se usan en resultados.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pobreza.config import CRUDOS, IPM_INDICADORES, PROCESADOS  # noqa: E402
from pobreza.procesar import DEPARTAMENTOS, NOMBRES, construir_base_municipal  # noqa: E402

rng = np.random.default_rng(7)


def main(geojson: str | None) -> None:
    if geojson:
        import geopandas as gpd
        g = gpd.read_file(geojson)
        codigos = sorted((g["DPTO_CCDGO"].astype(str).str.zfill(2) + g["MPIO_CCDGO"].astype(str).str[-3:]).unique())
        shutil.copy(geojson, CRUDOS / "municipios_mgn2018.geojson")
    else:
        codigos = [f"{d}{m:03d}" for d in DEPARTAMENTOS for m in range(1, 30, 2)]

    filas = []
    for cod in codigos:
        base = rng.beta(2, 5) + (0.35 if cod.startswith("27") else 0)
        for dom, extra in (("total", 0), ("cabecera", -0.15), ("rural", 0.15)):
            p = np.clip(base + extra + rng.normal(0, 0.05), 0.01, 0.98)
            fila = {"cod_mpio": cod, "cod_dpto": cod[:2], "municipio": f"Municipio {cod}",
                    "departamento": NOMBRES.get(cod[:2], "x"), "dominio": dom}
            for ind in IPM_INDICADORES:
                fila[ind] = float(np.clip(100 * (p * rng.uniform(0.3, 1.4)), 0, 100))
            fila["ipm"] = float(np.clip(100 * p * 0.9, 0, 100))
            filas.append(fila)
    ipm = pd.DataFrame(filas)
    ipm.to_csv(PROCESADOS / "ipm_municipal.csv", index=False)

    tot = ipm[ipm["dominio"] == "total"]
    nbi = pd.DataFrame({"cod_mpio": tot["cod_mpio"], "dominio": "total",
                        "nbi": (tot["ipm"] * rng.uniform(0.6, 1.1, len(tot))).clip(0, 100),
                        "nbi_miseria": (tot["ipm"] * rng.uniform(0.1, 0.4, len(tot))).clip(0, 100)})
    nbi.to_csv(PROCESADOS / "nbi_municipal.csv", index=False)

    pob = pd.DataFrame({"cod_mpio": tot["cod_mpio"]})
    pob["poblacion_total"] = rng.lognormal(9.5, 1.1, len(pob)).round()
    pob["poblacion_rural"] = (pob["poblacion_total"] * rng.uniform(0.1, 0.9, len(pob))).round()
    pob["poblacion_cabecera"] = pob["poblacion_total"] - pob["poblacion_rural"]
    pob.to_csv(PROCESADOS / "poblacion_2018.csv", index=False)

    s11 = pd.DataFrame({"cod_mpio": tot["cod_mpio"], "punt_global": 280 - 0.9 * tot["ipm"].values
                        + rng.normal(0, 10, len(tot)), "estudiantes": rng.integers(20, 3000, len(tot))})
    s11.to_csv(PROCESADOS / "saber11_2018.csv", index=False)

    dep = []
    for cod in ["00", *DEPARTAMENTOS]:
        nivel = 15 + (25 if cod == "27" else rng.uniform(-8, 15))
        for anio in range(2018, 2026):
            for dom in ("total", "cabecera", "rural"):
                for ind in ["ipm", *IPM_INDICADORES]:
                    dep.append({"cod_dpto": cod, "dominio": dom, "indicador": ind, "anio": anio,
                                "valor": max(0.5, nivel - 0.8 * (anio - 2018) + rng.normal(0, 1.5)),
                                "departamento": NOMBRES[cod]})
    pd.DataFrame(dep).to_csv(PROCESADOS / "ipm_departamental.csv", index=False)
    construir_base_municipal()
    print(f"Datos sintéticos en {PROCESADOS}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
