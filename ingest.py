# ingest.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
# --- CAMBIO 1: Importar desde 'langchain-huggingface' ---
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.tools.text import RecursiveCharacterTextSplitter

# Cargar variables de entorno
load_dotenv()

# --- Configuración ---
print("Cargando modelo de embeddings local (la primera vez puede tardar)...")
# --- CAMBIO 2: Usar la nueva clase 'HuggingFaceEmbeddings' ---
# El nombre del modelo 'all-MiniLM-L6-v2' sigue siendo el mismo.
embeddings_model = HuggingFaceEmbeddings(
    model_name='all-MiniLM-L6-v2'
)
print("Modelo de embeddings cargado.")

vectorstore_path = "chroma_db"
corpus_path = "corpus"

def ingest_documents():
    print("Iniciando ingesta de documentos...")
    
    all_documents = [] 
    print(f"Buscando PDFs en el directorio: {corpus_path}")

    try:
        pdf_files = [f for f in os.listdir(corpus_path) if f.endswith(".pdf")]
        if not pdf_files:
            print("Error: No se encontraron archivos .pdf en la carpeta 'corpus'.")
            return

        for filename in pdf_files:
            file_path = os.path.join(corpus_path, filename)
            print(f"Cargando documento: {filename}")
            
            try:
                loader = PyPDFLoader(file_path)
                documents = loader.load()
                all_documents.extend(documents)
            except Exception as e:
                print(f"  -> Error al cargar {filename}: {e}. Saltando este archivo.")
                continue

    except FileNotFoundError:
        print(f"Error: El directorio '{corpus_path}' no existe.")
        return
    
    if not all_documents:
        print("No se pudieron cargar documentos. Terminando ingesta.")
        return

    print(f"Total de páginas cargadas de {len(pdf_files)} PDFs: {len(all_documents)}")

    print("Dividiendo documentos en 'chunks'...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(all_documents)

    print(f"Creando embeddings y guardando en '{vectorstore_path}'...")
    vectorstore = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings_model, # <--- Usa el modelo local
        persist_directory=vectorstore_path
    )
    
    vectorstore.persist()
    print(f"¡Ingesta completa! {len(chunks)} chunks creados y guardados.")

if __name__ == "__main__":
    ingest_documents()