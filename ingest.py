# ingest.py
import os
import time  # Necesario para pausas entre lotes
from dotenv import load_dotenv
import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Cargar variables de entorno
load_dotenv()

# --- Configuración de la Base de Datos en la Nube ---
API_KEY = os.getenv("CHROMA_API_KEY")
TENANT = os.getenv("CHROMA_TENANT")
DATABASE_NAME = os.getenv("CHROMA_DATABASE", "ChatBotSI")
COLLECTION_NAME = "IA_DOCS"
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "300"))

# Validar que las variables existan
if not API_KEY or not TENANT:
    print("Error: CHROMA_API_KEY y CHROMA_TENANT deben estar configurados en el archivo .env")
    exit()

# Inicializar el cliente de Chroma Cloud
try:
    client = chromadb.CloudClient(
        api_key=API_KEY,
        tenant=TENANT,
        database=DATABASE_NAME
    )
    print(f"✅ Conectado a ChromaDB en la nube - Database: {DATABASE_NAME}")
except Exception as e:
    print(f"❌ Error al conectar con Chroma Cloud: {e}")
    exit()

# --- Configuración de Embeddings ---
print("Cargando modelo de embeddings local (la primera vez puede tardar)...")
embeddings_model = HuggingFaceEmbeddings(
    model_name='all-MiniLM-L6-v2',
    model_kwargs={'device': 'cpu'}
)
print("✅ Modelo de embeddings cargado.")

corpus_path = "corpus"

def ingest_documents():
    print("\n🔄 Iniciando ingesta de documentos...")
    
    all_documents = [] 
    pdf_files = [f for f in os.listdir(corpus_path) if f.endswith(".pdf")]

    # --- Lógica de carga y chunking de documentos ---
    try:
        if not pdf_files:
            print("❌ Error: No se encontraron archivos .pdf en la carpeta 'corpus'.")
            return
        
        for filename in pdf_files:
            file_path = os.path.join(corpus_path, filename)
            print(f"📄 Cargando documento: {filename}")
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            all_documents.extend(documents)

    except Exception as e:
        print(f"❌ Error durante la carga de documentos: {e}")
        return
    
    if not all_documents:
        print("❌ No se pudieron cargar documentos. Terminando ingesta.")
        return

    print(f"✅ Total de páginas cargadas de {len(pdf_files)} PDFs: {len(all_documents)}")
    print("✂️  Dividiendo documentos en 'chunks'...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(all_documents)
    total_chunks = len(chunks)

    # --- Cargar a Chroma Cloud ---
    print(f"☁️  Creando embeddings y guardando en la colección '{COLLECTION_NAME}' en la nube...")
    
    # 1. Creamos la instancia de Chroma apuntando a la nube
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings_model,
        client=client
    )
    
    # 2. Eliminamos la colección existente para una carga limpia
    try:
        client.delete_collection(name=COLLECTION_NAME)
        # Se necesita recrear la colección después de borrarla
        vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings_model,
            client=client
        )
        print(f"🗑️  Colección antigua '{COLLECTION_NAME}' eliminada y recreada.")
    except Exception as e:
        print(f"⚠️  Advertencia: No se pudo eliminar la colección antigua (puede ser la primera vez): {e}")

    # --- INICIO DEL BATCHING (LOTES) ---
    for i in range(0, total_chunks, MAX_BATCH_SIZE):
        batch = chunks[i:i + MAX_BATCH_SIZE]
        batch_number = i // MAX_BATCH_SIZE + 1
        total_batches = (total_chunks + MAX_BATCH_SIZE - 1) // MAX_BATCH_SIZE
        print(f"  📦 Insertando lote {batch_number}/{total_batches} ({len(batch)} documentos)...")
        
        # Agregamos los documentos del lote
        vectorstore.add_documents(documents=batch)
        
        # Pausa para no saturar la API
        if i + MAX_BATCH_SIZE < total_chunks:
            time.sleep(2)

    print(f"✅ ¡Ingesta completa y subida a la nube! {total_chunks} chunks creados y guardados en '{COLLECTION_NAME}'.")
    # --- FIN DEL BATCHING ---


if __name__ == "__main__":
    ingest_documents()