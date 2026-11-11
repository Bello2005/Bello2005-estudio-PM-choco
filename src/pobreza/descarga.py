"""Descarga de las fuentes del catálogo, con reintentos y un manifiesto de lo bajado."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from .config import CRUDOS
from .fuentes import FUENTES, Fuente

MANIFIESTO = CRUDOS / "manifiesto.json"
CABECERAS = {
    # Algunos servidores del Estado rechazan clientes sin navegador conocido.
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) pobreza-choco/1.0 (+https://github.com/Bello2005/Bello2005-estudio-PM-choco)",
    "Accept": "*/*",
}


def _sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _parece_html(ruta: Path) -> bool:
    """Un .xlsx que en realidad es una página de error HTML."""
    with ruta.open("rb") as f:
        inicio = f.read(512).lstrip().lower()
    return inicio.startswith(b"<!doctype html") or inicio.startswith(b"<html")


def descargar_fuente(fuente: Fuente, forzar: bool = False, intentos: int = 3) -> dict:
    destino = CRUDOS / fuente.archivo
    if destino.exists() and destino.stat().st_size > 0 and not forzar:
        return {"clave": fuente.clave, "estado": "ya estaba", "archivo": fuente.archivo,
                "bytes": destino.stat().st_size, "sha256": _sha256(destino)}

    errores = []
    for url in fuente.urls:
        for intento in range(1, intentos + 1):
            try:
                with requests.get(url, params=fuente.params or None, headers=CABECERAS,
                                  timeout=(20, 300), stream=True) as r:
                    r.raise_for_status()
                    tmp = destino.with_suffix(destino.suffix + ".part")
                    with tmp.open("wb") as f:
                        for bloque in r.iter_content(1 << 20):
                            f.write(bloque)
                if tmp.stat().st_size == 0:
                    raise ValueError("archivo vacío")
                if destino.suffix not in (".csv", ".geojson", ".json") and _parece_html(tmp):
                    raise ValueError("el servidor devolvió una página HTML en vez del archivo")
                tmp.replace(destino)
                return {"clave": fuente.clave, "estado": "descargado", "archivo": fuente.archivo, "url": r.url,
                        "bytes": destino.stat().st_size, "sha256": _sha256(destino),
                        "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            except Exception as e:  # noqa: BLE001 — se registra y se prueba lo siguiente
                errores.append(f"{url} (intento {intento}): {e}")
                if "/resource/" in url and "400" in str(e):
                    # Consulta mal armada para este conjunto: se muestran sus columnas para poder corregirla.
                    try:
                        muestra = requests.get(url, params={"$limit": 1}, headers=CABECERAS, timeout=60)
                        errores.append(f"   columnas disponibles: {muestra.text.splitlines()[0][:600]}")
                    except Exception:  # noqa: BLE001
                        pass
                    break
                time.sleep(2 * intento)
    return {"clave": fuente.clave, "estado": "error", "archivo": fuente.archivo, "errores": errores}


def descargar_todo(claves: list[str] | None = None, forzar: bool = False) -> list[dict]:
    fuentes = [f for f in FUENTES if claves is None or f.clave in claves]
    previo = json.loads(MANIFIESTO.read_text()) if MANIFIESTO.exists() else {}
    resultados = []
    for f in fuentes:
        print(f"→ {f.clave}: {f.nombre}", flush=True)
        res = descargar_fuente(f, forzar=forzar)
        res["obligatoria"] = f.obligatoria
        print(f"   {res['estado']}" + (f" ({res.get('bytes', 0) / 1e6:.2f} MB)" if "bytes" in res else ""), flush=True)
        for err in res.get("errores", []):
            print(f"   ✗ {err}", flush=True)
        datos = {k: v for k, v in res.items() if k not in ("estado", "obligatoria")}
        if res["estado"] == "descargado":
            previo[f.clave] = datos
        elif res["estado"] == "ya estaba":
            previo.setdefault(f.clave, datos)
        resultados.append(res)
    MANIFIESTO.write_text(json.dumps(previo, indent=2, ensure_ascii=False))
    return resultados
