from __future__ import annotations

import streamlit as st

from src import config
from src.dashboard import (
    render_cobertura_lineas_chart,
    render_decision_vigencia_chart,
    render_estado_mapeo_chart,
    render_kpis,
    render_matriz_proyecto_linea,
    render_tabla_respaldo,
)
from src.data_loader import file_exists, load_csv


st.set_page_config(
    page_title="Mapa de alineacion ED01-ED14 vs Hoja de Ruta SGP",
    layout="wide",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stAppViewContainer"] > .main {padding-top: 1.4rem;}
        .block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1440px;}
        h1 {letter-spacing: 0;}
        .subtitle {font-size: 1.05rem; color: #4B5563; margin-top: -0.4rem;}
        .note {
            color: #5F6B7A;
            background: #F6F8FA;
            border: 1px solid #E4E7EC;
            padding: 0.75rem 0.9rem;
            border-radius: 8px;
            margin: 0.8rem 0 1rem 0;
        }
        .kpi-card {
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 0.8rem 0.9rem;
            background: #FFFFFF;
            min-height: 88px;
        }
        .kpi-label {
            color: #667085;
            font-size: 0.82rem;
            line-height: 1.2;
            min-height: 2.1rem;
        }
        .kpi-value {
            color: #101828;
            font-size: 1.75rem;
            font-weight: 700;
            line-height: 1.1;
        }
        .matrix-wrap {
            width: 100%;
            overflow-x: auto;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            background: white;
        }
        .matrix-table {
            border-collapse: collapse;
            width: 100%;
            min-width: 960px;
            font-size: 0.78rem;
        }
        .matrix-table th {
            position: sticky;
            left: 0;
            z-index: 1;
            background: #F9FAFB;
            color: #344054;
            border: 1px solid #E5E7EB;
            padding: 0.45rem;
            vertical-align: middle;
            min-width: 86px;
        }
        .matrix-table thead th {
            position: static;
            min-width: 150px;
        }
        .matrix-table td {
            border: 1px solid #E5E7EB;
            color: #FFFFFF;
            font-weight: 600;
            text-align: center;
            padding: 0.45rem;
            min-width: 150px;
            max-width: 220px;
            overflow-wrap: anywhere;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.title("Mapa de alineación ED01-ED14 vs Hoja de Ruta SGP")
    st.markdown(
        '<div class="subtitle">Vista ejecutiva para identificar proyectos alineados, '
        "pendientes de validacion, elementos por fuera y candidatos a siguiente vigencia.</div>",
        unsafe_allow_html=True,
    )


def render_missing_processed_file() -> None:
    st.info(
        "No se encontro data/processed/mapeo_generado.csv.\n\n"
        "Ejecuta primero:\n\n"
        "```bash\npython scripts/run_pipeline.py\n```"
    )


def render_dashboard(df_mapeo) -> None:
    render_kpis(df_mapeo)
    st.divider()

    col_left, col_right = st.columns(2)
    with col_left:
        render_estado_mapeo_chart(df_mapeo)
    with col_right:
        render_cobertura_lineas_chart(df_mapeo)

    st.divider()
    render_matriz_proyecto_linea(df_mapeo)

    st.divider()
    render_decision_vigencia_chart(df_mapeo)

    st.divider()
    render_tabla_respaldo(df_mapeo)


def main() -> None:
    inject_styles()
    render_header()

    if not file_exists(config.MAPEO_GENERADO_CSV):
        render_missing_processed_file()
        return

    try:
        df_mapeo = load_csv(config.MAPEO_GENERADO_CSV)
    except Exception:
        st.error("No fue posible leer data/processed/mapeo_generado.csv.")
        return

    render_dashboard(df_mapeo)


if __name__ == "__main__":
    main()
