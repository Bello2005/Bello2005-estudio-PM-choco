# Estudio de pobreza multidimensional del Chocó

Análisis reproducible de la pobreza multidimensional en los 30 municipios del Chocó frente al resto de
Colombia, con datos oficiales y abiertos: el **IPM municipal de fuente censal 2018** y la serie
**departamental 2018–2025** del DANE, junto con el NBI, la población del censo 2018 y Saber 11.

Todo se descarga, se procesa y se ejecuta solo, con **GitHub Actions**. No hace falta bajar nada a mano.

## Lo que encontramos

| | Chocó | Resto del país |
|---|---|---|
| Mediana municipal del IPM (2018) | **68,2 %** | 40,8 % (mediana del país) |
| Municipios en el 25 % más pobre del país | **27 de 30** | — |
| IPM departamental 2025 (ECV) | **30,8 %** | 9,9 % (nacional) |
| Razón Chocó ÷ nacional | 2,4 en 2018 → **3,1 en 2025** | — |

- **La brecha relativa crece.** Entre 2018 y 2025 el IPM del Chocó bajó de 46,3 % a 30,8 %, pero el
  país mejoró más rápido en proporción: en 2018 el Chocó era 2,4 veces más pobre que el promedio nacional
  y en 2025 es 3,1 veces.
- **Agua y saneamiento son la brecha más grande.** Sin fuente de agua mejorada: 68,5 % de los hogares
  del Chocó frente a 11,9 % en el resto del país. Eliminación inadecuada de excretas: 72,4 % frente a 13,3 %.
- **No es solo ruralidad.** Si se compara con municipios igual de rurales y del mismo tamaño, un municipio
  del Chocó sigue teniendo unos **22,5 puntos más de IPM** (IC 95 %: 19,8–25,2).
- **Las cabeceras también están rezagadas.** 16 de las 30 cabeceras chocoanas tienen más pobreza que la
  zona rural típica del país.
- **El resultado no depende de los pesos.** Con cuatro esquemas de pesos distintos, el orden de los
  municipios cambia muy poco (correlación de Spearman ≥ 0,95).

Las cifras salen de los notebooks y se actualizan solas si el DANE publica datos nuevos.

## Cómo está organizado

```
notebooks/                 Análisis, en orden
  01_fuentes_y_calidad         Qué se descargó, cobertura y pruebas de coherencia
  02_ipm_municipal_choco       Ranking, cabecera vs. rural, personas pobres y mapas
  03_dimensiones_e_indicadores Las 15 privaciones, brechas, aportes y tipologías de municipios
  04_choco_vs_pais_en_el_tiempo Serie 2018–2025: incidencia, intensidad y cada indicador
  05_ipm_nbi_y_educacion       IPM vs. NBI, Saber 11 y el "efecto Chocó" (regresión)
  06_robustez_y_prioridades    Pesos alternativos, matriz de prioridades, simulación y fichas
src/pobreza/               Código reutilizable
  fuentes.py                   Catálogo de fuentes (URLs oficiales)
  descarga.py                  Descarga con reintentos y manifiesto (tamaño y SHA-256)
  lectura.py / procesar.py     Lectura tolerante de los anexos en Excel del DANE → tablas limpias
  ipm.py                       Método Alkire-Foster y aproximaciones con datos agregados
scripts/                   01_descargar · 02_inspeccionar · 03_procesar
datos/procesados/          Tablas limpias (CSV) que usan los notebooks
reportes/                  Figuras y tablas finales (fichas por municipio, prioridades)
tests/                     Pruebas (pytest)
```

Los archivos originales del DANE no se guardan en `main`. Cada corrida deja una copia en la rama
`datos-crudos`, con el manifiesto de qué se bajó, de dónde y cuándo.

## Cómo correrlo

**En GitHub (recomendado):** pestaña *Actions* → *Descargar datos y correr el estudio* → *Run workflow*.
También corre solo cada vez que cambia el código y el día 1 de cada mes.

**En un computador:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/01_descargar.py     # baja las fuentes a datos/crudos
python scripts/03_procesar.py      # arma las tablas en datos/procesados
jupyter lab notebooks/
```

## Método, en corto

El IPM de Colombia sigue el método de **Alkire-Foster**: 5 dimensiones con el mismo peso (educación del
hogar, niñez y juventud, trabajo, salud, vivienda y servicios) y 15 indicadores. Un hogar es pobre si
está privado en al menos el 33,3 % de los indicadores ponderados.

La medida municipal de 2018 la calculó el DANE con el censo y con registros administrativos para salud
(BDUA) y empleo formal (PILA). En el trabajo se usa la **tasa de dependencia económica** en lugar del
desempleo de larga duración.

Con porcentajes municipales no se puede calcular la intensidad ni las contribuciones exactas por
municipio, porque para eso hay que saber qué privaciones tiene a la vez cada hogar. Por eso los notebooks
usan el **puntaje promedio de privación** (Σ peso × % privado) y lo dicen en cada caso. La función
`ipm.alkire_foster` hace el cálculo exacto cuando hay microdatos, y está probada en `tests/`.

## Límites

- Los datos municipales son de 2018. La evolución posterior solo existe a nivel departamental.
- El censo 2018 tuvo omisión alta en zonas rurales del Chocó.
- Las regresiones del notebook 5 describen diferencias; no prueban causas.

## Fuentes

- DANE — [Medida de pobreza multidimensional municipal de fuente censal 2018](https://www.dane.gov.co/index.php/estadisticas-por-tema/pobreza-y-condiciones-de-vida/pobreza-y-desigualdad/medida-de-pobreza-multidimensional-de-fuente-censal)
- DANE — [Pobreza multidimensional (ECV), anexos nacional y departamental](https://www.dane.gov.co/index.php/estadisticas-por-tema/pobreza-y-condiciones-de-vida/pobreza-multidimensional)
- DANE — [CNPV 2018: NBI y población ajustada por cobertura](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/censo-nacional-de-poblacion-y-vivenda-2018/informacion-tecnica)
- DANE — [Proyecciones de población municipal](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion)
- ICFES vía [datos.gov.co](https://www.datos.gov.co) — Saber 11
- DANE — Marco Geoestadístico Nacional 2018 (límites municipales)
