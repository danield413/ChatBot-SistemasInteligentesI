# evaluate.py

import os
import time
import json
from dotenv import load_dotenv
import chromadb # Para la conexión a la nube
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter


# --- 1. CONFIGURACIÓN INICIAL ---
load_dotenv()

# Variables de archivos
GOLD_SET_FILE = "./json/gold_set.json"
RESULTS_FILE = "./json/cuaderno_metricas.json"

# Configuración de Chroma Cloud desde .env
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "ChatBotSI")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "ai_documents")
# Establecer el tamaño máximo de lote para evitar errores, si bien ya no es crítico.
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "300")) 

# Validar claves
if not CHROMA_API_KEY or not CHROMA_TENANT or not os.getenv("GOOGLE_API_KEY") or not os.getenv("GROQ_API_KEY"):
    print("❌ ERROR: Una o más variables de entorno (CHROMA, GOOGLE, GROQ) no están configuradas en .env.")
    exit()

print(f"✅ Conectando a ChromaDB en la nube - Database: {CHROMA_DATABASE}")
try:
    client = chromadb.CloudClient(
        api_key=CHROMA_API_KEY,
        tenant=CHROMA_TENANT,
        database=CHROMA_DATABASE
    )
except Exception as e:
    print(f"❌ Error al conectar con Chroma Cloud: {e}")
    exit()

# --- 2. CARGA DE MODELOS ---

# Carga de Embeddings
embeddings_model = HuggingFaceEmbeddings(
    model_name='all-MiniLM-L6-v2',
    model_kwargs={'device': 'cpu'}
)

# Carga de Retriever desde Chroma Cloud
try:
    vectorstore = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings_model
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    print("✅ Retriever cargado exitosamente desde la nube.")
except Exception as e:
    print(f"❌ Error fatal al cargar el retriever: {e}")
    exit()

# Definición de Modelos LLM
models_to_evaluate = {
    "Gemini": ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0),
    "Llama_3_1": ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)
}

# --- 3. PROMPT Y FUNCIONES AUXILIARES ---

template = """
Eres un asistente de IA de la Facultad de Inteligencia Artificial e Ingenierías de la Universidad de Caldas.
Tu tarea es responder preguntas sobre IA basándote EXCLUSIVAMENTE en el siguiente contexto.
Si la información no está en el contexto, debes indicar explícitamente: "Lo siento, no tengo información suficiente sobre ese tema."
Incluye siempre la fuente de la información al final de tu respuesta, si la encuentras.

Contexto:
{context}

Pregunta:
{question}

Respuesta:
"""
prompt = PromptTemplate(template=template, input_variables=["context", "question"])

def format_docs(docs):
    """Función auxiliar para formatear los documentos de contexto con fuentes."""
    context_str = ""
    for doc in docs:
        source = doc.metadata.get('source', 'Fuente desconocida')
        source_name = os.path.basename(source) # Solo el nombre del archivo
        context_str += f"[Fuente: {source_name}]\n"
        context_str += doc.page_content + "\n\n"
    return context_str

def create_rag_chain(llm, retriever, prompt, formatter):
    """Crea la cadena RAG para un LLM específico."""
    return (
        {"context": retriever | formatter, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

# --- 4. EJECUCIÓN DE LA EVALUACIÓN ---
try:
    with open(GOLD_SET_FILE, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)
    print(f"🔬 Gold Set cargado. Se encontraron {len(gold_set)} preguntas.")
except FileNotFoundError:
    print(f"❌ Error: No se encontró el archivo '{GOLD_SET_FILE}'. Asegúrate de que exista y tenga formato JSON.")
    exit()
except json.JSONDecodeError as e:
    print(f"❌ Error al decodificar el archivo JSON: {e}")
    exit()

results_list = []

for model_name, llm in models_to_evaluate.items():
    print(f"\n--- 🚀 Evaluando Modelo: {model_name} ---")
    rag_chain = create_rag_chain(llm, retriever, prompt, format_docs)
    
    for index, item in enumerate(gold_set):
        question = item['question']
        category = item['category']
        
        # Ejecución y medición de latencia
        print(f"  Pregunta {index+1}/{len(gold_set)}: {question[:50]}...")
        
        try:
            start_time = time.perf_counter() 
            response = rag_chain.invoke(question)
            end_time = time.perf_counter()
            latency = end_time - start_time 

            # Recuperar el contexto (para análisis de cobertura/fuentes)
            context_docs = retriever.invoke(question)
            retrieved_context = [
                {
                    "source": os.path.basename(doc.metadata.get('source', 'N/A')),
                    "content": doc.page_content
                }
                for doc in context_docs
            ]

            # Guardar resultados
            results_list.append({
                "model_name": model_name,
                "category": category,
                "question": question,
                "response": response,
                "retrieved_context": retrieved_context,
                "latency_sec": round(latency, 3),
                "evaluation": {
                    "exactitud_factica": None,
                    "citas_validas": None,
                    "claridad": None,
                    "alucinacion": None,
                    "seguridad": None,
                    "score_individual": None
                }
            })
            
        except Exception as e:
            error_msg = f"ERROR: {e}"
            print(f"    ❌ ERROR al procesar la pregunta: {e}")
            results_list.append({
                "model_name": model_name,
                "category": category,
                "question": question,
                "response": error_msg,
                "retrieved_context": [],
                "latency_sec": 999,
                "evaluation": {
                    "exactitud_factica": None,
                    "citas_validas": None,
                    "claridad": None,
                    "alucinacion": None,
                    "seguridad": None,
                    "score_individual": None
                }
            })
        
        # Pausa cada 10 preguntas para evitar límites de cuota
        if (index + 1) % 10 == 0 and (index + 1) < len(gold_set):
            print(f"\n⏸️  Pausa de 30 segundos después de {index + 1} preguntas para evitar límites de API...")
            time.sleep(30)
            print("▶️  Continuando evaluación...\n")

# --- 5. GUARDAR Y PREPARAR RESULTADOS FINALES ---
print("\nEvaluación completada. 💾 Guardando resultados...")

# Crear el directorio si no existe
os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)

# Guardar en formato JSON con indentación para legibilidad
with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(results_list, f, ensure_ascii=False, indent=2)

print(f"✅ ¡Éxito! Resultados guardados en '{RESULTS_FILE}'.")
print("\nPASO SIGUIENTE: Abre el archivo JSON y realiza la calificación manual en el objeto 'evaluation'.")