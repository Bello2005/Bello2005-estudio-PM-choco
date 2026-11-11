"""Lectura tolerante de los anexos en Excel del DANE.

Los anexos del DANE traen títulos arriba, encabezados de varias filas con celdas combinadas y notas al final.
En vez de amarrar el código a números de fila, aquí se busca la fila de encabezados por palabras clave, se
arman los nombres de columna juntando las filas de encabezado y se pasa la tabla a formato largo:

    cod_mpio | municipio | encabezado | valor

Después, cada script decide qué significa cada encabezado (con expresiones regulares).
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


def normalizar(texto) -> str:
    """minúsculas, sin tildes, sin saltos de línea ni espacios dobles."""
    if texto is None or (isinstance(texto, float) and np.isnan(texto)):
        return ""
    s = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def codigo(x, digitos: int) -> str | None:
    """Convierte 27001, '27001', 27001.0 o ' 5001' en '27001' / '05001'. Devuelve None si no es un código."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip()
    if re.fullmatch(r"\d+\.0+", s):
        s = s.split(".")[0]
    if not re.fullmatch(r"\d{1,%d}" % digitos, s):
        return None
    return s.zfill(digitos)


def leer_crudo(ruta: Path, hoja) -> pd.DataFrame:
    motor = "xlrd" if Path(ruta).suffix.lower() == ".xls" else None
    return pd.read_excel(ruta, sheet_name=hoja, header=None, dtype=object, engine=motor)


def hojas(ruta: Path) -> list[str]:
    motor = "xlrd" if Path(ruta).suffix.lower() == ".xls" else None
    return pd.ExcelFile(ruta, engine=motor).sheet_names


def _fila_encabezado(crudo: pd.DataFrame, claves=("municipio",), max_filas: int = 40) -> int | None:
    """Primera fila con las palabras clave y al menos dos celdas llenas (los títulos ocupan una sola celda)."""
    for i in range(min(max_filas, len(crudo))):
        celdas = [normalizar(v) for v in crudo.iloc[i].tolist()]
        if sum(bool(c) for c in celdas) < 2:
            continue
        fila = " | ".join(celdas)
        if all(c in fila for c in claves):
            return i
    return None


def _es_numero(v) -> bool:
    if isinstance(v, (int, float, np.integer, np.floating)) and not pd.isna(v):
        return True
    return bool(re.fullmatch(r"\s*-?\d+([.,]\d+)?\s*", str(v))) if v is not None else False


def _primera_fila_de_datos(crudo: pd.DataFrame, desde: int) -> int | None:
    """Primera fila después de los encabezados con al menos tres celdas numéricas."""
    for i in range(desde, min(desde + 15, len(crudo))):
        if sum(_es_numero(v) for v in crudo.iloc[i].tolist()) >= 3:
            return i
    return None


def tabla_municipal(ruta: Path, hoja, claves=("municipio",)) -> pd.DataFrame | None:
    """Lee una hoja con una fila por municipio y la devuelve en formato largo.

    Columnas del resultado: cod_dpto, cod_mpio, municipio, departamento, encabezado, valor.
    Devuelve None si la hoja no parece una tabla municipal.
    """
    crudo = leer_crudo(ruta, hoja)
    if crudo.empty:
        return None
    i_enc = _fila_encabezado(crudo, claves)
    if i_enc is None:
        return None
    i_dat = _primera_fila_de_datos(crudo, i_enc + 1)
    if i_dat is None:
        return None

    # Encabezados: desde la fila de "municipio" (o un poco antes, si hay títulos de grupo) hasta antes de los datos.
    inicio = max(0, i_enc - 2)
    bloque = crudo.iloc[inicio:i_dat].copy()
    # Las filas de título (una sola celda con texto en toda la fila) no aportan al encabezado.
    filas_utiles = [r for r in range(len(bloque)) if bloque.iloc[r].notna().sum() > 1 or r >= (i_enc - inicio)]
    # Celdas combinadas: en Excel quedan vacías salvo la primera; se rellenan hacia la derecha por fila.
    bloque = bloque.apply(lambda fila: fila.ffill(), axis=1)
    nombres = []
    for j in range(crudo.shape[1]):
        partes = []
        for r in filas_utiles:
            t = normalizar(bloque.iloc[r, j])
            if t and (not partes or partes[-1] != t):
                partes.append(t)
        nombres.append(" / ".join(partes) if partes else f"col_{j}")

    datos = crudo.iloc[i_dat:].copy()
    datos.columns = range(datos.shape[1])

    # Columnas de identificación
    col_mpio5 = col_dpto = col_mpio3 = col_nom_mpio = col_nom_dpto = None
    for j, n in enumerate(nombres[:8]):
        muestra = datos[j].dropna().head(200)
        if muestra.empty:
            continue
        txt = muestra.astype(str).str.strip().str.replace(r"\.0+$", "", regex=True)
        cinco_digitos = txt.str.fullmatch(r"\d{4,5}").mean()   # 5001 o 05001
        corto = txt.str.fullmatch(r"\d{1,3}").mean()
        es_texto = (~txt.str.fullmatch(r"-?\d+([.,]\d+)?")).mean()
        ultimo = n.split(" / ")[-1]   # la fila de encabezado más cercana a los datos
        if col_mpio5 is None and cinco_digitos > 0.9 and ("depart" not in ultimo):
            col_mpio5 = j
        elif "municip" in ultimo and "cod" in ultimo and corto > 0.9:
            col_mpio3 = j
        elif "depart" in ultimo and "cod" in ultimo and corto > 0.9:
            col_dpto = j
        elif "municip" in ultimo and es_texto > 0.9:
            col_nom_mpio = j
        elif "depart" in ultimo and es_texto > 0.9:
            col_nom_dpto = j

    if col_mpio5 is not None:
        cod_mpio = datos[col_mpio5].map(lambda v: codigo(v, 5))
    elif col_dpto is not None and col_mpio3 is not None:
        d = datos[col_dpto].map(lambda v: codigo(v, 2))
        m = datos[col_mpio3].map(lambda v: codigo(v, 3))
        cod_mpio = pd.Series([a + b if a and b else None for a, b in zip(d, m)], index=datos.index)
    else:
        return None

    ident = pd.DataFrame({
        "cod_mpio": cod_mpio,
        "municipio": datos[col_nom_mpio] if col_nom_mpio is not None else None,
        "departamento": datos[col_nom_dpto] if col_nom_dpto is not None else None,
    })
    ident = ident[ident["cod_mpio"].notna()]
    if ident.empty:
        return None
    ident["cod_dpto"] = ident["cod_mpio"].str[:2]

    usadas = {c for c in (col_mpio5, col_dpto, col_mpio3, col_nom_mpio, col_nom_dpto) if c is not None}
    largos = []
    for j, n in enumerate(nombres):
        if j in usadas:
            continue
        valores = pd.to_numeric(datos.loc[ident.index, j], errors="coerce")
        if valores.notna().mean() < 0.5:
            continue
        largos.append(ident.assign(encabezado=n, valor=valores.values, hoja=str(hoja)))
    if not largos:
        return None
    return pd.concat(largos, ignore_index=True)


def describir_libro(ruta: Path, filas: int = 14) -> str:
    """Texto con la forma de cada hoja (para revisar a ojo cuando un anexo cambia de formato)."""
    salida = [f"## {Path(ruta).name}\n"]
    for h in hojas(ruta):
        crudo = leer_crudo(ruta, h)
        salida.append(f"### Hoja «{h}» — {crudo.shape[0]} filas × {crudo.shape[1]} columnas\n")
        salida.append("```")
        for i in range(min(filas, len(crudo))):
            celdas = [str(v)[:28] for v in crudo.iloc[i].tolist()[:14] if pd.notna(v)]
            if celdas:
                salida.append(f"{i:>3}: " + " | ".join(celdas))
        salida.append("```\n")
    return "\n".join(salida)
