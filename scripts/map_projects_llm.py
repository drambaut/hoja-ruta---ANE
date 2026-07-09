from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import config
from src.data_loader import load_csv
from src.llm_mapper import MAPPING_COLUMNS, map_projects_to_roadmap_with_gemini


def validate_columns(output_path: Path) -> None:
    df = load_csv(output_path)
    missing_columns = sorted(MAPPING_COLUMNS - set(df.columns))
    if missing_columns:
        raise ValueError(
            "mapeo_generado.csv no tiene las columnas esperadas: "
            + ", ".join(missing_columns)
        )

    if "codigo_proyecto" in df.columns:
        expected_projects = {f"ED{index:02d}" for index in range(1, 15)}
        found_projects = set(df["codigo_proyecto"].dropna().astype(str))
        missing_projects = sorted(expected_projects - found_projects)
        if missing_projects:
            print(
                "WARNING - No se encontraron filas para estos proyectos: "
                + ", ".join(missing_projects)
            )


def main() -> None:
    try:
        config.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        if not config.PROYECTOS_RAW_CSV.exists():
            raise FileNotFoundError("No se encontro data/raw/proyectos__raw.csv.")
        if not config.HOJA_RUTA_CSV.exists():
            raise FileNotFoundError(
                "No se encontro data/processed/hoja_ruta.csv. "
                "Ejecuta primero python scripts/extract_roadmap_llm.py."
            )

        print("Leyendo proyectos...")
        projects_df = load_csv(config.PROYECTOS_RAW_CSV)
        print("Leyendo hoja_ruta.csv...")
        roadmap_df = load_csv(config.HOJA_RUTA_CSV)

        print("Enviando tablas a Gemini...")
        map_projects_to_roadmap_with_gemini(
            projects_df,
            roadmap_df,
            config.MAPEO_GENERADO_CSV,
        )

        print("Guardando mapeo_generado.csv...")
        validate_columns(config.MAPEO_GENERADO_CSV)
        print("Mapeo finalizado.")
    except Exception as exc:
        print(f"ERROR - {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
