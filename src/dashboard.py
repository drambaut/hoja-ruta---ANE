from __future__ import annotations

import html

import pandas as pd
import plotly.express as px
import streamlit as st


STATUS_ORDER = [
    "Mapeado",
    "Mapeo parcial",
    "Por validar",
    "Por fuera",
    "Siguiente vigencia",
]

STATUS_COLORS = {
    "Mapeado": "#2E7D32",
    "Mapeo parcial": "#F9A825",
    "Por validar": "#9E9E9E",
    "Por fuera": "#C62828",
    "Siguiente vigencia": "#1565C0",
}

DECISION_COLORS = {
    "Se mantiene": "#2E7D32",
    "Pasa a siguiente vigencia": "#1565C0",
    "Requiere validacion": "#9E9E9E",
    "Requiere validación": "#9E9E9E",
    "Por fuera de la hoja de ruta": "#C62828",
}

EXCLUDED_LINE_VALUES = {
    "Sin informacion suficiente",
    "Sin información suficiente",
    "No identificada",
    "No identificado",
    "",
}


def _has_columns(df: pd.DataFrame, columns: set[str], context: str) -> bool:
    missing = sorted(columns - set(df.columns))
    if missing:
        st.info(f"No hay informacion suficiente para mostrar {context}.")
        return False
    return True


def _project_status_counts(df_mapeo: pd.DataFrame) -> pd.Series:
    if not _has_columns(df_mapeo, {"codigo_proyecto", "estado_mapeo"}, "los KPIs"):
        return pd.Series(dtype="int64")

    priority = {status: index for index, status in enumerate(STATUS_ORDER)}
    status_by_project = (
        df_mapeo.assign(
            _priority=df_mapeo["estado_mapeo"].map(priority).fillna(len(priority))
        )
        .sort_values("_priority")
        .drop_duplicates("codigo_proyecto")
    )
    return status_by_project["estado_mapeo"].value_counts()


def render_kpis(df_mapeo: pd.DataFrame) -> None:
    if df_mapeo.empty:
        st.info("No hay datos de mapeo para mostrar.")
        return

    if not _has_columns(df_mapeo, {"codigo_proyecto", "estado_mapeo"}, "los KPIs"):
        return

    total_projects = df_mapeo["codigo_proyecto"].nunique()
    status_counts = _project_status_counts(df_mapeo)

    kpis = [
        ("Total proyectos", total_projects),
        ("Mapeados", int(status_counts.get("Mapeado", 0))),
        ("Mapeo parcial", int(status_counts.get("Mapeo parcial", 0))),
        ("Por validar", int(status_counts.get("Por validar", 0))),
        ("Por fuera", int(status_counts.get("Por fuera", 0))),
        ("Siguiente vigencia", int(status_counts.get("Siguiente vigencia", 0))),
    ]

    cols = st.columns(6)
    for col, (label, value) in zip(cols, kpis):
        col.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{html.escape(label)}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_estado_mapeo_chart(df_mapeo: pd.DataFrame) -> None:
    if df_mapeo.empty:
        return
    if not _has_columns(df_mapeo, {"codigo_proyecto", "estado_mapeo"}, "estado de mapeo"):
        return

    st.subheader("Estado de mapeo")
    st.caption(
        "Esta vista muestra cuantos proyectos tienen relacion clara, parcial o pendiente con la hoja de ruta. "
        "No mide avance tecnico, solo alineacion."
    )

    counts = _project_status_counts(df_mapeo).reindex(STATUS_ORDER, fill_value=0)
    data = counts.reset_index()
    data.columns = ["estado_mapeo", "cantidad"]
    data = data[data["cantidad"] > 0]

    fig = px.pie(
        data,
        names="estado_mapeo",
        values="cantidad",
        hole=0.55,
        color="estado_mapeo",
        color_discrete_map=STATUS_COLORS,
    )
    fig.update_traces(textposition="inside", textinfo="label+value")
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)


def render_cobertura_lineas_chart(df_mapeo: pd.DataFrame) -> None:
    if df_mapeo.empty:
        return
    required = {"linea_hoja_ruta", "codigo_proyecto"}
    if not _has_columns(df_mapeo, required, "cobertura por linea"):
        return

    st.subheader("Cobertura por linea de hoja de ruta")
    st.caption(
        "Esta grafica permite ver en que lineas se concentran los proyectos y cuales tienen menor cobertura."
    )

    filtered = df_mapeo[
        ~df_mapeo["linea_hoja_ruta"].fillna("").astype(str).isin(EXCLUDED_LINE_VALUES)
    ].copy()
    if filtered.empty:
        st.info("No hay lineas de hoja de ruta identificadas para graficar.")
        return

    data = (
        filtered.groupby("linea_hoja_ruta")["codigo_proyecto"]
        .nunique()
        .reset_index(name="proyectos_unicos")
        .sort_values("proyectos_unicos", ascending=True)
    )
    fig = px.bar(
        data,
        x="proyectos_unicos",
        y="linea_hoja_ruta",
        orientation="h",
        text="proyectos_unicos",
        color_discrete_sequence=["#3F7CAC"],
    )
    fig.update_layout(
        xaxis_title="Proyectos unicos",
        yaxis_title="",
        margin=dict(l=10, r=10, t=20, b=10),
        height=max(320, 42 * len(data)),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_matriz_proyecto_linea(df_mapeo: pd.DataFrame) -> None:
    if df_mapeo.empty:
        return
    required = {"codigo_proyecto", "linea_hoja_ruta", "estado_mapeo"}
    if not _has_columns(df_mapeo, required, "la matriz proyecto-linea"):
        return

    st.subheader("Matriz Proyecto x Linea de accion")
    st.caption(
        "La matriz muestra si cada proyecto aporta a alguna linea de la hoja de ruta. "
        "Los grises indican que falta informacion para decidir."
    )

    filtered = df_mapeo[
        ~df_mapeo["linea_hoja_ruta"].fillna("").astype(str).isin(EXCLUDED_LINE_VALUES)
    ].copy()
    if filtered.empty:
        st.info("No hay relaciones proyecto-linea suficientes para construir la matriz.")
        return

    status_rank = {status: index for index, status in enumerate(STATUS_ORDER, start=1)}
    matrix = filtered.pivot_table(
        index="codigo_proyecto",
        columns="linea_hoja_ruta",
        values="estado_mapeo",
        aggfunc=lambda values: sorted(
            set(str(value) for value in values),
            key=lambda value: status_rank.get(value, 99),
        )[0],
        fill_value="",
    )

    html_table = ['<div class="matrix-wrap"><table class="matrix-table">']
    html_table.append("<thead><tr><th>Proyecto</th>")
    for column in matrix.columns:
        html_table.append(f"<th>{html.escape(str(column))}</th>")
    html_table.append("</tr></thead><tbody>")

    for project, row in matrix.iterrows():
        html_table.append(f"<tr><th>{html.escape(str(project))}</th>")
        for value in row:
            value_text = str(value) if value else ""
            color = STATUS_COLORS.get(value_text, "#ECEFF1")
            html_table.append(
                f'<td style="background:{color};" title="{html.escape(value_text)}">'
                f"{html.escape(value_text)}</td>"
            )
        html_table.append("</tr>")

    html_table.append("</tbody></table></div>")
    st.markdown("".join(html_table), unsafe_allow_html=True)


def render_decision_vigencia_chart(df_mapeo: pd.DataFrame) -> None:
    if df_mapeo.empty:
        return
    required = {"codigo_proyecto", "decision_vigencia"}
    if not _has_columns(df_mapeo, required, "decision de vigencia"):
        return

    st.subheader("Decision de vigencia")
    st.caption("Esta vista resume la decision preliminar de gestion para cada proyecto.")

    decision_by_project = df_mapeo.drop_duplicates("codigo_proyecto")
    data = decision_by_project["decision_vigencia"].value_counts().reset_index()
    data.columns = ["decision_vigencia", "cantidad"]
    fig = px.bar(
        data,
        x="cantidad",
        y="decision_vigencia",
        orientation="h",
        text="cantidad",
        color="decision_vigencia",
        color_discrete_map=DECISION_COLORS,
    )
    fig.update_layout(
        xaxis_title="Proyectos",
        yaxis_title="",
        legend_title_text="",
        showlegend=False,
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_tabla_respaldo(df_mapeo: pd.DataFrame) -> None:
    if df_mapeo.empty:
        return

    st.subheader("Tabla minima de respaldo")

    required_columns = [
        "codigo_proyecto",
        "nombre_proyecto",
        "linea_hoja_ruta",
        "estado_mapeo",
        "decision_vigencia",
        "nivel_confianza_mapeo",
        "justificacion",
    ]
    available_columns = [column for column in required_columns if column in df_mapeo.columns]
    if not available_columns:
        st.info("No hay columnas esperadas para mostrar la tabla de respaldo.")
        return

    filtered = df_mapeo.copy()
    filter_cols = st.columns(3)

    for column, label, container in [
        ("estado_mapeo", "Estado", filter_cols[0]),
        ("decision_vigencia", "Decision", filter_cols[1]),
        ("linea_hoja_ruta", "Linea", filter_cols[2]),
    ]:
        if column not in filtered.columns:
            continue
        options = sorted(value for value in filtered[column].dropna().astype(str).unique())
        selected = container.multiselect(label, options=options)
        if selected:
            filtered = filtered[filtered[column].astype(str).isin(selected)]

    st.dataframe(filtered[available_columns], use_container_width=True, hide_index=True)
