# Estudio de pobreza multidimensional del Chocó

Este proyecto mide la pobreza en los 30 municipios del Chocó y la compara con el resto de Colombia. Usa
solo datos oficiales y abiertos del DANE y del ICFES. El análisis está en **notebooks de Jupyter**
(archivos `.ipynb`) escritos en Python, con las librerías pandas, numpy, matplotlib, seaborn, scipy,
statsmodels, scikit-learn y geopandas.

Esta guía está pensada para **Windows** y para quien **nunca ha usado Python**. Si sigue los pasos en orden,
el estudio le va a funcionar.

---

## ¿Solo quiere ver los resultados?

No tiene que instalar nada. Entre a la carpeta [`notebooks`](notebooks) aquí en GitHub y haga clic en
cualquier archivo `.ipynb`: GitHub lo muestra con las tablas y los gráficos ya calculados.

Los gráficos sueltos están en [`reportes/figuras`](reportes/figuras), y las tablas finales (fichas por
municipio y prioridades) en [`reportes`](reportes).

---

## Paso a paso en Windows

Le toma unos 20 minutos la primera vez. La mayor parte es esperar instalaciones.

### Paso 1. Instalar Python

1. Entre a <https://www.python.org/downloads/windows/> y descargue **Python 3.12** (el instalador de 64 bits,
   *Windows installer (64-bit)*).
2. Abra el instalador. **Antes de darle a instalar**, marque la casilla de abajo que dice
   **"Add python.exe to PATH"**. Este paso es el más importante: si no la marca, nada de lo que sigue funciona.
3. Haga clic en **Install Now** y espere a que termine.

### Paso 2. Instalar Git

Git sirve para descargar el proyecto y mantenerlo actualizado.

1. Entre a <https://git-scm.com/download/win> y descargue el instalador.
2. Instálelo dejando **todas las opciones como vienen** (solo dele *Next* hasta el final).

> **¿No quiere instalar Git?** Puede usar el botón verde **Code → Download ZIP** de esta página,
> descomprimir el ZIP en *Documentos* y seguir desde el paso 3. Solo tenga en cuenta que así no podrá
> actualizar el proyecto con un comando.

### Paso 3. Abrir la terminal (PowerShell)

La terminal es una ventana donde se escriben órdenes. Todo lo que está en los recuadros grises de esta guía
se copia y se pega ahí, y se ejecuta con **Enter**.

1. Oprima la tecla **Windows**, escriba `PowerShell` y ábralo.
2. Compruebe que Python quedó bien instalado:

   ```powershell
   python --version
   ```

   Debe salir algo como `Python 3.12.x`. Si sale un error, vaya a [Problemas comunes](#problemas-comunes).

### Paso 4. Descargar el proyecto

Vaya a su carpeta *Documentos* y descargue el proyecto ahí:

```powershell
cd $HOME\Documents
git clone https://github.com/Bello2005/Bello2005-estudio-PM-choco.git
cd Bello2005-estudio-PM-choco
```

> Si descargó el ZIP en el paso 2, en vez de esto solo entre a la carpeta que descomprimió, por ejemplo:
> `cd $HOME\Documents\Bello2005-estudio-PM-choco-main`

### Paso 5. Crear un entorno para el proyecto

Un *entorno virtual* es una caja aparte donde se instalan las librerías de este proyecto, para que no se
mezclen con nada más del computador.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si funcionó, al principio de la línea aparece **`(.venv)`** en verde. Eso indica que el entorno está activo.

> **¿Salió un error rojo que dice "la ejecución de scripts está deshabilitada"?** Es normal en Windows.
> Ejecute esto una sola vez, escriba `S` y Enter cuando le pregunte, y vuelva a intentar el paso 5:
>
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

### Paso 6. Instalar las librerías

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Esto descarga pandas, numpy, Jupyter y las demás librerías. Puede tardar entre 3 y 10 minutos según la
conexión. Al final no debe aparecer ninguna línea que empiece por `ERROR`.

### Paso 7. Descargar los datos oficiales

```powershell
python scripts\01_descargar.py
```

El programa baja los archivos del DANE y del ICFES a la carpeta `datos\crudos`. Al final debe decir algo como
`Listo: 10 bien, 0 con error`. Si alguna fuente opcional falla (por ejemplo, Saber 11), el estudio igual
funciona.

### Paso 8. Preparar las tablas

```powershell
python scripts\03_procesar.py
```

El programa convierte los Excel del DANE en tablas limpias dentro de `datos\procesados`. Debe terminar
con una línea como `base_municipal.csv: 1122 municipios ... (30 del Chocó)`.

### Paso 9. Abrir los notebooks

```powershell
jupyter lab
```

Se abre una pestaña en el navegador con Jupyter. Para usarlo:

1. A la izquierda, entre a la carpeta **`notebooks`**.
2. Abra **`01_fuentes_y_calidad.ipynb`** con doble clic.
3. En el menú de arriba elija **Run → Run All Cells**. Cada bloque se ejecuta y muestra su resultado debajo.
4. Siga con los demás notebooks **en orden** (del 01 al 06).

Para ejecutar un solo bloque, haga clic en él y oprima **Shift + Enter**.

### Paso 10. Cerrar y volver otro día

- **Para cerrar:** cierre la pestaña del navegador, vuelva a PowerShell y oprima **Ctrl + C**.
- **Para volver:** abra PowerShell y ejecute estas tres líneas (ya no hay que instalar nada):

  ```powershell
  cd $HOME\Documents\Bello2005-estudio-PM-choco
  .\.venv\Scripts\Activate.ps1
  jupyter lab
  ```

- **Para traer la última versión del proyecto** (solo si lo descargó con Git):

  ```powershell
  git pull
  ```

---

## Problemas comunes

| Lo que pasa | Qué hacer |
|---|---|
| `python` no se reconoce como comando | No se marcó **Add python.exe to PATH** en el paso 1. Vuelva a abrir el instalador de Python, elija *Modify*, marque esa opción y reinicie PowerShell. Mientras tanto, puede cambiar `python` por `py` en todos los comandos. |
| `git` no se reconoce como comando | Cierre y vuelva a abrir PowerShell después de instalar Git. Si sigue igual, use la opción del ZIP del paso 2. |
| Error rojo al activar el entorno (`Activate.ps1`) | Use el comando `Set-ExecutionPolicy` del paso 5. |
| No aparece `(.venv)` al inicio de la línea | El entorno no está activo. Ejecute `.\.venv\Scripts\Activate.ps1` estando dentro de la carpeta del proyecto. |
| `No module named pandas` (o cualquier otra librería) | Casi siempre es porque el entorno no está activo. Actívelo y repita el paso 6. |
| Una descarga falla en el paso 7 | Revise la conexión y vuelva a ejecutar el paso 7. El programa solo baja lo que falta. |
| En Jupyter sale `FileNotFoundError ... base_municipal.csv` | Faltan los pasos 7 y 8. Ejecútelos y vuelva a correr el notebook. |
| Jupyter pregunta qué *kernel* usar | Elija **Python 3 (ipykernel)**. |

---

## Otra opción: correrlo en GitHub, sin instalar nada

El proyecto trae un flujo de **GitHub Actions** que hace todo en los servidores de GitHub: descarga los
datos, los procesa, ejecuta los notebooks y guarda los resultados en el repositorio. Corre solo cada vez que
cambia el código y el día 1 de cada mes, y también se puede lanzar a mano en la pestaña **Actions →
Descargar datos y correr el estudio → Run workflow**.

El mismo flujo repite en una máquina **Windows** los pasos de esta guía, para comprobar que siguen
funcionando.

---

## Lo que encontró el estudio

| | Chocó | Resto del país |
|---|---|---|
| Mediana municipal del IPM (2018) | **68,2 %** | 40,8 % (mediana del país) |
| Municipios en el 25 % más pobre del país | **27 de 30** | — |
| IPM departamental 2025 | **30,8 %** | 9,9 % (nacional) |
| Veces más pobre que el país | 2,4 en 2018 → **3,1 en 2025** | — |

- **La brecha relativa crece.** El Chocó bajó su pobreza entre 2018 y 2025, pero el país lo hizo más rápido.
- **Agua y saneamiento son la brecha más grande.** El 68,5 % de los hogares no tiene fuente de agua mejorada,
  frente al 11,9 % en el resto del país.
- **No es solo ruralidad.** Frente a municipios igual de rurales y del mismo tamaño, un municipio del Chocó
  tiene unos **22,5 puntos más** de IPM.
- **La brecha educativa va más allá de la pobreza.** En Saber 11 (2017 y 2019), los colegios del Chocó sacan
  en promedio **22,8 puntos menos** de lo esperado para su nivel de IPM.
- **Las cabeceras también están rezagadas.** 16 de las 30 cabeceras chocoanas tienen más pobreza que la
  zona rural típica del país.
- **El resultado no depende de los pesos.** Con cuatro formas distintas de pesar los indicadores, el orden de
  los municipios casi no cambia.

---

## Qué hay en cada carpeta

```
notebooks\                     El análisis, para leer en orden
  01_fuentes_y_calidad           Qué se descargó y si los datos tienen sentido
  02_ipm_municipal_choco         Los 30 municipios, cabecera vs. zona rural, mapas
  03_dimensiones_e_indicadores   Las 15 privaciones y tipos de municipios
  04_choco_vs_pais_en_el_tiempo  Cómo ha cambiado la pobreza de 2018 a 2025
  05_ipm_nbi_y_educacion         NBI, Saber 11 y el "efecto Chocó"
  06_robustez_y_prioridades      Prioridades, simulaciones y ficha por municipio
scripts\                       Programas que se ejecutan en los pasos 7 y 8
src\pobreza\                   Código que usan los scripts y los notebooks
datos\crudos\                  Archivos originales descargados (no se suben a GitHub)
datos\procesados\              Tablas limpias que leen los notebooks
reportes\                      Gráficos y tablas finales
tests\                         Pruebas automáticas del código
```

## Cómo se mide la pobreza aquí

El **Índice de Pobreza Multidimensional (IPM)** revisa 15 carencias de los hogares, agrupadas en 5
dimensiones con el mismo peso: educación, niñez y juventud, trabajo, salud, y vivienda y servicios. Un
hogar es pobre si tiene al menos un tercio de esas carencias, contadas según su peso. Es el método
*Alkire-Foster*, el mismo que usa el DANE.

**Límites que conviene tener presentes:**

- Los datos por municipio son de 2018 (censo). Para años posteriores solo hay datos por departamento.
- Se trabajó con los porcentajes que publica el DANE por municipio, no hogar por hogar. Los notebooks dicen
  cuándo eso importa.
- Las comparaciones del notebook 5 muestran diferencias, pero no prueban qué las causa.

## Fuentes

- DANE — [Pobreza multidimensional municipal de fuente censal 2018](https://www.dane.gov.co/index.php/estadisticas-por-tema/pobreza-y-condiciones-de-vida/pobreza-y-desigualdad/medida-de-pobreza-multidimensional-de-fuente-censal)
- DANE — [Pobreza multidimensional nacional y departamental](https://www.dane.gov.co/index.php/estadisticas-por-tema/pobreza-y-condiciones-de-vida/pobreza-multidimensional)
- DANE — [Censo 2018: NBI y población](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/censo-nacional-de-poblacion-y-vivenda-2018/informacion-tecnica)
- DANE — [Proyecciones de población municipal](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion)
- ICFES, vía [datos.gov.co](https://www.datos.gov.co) — resultados de Saber 11
- DANE — Marco Geoestadístico Nacional 2018 (límites de los municipios)
