"""Convierte los archivos crudos en tablas limpias (datos/procesados).

Cada función lee un anexo, reconoce sus columnas por el texto del encabezado y escribe un CSV ordenado.
Si un anexo no está (porque la descarga falló), se salta con un aviso y el resto sigue.
"""
from __future__ import annotations

import re
import warnings

import numpy as np
import pandas as pd

from .config import CRUDOS, IPM_INDICADORES, PROCESADOS
from .lectura import codigo, hojas, leer_crudo, normalizar, tabla_municipal

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# --- Reconocer encabezados ---------------------------------------------------------------------

# El orden importa: "primera infancia" va antes que "acceso a salud", y los indicadores antes que el IPM.
PATRONES_IPM = [
    ("barreras_primera_infancia", r"primera infancia"),
    ("analfabetismo", r"analfabet"),
    ("bajo_logro_educativo", r"logro educ"),
    ("inasistencia_escolar", r"inasistencia"),
    ("rezago_escolar", r"rezago"),
    ("trabajo_infantil", r"trabajo infantil"),
    ("dependencia_economica", r"dependencia"),
    ("empleo_informal", r"informal"),
    ("sin_aseguramiento_salud", r"aseguramiento"),
    ("barreras_acceso_salud", r"(barrera|acceso).*salud|salud.*(barrera|acceso)"),
    ("sin_acueducto", r"agua|acueducto"),
    ("sin_alcantarillado", r"excreta|alcantarill"),
    ("pisos_inadecuados", r"piso"),
    ("paredes_inadecuadas", r"pared"),
    ("hacinamiento_critico", r"hacinamiento"),
    ("desempleo_larga_duracion", r"desempleo"),
    ("ipm", r"(^|[^a-z])ipm([^a-z]|$)|pobreza multidimensional|incidencia|^pobre"),
]
PATRONES_NBI = [
    ("nbi_miseria", r"miseria"),
    ("nbi_vivienda", r"vivienda"),
    ("nbi_servicios", r"servicio"),
    ("nbi_hacinamiento", r"hacinamiento"),
    ("nbi_inasistencia", r"inasistencia"),
    ("nbi_dependencia", r"dependencia"),
    ("nbi", r"\bnbi\b|necesidades"),
]
DESCARTAR = r"coeficiente|\bcv\b|intervalo|limite|error|\bic\b|variacion"


def dominio_de(texto: str) -> str:
    t = normalizar(texto)
    if re.search(r"centro.? poblado|rural|resto", t):
        return "rural"
    if re.search(r"cabecera", t):
        return "cabecera"
    return "total"


def clasificar(texto: str, patrones) -> str | None:
    t = normalizar(texto)
    if re.search(DESCARTAR, t):
        return None
    for clave, patron in patrones:
        if re.search(patron, t):
            return clave
    return None


def a_porcentaje(s: pd.Series) -> pd.Series:
    """Algunos anexos traen proporciones (0-1) y otros porcentajes (0-100). Se deja todo en 0-100."""
    s = pd.to_numeric(s, errors="coerce")
    return s * 100 if s.dropna().between(0, 1.0001).all() and s.max() <= 1.0001 else s


# --- IPM municipal de fuente censal 2018 ---------------------------------------------------------

def procesar_ipm_municipal() -> pd.DataFrame | None:
    ruta = CRUDOS / "ipm_municipal_2018.xlsx"
    if not ruta.exists():
        print("  (falta ipm_municipal_2018.xlsx, se salta)")
        return None
    partes = []
    for h in hojas(ruta):
        t = tabla_municipal(ruta, h)
        if t is not None:
            partes.append(t)
    if not partes:
        raise RuntimeError("No se reconoció ninguna tabla municipal en el anexo de IPM. "
                           "Revise reportes/estructura_anexos.md y ajuste lectura.py.")
    largo = pd.concat(partes, ignore_index=True)
    contexto = largo["hoja"].astype(str) + " / " + largo["encabezado"].astype(str)
    largo["indicador"] = contexto.map(lambda x: clasificar(x, PATRONES_IPM))
    largo["dominio"] = contexto.map(dominio_de)
    largo = largo[largo["indicador"].notna()].copy()
    largo["valor"] = largo.groupby(["indicador"])["valor"].transform(a_porcentaje)

    # Si una misma (municipio, dominio, indicador) aparece más de una vez, se queda la primera y se avisa.
    dup = largo.duplicated(["cod_mpio", "dominio", "indicador"], keep="first")
    # Las hojas del anexo repiten el total (hoja 6 y hoja 8): solo se avisa si los valores no coinciden.
    distintos = largo.groupby(["cod_mpio", "dominio", "indicador"])["valor"].transform(lambda v: v.round(1).nunique() > 1)
    if (dup & distintos).any():
        ejemplos = largo.loc[dup & distintos, ["hoja", "encabezado"]].drop_duplicates().head(8).to_string(index=False)
        print(f"  aviso: {(dup & distintos).sum()} valores repetidos y distintos; se usó el primero:\n{ejemplos}")
    largo = largo[~dup]

    nombres = (largo.dropna(subset=["municipio"]).groupby("cod_mpio")[["municipio", "departamento"]].first())
    largo.drop(columns=["municipio", "departamento"]).to_csv(PROCESADOS / "ipm_municipal_largo.csv", index=False)

    ancho = largo.pivot_table(index=["cod_mpio", "dominio"], columns="indicador", values="valor").reset_index()
    ancho = ancho.merge(nombres, on="cod_mpio", how="left")
    ancho.insert(1, "cod_dpto", ancho["cod_mpio"].str[:2])
    ancho["departamento"] = ancho["cod_dpto"].map(NOMBRES)
    columnas = ["cod_mpio", "cod_dpto", "municipio", "departamento", "dominio", "ipm"] + \
               [c for c in IPM_INDICADORES if c in ancho.columns] + \
               [c for c in ancho.columns if c not in IPM_INDICADORES and c not in
                ("cod_mpio", "cod_dpto", "municipio", "departamento", "dominio", "ipm")]
    ancho = ancho[[c for c in columnas if c in ancho.columns]].sort_values(["cod_mpio", "dominio"])
    ancho.to_csv(PROCESADOS / "ipm_municipal.csv", index=False)
    resumen = ancho.groupby("dominio")["cod_mpio"].nunique().to_dict()
    print(f"  ipm_municipal.csv: municipios por dominio {resumen}; columnas {list(ancho.columns)}")
    return ancho


# --- NBI 2018 ------------------------------------------------------------------------------------

def procesar_nbi() -> pd.DataFrame | None:
    ruta = CRUDOS / "nbi_2018.xlsx"
    if not ruta.exists():
        print("  (falta nbi_2018.xlsx, se salta)")
        return None
    partes = [t for h in hojas(ruta) if (t := tabla_municipal(ruta, h)) is not None]
    if not partes:
        print("  aviso: no se reconoció la tabla municipal de NBI")
        return None
    largo = pd.concat(partes, ignore_index=True)
    contexto = largo["hoja"].astype(str) + " / " + largo["encabezado"].astype(str)
    largo["indicador"] = contexto.map(lambda x: clasificar(x, PATRONES_NBI))
    largo["dominio"] = contexto.map(dominio_de)
    # Se prefieren los porcentajes de personas (no los conteos absolutos)
    es_conteo = largo["valor"].abs() > 100
    largo = largo[largo["indicador"].notna() & ~es_conteo]
    largo = largo[~largo.duplicated(["cod_mpio", "dominio", "indicador"], keep="first")]
    ancho = largo.pivot_table(index=["cod_mpio", "dominio"], columns="indicador", values="valor").reset_index()
    ancho.to_csv(PROCESADOS / "nbi_municipal.csv", index=False)
    print(f"  nbi_municipal.csv: {ancho['cod_mpio'].nunique()} municipios; columnas {list(ancho.columns)}")
    return ancho


# --- Población -----------------------------------------------------------------------------------

def procesar_poblacion_censo() -> pd.DataFrame | None:
    ruta = CRUDOS / "poblacion_censo_2018.xls"
    if not ruta.exists():
        print("  (falta poblacion_censo_2018.xls, se salta)")
        return None
    partes = [t for h in hojas(ruta) if (t := tabla_municipal(ruta, h)) is not None]
    if not partes:
        print("  aviso: no se reconoció la tabla de población")
        return None
    largo = pd.concat(partes, ignore_index=True)
    largo = largo[~largo["encabezado"].str.contains(DESCARTAR + r"|%|porcentaje|omision", regex=True)]
    largo["dominio"] = largo["encabezado"].map(dominio_de)
    largo = largo[~largo.duplicated(["cod_mpio", "dominio"], keep="first")]
    ancho = largo.pivot_table(index="cod_mpio", columns="dominio", values="valor").add_prefix("poblacion_")
    ancho = ancho.reset_index()
    ancho.to_csv(PROCESADOS / "poblacion_2018.csv", index=False)
    print(f"  poblacion_2018.csv: {len(ancho)} municipios; total {ancho.get('poblacion_total', pd.Series()).sum():,.0f}")
    return ancho


def procesar_proyecciones() -> pd.DataFrame | None:
    """Proyecciones municipales: vienen en formato largo (municipio × año × área)."""
    ruta = CRUDOS / "proyecciones_municipales.xlsx"
    if not ruta.exists():
        print("  (falta proyecciones_municipales.xlsx, se salta)")
        return None
    for h in hojas(ruta):
        crudo = leer_crudo(ruta, h)
        i = next((r for r in range(min(30, len(crudo)))
                  if any(normalizar(v) in ("ano", "año", "anio") for v in crudo.iloc[r].tolist())), None)
        if i is None:
            continue
        df = crudo.iloc[i + 1:].copy()
        df.columns = [normalizar(v) for v in crudo.iloc[i].tolist()]
        col_cod = next((c for c in df.columns
                        if df[c].dropna().head(200).astype(str).str.fullmatch(r"\d{4,5}").mean() > 0.9), None)
        col_ano = next(c for c in df.columns if c in ("ano", "año", "anio"))
        col_area = next((c for c in df.columns if "area" in c), None)
        col_pob = next((c for c in df.columns if "poblaci" in c or c == "total"), None)
        if not (col_cod and col_pob):
            continue
        out = pd.DataFrame({
            "cod_mpio": df[col_cod].map(lambda v: codigo(v, 5)),
            "anio": pd.to_numeric(df[col_ano], errors="coerce"),
            "dominio": df[col_area].map(dominio_de) if col_area else "total",
            "poblacion": pd.to_numeric(df[col_pob], errors="coerce"),
        }).dropna()
        out["anio"] = out["anio"].astype(int)
        out = out.groupby(["cod_mpio", "anio", "dominio"], as_index=False)["poblacion"].sum()
        out.to_csv(PROCESADOS / "poblacion_proyecciones.csv", index=False)
        print(f"  poblacion_proyecciones.csv: {out['cod_mpio'].nunique()} municipios, años {out['anio'].min()}–{out['anio'].max()}")
        return out
    print("  aviso: no se reconoció el formato de las proyecciones")
    return None


# --- IPM departamental (serie de la ECV) ---------------------------------------------------------

DEPARTAMENTOS = {
    "05": "antioquia", "08": "atlantico", "11": "bogota", "13": "bolivar", "15": "boyaca", "17": "caldas",
    "18": "caqueta", "19": "cauca", "20": "cesar", "23": "cordoba", "25": "cundinamarca", "27": "choco",
    "41": "huila", "44": "la guajira", "47": "magdalena", "50": "meta", "52": "narino", "54": "norte de santander",
    "63": "quindio", "66": "risaralda", "68": "santander", "70": "sucre", "73": "tolima", "76": "valle del cauca",
    "81": "arauca", "85": "casanare", "86": "putumayo", "88": "san andres", "91": "amazonas", "94": "guainia",
    "95": "guaviare", "97": "vaupes", "99": "vichada",
}


NOMBRES = {
    "00": "Nacional", "05": "Antioquia", "08": "Atlántico", "11": "Bogotá D.C.", "13": "Bolívar", "15": "Boyacá",
    "17": "Caldas", "18": "Caquetá", "19": "Cauca", "20": "Cesar", "23": "Córdoba", "25": "Cundinamarca",
    "27": "Chocó", "41": "Huila", "44": "La Guajira", "47": "Magdalena", "50": "Meta", "52": "Nariño",
    "54": "Norte de Santander", "63": "Quindío", "66": "Risaralda", "68": "Santander", "70": "Sucre",
    "73": "Tolima", "76": "Valle del Cauca", "81": "Arauca", "85": "Casanare", "86": "Putumayo",
    "88": "San Andrés", "91": "Amazonas", "94": "Guainía", "95": "Guaviare", "97": "Vaupés", "99": "Vichada",
}


def _cod_departamento(texto) -> str | None:
    t = normalizar(texto)
    if not t:
        return None
    if t in ("nacional", "total nacional", "total"):
        return "00"
    for cod, nombre in DEPARTAMENTOS.items():
        if t == nombre or t.startswith(nombre + " ") or (nombre == "bogota" and t.startswith("bogota")) \
                or (nombre == "valle del cauca" and t == "valle") or (nombre == "san andres" and "san andres" in t):
            return cod
    return None


HOJAS_DEPARTAMENTALES = {
    # hoja (normalizada) -> indicador fijo (None = viene en la columna "Variable")
    "ipm_departamentos": "ipm",
    "ipm_indicadores_departamento": None,
    "intensidad_ipm": "intensidad",
    "incidencia_ajustada_ipm": "m0",
}


def _anio(texto) -> int | None:
    m = re.match(r"\s*(20\d\d)", str(texto)) if texto is not None and not pd.isna(texto) else None
    return int(m.group(1)) if m else None


def _hoja_departamental(crudo: pd.DataFrame, indicador_fijo: str | None) -> list[dict]:
    """Hojas con departamentos en filas y años (y a veces dominios) en columnas."""
    r_dep = next((r for r in range(min(30, len(crudo)))
                  if any(normalizar(v) == "departamento" for v in crudo.iloc[r].tolist())), None)
    if r_dep is None:
        return []
    fila_anios = next((r for r in (r_dep, r_dep - 1)
                       if r >= 0 and sum(_anio(v) is not None for v in crudo.iloc[r].tolist()) >= 2), None)
    if fila_anios is None:
        return []
    fila_dom = next((r for r in (r_dep + 1, r_dep) if r != fila_anios and r < len(crudo) and
                     any(normalizar(v) in ("total", "cabeceras") for v in crudo.iloc[r].tolist())), None)
    anios = pd.Series([_anio(v) for v in crudo.iloc[fila_anios].tolist()], dtype="object").ffill()
    doms = (crudo.iloc[fila_dom].map(lambda v: dominio_de(v) if normalizar(v) else None).tolist()
            if fila_dom is not None else ["total"] * crudo.shape[1])
    enc = [normalizar(v) for v in crudo.iloc[fila_dom if fila_dom is not None else r_dep].tolist()]
    col_var = next((j for j, t in enumerate(enc) if t == "variable"), None)
    inicio = max(fila_anios, fila_dom or 0) + 1
    columnas = [j for j in range(crudo.shape[1]) if j not in (0, col_var) and anios[j] is not None and doms[j]]

    filas = []
    depto = None
    for r in range(inicio, len(crudo)):
        valores = crudo.iloc[r].tolist()
        if normalizar(valores[0]):
            depto = _cod_departamento(valores[0])
        if depto is None:
            continue
        ind = indicador_fijo if col_var is None else clasificar(valores[col_var], PATRONES_IPM)
        if ind is None:
            continue
        for j in columnas:
            v = pd.to_numeric(valores[j], errors="coerce")
            if pd.notna(v):
                filas.append({"cod_dpto": depto, "dominio": doms[j], "indicador": ind,
                              "anio": int(anios[j]), "valor": float(v)})
    return filas


HOJAS_NACIONALES = {
    "ipm_dominios": "ipm",
    "ipm_indicadores": None,
    "intensidad_ipm": "intensidad",
    "incidencia_ajustada_ipm": "m0",
}


def _hoja_nacional(crudo: pd.DataFrame, indicador_fijo: str | None) -> list[dict]:
    """Primer bloque de la hoja: total nacional, cabecera y rural por año (antes de las regiones)."""
    r_anios = next((r for r in range(min(30, len(crudo)))
                    if sum(_anio(v) is not None for v in crudo.iloc[r].tolist()) >= 3), None)
    if r_anios is None:
        return []
    anios = {j: _anio(v) for j, v in enumerate(crudo.iloc[r_anios].tolist()) if _anio(v) is not None}
    filas, dominio = [], None
    for r in range(r_anios + 1, len(crudo)):
        valores = crudo.iloc[r].tolist()
        if not any(normalizar(v) for v in valores):
            break                                   # fin del bloque nacional
        if normalizar(valores[0]):
            dominio = dominio_de(valores[0])
        if indicador_fijo is None:
            ind = clasificar(valores[1], PATRONES_IPM)
        else:
            ind = indicador_fijo
        if ind is None or dominio is None:
            continue
        for j, anio in anios.items():
            v = pd.to_numeric(valores[j], errors="coerce")
            if pd.notna(v):
                filas.append({"cod_dpto": "00", "dominio": dominio, "indicador": ind, "anio": anio, "valor": float(v)})
    return filas


def procesar_ipm_departamental() -> pd.DataFrame | None:
    ruta = CRUDOS / "ipm_departamental.xlsx"
    if not ruta.exists():
        print("  (falta ipm_departamental.xlsx, se salta)")
        return None
    filas = []
    for h in hojas(ruta):
        clave = normalizar(h).replace(" ", "_")
        if clave in HOJAS_DEPARTAMENTALES:
            filas += _hoja_departamental(leer_crudo(ruta, h), HOJAS_DEPARTAMENTALES[clave])
    nacional = CRUDOS / "ipm_nacional.xlsx"
    if nacional.exists():
        for h in hojas(nacional):
            clave = normalizar(h).replace(" ", "_")
            if clave in HOJAS_NACIONALES:
                filas += _hoja_nacional(leer_crudo(nacional, h), HOJAS_NACIONALES[clave])
    if not filas:
        print("  aviso: no se reconoció la serie departamental")
        return None
    df = pd.DataFrame(filas)
    df = df[~df.duplicated(["cod_dpto", "dominio", "indicador", "anio"], keep="first")]
    df["departamento"] = df["cod_dpto"].map(NOMBRES)
    df = df.sort_values(["indicador", "dominio", "cod_dpto", "anio"])
    df.to_csv(PROCESADOS / "ipm_departamental.csv", index=False)
    print(f"  ipm_departamental.csv: {df['cod_dpto'].nunique()} territorios, indicadores {sorted(df['indicador'].unique())}, "
          f"años {df['anio'].min()}–{df['anio'].max()}")
    return df


# --- Saber 11 ------------------------------------------------------------------------------------

def procesar_saber11() -> pd.DataFrame | None:
    """Promedio por municipio en el año más cercano a 2018 (el del censo), ponderado por estudiantes."""
    ruta = CRUDOS / "saber11_municipios.csv"
    if not ruta.exists():
        print("  (falta saber11_municipios.csv, se salta)")
        return None
    df = pd.read_csv(ruta, dtype=str).rename(columns={"puntaje": "punt_global"})
    df["cod_mpio"] = df["cod_mpio"].map(lambda v: codigo(v, 5))
    df["punt_global"] = pd.to_numeric(df["punt_global"], errors="coerce")
    df["estudiantes"] = pd.to_numeric(df["estudiantes"], errors="coerce")
    df["anio"] = pd.to_numeric(df["periodo"].str[:4], errors="coerce") if "periodo" in df else 2018
    df = df.dropna(subset=["cod_mpio", "punt_global", "estudiantes", "anio"])
    df["anio"] = df["anio"].astype(int)
    df["suma"] = df["punt_global"] * df["estudiantes"]
    serie = df.groupby(["cod_mpio", "anio"], as_index=False)[["suma", "estudiantes"]].sum()
    serie["punt_global"] = serie["suma"] / serie["estudiantes"]
    serie = serie.drop(columns="suma")
    serie.to_csv(PROCESADOS / "saber11_serie.csv", index=False)
    anio = min(serie["anio"].unique(), key=lambda a: (abs(a - 2018), a))
    corte = serie[serie["anio"] == anio].drop(columns="anio")
    corte.to_csv(PROCESADOS / "saber11_2018.csv", index=False)
    print(f"  saber11_2018.csv: año {anio}, {len(corte)} municipios, {corte['estudiantes'].sum():,.0f} estudiantes; "
          f"serie {serie['anio'].min()}–{serie['anio'].max()}")
    return corte


# --- Tabla maestra -------------------------------------------------------------------------------

def construir_base_municipal() -> pd.DataFrame | None:
    """Una fila por municipio con todo lo disponible (dominio total)."""
    p = PROCESADOS
    if not (p / "ipm_municipal.csv").exists():
        return None
    ipm = pd.read_csv(p / "ipm_municipal.csv", dtype={"cod_mpio": str, "cod_dpto": str})
    base = ipm[ipm["dominio"] == "total"].drop(columns="dominio")
    # IPM de cabecera y rural como columnas aparte
    for dom in ("cabecera", "rural"):
        sub = ipm.loc[ipm["dominio"] == dom, ["cod_mpio", "ipm"]].rename(columns={"ipm": f"ipm_{dom}"})
        base = base.merge(sub, on="cod_mpio", how="left")
    if (p / "nbi_municipal.csv").exists():
        nbi = pd.read_csv(p / "nbi_municipal.csv", dtype={"cod_mpio": str})
        base = base.merge(nbi[nbi["dominio"] == "total"].drop(columns="dominio"), on="cod_mpio", how="left")
    if (p / "poblacion_2018.csv").exists():
        base = base.merge(pd.read_csv(p / "poblacion_2018.csv", dtype={"cod_mpio": str}), on="cod_mpio", how="left")
    if (p / "saber11_2018.csv").exists():
        base = base.merge(pd.read_csv(p / "saber11_2018.csv", dtype={"cod_mpio": str}), on="cod_mpio", how="left")
    base["es_choco"] = base["cod_dpto"] == "27"
    if "poblacion_total" in base and "ipm" in base:
        base["personas_pobres_ipm"] = (base["ipm"] / 100 * base["poblacion_total"]).round()
    if "poblacion_rural" in base and "poblacion_total" in base:
        base["pct_rural"] = 100 * base["poblacion_rural"] / base["poblacion_total"]
    base.to_csv(p / "base_municipal.csv", index=False)
    print(f"  base_municipal.csv: {len(base)} municipios × {base.shape[1]} columnas "
          f"({int(base['es_choco'].sum())} del Chocó)")
    return base


def procesar_todo() -> None:
    pasos = [
        ("IPM municipal 2018", procesar_ipm_municipal),
        ("NBI 2018", procesar_nbi),
        ("Población censo 2018", procesar_poblacion_censo),
        ("Proyecciones de población", procesar_proyecciones),
        ("IPM departamental", procesar_ipm_departamental),
        ("Saber 11", procesar_saber11),
        ("Tabla maestra", construir_base_municipal),
    ]
    for nombre, f in pasos:
        print(f"→ {nombre}", flush=True)
        f()
