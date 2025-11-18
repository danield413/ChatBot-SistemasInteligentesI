# app.py
import streamlit as st
import os
from dotenv import load_dotenv
import time

# --- Imports de LangChain (Core) ---
# LangChain es el framework que nos permite construir aplicaciones con LLMs
from langchain_core.prompts import PromptTemplate  # Para crear templates de prompts reutilizables
from langchain_core.runnables import RunnablePassthrough  # Permite pasar datos sin modificarlos en la cadena
from langchain_core.output_parsers import StrOutputParser  # Convierte la salida del LLM a string

# --- Imports para los LLMs (Gemini y Groq) ---
from langchain_google_genai import ChatGoogleGenerativeAI  # Cliente para usar Gemini de Google
from langchain_groq import ChatGroq  # Cliente para usar Llama a través de Groq

# --- Imports para el RAG (Embeddings y VectorDB) ---
from langchain_huggingface import HuggingFaceEmbeddings  # Modelo de embeddings para convertir texto a vectores
from langchain_chroma import Chroma  # Cliente para la base de datos vectorial ChromaDB


# --- 1. Configuración y Carga de Variables ---
load_dotenv()  # Carga las variables de entorno desde el archivo .env

# Para Chroma Cloud - Variables necesarias para conectarse a ChromaDB en la nube
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")  # API key para autenticación
CHROMA_TENANT = os.getenv("CHROMA_TENANT")  # Tenant ID (organización)
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "ChatBotSI")  # Nombre de la BD (valor por defecto)
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "ai_documents")  # Nombre de la colección

# --- 2. Configuración de Página (DEBE SER LO PRIMERO) ---
# set_page_config debe llamarse antes de cualquier otro comando de Streamlit
st.set_page_config(
    layout="wide",  # Usa el ancho completo de la pantalla
    page_title="ChatBot SI - UCaldas",  # Título en la pestaña del navegador
    page_icon="🤖",  # Emoji que aparece en la pestaña
    initial_sidebar_state="collapsed"  # Sidebar colapsado por defecto
)

# --- 3. CSS Personalizado para diseño moderno ---
# Inyecta CSS personalizado para mejorar la apariencia de la aplicación
st.markdown("""
<style>
    /* Tema oscuro principal con gradiente */
    .stApp {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    }
    
    /* Header personalizado con gradiente y sombra */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .main-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        text-align: center;
        margin-top: 0.5rem;
    }
    
    /* Contenedores de chat con efecto glassmorphism */
    .chat-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);  /* Efecto de desenfoque del fondo */
        border: 1px solid rgba(255, 255, 255, 0.1);
        height: 600px;
        overflow-y: auto;
    }
    
    /* Headers diferenciados para cada modelo */
    .model-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    /* Color verde para Llama */
    .llama-header {
        border-left: 4px solid #10b981;
    }
    
    /* Color azul para Gemini */
    .gemini-header {
        border-left: 4px solid #3b82f6;
    }
    
    /* Estilos para mensajes de chat */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
        margin: 0.5rem 0 !important;
        padding: 1rem !important;
    }
    
    /* Input de chat estilizado */
    .stChatInputContainer {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 15px;
        padding: 0.5rem;
        backdrop-filter: blur(10px);
    }
    
    /* Botones con gradiente y animación */
    .stButton button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;  /* Transición suave para hover */
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    /* Efecto hover en botones */
    .stButton button:hover {
        transform: translateY(-2px);  /* Levanta el botón */
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);  /* Sombra más pronunciada */
    }
    
    /* Expander personalizado */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Spinner con color personalizado */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Scrollbar personalizado para coherencia visual */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Badges de estado para identificar modelos */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    
    .badge-success {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid #10b981;
    }
    
    .badge-info {
        background: rgba(59, 130, 246, 0.2);
        color: #3b82f6;
        border: 1px solid #3b82f6;
    }
    
    /* Animación de entrada suave */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeInUp 0.5s ease-out;
    }
    
    /* Tarjetas de estadísticas */
    .stats-card {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stats-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .stats-label {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.9rem;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Validar que las API keys existan antes de continuar
if not (os.getenv("GOOGLE_API_KEY") and os.getenv("GROQ_API_KEY")):
    st.warning("⚠️ Advertencia: Una o ambas API keys (GOOGLE_API_KEY, GROQ_API_KEY) no están en el .env.")

# Validar configuración de Chroma - detiene la app si falta
if not CHROMA_API_KEY or not CHROMA_TENANT:
    st.error("❌ Error: CHROMA_API_KEY y CHROMA_TENANT deben estar configurados en el archivo .env")
    st.stop()

# --- 4. Cargar la Base de Datos Vectorial (Chroma Cloud) ---
@st.cache_resource  # Cachea el recurso para no recargarlo en cada interacción
def initialize_rag_system():
    """
    Inicializa el sistema RAG (Retrieval Augmented Generation):
    1. Carga el modelo de embeddings
    2. Conecta con ChromaDB en la nube
    3. Crea un retriever para buscar documentos relevantes
    """
    try:
        # Modelo de embeddings: convierte texto en vectores numéricos
        # 'all-MiniLM-L6-v2' es un modelo pequeño y eficiente de HuggingFace
        embeddings_model = HuggingFaceEmbeddings(
            model_name='all-MiniLM-L6-v2',
            model_kwargs={'device': 'cpu'}  # Usa CPU (no requiere GPU)
        )
        
        import chromadb
        
        # Cliente de ChromaDB en la nube
        chroma_client = chromadb.CloudClient(
            api_key=CHROMA_API_KEY,
            tenant=CHROMA_TENANT,
            database=CHROMA_DATABASE
        )
        
        # Vectorstore: almacén de vectores donde están los documentos embeddeados
        vectorstore = Chroma(
            client=chroma_client,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings_model
        )
        
        # Retriever: componente que busca los documentos más relevantes
        # search_type="similarity": busca por similitud de coseno
        # k=3: devuelve los 3 documentos más relevantes
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        return retriever, True
        
    except Exception as e:
        st.error(f"❌ Error al conectar con Chroma Cloud: {e}")
        return None, False

# Inicializar el sistema RAG
retriever, rag_status = initialize_rag_system()

# Si falla la conexión, detener la aplicación
if not rag_status:
    st.stop()

# --- 5. Definir los Prompts (Breve y Extendido) ---
# Prompt para modo breve: respuestas concisas de 2-3 frases
template_breve = """
Eres un asistente de IA de la Facultad de Inteligencia Artificial e Ingenierías de la Universidad de Caldas.
Tu tarea es responder preguntas sobre IA basándose EXCLUSIVAMENTE en el siguiente contexto.

Contexto:
{context}

Pregunta:
{question}

Instrucciones:
1. Responde de forma BREVE y CONCISA en 2-3 frases máximo.
2. Ve directo al grano, sin introducciones largas.
3. Si la información no está en el contexto, indica brevemente: "No tengo información sobre ese tema."
4. NO incluyas citas ni fuentes en la respuesta.

Respuesta:
"""

# Prompt para modo extendido: explicaciones detalladas con citas
template_extendida = """
Eres un asistente de IA de la Facultad de Inteligencia Artificial e Ingenierías de la Universidad de Caldas.
Tu tarea es responder preguntas sobre IA basándose EXCLUSIVAMENTE en el siguiente contexto.

Contexto:
{context}

Pregunta:
{question}

Instrucciones:
1. Proporciona una EXPLICACIÓN DETALLADA y COMPLETA del tema.
2. Organiza la respuesta en párrafos bien estructurados.
3. INCLUYE CITAS TEXTUALES del contexto usando comillas ("...") cuando sea relevante.
4. Al final, lista las fuentes utilizadas en formato:
   📚 **Fuentes:** [Nombre del documento 1], [Nombre del documento 2]
5. Si la información no está en el contexto, indica: "Lo siento, no tengo información suficiente sobre ese tema en mis documentos."

Respuesta:
"""

# Crear objetos PromptTemplate que LangChain puede usar
prompt_breve = PromptTemplate(template=template_breve, input_variables=["context", "question"])
prompt_extendida = PromptTemplate(template=template_extendida, input_variables=["context", "question"])

def format_docs(docs):
    """
    Función auxiliar para formatear los documentos recuperados.
    Concatena el contenido de todos los documentos con doble salto de línea.
    """
    return "\n\n".join(doc.page_content for doc in docs)

# --- 6. Header Personalizado ---
st.markdown("""
<div class="main-header fade-in">
    <h1 class="main-title">🤖 ChatBot de Sistemas Inteligentes</h1>
    <p class="subtitle">🎓 Facultad de Inteligencia Artificial e Ingenierías - Universidad de Caldas</p>
    <p class="subtitle">Daniel Alberto Díaz - Juan Manuel Figueroa</p>
    <p class="subtitle">Compara respuestas de Llama 3.1 y Gemini en tiempo real</p>
</div>
""", unsafe_allow_html=True)

# --- 7. Selector de Modo de Respuesta ---
st.markdown("### ⚙️ Configuración de Respuesta")
col_mode1, col_mode2, col_mode3 = st.columns([1, 2, 1])

with col_mode2:
    # Radio buttons para seleccionar el modo de respuesta
    response_mode = st.radio(
        "Selecciona el modo de respuesta:",
        options=["📝 Breve (2-3 frases)", "📖 Extendida (explicación con citas)"],
        horizontal=True,
        help="**Breve:** Respuestas concisas y directas.\n**Extendida:** Explicaciones detalladas con citas del contexto."
    )
    
    # Determinar qué prompt usar basándose en la selección
    use_extended = "Extendida" in response_mode
    current_prompt = prompt_extendida if use_extended else prompt_breve
    
    # Mostrar descripción del modo seleccionado
    if use_extended:
        st.info("🔍 **Modo Extendido:** Recibirás explicaciones detalladas con citas textuales y fuentes.")
    else:
        st.success("⚡ **Modo Breve:** Recibirás respuestas rápidas y concisas.")

st.markdown("<br>", unsafe_allow_html=True)

# --- 8. Stats Cards ---
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

# Inicializar contadores en session_state (persisten durante la sesión)
if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0
if "llama_responses" not in st.session_state:
    st.session_state.llama_responses = 0
if "gemini_responses" not in st.session_state:
    st.session_state.gemini_responses = 0

# Mostrar estadísticas en tarjetas
with col_stat1:
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{st.session_state.total_questions}</div>
        <div class="stats-label">Preguntas Realizadas</div>
    </div>
    """, unsafe_allow_html=True)

with col_stat2:
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{st.session_state.llama_responses}</div>
        <div class="stats-label">Respuestas Llama</div>
    </div>
    """, unsafe_allow_html=True)

with col_stat3:
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{st.session_state.gemini_responses}</div>
        <div class="stats-label">Respuestas Gemini</div>
    </div>
    """, unsafe_allow_html=True)

with col_stat4:
    mode_emoji = "📖" if use_extended else "📝"
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{mode_emoji}</div>
        <div class="stats-label">{"Modo Extendido" if use_extended else "Modo Breve"}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 9. Inicializar historiales de chat ---
# Cada modelo tiene su propio historial de mensajes
if "messages_llama" not in st.session_state:
    st.session_state.messages_llama = []
if "messages_gemini" not in st.session_state:
    st.session_state.messages_gemini = []

# --- 10. Crear dos columnas para los chats ---
# Divide la pantalla en dos para comparar respuestas lado a lado
col_llama, col_gemini = st.columns(2, gap="large")

# --- Columna izquierda: Llama 3.1 ---
with col_llama:
    # Header con identificación visual de Llama
    st.markdown("""
    <div class="model-header llama-header">
        <span style="font-size: 1.5rem;">🦙</span>
        <span style="font-size: 1.2rem; font-weight: 700; color: white;">Llama 3.1</span>
        <span class="status-badge badge-success">8B via Groq</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar todos los mensajes del historial de Llama
    for message in st.session_state.messages_llama:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Columna derecha: Gemini ---
with col_gemini:
    # Header con identificación visual de Gemini
    st.markdown("""
    <div class="model-header gemini-header">
        <span style="font-size: 1.5rem;">✨</span>
        <span style="font-size: 1.2rem; font-weight: 700; color: white;">Gemini</span>
        <span class="status-badge badge-info">Flash 2.5</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar todos los mensajes del historial de Gemini
    for message in st.session_state.messages_gemini:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- 11. Input del usuario ---
# chat_input proporciona un campo de texto estilizado en la parte inferior
user_question = st.chat_input("💭 Escribe tu pregunta sobre Inteligencia Artificial...", key="user_input")

if user_question:
    # Se ejecuta cuando el usuario envía una pregunta
    
    # Incrementar contador de preguntas
    st.session_state.total_questions += 1
    
    # Agregar la pregunta a ambos historiales
    st.session_state.messages_llama.append({"role": "user", "content": user_question})
    st.session_state.messages_gemini.append({"role": "user", "content": user_question})
    
    # Mostrar la pregunta del usuario en ambas columnas
    with col_llama:
        with st.chat_message("user"):
            st.markdown(user_question)
    
    with col_gemini:
        with st.chat_message("user"):
            st.markdown(user_question)
    
    # --- Generar respuesta de Llama 3.1 ---
    with col_llama:
        with st.chat_message("assistant"):
            try:
                # Inicializar el modelo Llama 3.1 a través de Groq
                llm_llama = ChatGroq(
                    model_name="llama-3.1-8b-instant",
                    temperature=0  # 0 = respuestas determinísticas, sin aleatoriedad
                )
                
                # Construir la cadena RAG (Retrieval Augmented Generation):
                # 1. retriever busca documentos relevantes
                # 2. format_docs los formatea
                # 3. current_prompt crea el prompt con contexto y pregunta
                # 4. llm_llama genera la respuesta
                # 5. StrOutputParser convierte a string
                rag_chain_llama = (
                    {"context": retriever | format_docs, "question": RunnablePassthrough()}
                    | current_prompt
                    | llm_llama
                    | StrOutputParser()
                )
                
                # Texto del spinner según el modo
                spinner_text = "🦙 Llama generando respuesta extendida..." if use_extended else "🦙 Llama respondiendo brevemente..."
                with st.spinner(spinner_text):
                    # Medir tiempo de respuesta
                    start_time = time.time()
                    # Invocar la cadena RAG con la pregunta del usuario
                    response_llama = rag_chain_llama.invoke(user_question)
                    elapsed_time = time.time() - start_time
                    
                    # Mostrar la respuesta
                    st.markdown(response_llama)
                    
                    # Mostrar estadísticas de la respuesta
                    word_count = len(response_llama.split())
                    st.caption(f"⏱️ Tiempo: {elapsed_time:.2f}s | 📊 Palabras: {word_count} | {'📖 Extendida' if use_extended else '📝 Breve'}")
                    
                    # Mostrar contexto utilizado solo en modo extendido
                    if use_extended:
                        with st.expander("📚 Ver contexto utilizado"):
                            # Recuperar los documentos que se usaron
                            context_docs = retriever.invoke(user_question)
                            for i, doc in enumerate(context_docs, 1):
                                st.markdown(f"**Fuente {i}:** {doc.metadata.get('source', 'N/A')}")
                                st.text(doc.page_content[:300] + "...")
                                st.divider()
                
                # Agregar respuesta al historial
                st.session_state.messages_llama.append({"role": "assistant", "content": response_llama})
                st.session_state.llama_responses += 1
                
            except Exception as e:
                # Manejo de errores
                error_msg = f"❌ Error con Llama: {str(e)}"
                st.error(error_msg)
                st.session_state.messages_llama.append({"role": "assistant", "content": error_msg})
    
    # --- Generar respuesta de Gemini ---
    with col_gemini:
        with st.chat_message("assistant"):
            try:
                # Inicializar el modelo Gemini de Google
                llm_gemini = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
                
                # Construir la cadena RAG para Gemini (misma estructura que Llama)
                rag_chain_gemini = (
                    {"context": retriever | format_docs, "question": RunnablePassthrough()}
                    | current_prompt
                    | llm_gemini
                    | StrOutputParser()
                )
                
                spinner_text = "✨ Gemini generando respuesta extendida..." if use_extended else "✨ Gemini respondiendo brevemente..."
                with st.spinner(spinner_text):
                    start_time = time.time()
                    response_gemini = rag_chain_gemini.invoke(user_question)
                    elapsed_time = time.time() - start_time
                    
                    st.markdown(response_gemini)
                    
                    word_count = len(response_gemini.split())
                    st.caption(f"⏱️ Tiempo: {elapsed_time:.2f}s | 📊 Palabras: {word_count} | {'📖 Extendida' if use_extended else '📝 Breve'}")
                    
                    if use_extended:
                        with st.expander("📚 Ver contexto utilizado"):
                            context_docs = retriever.invoke(user_question)
                            for i, doc in enumerate(context_docs, 1):
                                st.markdown(f"**Fuente {i}:** {doc.metadata.get('source', 'N/A')}")
                                st.text(doc.page_content[:300] + "...")
                                st.divider()
                
                st.session_state.messages_gemini.append({"role": "assistant", "content": response_gemini})
                st.session_state.gemini_responses += 1
                
            except Exception as e:
                error_msg = f"❌ Error con Gemini: {str(e)}"
                st.error(error_msg)
                st.session_state.messages_gemini.append({"role": "assistant", "content": error_msg})
    
    # Rerun para actualizar la UI con las nuevas respuestas
    st.rerun()

# --- 12. Botones de control ---
st.markdown("<br>", unsafe_allow_html=True)
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

with col_btn2:
    # Botón para limpiar todo el historial de conversaciones
    if st.button("🗑️ Limpiar Conversaciones", use_container_width=True):
        st.session_state.messages_llama = []
        st.session_state.messages_gemini = []
        st.session_state.total_questions = 0
        st.session_state.llama_responses = 0
        st.session_state.gemini_responses = 0
        st.rerun()

# --- 13. Footer ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.5); font-size: 0.9rem;">
    <p>💡 Este chatbot utiliza RAG (Retrieval Augmented Generation) para responder basándose en documentos académicos</p>
    <p>Powered by LangChain | Chroma | Groq | Google Gemini</p>
</div>
""", unsafe_allow_html=True)