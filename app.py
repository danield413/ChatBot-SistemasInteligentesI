# app.py
import streamlit as st
import os
from dotenv import load_dotenv
import time

# --- Imports de LangChain (Core) ---
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- Imports para los LLMs (Gemini y Groq) ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

# --- Imports para el RAG (Embeddings y VectorDB) ---
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# --- 1. Configuración y Carga de Variables ---
load_dotenv()

# Para Chroma Cloud
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "ChatBotSI")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "ai_documents")

# --- 2. Configuración de Página (DEBE SER LO PRIMERO) ---
st.set_page_config(
    layout="wide",
    page_title="ChatBot SI - UCaldas",
    page_icon="🤖",
    initial_sidebar_state="collapsed"
)

# --- 3. CSS Personalizado para diseño moderno ---
st.markdown("""
<style>
    /* Tema oscuro principal */
    .stApp {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    }
    
    /* Header personalizado */
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
    
    /* Contenedores de chat mejorados */
    .chat-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        height: 600px;
        overflow-y: auto;
    }
    
    /* Títulos de modelos */
    .model-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .llama-header {
        border-left: 4px solid #10b981;
    }
    
    .gemini-header {
        border-left: 4px solid #3b82f6;
    }
    
    /* Mensajes de chat */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
        margin: 0.5rem 0 !important;
        padding: 1rem !important;
    }
    
    /* Input de chat */
    .stChatInputContainer {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 15px;
        padding: 0.5rem;
        backdrop-filter: blur(10px);
    }
    
    /* Botones */
    .stButton button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Expander personalizado */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Scrollbar personalizado */
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
    
    /* Badges de estado */
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
    
    /* Animación de entrada */
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
    
    /* Stats cards */
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

# Validar que las API keys existan
if not (os.getenv("GOOGLE_API_KEY") and os.getenv("GROQ_API_KEY")):
    st.warning("⚠️ Advertencia: Una o ambas API keys (GOOGLE_API_KEY, GROQ_API_KEY) no están en el .env.")

if not CHROMA_API_KEY or not CHROMA_TENANT:
    st.error("❌ Error: CHROMA_API_KEY y CHROMA_TENANT deben estar configurados en el archivo .env")
    st.stop()

# --- 4. Cargar la Base de Datos Vectorial (Chroma Cloud) ---
@st.cache_resource
def initialize_rag_system():
    try:
        embeddings_model = HuggingFaceEmbeddings(
            model_name='all-MiniLM-L6-v2',
            model_kwargs={'device': 'cpu'}
        )
        
        import chromadb
        
        chroma_client = chromadb.CloudClient(
            api_key=CHROMA_API_KEY,
            tenant=CHROMA_TENANT,
            database=CHROMA_DATABASE
        )
        
        vectorstore = Chroma(
            client=chroma_client,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings_model
        )
        
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        return retriever, True
        
    except Exception as e:
        st.error(f"❌ Error al conectar con Chroma Cloud: {e}")
        return None, False

retriever, rag_status = initialize_rag_system()

if not rag_status:
    st.stop()

# --- 5. Definir el Prompt ---
template = """
Eres un asistente de IA de la Facultad de Inteligencia Artificial e Ingenierías de la Universidad de Caldas.
Tu tarea es responder preguntas sobre IA basándose EXCLUSIVAMENTE en el siguiente contexto.

Contexto:
{context}

Pregunta:
{question}

Instrucciones:
1. Responde de forma clara y concisa.
2. Si la información no está en el contexto, indica: "Lo siento, no tengo información suficiente sobre ese tema."
3. Incluye siempre la fuente de la información al final de tu respuesta.

Respuesta:
"""
prompt = PromptTemplate(template=template, input_variables=["context", "question"])

def format_docs(docs):
    """Función auxiliar para formatear los documentos de contexto."""
    return "\n\n".join(doc.page_content for doc in docs)

# --- 6. Header Personalizado ---
st.markdown("""
<div class="main-header fade-in">
    <h1 class="main-title">ChatBot de Sistemas Inteligentes</h1>
    <p class="subtitle">🎓 Facultad de Inteligencia Artificial e Ingenierías - Universidad de Caldas</p>
    <p class="subtitle">Daniel Alberto Díaz - Juan Manuel Figueroa</p>
    <p class="subtitle">Compara respuestas de Llama 3.1 y Gemini en tiempo real</p>
</div>
""", unsafe_allow_html=True)

# --- 7. Stats Cards ---
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

# Inicializar contadores si no existen
if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0
if "llama_responses" not in st.session_state:
    st.session_state.llama_responses = 0
if "gemini_responses" not in st.session_state:
    st.session_state.gemini_responses = 0

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
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">✓</div>
        <div class="stats-label">Sistema Activo</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 8. Inicializar historiales de chat ---
if "messages_llama" not in st.session_state:
    st.session_state.messages_llama = []
if "messages_gemini" not in st.session_state:
    st.session_state.messages_gemini = []

# --- 9. Crear dos columnas para los chats ---
col_llama, col_gemini = st.columns(2, gap="large")

# --- Columna izquierda: Llama 3.1 ---
with col_llama:
    st.markdown("""
    <div class="model-header llama-header">
        <span style="font-size: 1.5rem;">🦙</span>
        <span style="font-size: 1.2rem; font-weight: 700; color: white;">Llama 3.1</span>
        <span class="status-badge badge-success">8B via Groq</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenedor de mensajes
    for message in st.session_state.messages_llama:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Columna derecha: Gemini ---
with col_gemini:
    st.markdown("""
    <div class="model-header gemini-header">
        <span style="font-size: 1.5rem;">✨</span>
        <span style="font-size: 1.2rem; font-weight: 700; color: white;">Gemini</span>
        <span class="status-badge badge-info">Flash 2.5</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenedor de mensajes
    for message in st.session_state.messages_gemini:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- 10. Input del usuario ---
user_question = st.chat_input("💭 Escribe tu pregunta sobre Inteligencia Artificial...", key="user_input")

if user_question:
    # Incrementar contador
    st.session_state.total_questions += 1
    
    # Agregar pregunta a ambos historiales
    st.session_state.messages_llama.append({"role": "user", "content": user_question})
    st.session_state.messages_gemini.append({"role": "user", "content": user_question})
    
    # Mostrar pregunta del usuario en ambas columnas
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
                llm_llama = ChatGroq(
                    model_name="llama-3.1-8b-instant",
                    temperature=0
                )
                
                rag_chain_llama = (
                    {"context": retriever | format_docs, "question": RunnablePassthrough()}
                    | prompt
                    | llm_llama
                    | StrOutputParser()
                )
                
                with st.spinner("🦙 Llama está pensando..."):
                    start_time = time.time()
                    response_llama = rag_chain_llama.invoke(user_question)
                    elapsed_time = time.time() - start_time
                    
                    st.markdown(response_llama)
                    st.caption(f"⏱️ Tiempo de respuesta: {elapsed_time:.2f}s")
                    
                    with st.expander("📚 Ver contexto utilizado"):
                        context_docs = retriever.invoke(user_question)
                        for i, doc in enumerate(context_docs, 1):
                            st.markdown(f"**Fuente {i}:** {doc.metadata.get('source', 'N/A')}")
                            st.text(doc.page_content[:200] + "...")
                            st.divider()
                
                st.session_state.messages_llama.append({"role": "assistant", "content": response_llama})
                st.session_state.llama_responses += 1
                
            except Exception as e:
                error_msg = f"❌ Error con Llama: {str(e)}"
                st.error(error_msg)
                st.session_state.messages_llama.append({"role": "assistant", "content": error_msg})
    
    # --- Generar respuesta de Gemini ---
    with col_gemini:
        with st.chat_message("assistant"):
            try:
                llm_gemini = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
                
                rag_chain_gemini = (
                    {"context": retriever | format_docs, "question": RunnablePassthrough()}
                    | prompt
                    | llm_gemini
                    | StrOutputParser()
                )
                
                with st.spinner("✨ Gemini está pensando..."):
                    start_time = time.time()
                    response_gemini = rag_chain_gemini.invoke(user_question)
                    elapsed_time = time.time() - start_time
                    
                    st.markdown(response_gemini)
                    st.caption(f"⏱️ Tiempo de respuesta: {elapsed_time:.2f}s")
                    
                    with st.expander("📚 Ver contexto utilizado"):
                        context_docs = retriever.invoke(user_question)
                        for i, doc in enumerate(context_docs, 1):
                            st.markdown(f"**Fuente {i}:** {doc.metadata.get('source', 'N/A')}")
                            st.text(doc.page_content[:200] + "...")
                            st.divider()
                
                st.session_state.messages_gemini.append({"role": "assistant", "content": response_gemini})
                st.session_state.gemini_responses += 1
                
            except Exception as e:
                error_msg = f"❌ Error con Gemini: {str(e)}"
                st.error(error_msg)
                st.session_state.messages_gemini.append({"role": "assistant", "content": error_msg})
    
    st.rerun()

# --- 11. Botones de control ---
st.markdown("<br>", unsafe_allow_html=True)
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

with col_btn2:
    if st.button("🗑️ Limpiar Conversaciones", use_container_width=True):
        st.session_state.messages_llama = []
        st.session_state.messages_gemini = []
        st.session_state.total_questions = 0
        st.session_state.llama_responses = 0
        st.session_state.gemini_responses = 0
        st.rerun()

# --- 12. Footer ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.5); font-size: 0.9rem;">
    <p>💡 Este chatbot utiliza RAG (Retrieval Augmented Generation) para responder basándose en documentos académicos</p>
    <p>Powered by LangChain | Chroma | Groq | Google Gemini</p>
</div>
""", unsafe_allow_html=True)
