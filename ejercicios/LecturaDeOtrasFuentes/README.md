# Ejercicio: Importación de Vehículos — Portal SAT Guatemala

## Repositorio: https://github.com/AscencioSIUU/dataScience.git

Fuente: [Portal SAT — Alza e Importación de Vehículos](https://portal.sat.gob.gt/portal/alza-e-importacion-vehiculos/)

## Enunciado

Construir un pipeline automatizado que:

1. Descargue los archivos `.zip` con los datos de importación de vehículos de todo 2025 y los meses disponibles de 2026 directamente del Portal SAT.
2. Descomprima y guarde los archivos en la carpeta `Datos/`.
3. Lea los archivos de texto y cree un conjunto de datos unificado.
4. Guarde el conjunto de datos en `Datos/importacion_vehiculos_2025_2026.csv`.

Luego, en el notebook `exploracion.ipynb`, responder:

1. ¿Cuántos vehículos livianos de cada tipo se importaron en 2025?
2. ¿Cuál es la distribución de modelos (año) de carros, pickups y SUV importados en 2025?
3. ¿Cuál es el tipo de vehículo que más se importó el año pasado?
4. ¿Cuáles son los meses en los que más se importan vehículos livianos?
5. ¿Cómo van las importaciones por tipo de vehículo en 2026 (enero–junio) vs. el mismo período de 2025?

## Ejecución

```bash
# 1. Crear y activar entorno virtual (una sola vez)
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# 2. Instalar dependencias dentro del venv
pip install -r requirements.txt

# 3. Descargar y unificar datos (crea Datos/ automáticamente)
python descargar_datos.py

# 4. Exploración
jupyter notebook exploracion.ipynb
```

> Para salir del venv cuando termines: `deactivate`

## Archivos

| Archivo | Descripción |
|---|---|
| `descargar_datos.py` | Descarga, extrae y unifica los datos del SAT → CSV |
| `exploracion.ipynb` | Análisis exploratorio con tablas y gráficas |
| `Datos/` | Datos generados (ignorado por git) |
