import streamlit as st
import pandas as pd
import json
import os

# --- Configuración ---
# Asegúrate de que este path sea correcto
METRICS_FILE = './json/cuaderno_metricas.json'
# Si creaste una carpeta 'json', usa:
# METRICS_FILE = './json/cuaderno_metricas.json'


# --- Funciones de Carga y Guardado ---
@st.cache_data
def load_data(file_path):
    """
    Carga y normaliza el JSON de métricas.
    Maneja la estructura anidada de 'evaluation'.
    """
    if not os.path.exists(file_path):
        st.error(f"❌ Error: No se encontró el archivo '{file_path}'.")
        st.error("Por favor, asegúrate de que el archivo JSON (como 'cuaderno_metricas_evaluado.json' que generé) "
                 "esté en la misma carpeta que este script y se llame 'cuaderno_metricas.json'.")
        return None, None
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Usar json_normalize para aplanar la estructura anidada
        df = pd.json_normalize(data, sep='_')
        
        # Renombrar columnas para quitar el prefijo 'evaluation_'
        df.columns = df.columns.str.replace('evaluation_', '')
        
        return df, data
    except Exception as e:
        st.error(f"Error al cargar o normalizar el archivo JSON: {e}")
        return None, None

def save_data(file_path, data):
    """Guarda los datos actualizados en el archivo JSON."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Error al guardar el archivo: {e}")
        return False

def update_json_from_dataframe(raw_json_data, edited_df):
    """Actualiza el JSON original con los valores editados del DataFrame."""
    # Convertir el DataFrame editado a un diccionario para búsqueda fácil
    # Usamos el índice original del DataFrame para alinear
    edited_records = edited_df.set_index(pd.Index(range(len(edited_df)))).to_dict('index')

    for i, item in enumerate(raw_json_data):
        if i in edited_records:
            row = edited_records[i]
            
            # Función auxiliar para convertir a float o mantener None
            def to_float_or_none(val):
                if pd.isna(val):
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            # Actualizar las métricas de evaluación
            item['evaluation']['exactitud_factica'] = to_float_or_none(row.get('exactitud_factica'))
            item['evaluation']['cobertura'] = to_float_or_none(row.get('cobertura'))
            item['evaluation']['citas_validas'] = to_float_or_none(row.get('citas_validas'))
            item['evaluation']['claridad'] = to_float_or_none(row.get('claridad'))
            item['evaluation']['alucinacion'] = to_float_or_none(row.get('alucinacion'))
            item['evaluation']['seguridad'] = to_float_or_none(row.get('seguridad'))
            item['evaluation']['score_individual'] = to_float_or_none(row.get('score_individual'))
    
    return raw_json_data

def convert_metrics_to_numeric(df):
    """Convierte las columnas de métricas a números para poder calcularlas."""
    
    cols_to_convert = [
        'latency_sec',
        'exactitud_factica',
        'cobertura',
        'citas_validas',
        'claridad',
        'alucinacion',
        'seguridad',
        'score_individual'
    ]
    
    df_processed = df.copy()
    
    for col in cols_to_convert:
        if col in df_processed.columns:
            df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
    
    return df_processed

# --- NUEVA FUNCIÓN DE CÁLCULO ---
def calculate_score(row):
    """
    Calcula el score individual basado en la fórmula del proyecto.
    Score = 0.35*Exactitud + 0.20*Cobertura + 0.15*Claridad + 0.20*Citas - 0.10*Alucinacion - 0.05*Seguridad
    """
    try:
        e = float(row['exactitud_factica']) if pd.notna(row['exactitud_factica']) else 0
        c = float(row['cobertura']) if pd.notna(row['cobertura']) else 0
        # Normalizar claridad de 0-5 a 0-1 para la fórmula
        cl = (float(row['claridad']) / 5.0) if pd.notna(row['claridad']) else 0
        ci = float(row['citas_validas']) if pd.notna(row['citas_validas']) else 0
        # Penalizaciones (1 = ocurrió, 0 = no ocurrió)
        a = float(row['alucinacion']) if pd.notna(row['alucinacion']) else 0
        s = float(row['seguridad']) if pd.notna(row['seguridad']) else 0
        
        # Aplicar la fórmula
        score = (0.35 * e) + (0.20 * c) + (0.15 * cl) + (0.20 * ci) - (0.10 * a) - (0.05 * s)
        
        return round(score, 4)
    
    except (TypeError, ValueError, ZeroDivisionError):
        # Si falta algún valor (NaN, None), no se puede calcular
        return None

# --- Configuración de la Página ---
st.set_page_config(layout="wide", page_title="Dashboard de Evaluación (SI)")

st.title("📊 Dashboard de Evaluación del ChatBot")
st.write("Visualizador y Editor para `cuaderno_metricas.json` del Proyecto de Sistemas Inteligentes.")

# --- Carga de Datos ---
# Usamos session_state para manejar las actualizaciones
if 'data_loaded' not in st.session_state:
    df_raw, raw_json_data = load_data(METRICS_FILE)
    if df_raw is not None:
        st.session_state.df_raw = df_raw
        st.session_state.raw_json_data = raw_json_data
        st.session_state.data_loaded = True
else:
    df_raw = st.session_state.df_raw
    raw_json_data = st.session_state.raw_json_data

if 'df_raw' in st.session_state and st.session_state.df_raw is not None:
    df_processed = convert_metrics_to_numeric(st.session_state.df_raw)
    
    # --- CALCULAR SCORES AUTOMÁTICAMENTE AL CARGAR ---
    df_processed['score_individual'] = df_processed.apply(calculate_score, axis=1)

    # --- Barra Lateral de Filtros ---
    st.sidebar.header("Filtros de Visualización")
    
    all_models = sorted(df_processed['model_name'].unique())
    all_categories = sorted(df_processed['category'].unique())

    selected_models = st.sidebar.multiselect(
        "Seleccionar Modelos:",
        options=all_models,
        default=all_models
    )
    
    categories_with_all = ["Todas"] + list(all_categories)
    selected_category = st.sidebar.selectbox(
        "Seleccionar Categoría:",
        options=categories_with_all,
        index=0
    )

    # --- Aplicar Filtros ---
    if not selected_models:
        st.warning("Por favor, selecciona al menos un modelo para ver los resultados.")
        st.stop()
        
    df_filtered = df_processed[df_processed['model_name'].isin(selected_models)]
    
    if selected_category != "Todas":
        df_filtered = df_filtered[df_filtered['category'] == selected_category]

    st.sidebar.info(f"Mostrando {len(df_filtered)} de {len(df_processed)} registros totales.")

    # --- Visualización de Métricas (KPIs) ---
    st.header(f"Resultados para: {selected_category} (Categoría)")
    
    # --- Cálculo del Score Global ---
    overall_score = df_filtered['score_individual'].mean()
    
    kpi_cols = st.columns([1.5] + [1] * len(selected_models))

    with kpi_cols[0]:
        st.subheader("Score Global (Promedio)")
        st.metric("Score Promedio (0-1)", f"{overall_score:.4f}")
        # Criterios de Aceptación del Proyecto
        st.markdown("---")
        st.markdown("**Criterios de Aceptación:**")
        st.metric("Score Global (Min 0.70)", f"{overall_score:.4f}", delta=f"{overall_score-0.70:.4f}")
        
        # Calcular tasas globales para los criterios
        if len(df_filtered) > 0:
            global_hallucination_rate = df_filtered['alucinacion'].mean() * 100
            global_citation_rate = df_filtered['citas_validas'].mean() * 100
            global_coverage_rate = df_filtered['cobertura'].mean() * 100
        else:
            global_hallucination_rate = 0
            global_citation_rate = 0
            global_coverage_rate = 0
            
        st.metric("Cobertura Promedio (%)", f"{global_coverage_rate:.1f}%")
        st.metric("Tasa Alucinación (Max 10%)", f"{global_hallucination_rate:.1f}%", delta=f"{10.0 - global_hallucination_rate:.1f}%", delta_color="inverse")
        st.metric("Tasa Citas Válidas (Min 85%)", f"{global_citation_rate:.1f}%", delta=f"{global_citation_rate - 85.0:.1f}%")

    for i, model_name in enumerate(selected_models):
        with kpi_cols[i+1]:
            st.subheader(f"{model_name}")
            df_model = df_filtered[df_filtered['model_name'] == model_name]
            
            # Calcular score promedio por modelo
            avg_score = df_model['score_individual'].mean()
            avg_latency = df_model['latency_sec'].mean()
            avg_clarity = df_model['claridad'].mean()
            
            total_responses = len(df_model)
            if total_responses > 0:
                accuracy_rate = df_model['exactitud_factica'].mean() * 100
                citation_rate = df_model['citas_validas'].mean() * 100
                hallucination_rate = df_model['alucinacion'].mean() * 100
                coverage_rate = df_model['cobertura'].mean() * 100
            else:
                avg_score = 0
                avg_latency = 0
                avg_clarity = 0
                accuracy_rate = 0
                citation_rate = 0
                hallucination_rate = 0
                coverage_rate = 0
            
            # Mostrar Score Promedio del Modelo
            st.metric(f"Score Promedio", f"{avg_score:.4f}")

            kpi_cols_inner = st.columns(2)
            kpi_cols_inner[0].metric("Latencia (s)", f"{avg_latency:.2f}")
            kpi_cols_inner[1].metric("Claridad (0-5)", f"{avg_clarity:.2f}")
            kpi_cols_inner[0].metric("Cobertura (%)", f"{coverage_rate:.1f}")
            kpi_cols_inner[1].metric("Exactitud (%)", f"{accuracy_rate:.1f}")
            kpi_cols_inner[0].metric("Citas (%)", f"{citation_rate:.1f}")
            kpi_cols_inner[1].metric("Alucinación (%)", f"{hallucination_rate:.1f}")

    st.divider()

    # --- MEJORA: Gráficos Comparativos ---
    st.header("Comparativa de Modelos")
    
    if len(df_filtered) > 0 and len(selected_models) > 0:
        
        # --- NUEVO GRÁFICO: Score Promedio ---
        st.subheader("Score Promedio (0-1)")
        avg_score_data = df_filtered.groupby('model_name')['score_individual'].mean().reset_index()
        st.bar_chart(avg_score_data.set_index('model_name'))
        
        chart1, chart2 = st.columns(2)
        
        with chart1:
            st.subheader("Latencia Promedio (seg)")
            avg_latency_data = df_filtered.groupby('model_name')['latency_sec'].mean().reset_index()
            st.bar_chart(avg_latency_data.set_index('model_name'))
            
        with chart2:
            st.subheader("Claridad Promedio (0-5)")
            avg_clarity_data = df_filtered.groupby('model_name')['claridad'].mean().reset_index()
            st.bar_chart(avg_clarity_data.set_index('model_name'))

        chart3, chart4 = st.columns(2)

        with chart3:
            st.subheader("Cobertura Promedio (%)")
            coverage_data = (df_filtered.groupby('model_name')['cobertura'].mean() * 100).reset_index()
            st.bar_chart(coverage_data.set_index('model_name'))

        with chart4:
            st.subheader("Tasa de Exactitud Fáctica (%)")
            accuracy_data = (df_filtered.groupby('model_name')['exactitud_factica'].mean() * 100).reset_index()
            st.bar_chart(accuracy_data.set_index('model_name'))

        chart5, chart6 = st.columns(2)

        with chart5:
            st.subheader("Tasa de Alucinación (%)")
            hallucination_data = (df_filtered.groupby('model_name')['alucinacion'].mean() * 100).reset_index()
            st.bar_chart(hallucination_data.set_index('model_name'))

        with chart6:
            st.subheader("Citas Válidas (%)")
            citation_data = (df_filtered.groupby('model_name')['citas_validas'].mean() * 100).reset_index()
            st.bar_chart(citation_data.set_index('model_name'))
            
    elif len(selected_models) <= 1:
        st.info("Selecciona 2 o más modelos para ver gráficos comparativos.")
    else:
        st.info("No hay datos para los filtros seleccionados.")

    st.divider()

    # --- Tabla de Datos Editable ---
    st.subheader("📝 Editor de Métricas (Tabla Editable)")
    st.info("💡 Edita las métricas y el **Score se recalculará automáticamente** al guardar.\n\n"
             "**Fórmula:** Score = 0.35×Exactitud + 0.20×Cobertura + 0.15×Claridad + 0.20×Citas - 0.10×Alucinación - 0.05×Seguridad")

    # Función auxiliar para extraer fuentes del contexto recuperado
    def extract_sources(retrieved_context):
        """Extrae y une todas las fuentes del contexto recuperado."""
        if isinstance(retrieved_context, list):
            sources = [ctx.get('source', 'N/A') for ctx in retrieved_context if isinstance(ctx, dict)]
            return ", ".join(sources) if sources else "N/A"
        return "N/A"

    # Crear columna con fuentes extraídas
    df_filtered_copy = df_filtered.copy()
    df_filtered_copy['fuentes_contexto'] = df_filtered_copy['retrieved_context'].apply(extract_sources)

    # Columnas editables (solo métricas)
    editable_columns = [
        'exactitud_factica',
        'cobertura',
        'citas_validas',
        'claridad',
        'alucinacion',
        'seguridad'
    ]

    # Columnas para mostrar
    display_columns = [
        'question',
        'response',
        'exactitud_factica',
        'cobertura',
        'citas_validas',
        'claridad',
        'alucinacion',
        'seguridad',
        'score_individual',
        'model_name',
        'category',
        'fuentes_contexto',
        'latency_sec'
    ]

    column_config = {
        'question': st.column_config.TextColumn('Pregunta', disabled=True, width='large'),
        'response': st.column_config.TextColumn('Respuesta', disabled=True, width='large'),
        'exactitud_factica': st.column_config.NumberColumn('Exactitud (0/1)', min_value=0, max_value=1, step=1),
        'cobertura': st.column_config.NumberColumn('Cobertura (0/1)', min_value=0, max_value=1, step=1),
        'citas_validas': st.column_config.NumberColumn('Citas (0/1)', min_value=0, max_value=1, step=1),
        'claridad': st.column_config.NumberColumn('Claridad (0-5)', min_value=0, max_value=5, step=1),
        'alucinacion': st.column_config.NumberColumn('Alucinación (0/1)', min_value=0, max_value=1, step=1),
        'seguridad': st.column_config.NumberColumn('Seguridad (0/1)', min_value=0, max_value=1, step=1),
        'score_individual': st.column_config.NumberColumn(
            '🧮 Score', 
            disabled=True,
            format="%.4f",
            width='small',
            help="Calculado automáticamente"
        ),
        'model_name': st.column_config.TextColumn('Modelo', disabled=True, width='small'),
        'category': st.column_config.TextColumn('Categoría', disabled=True, width='small'),
        'fuentes_contexto': st.column_config.TextColumn('Fuentes', disabled=True, width='medium'),
        'latency_sec': st.column_config.NumberColumn('Latencia (s)', disabled=True, format="%.3f", width='small'),
    }

    # Mostrar tabla editable
    edited_df = st.data_editor(
        df_filtered_copy[display_columns],
        column_config=column_config,
        use_container_width=True,
        num_rows="fixed",
        key="metrics_editor",
        height=600
    )

    # Botón para guardar cambios
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 Guardar Cambios y Recalcular Scores", type="primary", use_container_width=True):
            
            # 1. Copiar los datos editados
            df_to_save = edited_df.copy()
            
            # 2. Convertir métricas a numéricas
            for col in editable_columns:
                df_to_save[col] = pd.to_numeric(df_to_save[col], errors='coerce')

            # 3. RECALCULAR el score para las filas editadas
            df_to_save['score_individual'] = df_to_save.apply(calculate_score, axis=1)
            
            # 4. Actualizar el dataframe completo con los cambios
            # Obtener los índices originales de las filas filtradas
            indices_filtered = df_filtered.index
            
            # Actualizar df_processed con los valores editados
            for idx, filtered_idx in enumerate(indices_filtered):
                if idx < len(df_to_save):
                    for col in editable_columns + ['score_individual']:
                        df_processed.at[filtered_idx, col] = df_to_save.iloc[idx][col]
            
            # 5. Guardar en JSON
            updated_json = update_json_from_dataframe(st.session_state.raw_json_data, df_processed)
            
            if save_data(METRICS_FILE, updated_json):
                st.success("✅ ¡Cambios guardados y scores recalculados exitosamente!")
                # Limpiar caché y recargar
                load_data.clear()
                st.session_state.raw_json_data = updated_json
                st.session_state.df_raw, _ = load_data(METRICS_FILE)
                st.rerun()
            else:
                st.error("❌ Error al guardar los cambios.")

    st.divider()

    # Expander para ver los datos crudos (JSON original)
    with st.expander("🔍 Ver datos crudos (JSON original)"):
        st.json(st.session_state.raw_json_data)

else:
    st.info("Cargando datos... o esperando que se genere el archivo `cuaderno_metricas.json`...")
    if st.button("Reintentar carga"):
        st.rerun()