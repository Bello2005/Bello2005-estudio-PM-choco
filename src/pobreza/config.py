"""Rutas y constantes compartidas por los scripts y los notebooks.

Todas las rutas salen de la raíz del repo. Se pueden cambiar con variables de entorno:

- POBREZA_DATOS: carpeta de datos (por defecto ./datos)
"""
from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATOS = Path(os.environ.get("POBREZA_DATOS", RAIZ / "datos")).resolve()
CRUDOS = DATOS / "crudos"          # tal cual se descargan (no van a git)
PROCESADOS = DATOS / "procesados"  # tablas limpias y ordenadas (sí van a git, son pequeñas)
REPORTES = RAIZ / "reportes"       # figuras y tablas finales
FIGURAS = REPORTES / "figuras"

for _d in (CRUDOS, PROCESADOS, FIGURAS):
    _d.mkdir(parents=True, exist_ok=True)

# Código DIVIPOLA del Chocó
COD_CHOCO = "27"
NOMBRE_CHOCO = "Chocó"

# Departamentos de la región Pacífica (para comparar con vecinos parecidos)
PACIFICO = {"27": "Chocó", "76": "Valle del Cauca", "19": "Cauca", "52": "Nariño"}

# Dimensiones e indicadores del IPM (DANE). Mismos pesos en la medida municipal de fuente censal 2018.
# Cada dimensión pesa 0,2; dentro de cada dimensión el peso se reparte por igual.
IPM_INDICADORES: dict[str, tuple[str, float]] = {
    # clave: (dimensión, peso)
    "analfabetismo": ("Educación del hogar", 0.10),
    "bajo_logro_educativo": ("Educación del hogar", 0.10),
    "barreras_primera_infancia": ("Niñez y juventud", 0.05),
    "inasistencia_escolar": ("Niñez y juventud", 0.05),
    "rezago_escolar": ("Niñez y juventud", 0.05),
    "trabajo_infantil": ("Niñez y juventud", 0.05),
    "dependencia_economica": ("Trabajo", 0.10),
    "empleo_informal": ("Trabajo", 0.10),
    "sin_aseguramiento_salud": ("Salud", 0.10),
    "barreras_acceso_salud": ("Salud", 0.10),
    "sin_acueducto": ("Vivienda y servicios", 0.04),
    "sin_alcantarillado": ("Vivienda y servicios", 0.04),
    "pisos_inadecuados": ("Vivienda y servicios", 0.04),
    "paredes_inadecuadas": ("Vivienda y servicios", 0.04),
    "hacinamiento_critico": ("Vivienda y servicios", 0.04),
}
IPM_CORTE_K = 1 / 3  # un hogar es pobre si está privado en al menos el 33,3 % de los indicadores ponderados

DIMENSIONES = list(dict.fromkeys(d for d, _ in IPM_INDICADORES.values()))

# Nombres legibles para gráficos
ETIQUETAS = {
    "analfabetismo": "Analfabetismo",
    "bajo_logro_educativo": "Bajo logro educativo",
    "barreras_primera_infancia": "Barreras primera infancia",
    "inasistencia_escolar": "Inasistencia escolar",
    "rezago_escolar": "Rezago escolar",
    "trabajo_infantil": "Trabajo infantil",
    "dependencia_economica": "Dependencia económica",
    "empleo_informal": "Empleo informal",
    "sin_aseguramiento_salud": "Sin aseguramiento en salud",
    "barreras_acceso_salud": "Barreras de acceso a salud",
    "sin_acueducto": "Sin fuente de agua mejorada",
    "sin_alcantarillado": "Eliminación inadecuada de excretas",
    "pisos_inadecuados": "Pisos inadecuados",
    "paredes_inadecuadas": "Paredes inadecuadas",
    "hacinamiento_critico": "Hacinamiento crítico",
}
