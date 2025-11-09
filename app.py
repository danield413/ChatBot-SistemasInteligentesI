# app.py
import streamlit as st
import os
from dotenv import load_dotenv

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

# Validar que las API keys existan
if not (os.getenv("GOOGLE_API_KEY") and os.getenv("GROQ_API_KEY")):
    st.warning("Advertencia: Una o ambas API keys (GOOGLE_API_KEY, GROQ_API_KEY) no están en el .env.")

if not CHROMA_API_KEY or not CHROMA_TENANT:
    st.error("Error: CHROMA_API_KEY y CHROMA_TENANT deben estar configurados en el archivo .env")
    st.stop()

# --- 3. Cargar la Base de Datos Vectorial (Chroma Cloud) ---
try:
    # Usamos el mismo modelo de embeddings forzado a CPU
    embeddings_model = HuggingFaceEmbeddings(
        model_name='all-MiniLM-L6-v2',
        model_kwargs={'device': 'cpu'}
    )
    
    # Importar chromadb
    import chromadb
    
    # Crear cliente de Chroma Cloud
    chroma_client = chromadb.CloudClient(
        api_key=CHROMA_API_KEY,
        tenant=CHROMA_TENANT,
        database=CHROMA_DATABASE
    )
    
    # Cargar la base de datos desde Chroma Cloud
    vectorstore = Chroma(
        client=chroma_client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings_model
    )
    
    # Crear el "retriever"
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )
    
    st.success(f"✅ Conectado a Chroma Cloud - Database: {CHROMA_DATABASE}")
    
except Exception as e:
    st.error(f"Error al conectar con Chroma Cloud.")
    st.error(f"Detalle: {e}")
    st.info("Verifica que CHROMA_API_KEY, CHROMA_TENANT y CHROMA_DATABASE estén correctamente configurados en el .env")
    st.stop()


# --- 4. Definir el Prompt (Plantilla de instrucciones) ---
template = """
Eres un asistente de IA de la Facultad de Inteligencia Artificial e Ingenierías de la Universidad de Caldas.
Tu tarea es responder preguntas sobre IA basándote EXCLUSIVAMENTE en el siguiente contexto.

Contexto:
{context}

Pregunta:
{question}

Instrucciones:
1.  Responde de forma clara y concisa.
2.  Si la información no está en el contexto, debes indicar explícitamente: "Lo siento, no tengo información suficiente sobre ese tema."
3.  Incluye siempre la fuente de la información al final de tu respuesta, si la encuentras.

Respuesta:
"""
prompt = PromptTemplate(template=template, input_variables=["context", "question"])


# --- 5. Función auxiliar ---
def format_docs(docs):
    """Función auxiliar para formatear los documentos de contexto."""
    return "\n\n".join(doc.page_content for doc in docs)

# --- 6. Configurar página ---
st.set_page_config(layout="wide", page_title="ChatBot Dual - SI", page_icon="🤖")

# --- 7. Interfaz de Streamlit ---

st.title("ChatBot de Sistemas Inteligentes 🤖 - Comparación Dual")
st.write("Facultad de Inteligencia Artificial e Ingenierías - U. de Caldas")
st.write("¡Pregunta y compara las respuestas de ambos modelos simultáneamente!")

st.write("---")

# Inicializar historiales de chat separados
if "messages_llama" not in st.session_state:
    st.session_state.messages_llama = []
if "messages_gemini" not in st.session_state:
    st.session_state.messages_gemini = []

# Crear dos columnas para los chats
col_llama, col_gemini = st.columns(2)

# --- Columna izquierda: Llama 3.1 ---
with col_llama:
    st.subheader("🦙 Llama 3.1 (8B via Groq)")
    st.write("---")
    
    # Contenedor para mensajes de Llama
    for message in st.session_state.messages_llama:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Columna derecha: Gemini ---
with col_gemini:
    st.subheader("✨ Gemini (gemini-2.5-flash)")
    st.write("---")
    
    # Contenedor para mensajes de Gemini
    for message in st.session_state.messages_gemini:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input del usuario (único para ambos)
if user_question := st.chat_input("Escribe tu pregunta sobre IA..."):
    
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
                    | StrOutputParser()  # <-- Agregar paréntesis aquí
                )
                
                with st.spinner("🦙 Pensando con Llama 3.1..."):
                    response_llama = rag_chain_llama.invoke(user_question)
                    st.markdown(response_llama)
                    
                    with st.expander("Ver contexto utilizado"):
                        context_docs = retriever.invoke(user_question)
                        st.json([doc.metadata for doc in context_docs])
                
                st.session_state.messages_llama.append({"role": "assistant", "content": response_llama})
                
            except Exception as e:
                error_msg = f"❌ Error con Llama: {e}"
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
                
                with st.spinner("✨ Pensando con Gemini..."):
                    response_gemini = rag_chain_gemini.invoke(user_question)
                    st.markdown(response_gemini)
                    
                    with st.expander("Ver contexto utilizado"):
                        context_docs = retriever.invoke(user_question)
                        st.json([doc.metadata for doc in context_docs])
                
                st.session_state.messages_gemini.append({"role": "assistant", "content": response_gemini})
                
            except Exception as e:
                error_msg = f"❌ Error con Gemini: {e}"
                st.error(error_msg)
                st.session_state.messages_gemini.append({"role": "assistant", "content": error_msg})

# Botón para limpiar ambos chats
st.write("---")
if st.button("🗑️ Limpiar ambas conversaciones"):
    st.session_state.messages_llama = []
    st.session_state.messages_gemini = []
    st.rerun()
