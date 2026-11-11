"""Herramientas de medición: método Alkire-Foster y aproximaciones con datos agregados.

Dos niveles:

1. `alkire_foster`: el cálculo exacto, hogar por hogar. Sirve cuando se tienen microdatos
   (una fila por hogar con 0/1 en cada indicador).
2. Funciones `*_agregado`: lo que se puede decir con porcentajes municipales ya publicados.
   No reemplazan el cálculo exacto, porque no saben cuántas privaciones tiene a la vez un mismo hogar.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import DIMENSIONES, IPM_CORTE_K, IPM_INDICADORES


def pesos(indicadores: list[str] | None = None) -> pd.Series:
    """Pesos oficiales; si se pasa una lista, se re-normalizan para que sumen 1."""
    w = pd.Series({k: p for k, (_, p) in IPM_INDICADORES.items()})
    if indicadores is not None:
        w = w.reindex(indicadores).dropna()
        w = w / w.sum()
    return w


def dimension_de(indicador: str) -> str:
    return IPM_INDICADORES[indicador][0]


# --- 1. Alkire-Foster con microdatos -------------------------------------------------------------

@dataclass
class ResultadoAF:
    H: float                     # incidencia: proporción de pobres
    A: float                     # intensidad: privación promedio entre los pobres
    M0: float                    # IPM ajustado = H × A
    censurado: pd.Series         # % de la población pobre Y privada en cada indicador
    no_censurado: pd.Series      # % privada en cada indicador (pobre o no)
    contribucion: pd.Series      # aporte % de cada indicador al M0
    k: float


def alkire_foster(privaciones: pd.DataFrame, w: pd.Series | None = None, k: float = IPM_CORTE_K,
                  factor: pd.Series | None = None) -> ResultadoAF:
    """Calcula H, A y M0.

    privaciones: DataFrame 0/1, una fila por hogar (o persona) y una columna por indicador.
    w: pesos por indicador (por defecto, los oficiales re-normalizados a las columnas presentes).
    factor: factor de expansión (por ejemplo, número de personas del hogar). Por defecto, 1.
    """
    X = privaciones.astype(float)
    w = pesos(list(X.columns)) if w is None else (w.reindex(X.columns) / w.reindex(X.columns).sum())
    f = pd.Series(1.0, index=X.index) if factor is None else factor.reindex(X.index).astype(float)
    total = f.sum()

    c = X.mul(w, axis=1).sum(axis=1)          # puntaje de privación de cada hogar
    pobre = c >= k - 1e-9
    H = f[pobre].sum() / total
    A = (c[pobre] * f[pobre]).sum() / f[pobre].sum() if pobre.any() else 0.0
    M0 = H * A
    no_cens = X.mul(f, axis=0).sum() / total
    cens = X[pobre].mul(f[pobre], axis=0).sum() / total
    contrib = (w * cens) / M0 if M0 > 0 else w * 0
    return ResultadoAF(H=H, A=A, M0=M0, censurado=cens * 100, no_censurado=no_cens * 100,
                       contribucion=contrib * 100, k=k)


def curva_k(privaciones: pd.DataFrame, ks=np.linspace(0.1, 0.9, 17), **kw) -> pd.DataFrame:
    """Cómo cambian H, A y M0 al mover el corte k (prueba de robustez)."""
    filas = []
    for k in ks:
        r = alkire_foster(privaciones, k=k, **kw)
        filas.append({"k": k, "H": r.H * 100, "A": r.A * 100, "M0": r.M0})
    return pd.DataFrame(filas)


# --- 2. Aproximaciones con porcentajes municipales ----------------------------------------------

def indicadores_presentes(df: pd.DataFrame) -> list[str]:
    return [c for c in IPM_INDICADORES if c in df.columns]


def privacion_ponderada_agregado(df: pd.DataFrame, w: pd.Series | None = None) -> pd.Series:
    """Σ wᵢ·hᵢ con los porcentajes no censurados.

    Es el puntaje promedio de privación de los hogares del municipio (entre 0 y 100). Coincide con el M0 que
    resultaría con k = 0 (todos cuentan) y sirve para ordenar municipios cuando no hay microdatos.
    """
    ind = indicadores_presentes(df)
    w = pesos(ind) if w is None else w.reindex(ind) / w.reindex(ind).sum()
    return df[ind].mul(w, axis=1).sum(axis=1)


def contribucion_agregado(df: pd.DataFrame, w: pd.Series | None = None, por: str = "indicador") -> pd.DataFrame:
    """Peso relativo de cada indicador (o dimensión) en la privación ponderada de cada fila (suma 100)."""
    ind = indicadores_presentes(df)
    w = pesos(ind) if w is None else w.reindex(ind) / w.reindex(ind).sum()
    aporte = df[ind].mul(w, axis=1)
    aporte = aporte.div(aporte.sum(axis=1), axis=0) * 100
    if por == "dimension":
        aporte = aporte.T.groupby(dimension_de).sum().T[[d for d in DIMENSIONES if d in set(map(dimension_de, ind))]]
    return aporte


def pesos_alternativos(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Esquemas de pesos para probar que las conclusiones no dependen de una sola elección."""
    ind = indicadores_presentes(df)
    oficiales = pesos(ind)
    iguales = pd.Series(1 / len(ind), index=ind)
    # Inverso de la desviación estándar: evita que un indicador muy disperso domine.
    sd = df[ind].std().replace(0, np.nan)
    inv_sd = (1 / sd).fillna(0)
    inv_sd = inv_sd / inv_sd.sum()
    # Primer componente principal (en valor absoluto), sobre datos estandarizados.
    z = (df[ind] - df[ind].mean()) / df[ind].std()
    z = z.dropna()
    _, _, vt = np.linalg.svd(z.values, full_matrices=False)
    pc1 = pd.Series(np.abs(vt[0]), index=ind)
    pc1 = pc1 / pc1.sum()
    return {"Oficiales DANE": oficiales, "Iguales por indicador": iguales,
            "Inverso de la dispersión": inv_sd, "Componente principal": pc1}


def brecha(df: pd.DataFrame, columnas: list[str], grupo: pd.Series, peso: pd.Series | None = None) -> pd.DataFrame:
    """Promedio (ponderado por población si se da `peso`) de cada columna en el grupo y fuera de él."""
    filas = {}
    for nombre, mascara in (("Grupo", grupo), ("Resto", ~grupo)):
        sub = df.loc[mascara, columnas]
        if peso is None:
            filas[nombre] = sub.mean()
        else:
            p = peso[mascara]
            filas[nombre] = sub.mul(p, axis=0).sum() / sub.notna().mul(p, axis=0).sum()
    out = pd.DataFrame(filas)
    out["Diferencia (pp)"] = out["Grupo"] - out["Resto"]
    out["Razón"] = out["Grupo"] / out["Resto"]
    return out
