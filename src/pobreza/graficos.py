"""Estilo común de los gráficos y utilidades para guardarlos."""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

from .config import FIGURAS

# Colores: el Chocó siempre en el mismo color para que se reconozca en todos los gráficos.
CHOCO = "#0f7b6c"
RESTO = "#b9c0c8"
ACENTO = "#e07a2f"
NEUTRO = "#3d4a57"
DIMENSION_COLORES = {
    "Educación del hogar": "#4c72b0",
    "Niñez y juventud": "#dd8452",
    "Trabajo": "#55a868",
    "Salud": "#c44e52",
    "Vivienda y servicios": "#8172b3",
}


def estilo() -> None:
    mpl.rcParams.update({
        "figure.figsize": (10, 5.5),
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.titleweight": "bold",
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "font.size": 10.5,
        "legend.frameon": False,
    })


def guardar(fig, nombre: str) -> None:
    fig.savefig(FIGURAS / f"{nombre}.png")


def fuente(ax, texto: str) -> None:
    """Pie de figura con la fuente de los datos."""
    ax.annotate(f"Fuente: {texto}", xy=(0, -0.13), xycoords="axes fraction", fontsize=8.5, color="#6b7680",
                ha="left", va="top")
