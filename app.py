# app.py
import streamlit as st
import os
from dotenv import load_dotenv

# --- Imports de LangChain (Core) ---
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- Imports para el LLM (Gemini) ---
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Imports para el RAG (Embeddings y VectorDB) ---
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# --- 1. Configuración y Carga de Variables ---
load_dotenv()
VECTORSTORE_PATH = "chroma_db"

# Validar que la API key de Google exista
if not os.getenv("GOOGLE_API_KEY"):
    st.error("Error: GOOGLE_API_KEY no encontrada. Revisa tu archivo .env")
    st.stop()

# --- 2. Cargar el LLM (Gemini) ---
try:
    # NOTA: Si 'gemini-1.5-pro-latest' te da error de cuota (429), 
    # cámbialo por "gemini-1.5-flash-latest", que es más rápido y generoso.
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
except Exception as e:
    st.error(f"Error al cargar el LLM de Gemini. Detalle: {e}")
    st.stop()

# --- 3. Cargar la Base de Datos Vectorial (Chroma) ---
try:
    # Usamos el mismo modelo de embeddings forzado a CPU
    embeddings_model = HuggingFaceEmbeddings(
        model_name='all-MiniLM-L6-v2',
        model_kwargs={'device': 'cpu'}  # Forzar uso de CPU
    )
    
    # Cargar la base de datos existente
    vectorstore = Chroma(
        persist_directory=VECTORSTORE_PATH, 
        embedding_function=embeddings_model
    )
    
    # Crear el "retriever" (el componente que busca en la DB)
    retriever = vectorstore.as_retriever(
        search_type="similarity", # Tipo de búsqueda
        search_kwargs={"k": 3}      # k=3 -> trae 3 chunks de contexto
    )
except Exception as e:
    st.error(f"Error al cargar la base de datos de Chroma desde '{VECTORSTORE_PATH}'.")
    st.error(f"¿Corriste ingest.py primero? Detalle: {e}")
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


# --- 5. Definir la Cadena (RAG Chain) ---

def format_docs(docs):
    """Función auxiliar para formatear los documentos de contexto."""
    return "\n\n".join(doc.page_content for doc in docs)

# Esto define el flujo:
# 1. El usuario hace una pregunta ({question: ...}).
# 2. La pregunta se usa para buscar contexto (retriever | format_docs).
# 3. La pregunta y el contexto se pasan al prompt.
# 4. El prompt se pasa al LLM.
# 5. El LLM genera una respuesta.
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --- 6. Interfaz de Streamlit ---

st.title("Proyecto 1: ChatBot SI 🤖")
st.write("Facultad de Inteligencia Artificial e Ingenierías - U. de Caldas")

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input del usuario
if user_question := st.chat_input("Escribe tu pregunta sobre IA..."):
    
    # Añadir mensaje de usuario al historial y mostrarlo
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Generar respuesta del bot
    with st.chat_message("assistant"):
        with st.spinner("Pensando con Gemini..."):
            try:
                # 1. Invocar la cadena RAG
                response = rag_chain.invoke(user_question)
                
                # 2. Mostrar la respuesta
                st.markdown(response)
                
                # 3. Mostrar las fuentes (opcional pero recomendado)
                with st.expander("Ver contexto utilizado"):
                    context_docs = retriever.invoke(user_question)
                    # Mostrar metadatos (como el nombre del archivo)
                    st.json([doc.metadata for doc in context_docs])

                # Añadir respuesta del bot al historial
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                st.error(f"Error al generar la respuesta: {e}")