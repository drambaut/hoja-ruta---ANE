# mapa_alineacion_hoja_ruta_sgp

Aplicacion en Python + Streamlit para visualizar un dashboard ejecutivo de alineacion de proyectos ED01-ED14 contra la Hoja de Ruta SGP.

El procesamiento con Gemini se ejecuta por consola y queda separado del dashboard. Streamlit solo lee `data/processed/mapeo_generado.csv` y no llama al LLM.

## Estructura

```text
mapa_alineacion_hoja_ruta_sgp/
|-- app.py
|-- requirements.txt
|-- README.md
|-- .env.example
|-- data/
|   |-- raw/
|   |-- processed/
|   `-- exports/
|-- prompts/
|   |-- extract_hoja_ruta.md
|   `-- map_projects_to_roadmap.md
|-- scripts/
|   |-- extract_roadmap_llm.py
|   |-- map_projects_llm.py
|   `-- run_pipeline.py
`-- src/
    |-- config.py
    |-- data_loader.py
    |-- preprocessing.py
    |-- gemini_client.py
    |-- llm_mapper.py
    |-- dashboard.py
    `-- utils.py
```

## Archivos de entrada

```text
data/raw/proyectos__raw.csv
data/raw/Estrategia de gestion de datos SGP_VF.pdf
```

## Archivos procesados

```text
data/processed/hoja_ruta.csv
data/processed/mapeo_generado.csv
```

## Instalacion local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuracion Gemini

Crea un archivo `.env` en la raiz del proyecto:

```text
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
```

Si el modelo configurado no esta disponible, cambia `GEMINI_MODEL` por uno disponible para `generateContent`.

## Ejecutar procesamiento

Flujo completo:

```bash
python scripts/run_pipeline.py
```

Pasos individuales:

```bash
python scripts/extract_roadmap_llm.py
python scripts/map_projects_llm.py
```

## Ejecutar dashboard

```bash
streamlit run app.py
```

Si `data/processed/mapeo_generado.csv` no existe, el dashboard muestra una instruccion para ejecutar primero el pipeline.


## Alcance

El dashboard muestra alineacion frente al plan. No mide avance tecnico, no tiene login, no permite edicion manual y no carga archivos desde la interfaz.
