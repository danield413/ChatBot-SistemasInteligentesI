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
from langchain_community.vectorstores import Chroma

# --- 1. Configuración y Carga de Variables ---
load_dotenv()
VECTORSTORE_PATH = "chroma_db"

# Validar que las API keys existan
if not (os.getenv("GOOGLE_API_KEY") and os.getenv("GROQ_API_KEY")):
    st.warning("Advertencia: Una o ambas API keys (GOOGLE_API_KEY, GROQ_API_KEY) no están en el .env.")

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


# --- 5. Función auxiliar ---
def format_docs(docs):
    """Función auxiliar para formatear los documentos de contexto."""
    return "\n\n".join(doc.page_content for doc in docs)

# --- 6. Interfaz de Streamlit ---

st.title("Proyecto 1: ChatBot SI 🤖")
st.write("Facultad de Inteligencia Artificial e Ingenierías - U. de Caldas")

# Selector de modelo (con los nombres actualizados)
st.write("---")
model_choice = st.selectbox(
    "Elige el modelo LLM que deseas usar:",
    ("Gemini (gemini-2.5-flash)", "Llama 3.1 (8B via Groq)") # <-- Actualizado
)
st.write("---")

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input del usuario
if user_question := st.chat_input("Escribe tu pregunta sobre IA..."):
    
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Generar respuesta del bot
    with st.chat_message("assistant"):
        
        try:
            # Seleccionar el LLM basado en la elección del usuario
            if model_choice == "Gemini (gemini-2.5-flash)":
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
                spinner_text = "Pensando con Gemini..."
            
            elif model_choice == "Llama 3.1 (8B via Groq)": # <-- Actualizado
                llm = ChatGroq(
                    model_name="llama-3.1-8b-instant", # <-- Modelo correcto
                    temperature=0
                )
                spinner_text = "Pensando con Llama 3.1..."

            # Definir la cadena RAG
            rag_chain = (
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )

            # Invocar la cadena
            with st.spinner(spinner_text):
                response = rag_chain.invoke(user_question)
                st.markdown(response)
                
                with st.expander("Ver contexto utilizado"):
                    context_docs = retriever.invoke(user_question)
                    st.json([doc.metadata for doc in context_docs])

            st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            st.error(f"Error al generar la respuesta: {e}")
            st.error("Asegúrate de que la API key para el modelo seleccionado sea válida y tenga créditos.")