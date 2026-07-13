import os
import re
import zipfile
import io

import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
URL_SAT = "https://portal.sat.gob.gt/portal/alza-e-importacion-vehiculos/"
ANIOS_OBJETIVO = (2025, 2026)
CARPETA_DATOS = "Datos"
ARCHIVO_CSV = os.path.join(CARPETA_DATOS, "importacion_vehiculos_2025_2026.csv")

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

# Evita que SAT devuelva 403 (bloquea user-agents genéricos)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# ---------------------------------------------------------------------------
# 1. Obtener enlaces de descarga desde la página del SAT
# ---------------------------------------------------------------------------
def obtener_enlaces(anios=ANIOS_OBJETIVO):
    """
    Extrae del HTML del portal SAT las URLs de descarga de importación de vehículos
    para los años indicados. Devuelve lista de (anio, num_mes, url).
    """
    resp = requests.get(URL_SAT, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    # Patrón: href="https://portal.sat.gob.gt/portal/descarga/5030/.../importacion_de_vehiculos_ANIO_MES"
    # El href termina en comilla — garantiza URL completa sin truncar
    patron = re.compile(
        r'href="(https://portal\.sat\.gob\.gt/portal/descarga/5030/importacion-de-vehiculos/\d+/'
        r'importacion_de_vehiculos_(\d{4})_([a-z]+))"'
    )
    vistos = set()
    enlaces = []
    for url, anio_str, mes_str in patron.findall(resp.text):
        anio = int(anio_str)
        clave = (anio, mes_str)
        if anio in anios and mes_str in MESES_ES and clave not in vistos:
            vistos.add(clave)
            enlaces.append((anio, MESES_ES[mes_str], url))

    # Orden cronológico
    enlaces.sort(key=lambda x: (x[0], x[1]))
    return enlaces


# ---------------------------------------------------------------------------
# 2. Descargar un ZIP y extraer el TXT interno
# ---------------------------------------------------------------------------
def descargar_y_extraer(url, anio, mes):
    """
    Descarga el ZIP de la URL dada y extrae el .txt a CARPETA_DATOS.
    Es idempotente: si el .txt ya existe, omite la descarga.
    Devuelve la ruta al archivo .txt extraído.
    """
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    nombre_zip = f"importacion_vehiculos_{anio}_{mes:02d}.zip"
    ruta_zip = os.path.join(CARPETA_DATOS, nombre_zip)

    # Verificar si ya se extrajo (evita re-descargar en corridas posteriores)
    # ponytail: idempotencia barata — basta con buscar el txt ya extraído
    patron_txt = re.compile(rf".*{anio}.*{mes:02d}.*\.txt|.*{anio}.*\.txt", re.IGNORECASE)
    txt_existente = next(
        (os.path.join(CARPETA_DATOS, f) for f in os.listdir(CARPETA_DATOS)
         if f.endswith(".txt") and str(anio) in f and nombre_zip.replace(".zip", "") in f),
        None,
    )

    # Búsqueda más simple: cualquier txt que ya estuviera del mes/año
    txts = [f for f in os.listdir(CARPETA_DATOS) if f.endswith(".txt")]
    txt_mes = next((t for t in txts if str(anio) in t and f"{mes:02d}" in t), None)
    # El nombre interno del zip tiene fecha de proceso, no mes — guardamos el zip
    # y buscamos el txt ya extraído en el zip anterior si lo hay.
    # Usamos el zip como marcador: si existe el zip, ya descargamos.
    if os.path.exists(ruta_zip):
        # Extraer si no hay txt aún
        with zipfile.ZipFile(ruta_zip) as zf:
            nombres = zf.namelist()
            txt_name = next((n for n in nombres if n.endswith(".txt")), None)
            if txt_name:
                ruta_txt = os.path.join(CARPETA_DATOS, f"imp_{anio}_{mes:02d}.txt")
                if not os.path.exists(ruta_txt):
                    data = zf.read(txt_name)
                    with open(ruta_txt, "wb") as f:
                        f.write(data)
                return ruta_txt

    print(f"  Descargando {anio}-{mes:02d}...", end=" ", flush=True)
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()

    # Guardar zip
    with open(ruta_zip, "wb") as f:
        f.write(resp.content)

    # Extraer txt con nombre predecible
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        txt_name = next((n for n in zf.namelist() if n.endswith(".txt")), None)
        if not txt_name:
            raise ValueError(f"No se encontró .txt en el ZIP de {anio}-{mes:02d}")
        data = zf.read(txt_name)
        ruta_txt = os.path.join(CARPETA_DATOS, f"imp_{anio}_{mes:02d}.txt")
        with open(ruta_txt, "wb") as f:
            f.write(data)

    print("OK")
    return ruta_txt


# ---------------------------------------------------------------------------
# 3. Leer un TXT y devolver DataFrame con columnas extra de año/mes
# ---------------------------------------------------------------------------
def leer_txt(ruta, anio, mes):
    """
    Lee el archivo pipe-delimited (Latin-1) y agrega columnas anio_archivo y mes_archivo.
    """
    # Los archivos del SAT tienen trailing | en cada fila de datos pero no en el header.
    # Eso hace que pandas desplace todas las columnas +1 (interpreta col[0] como índice).
    # ponytail: stripeamos el trailing | antes de parsear — más simple que index_col tricks.
    with open(ruta, "rb") as f:
        content = f.read().decode("latin-1")
    cleaned = "\n".join(line.rstrip("|") for line in content.splitlines())

    df = pd.read_csv(
        io.StringIO(cleaned),
        sep="|",
        dtype=str,
        on_bad_lines="skip",   # algunas filas del SAT tienen un campo extra (datos corruptos)
    )

    # Limpiar nombres de columna (el SAT deja espacios)
    df.columns = df.columns.str.strip()

    # Columna de fecha a datetime
    if "Fecha de la Poliza" in df.columns:
        df["Fecha de la Poliza"] = pd.to_datetime(
            df["Fecha de la Poliza"].str.strip(), dayfirst=True, errors="coerce"
        )

    # Normalizar texto en columnas clave (strip + mayúsculas)
    for col in ["Distintivo", "Tipo de Vehiculo", "Marca", "Linea", "Modelo del Vehiculo"]:
        if col in df.columns:
            df[col] = df[col].str.strip().str.upper()

    # Columnas de identificación temporal confiable
    df["anio_archivo"] = anio
    df["mes_archivo"] = mes

    return df


# ---------------------------------------------------------------------------
# 4. Pipeline principal
# ---------------------------------------------------------------------------
def main():
    print("=== Importación de Vehículos SAT — Pipeline de Datos ===\n")

    print("Obteniendo enlaces del portal SAT...")
    enlaces = obtener_enlaces()
    print(f"  Encontrados {len(enlaces)} archivos: {[(a, m) for a, m, _ in enlaces]}\n")

    if not enlaces:
        raise RuntimeError("No se encontraron enlaces. Verificar conectividad o cambios en la página SAT.")

    print("Descargando y extrayendo archivos:")
    frames = []
    for anio, mes, url in enlaces:
        ruta_txt = descargar_y_extraer(url, anio, mes)
        df = leer_txt(ruta_txt, anio, mes)
        frames.append(df)

    print("\nUnificando datos...")
    datos = pd.concat(frames, ignore_index=True)

    print(f"Guardando CSV en '{ARCHIVO_CSV}'...")
    datos.to_csv(ARCHIVO_CSV, index=False, encoding="utf-8")

    # -----------------------------------------------------------------------
    # Auto-chequeo básico
    # -----------------------------------------------------------------------
    meses_2025 = datos[datos["anio_archivo"] == 2025]["mes_archivo"].nunique()
    meses_2026 = datos[datos["anio_archivo"] == 2026]["mes_archivo"].nunique()
    assert meses_2025 == 12, f"Se esperaban 12 meses de 2025, hay {meses_2025}"
    assert meses_2026 >= 1, f"Se esperaba al menos 1 mes de 2026, hay {meses_2026}"
    # 17 columnas originales + anio_archivo + mes_archivo = 19 total
    assert len(datos.columns) >= 17, f"Columnas inesperadas: {list(datos.columns)}"

    print(f"\n✓ Dataset unificado: {len(datos):,} filas, {len(datos.columns)} columnas")
    print(f"  2025: {meses_2025} meses  |  2026: {meses_2026} meses")
    print(f"  Guardado en: {ARCHIVO_CSV}")


if __name__ == "__main__":
    main()
