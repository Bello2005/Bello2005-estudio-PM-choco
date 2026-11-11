"""Pruebas del método Alkire-Foster y de la lectura de anexos (corren sin internet: pytest)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pobreza import ipm  # noqa: E402
from pobreza.config import IPM_INDICADORES  # noqa: E402
from pobreza.lectura import codigo, tabla_municipal  # noqa: E402


def test_pesos_oficiales_suman_uno():
    assert ipm.pesos().sum() == pytest.approx(1.0)
    assert len(IPM_INDICADORES) == 15


def test_alkire_foster_ejemplo_a_mano():
    # Tres hogares, dos indicadores con peso 0,5 cada uno y k = 0,5
    X = pd.DataFrame({"a": [1, 1, 0], "b": [1, 0, 0]})
    r = ipm.alkire_foster(X, w=pd.Series({"a": 0.5, "b": 0.5}), k=0.5)
    # Hogar 1: puntaje 1 (pobre). Hogar 2: 0,5 (pobre). Hogar 3: 0 (no pobre).
    assert r.H == pytest.approx(2 / 3)
    assert r.A == pytest.approx(0.75)
    assert r.M0 == pytest.approx(0.5)
    assert r.contribucion.sum() == pytest.approx(100)


def test_alkire_foster_con_factor_de_expansion():
    X = pd.DataFrame({"a": [1, 0], "b": [1, 0]})
    r = ipm.alkire_foster(X, w=pd.Series({"a": 0.5, "b": 0.5}), k=0.5, factor=pd.Series([3, 1]))
    assert r.H == pytest.approx(0.75)


def test_privacion_ponderada_igual_a_m0_con_k_cero():
    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.integers(0, 2, size=(500, 15)), columns=list(IPM_INDICADORES))
    m0 = ipm.alkire_foster(X, k=0.0).M0
    agregado = ipm.privacion_ponderada_agregado((X.mean() * 100).to_frame().T).iloc[0] / 100
    assert agregado == pytest.approx(m0)


def test_codigo_divipola():
    assert codigo(5001, 5) == "05001"
    assert codigo("27001", 5) == "27001"
    assert codigo(27001.0, 5) == "27001"
    assert codigo("Total", 5) is None


def test_tabla_municipal_con_encabezado_de_dos_filas(tmp_path):
    # Imita la hoja "8_Privaciones Mpio dominio" del DANE: indicador arriba, dominio abajo.
    filas = [
        ["ID", "Municipio", "Analfabetismo", None, None],
        [None, None, "Total", "Cabeceras", "Centros poblados y rural disperso"],
        ["27001", "QUIBDÓ", 10.0, 8.0, 20.0],
        ["27025", "ALTO BAUDÓ", 47.0, 29.0, 50.3],
        ["05001", "MEDELLÍN", 5.0, 4.9, 11.6],
    ]
    ruta = tmp_path / "anexo.xlsx"
    pd.DataFrame(filas).to_excel(ruta, header=False, index=False)
    t = tabla_municipal(ruta, 0)
    assert set(t["cod_mpio"]) == {"27001", "27025", "05001"}
    fila = t[(t.cod_mpio == "27025") & t.encabezado.str.contains("cabeceras")]
    assert fila["valor"].iloc[0] == 29.0
