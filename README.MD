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

* `app.py`: Aplicación principal de Streamlit (Chatbot).
* `dashboard.py`: Aplicación de Streamlit (Dashboard de métricas).
* `evaluate.py`: Script para ejecutar la evaluación de modelos.
* `ingest.py`: Script para la ingesta de documentos a ChromaDB.
* `requirements.txt`: Lista de dependencias de Python.
* `.env.example`: Plantilla para las variables de entorno.
* `Dockerfile`: Instrucciones para construir la imagen de Docker.
* `Dockerfile.dashboard`: Instrucciones para construir la imagen de Docker.
* `docker-compose.yml`: Archivo para orquestar los servicios de Docker.
* `/json`: Contiene el `gold_set.json` y los resultados en `cuaderno_metricas.json`.
* `/corpus`: (Directorio local, no versionado) Debes crear esta carpeta y añadir tus archivos PDF allí.

---

## 🐳 Ejecución con Docker-Compose (Método Recomendado)

Este método te permite ejecutar todo el proyecto (chatbot, dashboard y scripts) de forma aislada y reproducible con un solo comando.

**Requisitos:**
* **Docker Desktop** instalado y en ejecución.

### Paso 1: Configurar Variables de Entorno

El repositorio ya incluye un `.env.example`.
1.  Crea una copia del archivo `.env.example` y renuébrala a `.env`.
2.  Abre el archivo `.env` y rellena todas las API keys necesarias (GOOGLE, GROQ, CHROMA).

### Paso 2: Preparar los Documentos

1.  Crea una carpeta llamada `corpus` en la raíz del proyecto (si no existe).
2.  Añade todos los archivos `.pdf` que desees ingestar dentro de la carpeta `corpus/`.

### Paso 3: Corregir `requirements.txt` (¡Crítico!)

Para que la imagen de Docker se construya correctamente, tu archivo `requirements.txt` no debe tener paquetes en conflicto. Asegúrate de que su contenido sea el siguiente:

```txt
streamlit
langchain_core
python-dotenv
langchain_google_genai
langchain_groq
langchain_community
langchain_huggingface
langchain-chroma
chromadb
pandas
plotly
sentence-transformers
```

### Paso 4: Ingesta de Datos (Solo la primera vez)

Este comando construirá tu imagen de Docker (basado en el `Dockerfile`) y ejecutará el script `ingest.py`.

```bash
docker-compose run --rm ingest
```

### Paso 5: Generar Métricas (Opcional)

Si deseas pre-generar el archivo `cuaderno_metricas.json` antes de lanzar el dashboard, ejecuta:

```bash
docker-compose run --rm evaluate
```
*(El archivo aparecerá en tu carpeta local `/json` gracias a la configuración de volúmenes en `docker-compose.yml`)*.

### Paso 6: ¡Levantar las Aplicaciones!

Este es el comando principal. Inicia el chatbot y el dashboard al mismo tiempo.

```bash
docker-compose up
```
(O para ejecutarlo en segundo plano, usa `docker-compose up -d`)

Una vez ejecutado, tus aplicaciones estarán disponibles en:
* **🤖 Chatbot:** `http://localhost:8501`
* **📊 Dashboard:** `http://localhost:8502`

### Paso 7: Detener los Servicios

* Si lo ejecutaste con `docker-compose up`, simplemente presiona `Ctrl + C` en la terminal.
* Si lo ejecutaste con `-d`, usa el comando:

```bash
docker-compose down
```

---

## ⚙️ Instalación y Uso (Método Local / Manual)

Este es el método alternativo si prefieres no usar Docker y ejecutar todo en tu máquina local.

### 1. Clonar el Repositorio

```bash
git clone [https://github.com/danield413/ChatBot-SistemasInteligentesI.git](https://github.com/danield413/ChatBot-SistemasInteligentesI.git)
cd ChatBot-SistemasInteligentesI
```

### 2. Crear un Entorno Virtual (Recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

Asegúrate de usar la versión corregida de `requirements.txt` (mencionada en la sección de Docker) para evitar conflictos.

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` (copiando de `.env.example`) y rellena tus API keys.

---

## 🚀 Uso del Pipeline (Método Local / Manual)

Sigue estos pasos en orden para ejecutar el proyecto localmente.

### Paso 1: Preparar los Documentos

1.  Crea una carpeta llamada `corpus` en la raíz del proyecto.
2.  Añade todos los archivos `.pdf` que desees ingestar dentro de la carpeta `corpus/`.

### Paso 2: Ingesta de Datos en ChromaDB

Ejecuta el script de ingesta. Este script leerá los PDFs de `/corpus`, los procesará y los subirá a tu instancia de ChromaDB Cloud.

```bash
python ingest.py
```

### Paso 3: Generar el Cuaderno de Métricas

Este script ejecutará el `gold_set.json` y guardará los resultados en `cuaderno_metricas.json`.

```bash
python evaluate.py
```

### Paso 4: Calificación Manual y Visualización

Inicia el dashboard de Streamlit.

```bash
streamlit run dashboard.py
```

### Paso 5: Iniciar el Chatbot Comparativo

Inicia la aplicación de chat principal.

```bash
streamlit run app.py
```