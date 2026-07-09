from pathlib import Path

import pandas as pd

from src.data_loader import save_csv
from src.gemini_client import generate_text
from src.preprocessing import csv_text_to_dataframe, extract_text_from_pdf


ROADMAP_COLUMNS = {
    "id_actividad",
    "linea_hoja_ruta",
    "actividad",
    "horizonte",
    "responsable_sugerido",
    "fuente",
    "observaciones",
}

MAPPING_COLUMNS = {
    "codigo_proyecto",
    "nombre_proyecto",
    "linea_hoja_ruta",
    "actividad_hoja_ruta_relacionada",
    "tipo_relacion",
    "estado_mapeo",
    "decision_vigencia",
    "nivel_confianza_mapeo",
    "justificacion",
    "vigencia",
}


def _warn_missing_columns(df: pd.DataFrame, expected_columns: set[str], label: str) -> None:
    missing_columns = sorted(expected_columns - set(df.columns))
    if missing_columns:
        print(f"WARNING - {label}: faltan columnas esperadas: {', '.join(missing_columns)}.")


def extract_roadmap_from_pdf_with_gemini(
    pdf_path: Path,
    output_path: Path,
) -> pd.DataFrame:
    """
    1. Extrae texto del PDF.
    2. Construye un prompt para Gemini.
    3. Gemini devuelve CSV estructurado.
    4. Guarda data/processed/hoja_ruta.csv.
    5. Devuelve DataFrame.
    """
    pdf_text = extract_text_from_pdf(pdf_path)
    prompt = f"""Eres un asistente experto en estructuracion de documentos institucionales.

Recibiras el texto extraido de un PDF llamado "Estrategia de gestion de datos SGP_VF.pdf".
Tu tarea es extraer unicamente las actividades de la hoja de ruta.

Busca la seccion relacionada con:
- Hoja de ruta 2026-2028
- Actividades
- Arquitectura, integracion y almacenamiento de datos
- Gobernanza de datos
- Analitica de datos
- Optimizacion
- Cultura organizacional en torno a la gestion de datos

Devuelve SOLO un CSV valido, sin markdown y sin explicacion, con estas columnas:

id_actividad,linea_hoja_ruta,actividad,horizonte,responsable_sugerido,fuente,observaciones

Reglas:
1. Extrae unicamente actividades de la hoja de ruta.
2. No inventes actividades.
3. Conserva el sentido del texto original.
4. Si no identificas responsable, pon "No identificado".
5. Si no identificas horizonte, pon "No identificado".
6. En fuente pon "PDF hoja de ruta".
7. En observaciones pon una frase corta o "Sin observaciones".
8. Se esperan aproximadamente 29 actividades.
9. El resultado debe ser CSV valido.
10. No uses saltos de linea dentro de una celda.
11. No devuelvas markdown.
12. No agregues texto antes ni despues del CSV.
13. Todas las celdas deben estar entre comillas dobles.
14. Si una celda contiene comillas dobles, escapalas duplicandolas.

Texto del PDF:
{pdf_text}
"""
    response_text = generate_text(prompt)
    df = csv_text_to_dataframe(response_text)
    _warn_missing_columns(df, ROADMAP_COLUMNS, "Hoja de ruta")

    activity_count = len(df)
    if activity_count < 24 or activity_count > 34:
        print(
            f"Gemini devolvio {activity_count} actividades; se esperaban aproximadamente 29."
        )

    save_csv(df, output_path)
    return df


def map_projects_to_roadmap_with_gemini(
    projects_df: pd.DataFrame,
    roadmap_df: pd.DataFrame,
    output_path: Path,
) -> pd.DataFrame:
    """
    1. Convierte proyectos y hoja de ruta a texto CSV.
    2. Construye prompt para Gemini.
    3. Gemini devuelve CSV con el mapeo.
    4. Guarda data/processed/mapeo_generado.csv.
    5. Devuelve DataFrame.
    """
    if projects_df.empty:
        raise ValueError("El DataFrame de proyectos esta vacio.")
    if roadmap_df.empty:
        raise ValueError("El DataFrame de hoja de ruta esta vacio.")

    projects_csv = projects_df.to_csv(index=False)
    roadmap_csv = roadmap_df.to_csv(index=False)
    prompt = f"""Eres un asistente experto en planeacion institucional, analisis de proyectos y hojas de ruta.

Recibiras dos tablas:

1. Proyectos crudos ED01-ED14.
2. Actividades de la hoja de ruta SGP.

Tu tarea es mapear cada proyecto contra la hoja de ruta para identificar:
- si se alinea con alguna linea o actividad;
- si la relacion es clara, parcial o requiere validacion;
- que queda por fuera;
- que podria pasar a la siguiente vigencia.

IMPORTANTE:
No evalues avance tecnico.
No entres al detalle de tareas internas.
No inventes informacion.
Usa unicamente objetivo, alcance, descripcion, evidencia disponible y observaciones de los proyectos.
Si no hay suficiente informacion, marca "Por validar".

Devuelve SOLO un CSV valido, sin markdown ni explicacion, con estas columnas:

codigo_proyecto,nombre_proyecto,linea_hoja_ruta,actividad_hoja_ruta_relacionada,tipo_relacion,estado_mapeo,decision_vigencia,nivel_confianza_mapeo,justificacion,vigencia

Valores permitidos:

tipo_relacion:
- Directa
- Parcial
- Inferida
- Sin informacion
- No relacionada

estado_mapeo:
- Mapeado
- Mapeo parcial
- Por validar
- Por fuera
- Siguiente vigencia

decision_vigencia:
- Se mantiene
- Pasa a siguiente vigencia
- Requiere validacion
- Por fuera de la hoja de ruta

nivel_confianza_mapeo:
- Alta
- Media
- Baja

Reglas:
1. Debe aparecer al menos una fila por cada proyecto ED01-ED14.
2. Si un proyecto se relaciona con varias lineas de la hoja de ruta, puedes crear varias filas para el mismo proyecto.
3. Si un proyecto no tiene informacion suficiente, crea una fila con:
   - linea_hoja_ruta: "Sin informacion suficiente"
   - actividad_hoja_ruta_relacionada: "No identificada"
   - tipo_relacion: "Sin informacion"
   - estado_mapeo: "Por validar"
   - decision_vigencia: "Requiere validacion"
   - nivel_confianza_mapeo: "Baja"
4. Si un proyecto no se relaciona con la hoja de ruta, marca "Por fuera".
5. La justificacion debe tener maximo una frase.
6. No uses saltos de linea dentro de una celda.
7. No devuelvas markdown.
8. No agregues texto antes ni despues del CSV.
9. Todas las celdas deben estar entre comillas dobles.
10. Si una celda contiene comillas dobles, escapalas duplicandolas.

Tabla de proyectos:
{projects_csv}

Tabla de hoja de ruta:
{roadmap_csv}
"""
    response_text = generate_text(prompt)
    df = csv_text_to_dataframe(response_text)
    _warn_missing_columns(df, MAPPING_COLUMNS, "Mapeo generado")
    save_csv(df, output_path)
    return df


def extract_roadmap_from_pdf(pdf_path: Path) -> pd.DataFrame:
    raise NotImplementedError(
        "Usa extract_roadmap_from_pdf_with_gemini(pdf_path, output_path)."
    )


def map_projects_to_roadmap(
    projects_df: pd.DataFrame,
    roadmap_df: pd.DataFrame,
) -> pd.DataFrame:
    raise NotImplementedError(
        "Usa map_projects_to_roadmap_with_gemini(projects_df, roadmap_df, output_path)."
    )
