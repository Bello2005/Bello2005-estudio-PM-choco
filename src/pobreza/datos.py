"""Funciones para que los notebooks carguen las tablas procesadas con los tipos correctos."""
from __future__ import annotations

import json

import pandas as pd

from .config import COD_CHOCO, CRUDOS, PROCESADOS

TIPOS = {"cod_mpio": str, "cod_dpto": str}


def disponible(nombre: str) -> bool:
    return (PROCESADOS / nombre).exists()


def leer(nombre: str) -> pd.DataFrame:
    ruta = PROCESADOS / nombre
    if not ruta.exists():
        raise FileNotFoundError(f"No está {ruta}. Corra primero scripts/01_descargar.py y scripts/03_procesar.py")
    return pd.read_csv(ruta, dtype=TIPOS)


def base_municipal() -> pd.DataFrame:
    df = leer("base_municipal.csv")
    df["es_choco"] = df["cod_dpto"] == COD_CHOCO
    df["municipio"] = df["municipio"].fillna(df["cod_mpio"]).astype(str).str.strip().str.title()
    return df


def ipm_municipal(dominio: str | None = None) -> pd.DataFrame:
    df = leer("ipm_municipal.csv")
    df["municipio"] = df["municipio"].fillna(df["cod_mpio"]).astype(str).str.strip().str.title()
    return df if dominio is None else df[df["dominio"] == dominio].reset_index(drop=True)


def ipm_departamental() -> pd.DataFrame:
    return leer("ipm_departamental.csv")


def manifiesto() -> pd.DataFrame:
    ruta = CRUDOS / "manifiesto.json"
    if not ruta.exists():
        return pd.DataFrame()
    m = json.loads(ruta.read_text())
    return pd.DataFrame([{"clave": k, **{c: v for c, v in d.items() if c != "clave"}} for k, d in m.items()])


def mapa_municipios():
    """GeoDataFrame con cod_mpio. Devuelve None si no hay geopandas o no se descargó el mapa."""
    ruta = CRUDOS / "municipios_mgn2018.geojson"
    if not ruta.exists():
        return None
    try:
        import geopandas as gpd
    except ImportError:
        return None
    g = gpd.read_file(ruta)
    cols = {c.upper(): c for c in g.columns}
    if "MPIO_CCNCT" in cols:
        g["cod_mpio"] = g[cols["MPIO_CCNCT"]].astype(str).str.zfill(5)
    else:
        g["cod_mpio"] = g[cols["DPTO_CCDGO"]].astype(str).str.zfill(2) + g[cols["MPIO_CCDGO"]].astype(str).str[-3:].str.zfill(3)
    return g[["cod_mpio", "geometry"]]
