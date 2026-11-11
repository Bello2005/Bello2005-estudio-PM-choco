"""Catálogo de fuentes de datos del estudio.

Cada fuente tiene una o varias URL candidatas: si la primera falla (el DANE a veces mueve archivos),
se prueba la siguiente. Agregar una fuente nueva es agregar una entrada a FUENTES.
"""
from __future__ import annotations

from dataclasses import dataclass, field

SOCRATA = "https://www.datos.gov.co/resource/{id}.csv"


@dataclass(frozen=True)
class Fuente:
    clave: str
    nombre: str
    entidad: str
    archivo: str                      # nombre con el que se guarda en datos/crudos
    urls: tuple[str, ...]
    pagina: str = ""                  # página oficial donde se puede verificar a mano
    descripcion: str = ""
    obligatoria: bool = True          # si falla, el proceso avisa con error
    params: dict = field(default_factory=dict)  # parámetros GET (para APIs como Socrata)


DANE_POBREZA = "https://www.dane.gov.co/files/investigaciones/condiciones_vida/pobreza/2018/informacion-censal"
DANE_PM = "https://www.dane.gov.co/files/operaciones/PM"
DANE_CENSO = "https://www.dane.gov.co/files/censo2018/informacion-tecnica"
DANE_PROY = "https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Municipal"

FUENTES: list[Fuente] = [
    # --- Pobreza multidimensional -------------------------------------------------------------
    Fuente(
        clave="ipm_municipal_2018",
        nombre="Medida de pobreza multidimensional municipal de fuente censal 2018",
        entidad="DANE",
        archivo="ipm_municipal_2018.xlsx",
        urls=(f"{DANE_POBREZA}/anexo-censal-pobreza-municipal-2018.xlsx",),
        pagina="https://www.dane.gov.co/index.php/estadisticas-por-tema/pobreza-y-condiciones-de-vida/"
               "pobreza-y-desigualdad/medida-de-pobreza-multidimensional-de-fuente-censal",
        descripcion="IPM e indicadores por municipio, total, cabeceras y centros poblados y rural disperso.",
    ),
    Fuente(
        clave="ipm_departamental",
        nombre="Pobreza multidimensional departamental (ECV) — serie más reciente",
        entidad="DANE",
        archivo="ipm_departamental.xlsx",
        urls=(
            f"{DANE_PM}/anex-PMultidimensional-Departamental-2025.xlsx",
            f"{DANE_PM}/anex-PMultidimensional-Departamental-2024.xlsx",
        ),
        pagina="https://www.dane.gov.co/index.php/estadisticas-por-tema/pobreza-y-condiciones-de-vida/"
               "pobreza-multidimensional",
        descripcion="IPM e indicadores por departamento, serie anual desde 2018.",
    ),
    Fuente(
        clave="ipm_nacional",
        nombre="Pobreza multidimensional nacional (ECV)",
        entidad="DANE",
        archivo="ipm_nacional.xlsx",
        urls=(
            f"{DANE_PM}/anex-PMultidimensional-2025.xlsx",
            f"{DANE_PM}/anex-PMultidimensional-2024.xlsx",
        ),
        pagina="https://www.dane.gov.co/index.php/estadisticas-por-tema/pobreza-y-condiciones-de-vida/"
               "pobreza-multidimensional",
        descripcion="IPM nacional, cabeceras y rural, con desagregaciones (sexo del jefe, etnia, etc.).",
        obligatoria=False,
    ),
    Fuente(
        clave="ipm_pdet",
        nombre="IPM para municipios PDET",
        entidad="DANE",
        archivo="ipm_pdet.xlsx",
        urls=(f"{DANE_PM}/anex-PMPDET-2025.xlsx", f"{DANE_PM}/anex-PMPDET-2024.xlsx"),
        pagina="https://www.dane.gov.co/index.php/estadisticas-por-tema/pobreza-y-condiciones-de-vida/"
               "pobreza-multidimensional",
        descripcion="IPM de los municipios con Programas de Desarrollo con Enfoque Territorial.",
        obligatoria=False,
    ),
    # --- Censo 2018 -----------------------------------------------------------------------------
    Fuente(
        clave="nbi_2018",
        nombre="Necesidades Básicas Insatisfechas (NBI) — CNPV 2018",
        entidad="DANE",
        archivo="nbi_2018.xlsx",
        urls=(f"{DANE_CENSO}/CNPV-2018-NBI.xlsx",),
        pagina="https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/"
               "censo-nacional-de-poblacion-y-vivenda-2018/informacion-tecnica",
        descripcion="NBI y sus componentes por municipio y área.",
    ),
    Fuente(
        clave="poblacion_censo_2018",
        nombre="Población ajustada por cobertura — CNPV 2018",
        entidad="DANE",
        archivo="poblacion_censo_2018.xls",
        urls=(f"{DANE_CENSO}/CNPV-2018-Poblacion-Ajustada-por-Cobertura.xls",),
        pagina="https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/"
               "censo-nacional-de-poblacion-y-vivenda-2018/informacion-tecnica",
        descripcion="Población por municipio y área en 2018.",
    ),
    Fuente(
        clave="proyecciones_municipales",
        nombre="Proyecciones de población municipal por área",
        entidad="DANE",
        archivo="proyecciones_municipales.xlsx",
        urls=(
            f"{DANE_PROY}/DCD-area-proypoblacion-Mun-2018-2042-ActPostCOVID-19.xlsx",
            f"{DANE_PROY}/DCD-area-proypoblacion-Mun-2020-2035-ActPostCOVID-19.xlsx",
        ),
        pagina="https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/"
               "proyecciones-de-poblacion",
        descripcion="Población proyectada por municipio y área (para pasar de porcentajes a personas).",
        obligatoria=False,
    ),
    # --- Educación (datos.gov.co, API Socrata) ---------------------------------------------------
    # Se pide el promedio ya agrupado por municipio para no bajar millones de filas.
    Fuente(
        clave="saber11_2018",
        nombre="Saber 11 2018-2 (calendario A) — promedios por municipio del colegio",
        entidad="ICFES / datos.gov.co",
        archivo="saber11_2018_municipios.csv",
        urls=(SOCRATA.format(id="m2nt-jw2h"),),
        pagina="https://www.datos.gov.co/d/m2nt-jw2h",
        descripcion="Puntaje global promedio y número de estudiantes por municipio, 2018-2.",
        obligatoria=False,
        params={
            "$select": "cole_cod_mcpio_ubicacion as cod_mpio, avg(punt_global) as punt_global, "
                       "count(*) as estudiantes",
            "$group": "cole_cod_mcpio_ubicacion",
            "$limit": "5000",
        },
    ),
    # --- Geometrías -----------------------------------------------------------------------------
    Fuente(
        clave="mapa_municipios",
        nombre="Límites municipales (MGN 2018, DANE) en GeoJSON",
        entidad="DANE (copia pública en GitHub)",
        archivo="municipios_mgn2018.geojson",
        urls=(
            "https://raw.githubusercontent.com/caticoa3/colombia_mapa/master/co_2018_MGN_MPIO_POLITICO.geojson",
        ),
        pagina="https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/descarga-mgn-marco-geoestadistico-nacional/",
        descripcion="Polígonos simplificados de los municipios con código DIVIPOLA.",
        obligatoria=False,
    ),
    # --- Documentos de referencia ---------------------------------------------------------------
    Fuente(
        clave="nota_metodologica_ipm_censal",
        nombre="Nota metodológica — IPM municipal de fuente censal",
        entidad="DANE",
        archivo="nota_metodologica_ipm_censal_2018.pdf",
        urls=(f"{DANE_POBREZA}/nota-metodologia-censal-pobreza-municipal-2018.pdf",),
        obligatoria=False,
    ),
]

POR_CLAVE = {f.clave: f for f in FUENTES}
