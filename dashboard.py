import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- Configuración ---
METRICS_FILE = './json/cuaderno_metricas.json'

# --- Configuración de la Página ---
st.set_page_config(
    layout="wide", 
    page_title="Dashboard de Evaluación - SI",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- CSS Personalizado Ultra Moderno ---
st.markdown("""
<style>
    /* Tema principal con gradiente dinámico */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    }
    
    /* Header principal con efecto de cristal */
    .main-header {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(99, 102, 241, 0.2);
        animation: fadeInDown 0.6s ease-out;
    }
    
    .dashboard-title {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 900;
        text-align: center;
        margin: 0;
        letter-spacing: -1px;
    }
    
    .dashboard-subtitle {
        color: rgba(255, 255, 255, 0.7);
        text-align: center;
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }
    
    /* Métricas KPI mejoradas */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.3);
        border-color: rgba(99, 102, 241, 0.5);
    }
    
    /* Tabs personalizados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        padding: 0.5rem;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: rgba(255, 255, 255, 0.6);
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.2);
        color: white;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%) !important;
        color: white !important;
    }
    
    /* Sidebar moderno */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    section[data-testid="stSidebar"] .stMarkdown {
        color: rgba(255, 255, 255, 0.9);
    }
    
    /* Botones mejorados */
    .stButton button {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
        text-transform: uppercase;
        font-size: 0.9rem;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.6);
        background: linear-gradient(90deg, #a855f7 0%, #6366f1 100%);
    }
    
    /* Data Editor personalizado */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Alertas y notificaciones */
    .stAlert {
        background: rgba(99, 102, 241, 0.1);
        border-left: 4px solid #6366f1;
        border-radius: 8px;
    }
    
    .stSuccess {
        background: rgba(34, 197, 94, 0.1);
        border-left: 4px solid #22c55e;
    }
    
    .stWarning {
        background: rgba(251, 146, 60, 0.1);
        border-left: 4px solid #fb923c;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #ef4444;
    }
    
    /* Scrollbar elegante */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #6366f1 0%, #a855f7 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #a855f7 0%, #ec4899 100%);
    }
    
    /* Animaciones */
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.6;
        }
    }
    
    .fade-in-up {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Badges y etiquetas */
    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-success {
        background: linear-gradient(90deg, #22c55e 0%, #10b981 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3);
    }
    
    .badge-warning {
        background: linear-gradient(90deg, #fb923c 0%, #f59e0b 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(251, 146, 60, 0.3);
    }
    
    .badge-danger {
        background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
    }
    
    .badge-info {
        background: linear-gradient(90deg, #6366f1 0%, #3b82f6 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
    }
    
    /* Expander mejorado */
    .streamlit-expanderHeader {
        background: rgba(99, 102, 241, 0.1);
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(99, 102, 241, 0.2);
    }
    
    /* Números grandes para métricas */
    .big-number {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1;
    }
    
    /* Gráficos con borde */
    .plot-container {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Funciones de Carga y Guardado ---
@st.cache_data
def load_data(file_path):
    """Carga y normaliza el JSON de métricas."""
    if not os.path.exists(file_path):
        return None, None
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        df = pd.json_normalize(data, sep='_')
        df.columns = df.columns.str.replace('evaluation_', '')
        
        return df, data
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
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
    edited_records = edited_df.reset_index(drop=True).to_dict('index')

    for i, item in enumerate(raw_json_data):
        if i in edited_records:
            row = edited_records[i]
            
            def to_float_or_none(val):
                if pd.isna(val):
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            item['evaluation']['exactitud_factica'] = to_float_or_none(row.get('exactitud_factica'))
            item['evaluation']['cobertura'] = to_float_or_none(row.get('cobertura'))
            item['evaluation']['citas_validas'] = to_float_or_none(row.get('citas_validas'))
            item['evaluation']['claridad'] = to_float_or_none(row.get('claridad'))
            item['evaluation']['alucinacion'] = to_float_or_none(row.get('alucinacion'))
            item['evaluation']['seguridad'] = to_float_or_none(row.get('seguridad'))
            item['evaluation']['score_individual'] = to_float_or_none(row.get('score_individual'))
    
    return raw_json_data

def convert_metrics_to_numeric(df):
    """Convierte las columnas de métricas a números."""
    cols_to_convert = [
        'latency_sec', 'exactitud_factica', 'cobertura', 'citas_validas',
        'claridad', 'alucinacion', 'seguridad', 'score_individual'
    ]
    
    df_processed = df.copy()
    for col in cols_to_convert:
        if col in df_processed.columns:
            df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
    
    return df_processed

def calculate_score(row):
    """Calcula el score individual según la fórmula del proyecto."""
    try:
        e = float(row['exactitud_factica']) if pd.notna(row['exactitud_factica']) else 0
        c = float(row['cobertura']) if pd.notna(row['cobertura']) else 0
        cl = (float(row['claridad']) / 5.0) if pd.notna(row['claridad']) else 0
        ci = float(row['citas_validas']) if pd.notna(row['citas_validas']) else 0
        a = float(row['alucinacion']) if pd.notna(row['alucinacion']) else 0
        s = float(row['seguridad']) if pd.notna(row['seguridad']) else 0
        
        score = (0.35 * e) + (0.20 * c) + (0.15 * cl) + (0.20 * ci) - (0.10 * a) - (0.05 * s)
        return round(score, 4)
    
    except (TypeError, ValueError, ZeroDivisionError):
        return None

# --- Header Principal ---
st.markdown("""
<div class="main-header">
    <h1 class="dashboard-title">📊 Dashboard de Evaluación</h1>
    <p class="dashboard-subtitle">Sistema de Análisis y Comparativa de Modelos LLM - Proyecto SI</p>
</div>
""", unsafe_allow_html=True)

# --- Carga de Datos ---
if 'data_loaded' not in st.session_state:
    df_raw, raw_json_data = load_data(METRICS_FILE)
    if df_raw is not None:
        st.session_state.df_raw = df_raw
        st.session_state.raw_json_data = raw_json_data
        st.session_state.data_loaded = True
        st.session_state.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
else:
    df_raw = st.session_state.df_raw
    raw_json_data = st.session_state.raw_json_data

if 'df_raw' in st.session_state and st.session_state.df_raw is not None:
    df_processed = convert_metrics_to_numeric(st.session_state.df_raw)
    df_processed['score_individual'] = df_processed.apply(calculate_score, axis=1)

    # --- Sidebar con Filtros Modernos ---
    with st.sidebar:
        st.markdown("### 🎯 Filtros de Visualización")
        st.markdown("---")
        
        all_models = sorted(df_processed['model_name'].unique())
        selected_models = st.multiselect(
            "🤖 Modelos:",
            options=all_models,
            default=all_models,
            help="Selecciona los modelos a comparar"
        )
        
        all_categories = sorted(df_processed['category'].unique())
        categories_with_all = ["Todas"] + list(all_categories)
        selected_category = st.selectbox(
            "📂 Categoría:",
            options=categories_with_all,
            index=0,
            help="Filtra por categoría de pregunta"
        )
        
        st.markdown("---")
        st.info(f"📅 **Última actualización:**\n{st.session_state.get('last_update', 'N/A')}")
        
        total_records = len(df_processed)
        st.metric("📊 Total de Registros", total_records)

    # --- Aplicar Filtros ---
    if not selected_models:
        st.warning("⚠️ Por favor, selecciona al menos un modelo.")
        st.stop()
        
    df_filtered = df_processed[df_processed['model_name'].isin(selected_models)]
    
    if selected_category != "Todas":
        df_filtered = df_filtered[df_filtered['category'] == selected_category]

    # --- KPIs Principales con diseño moderno ---
    st.markdown("### 🎯 Métricas Clave")
    
    overall_score = df_filtered['score_individual'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score_status = "✅" if overall_score >= 0.70 else "⚠️"
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: rgba(255,255,255,0.6); margin-bottom: 0.5rem;">SCORE GLOBAL</div>
            <div class="big-number">{overall_score:.3f}</div>
            <div style="margin-top: 0.5rem;">
                <span class="status-badge {'badge-success' if overall_score >= 0.70 else 'badge-warning'}">
                    {score_status} {"APROBADO" if overall_score >= 0.70 else "REVISAR"}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        coverage = df_filtered['cobertura'].mean() * 100
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: rgba(255,255,255,0.6); margin-bottom: 0.5rem;">COBERTURA</div>
            <div class="big-number">{coverage:.1f}%</div>
            <div style="margin-top: 0.5rem; color: rgba(255,255,255,0.6);">
                📚 Promedio general
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        hallucination = df_filtered['alucinacion'].mean() * 100
        hallucination_status = "✅" if hallucination <= 10 else "❌"
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: rgba(255,255,255,0.6); margin-bottom: 0.5rem;">ALUCINACIÓN</div>
            <div class="big-number">{hallucination:.1f}%</div>
            <div style="margin-top: 0.5rem;">
                <span class="status-badge {'badge-success' if hallucination <= 10 else 'badge-danger'}">
                    {hallucination_status} {"< 10%" if hallucination <= 10 else "> 10%"}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        citations = df_filtered['citas_validas'].mean() * 100
        citations_status = "✅" if citations >= 85 else "⚠️"
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: rgba(255,255,255,0.6); margin-bottom: 0.5rem;">CITAS VÁLIDAS</div>
            <div class="big-number">{citations:.1f}%</div>
            <div style="margin-top: 0.5rem;">
                <span class="status-badge {'badge-success' if citations >= 85 else 'badge-warning'}">
                    {citations_status} {"≥ 85%" if citations >= 85 else "< 85%"}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Tabs para organizar contenido ---
    tab1, tab2, tab3 = st.tabs(["📈 Comparativa", "📝 Editor de Métricas", "🔍 Análisis Detallado"])
    
    with tab1:
        st.markdown("### 📊 Gráficos Comparativos")
        
        if len(df_filtered) > 0:
            # Gráfico de Score Promedio con Plotly
            fig_score = go.Figure()
            
            for model in selected_models:
                model_data = df_filtered[df_filtered['model_name'] == model]
                avg_score = model_data['score_individual'].mean()
                
                fig_score.add_trace(go.Bar(
                    name=model,
                    x=[model],
                    y=[avg_score],
                    text=[f'{avg_score:.3f}'],
                    textposition='auto',
                    marker=dict(
                        color='#6366f1' if model == 'Gemini' else '#a855f7',
                        line=dict(color='rgba(255,255,255,0.2)', width=1)
                    )
                ))
            
            fig_score.update_layout(
                title="Score Promedio por Modelo",
                yaxis_title="Score (0-1)",
                template="plotly_dark",
                height=400,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig_score, use_container_width=True)
            
            # Gráficos adicionales en columnas
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Latencia
                fig_latency = px.bar(
                    df_filtered.groupby('model_name')['latency_sec'].mean().reset_index(),
                    x='model_name',
                    y='latency_sec',
                    title="⏱️ Latencia Promedio (seg)",
                    template="plotly_dark",
                    color='model_name',
                    color_discrete_map={'Gemini': '#6366f1', 'Llama_3_1': '#a855f7'}
                )
                fig_latency.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    height=350
                )
                st.plotly_chart(fig_latency, use_container_width=True)
            
            with col_chart2:
                # Claridad
                fig_clarity = px.bar(
                    df_filtered.groupby('model_name')['claridad'].mean().reset_index(),
                    x='model_name',
                    y='claridad',
                    title="✨ Claridad Promedio (0-5)",
                    template="plotly_dark",
                    color='model_name',
                    color_discrete_map={'Gemini': '#6366f1', 'Llama_3_1': '#a855f7'}
                )
                fig_clarity.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    height=350
                )
                st.plotly_chart(fig_clarity, use_container_width=True)
            
            # Más gráficos
            col_chart3, col_chart4 = st.columns(2)
            
            with col_chart3:
                # Cobertura
                coverage_data = (df_filtered.groupby('model_name')['cobertura'].mean() * 100).reset_index()
                fig_coverage = px.bar(
                    coverage_data,
                    x='model_name',
                    y='cobertura',
                    title="📚 Cobertura (%)",
                    template="plotly_dark",
                    color='model_name',
                    color_discrete_map={'Gemini': '#6366f1', 'Llama_3_1': '#a855f7'}
                )
                fig_coverage.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    height=350
                )
                st.plotly_chart(fig_coverage, use_container_width=True)
            
            with col_chart4:
                # Exactitud
                accuracy_data = (df_filtered.groupby('model_name')['exactitud_factica'].mean() * 100).reset_index()
                fig_accuracy = px.bar(
                    accuracy_data,
                    x='model_name',
                    y='exactitud_factica',
                    title="✓ Exactitud Fáctica (%)",
                    template="plotly_dark",
                    color='model_name',
                    color_discrete_map={'Gemini': '#6366f1', 'Llama_3_1': '#a855f7'}
                )
                fig_accuracy.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    height=350
                )
                st.plotly_chart(fig_accuracy, use_container_width=True)

    with tab2:
        st.markdown("### 📝 Editor de Métricas")
        st.info("💡 **Edita las métricas** directamente en la tabla. El score se recalculará automáticamente al guardar.\n\n"
                 "**Fórmula:** Score = 0.35×Exactitud + 0.20×Cobertura + 0.15×Claridad + 0.20×Citas - 0.10×Alucinación - 0.05×Seguridad")

        def extract_sources(retrieved_context):
            if isinstance(retrieved_context, list):
                sources = [ctx.get('source', 'N/A') for ctx in retrieved_context if isinstance(ctx, dict)]
                return ", ".join(sources) if sources else "N/A"
            return "N/A"

        df_filtered_copy = df_filtered.copy()
        df_filtered_copy['fuentes_contexto'] = df_filtered_copy['retrieved_context'].apply(extract_sources)

        editable_columns = [
            'exactitud_factica', 'cobertura', 'citas_validas',
            'claridad', 'alucinacion', 'seguridad'
        ]

        display_columns = [
            'question', 'response', 'exactitud_factica', 'cobertura',
            'citas_validas', 'claridad', 'alucinacion', 'seguridad',
            'score_individual', 'model_name', 'category',
            'fuentes_contexto', 'latency_sec'
        ]

        column_config = {
            'question': st.column_config.TextColumn('❓ Pregunta', disabled=True, width='large'),
            'response': st.column_config.TextColumn('💬 Respuesta', disabled=True, width='large'),
            'exactitud_factica': st.column_config.NumberColumn('✓ Exactitud', min_value=0, max_value=1, step=1),
            'cobertura': st.column_config.NumberColumn('📚 Cobertura', min_value=0, max_value=1, step=1),
            'citas_validas': st.column_config.NumberColumn('📖 Citas', min_value=0, max_value=1, step=1),
            'claridad': st.column_config.NumberColumn('✨ Claridad', min_value=0, max_value=5, step=1),
            'alucinacion': st.column_config.NumberColumn('⚠️ Alucinación', min_value=0, max_value=1, step=1),
            'seguridad': st.column_config.NumberColumn('🔒 Seguridad', min_value=0, max_value=1, step=1),
            'score_individual': st.column_config.NumberColumn('🎯 Score', disabled=True, format="%.4f"),
            'model_name': st.column_config.TextColumn('🤖 Modelo', disabled=True, width='small'),
            'category': st.column_config.TextColumn('📂 Categoría', disabled=True, width='small'),
            'fuentes_contexto': st.column_config.TextColumn('📄 Fuentes', disabled=True, width='medium'),
            'latency_sec': st.column_config.NumberColumn('⏱️ Latencia', disabled=True, format="%.3f", width='small'),
        }

        edited_df = st.data_editor(
            df_filtered_copy[display_columns],
            column_config=column_config,
            use_container_width=True,
            num_rows="fixed",
            key="metrics_editor",
            height=500
        )

        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("💾 GUARDAR CAMBIOS Y RECALCULAR", type="primary", use_container_width=True):
                df_to_save = edited_df.copy()
                
                for col in editable_columns:
                    df_to_save[col] = pd.to_numeric(df_to_save[col], errors='coerce')

                df_to_save['score_individual'] = df_to_save.apply(calculate_score, axis=1)
                
                indices_filtered = df_filtered.index
                
                for idx, filtered_idx in enumerate(indices_filtered):
                    if idx < len(df_to_save):
                        for col in editable_columns + ['score_individual']:
                            df_processed.at[filtered_idx, col] = df_to_save.iloc[idx][col]
                
                updated_json = update_json_from_dataframe(st.session_state.raw_json_data, df_processed)
                
                if save_data(METRICS_FILE, updated_json):
                    st.success("✅ ¡Cambios guardados y scores recalculados exitosamente!")
                    st.session_state.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    load_data.clear()
                    st.session_state.raw_json_data = updated_json
                    st.session_state.df_raw, _ = load_data(METRICS_FILE)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar los cambios.")

    with tab3:
        st.markdown("### 🔍 Análisis Detallado por Modelo")
        
        for model in selected_models:
            model_data = df_filtered[df_filtered['model_name'] == model]
            
            if len(model_data) > 0:
                with st.expander(f"🤖 {model} - Ver Estadísticas Completas", expanded=False):
                    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                    
                    with col_stat1:
                        st.metric("📊 Total Respuestas", len(model_data))
                        st.metric("🎯 Score Promedio", f"{model_data['score_individual'].mean():.3f}")
                    
                    with col_stat2:
                        st.metric("⏱️ Latencia Media", f"{model_data['latency_sec'].mean():.2f}s")
                        st.metric("✨ Claridad Media", f"{model_data['claridad'].mean():.2f}/5")
                    
                    with col_stat3:
                        st.metric("📚 Cobertura", f"{model_data['cobertura'].mean()*100:.1f}%")
                        st.metric("✓ Exactitud", f"{model_data['exactitud_factica'].mean()*100:.1f}%")
                    
                    with col_stat4:
                        st.metric("📖 Citas Válidas", f"{model_data['citas_validas'].mean()*100:.1f}%")
                        st.metric("⚠️ Alucinación", f"{model_data['alucinacion'].mean()*100:.1f}%")
                    
                    # Distribución por categoría
                    if 'category' in model_data.columns:
                        st.markdown("#### 📂 Desempeño por Categoría")
                        category_stats = model_data.groupby('category').agg({
                            'score_individual': 'mean',
                            'latency_sec': 'mean'
                        }).round(3)
                        st.dataframe(category_stats, use_container_width=True)

    # --- Footer ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; color: rgba(255,255,255,0.4); padding: 2rem;">
        <p style="font-size: 0.9rem;">💡 Dashboard de Evaluación de Modelos LLM - Proyecto de Sistemas Inteligentes</p>
        <p style="font-size: 0.8rem;">Desarrollado con Streamlit • Plotly • Pandas</p>
    </div>
    """, unsafe_allow_html=True)

else:
    st.error("❌ No se pudo cargar el archivo de métricas.")
    st.info("Por favor, asegúrate de que el archivo `cuaderno_metricas.json` exista en la carpeta `./json/`")
    
    if st.button("🔄 Reintentar Carga"):
        st.rerun()