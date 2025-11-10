# ChatBot de Sistemas Inteligentes I

Este proyecto es un sistema de chatbot RAG (Generación Aumentada por Recuperación) desarrollado para el curso de Sistemas Inteligentes I en la Universidad de Caldas. El sistema ingiere documentos académicos sobre IA, procesa preguntas y compara en tiempo real las respuestas de dos Grandes Modelos de Lenguaje (LLMs): **Gemini** (de Google) y **Llama 3.1** (ejecutado a través de Groq).

El proyecto incluye un pipeline completo:
1.  **Ingesta de Datos:** Para alimentar una base de datos vectorial en la nube (ChromaDB).
2.  **Evaluación de Modelos:** Un script para ejecutar un "gold set" de preguntas y generar métricas.
3.  **Dashboard de Métricas:** Una aplicación de Streamlit para visualizar y calificar manualmente el rendimiento de los modelos.
4.  **Aplicación de Chat:** Una interfaz de Streamlit para chatear y comparar los modelos lado a lado.

## 🤖 Autores

* Daniel Alberto Díaz
* Juan Manuel Figueroa

---

## 🚀 Características Principales

* **Comparativa de LLMs en Paralelo:** Interfaz de chat que muestra las respuestas de Gemini y Llama 3.1 simultáneamente.
* **Pipeline RAG:** Utiliza LangChain para orquestar un pipeline de RAG que recupera contexto de una base de datos vectorial antes de generar una respuesta.
* **Base de Datos Vectorial en la Nube:** Integración con **ChromaDB Cloud** para almacenar y consultar los embeddings de los documentos.
* **Ingesta de Documentos:** Script para procesar archivos PDF locales, dividirlos en fragmentos (`chunks`) y subirlos a la base de datos vectorial.
* **Evaluación Automatizada:** Script para ejecutar un conjunto de preguntas predefinidas (`gold_set.json`) contra ambos modelos y registrar sus respuestas, contexto y latencia.
* **Dashboard Interactivo de Métricas:** Visualización de KPIs (Score Global, Cobertura, Alucinación, Citas Válidas) y gráficos comparativos usando Streamlit y Plotly.
* **Editor de Calificaciones:** El dashboard permite editar y guardar manualmente las calificaciones (Exactitud, Claridad, etc.) para cada respuesta generada, recalculando el score en tiempo real.

---

## 🛠️ Stack Tecnológico

* **Frameworks:** Streamlit, LangChain
* **LLMs:**
    * Google Gemini (`gemini-2.5-flash`) via `langchain_google_genai`
    * Llama 3.1-8B (`llama-3.1-8b-instant`) via `langchain_groq`
* **Base de Datos Vectorial:** ChromaDB Cloud (`langchain-chroma`)
* **Modelo de Embeddings:** `all-MiniLM-L6-v2` (via `langchain_huggingface`)
* **Visualización y Datos:** Pandas, Plotly

---

## 📂 Componentes del Proyecto

* `app.py`: Aplicación principal de Streamlit. Es la interfaz de chat comparativa.
* `dashboard.py`: Aplicación de Streamlit. Es el dashboard de visualización y edición de métricas.
* `evaluate.py`: Script para ejecutar las preguntas del `gold_set.json` contra los modelos y generar el archivo `cuaderno_metricas.json`.
* `ingest.py`: Script para leer los PDFs de la carpeta `corpus/`, generar embeddings y subirlos a ChromaDB Cloud.
* `requirements.txt`: Lista de dependencias de Python.
* `.env.example`: Plantilla para las variables de entorno necesarias.
* `/json`: Contiene el `gold_set.json` (preguntas de prueba) y el `cuaderno_metricas.json` (respuestas y calificaciones).
* `/corpus`: (Directorio local, no versionado) Debes crear esta carpeta y añadir tus archivos PDF allí.

---

## ⚙️ Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/danield413/ChatBot-SistemasInteligentesI.git
cd ChatBot-SistemasInteligentesI
```

### 2. Crear un Entorno Virtual (lo recomendamos)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

En caso de que alguna dependencia no se instale, puedes hacerlo manualmente.

### 4. Configurar Variables de Entorno

Crea un archivo llamado `.env` en la raíz del proyecto, copiando el contenido de `.env.example`. Deberás conseguir las API keys correspondientes:

```ini
# Configuración del ChatBot IA

# LLMs y API Keys
GOOGLE_API_KEY=tu_google_api_key_aqui
GROQ_API_KEY=tu_groq_api_key_aqui

# Chroma Cloud Configuration
CHROMA_API_KEY=tu_chroma_api_key_aqui
CHROMA_TENANT=tu_tenant_id_aqui

# Estos valores ya vienen en el .env.example y son usados por los scripts
CHROMA_DATABASE=ChatBotSI
CHROMA_COLLECTION_NAME=IA_DOCS
MAX_BATCH_SIZE=300
```

---

## 🚀 Uso del Pipeline

Sigue estos pasos en orden para ejecutar el proyecto.

### Paso 1: Preparar los Documentos

1.  Crea una carpeta llamada `corpus` en la raíz del proyecto.
2.  Añade todos los archivos `.pdf` que desees ingestar dentro de la carpeta `corpus/`.

*(Nota: Esta carpeta está ignorada por `.gitignore`, por lo que no se subirá al repositorio).*

### Paso 2: Ingesta de Datos en ChromaDB

Ejecuta el script de ingesta. Este script leerá los PDFs de `/corpus`, los procesará y los subirá a tu instancia de ChromaDB Cloud.

```bash
python ingest.py
```

### Paso 3: Generar el Cuaderno de Métricas

Este script ejecutará todas las preguntas del archivo `json/gold_set.json` contra ambos modelos (Gemini y Llama 3.1) usando el contexto de RAG. Las respuestas y métricas de latencia se guardarán en `json/cuaderno_metricas.json`.

```bash
python evaluate.py
```

### Paso 4: Calificación Manual y Visualización

Inicia el dashboard de Streamlit. Esta aplicación te permitirá:
1.  Visualizar las métricas de rendimiento (Score, Latencia, etc.).
2.  Leer cada pregunta y la respuesta generada por los modelos.
3.  **Calificar manualmente** las métricas cualitativas (Exactitud, Cobertura, Claridad, etc.) en la pestaña "Editor de Métricas".
4.  Guardar tus calificaciones de vuelta en el archivo `json/cuaderno_metricas.json`.

```bash
streamlit run dashboard.py
```

### Paso 5: Iniciar el Chatbot Comparativo

Una vez que los datos están en ChromaDB, puedes iniciar la aplicación de chat principal para interactuar con los modelos en tiempo real.

```bash
streamlit run app.py
```