# Exploración técnica: vector stack local

Fecha: 2026-05-17

## Resumen ejecutivo

Hoy el repo no tiene capacidades implementadas de embeddings, retrieval, RAG, ingestión documental ni vector store. Sí tiene dos piezas reutilizables para construirlo con poco desvío del stack actual:

- Backend Python/FastAPI con arquitectura hexagonal y puertos claros para agregar un nuevo bounded context de documentos y recuperación: [back/app/domain/ports.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/domain/ports.py:8), [back/app/entrypoints/api/routes.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/entrypoints/api/routes.py:43).
- Ecosistema Google ya presente vía `google-adk` y `google-genai`, por lo que la opción más coherente para embeddings es Gemini en vez de introducir otro proveedor: [back/pyproject.toml](/Users/roshi/Dev/playGround/python_interviewI/back/pyproject.toml:7), [back/uv.lock](/Users/roshi/Dev/playGround/python_interviewI/back/uv.lock:607), [back/uv.lock](/Users/roshi/Dev/playGround/python_interviewI/back/uv.lock:1112).

Mi recomendación para una vector database local es `qdrant-client` en modo local persistido a disco. Mantiene la simplicidad de desarrollo local, encaja bien con Python, soporta filtros por metadata mejor que una solución casera en SQLite y deja un camino limpio a crecer a Qdrant server/cloud sin reescribir la capa de acceso.

## Qué existe ya en el repo

### 1. Stack backend reutilizable

- FastAPI + SQLAlchemy + configuración por `BaseSettings`: [back/pyproject.toml](/Users/roshi/Dev/playGround/python_interviewI/back/pyproject.toml:7), [back/app/core/config.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/core/config.py:9).
- Persistencia actual en SQLite por defecto: [back/app/core/config.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/core/config.py:13), [back/app/core/container.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/core/container.py:34).
- Contenedor central donde sería natural inyectar un `DocumentRepository`, `EmbeddingProvider` y `VectorStore`: [back/app/core/container.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/core/container.py:15).

### 2. Integración IA ya presente

- El agente actual usa Google ADK con `google.genai` y modelo Gemini configurado por env vars: [back/app/infrastructure/agent.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/infrastructure/agent.py:7), [back/app/infrastructure/agent.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/infrastructure/agent.py:39), [back/app/core/config.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/core/config.py:25).
- El estado conversacional del agente es en memoria (`InMemorySessionService`), no hay memoria documental ni recuperación persistente: [back/app/infrastructure/agent.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/infrastructure/agent.py:37).

### 3. Persistencia actual útil pero insuficiente

- Sólo existen tablas para usuarios y mensajes de chat: [back/app/infrastructure/db/models.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/infrastructure/db/models.py:15), [back/app/infrastructure/db/models.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/infrastructure/db/models.py:33).
- No hay tablas o entidades para documentos, chunks, embeddings, colecciones ni metadatos de archivo.

### 4. Superficie API actual

- Sólo hay endpoints de usuarios, chat, historial y health: [back/app/entrypoints/api/routes.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/entrypoints/api/routes.py:43), [back/app/entrypoints/api/routes.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/entrypoints/api/routes.py:99), [back/app/entrypoints/api/routes.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/entrypoints/api/routes.py:149), [back/app/entrypoints/api/routes.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/entrypoints/api/routes.py:181).
- No hay `UploadFile`, `multipart/form-data`, schemas de documentos ni endpoints para ingestión o búsqueda.

## Qué NO existe hoy

- Vector DB o índice vectorial.
- Capa de embeddings.
- Pipeline de chunking.
- Parsing de PDF, DOC/DOCX, XLS/XLSX.
- Persistencia de archivos subidos o referencia a blob storage.
- Metadata de documentos por usuario.
- Búsqueda híbrida, reranking o filtros por documento.
- Jobs asíncronos para ingestión pesada.

## Dependencias actuales relevantes

### Presentes

- `google-adk` y `google-genai`: ya permiten mantener el proveedor IA en Google: [back/uv.lock](/Users/roshi/Dev/playGround/python_interviewI/back/uv.lock:607), [back/uv.lock](/Users/roshi/Dev/playGround/python_interviewI/back/uv.lock:1112).
- `sqlalchemy` y SQLite: base para metadata transaccional de documentos: [back/uv.lock](/Users/roshi/Dev/playGround/python_interviewI/back/uv.lock:2670), [back/app/core/config.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/core/config.py:13).
- `aiosqlite` llega transitivamente por ADK, pero no se usa en la app: [back/uv.lock](/Users/roshi/Dev/playGround/python_interviewI/back/uv.lock:135).

### Ausentes

No aparecen dependencias directas o transitivas claras para:

- vector DB: `qdrant-client`, `chromadb`, `faiss-cpu`, `pgvector`, `sqlite-vec`
- parsing PDF: `pypdf`, `pdfplumber`, `pymupdf`
- DOCX: `python-docx`, `docx2txt`
- XLSX/XLS: `openpyxl`, `xlrd`, `pandas`
- chunking / loaders: `unstructured`, `langchain`, `llama-index`

## Opción más coherente para vector DB local

### Recomendación

Usar `qdrant-client` en modo local persistido en disco, y mantener embeddings con Gemini.

### Por qué esta opción encaja mejor

- Respeta el stack actual de Python backend sin meter otro runtime.
- No obliga a correr un servicio aparte en la primera iteración: Qdrant local puede persistir a un path.
- Es mejor candidato que “todo en SQLite” para búsqueda vectorial real con metadata filters.
- Da una ruta de crecimiento limpia: mismo cliente y modelo mental para pasar de local a server.
- Encaja bien con la arquitectura hexagonal: la app ya separa puertos y adaptadores, así que un `VectorStorePort` sería natural.

### Por qué no elegiría primero otras opciones

- `sqlite-vec`: conceptualmente atrae porque ya usan SQLite, pero añade fricción de extensiones, ergonomía más baja y un camino menos claro para retrieval con filtros y evolución operativa.
- `Chroma`: también serviría para local y es simple, pero aquí no aporta ventaja estructural clara porque el repo no usa LangChain/LlamaIndex, y Qdrant deja mejor camino de escalado manteniendo una API parecida.
- `FAISS`: útil como librería de índice, pero obligaría a resolver por cuenta propia persistencia, filtros por metadata y operación del índice.

## Opción más coherente para embeddings

Usar embeddings de Gemini vía `google-genai`, no otro proveedor.

Razones:

- Ya existe `GOOGLE_API_KEY` y `GCP_PROJECT_ID` en settings: [back/app/core/config.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/core/config.py:17).
- El backend ya inicializa y usa el stack Google para chat: [back/app/infrastructure/agent.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/infrastructure/agent.py:30).
- Reduce dispersión de credenciales, observabilidad y soporte.

## Gaps concretos por tipo de archivo

### PDF

Gap actual:

- No hay parser de PDF.
- No hay estrategia para extraer texto por página ni metadata.

Dependencias probables:

- `pypdf` como baseline simple.
- Si se espera PDF complejo, tablas o layouts difíciles, probablemente hará falta algo más fuerte que `pypdf`.

### CSV

Gap actual:

- No hay pipeline de ingestión tabular.

Dependencias probables:

- Se puede arrancar con `csv` de stdlib si el objetivo es texto plano.
- Si quieren normalización robusta, encoding handling, preview y chunking por filas/columnas, conviene `pandas`.

### DOC / DOCX

Gap actual:

- No hay parser ni estrategia diferenciada para `doc` vs `docx`.

Dependencias probables:

- `docx` moderno: `python-docx` o `docx2txt`.
- `doc` legacy: suele requerir conversión previa o tooling adicional. Es el formato con más riesgo operativo; conviene declararlo explícitamente como “best effort” o convertirlo a `docx/pdf` antes de indexar.

### XLS / XLSX

Gap actual:

- No hay parser de hojas ni estructura tabular.

Dependencias probables:

- `xlsx`: `openpyxl`.
- `xls` legacy: `xlrd` o conversión previa.
- Si quieren una sola capa tabular razonable para csv/xls/xlsx, `pandas` simplifica mucho el pipeline.

## Gaps transversales de configuración

- Falta un directorio/config para guardar archivos originales o temporales.
- Falta config para path local del vector store.
- Falta config para colección por ambiente.
- Falta config para modelo de embeddings y dimensiones.
- Falta config para límites de tamaño, extensiones y timeouts de ingestión.
- Falta modelado de metadata mínima: `user_id`, `document_id`, `filename`, `mime_type`, `source_type`, `page`, `sheet`, `row_range`, `chunk_index`, `created_at`.
- Falta decidir si los archivos se guardan en disco local o sólo se extrae texto y se descarta el binario.

## Lectura de coherencia con la arquitectura actual

La arquitectura actual favorece separar:

- metadata documental en SQLAlchemy/SQLite
- vectores y búsqueda en un adaptador independiente
- embeddings en un proveedor Google aislado

Eso conserva la forma actual del sistema:

- puertos de dominio: hoy ya existen para usuarios/chat: [back/app/domain/ports.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/domain/ports.py:8)
- adaptadores de infraestructura: hoy ya existen para DB y agente: [back/app/core/container.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/core/container.py:27)

## Conclusión

La capacidad de recuperación documental hoy es esencialmente cero, pero el repo sí tiene una base razonable para agregarla sin pelear contra el stack.

La combinación más coherente es:

- embeddings con Gemini usando `google-genai`
- vector store local con `qdrant-client` en modo local persistido
- metadata documental en la SQLite actual vía SQLAlchemy
- parsers mínimos nuevos: `pypdf`, `python-docx` o `docx2txt`, `openpyxl`, y probablemente `pandas` para tabulares

El principal punto delicado no es la vector DB sino los formatos legacy `doc` y `xls`, porque requieren una política explícita de soporte o conversión.

## Fuentes externas consultadas

- Gemini Embeddings API: https://ai.google.dev/api/embeddings
- Qdrant local mode en Python client: https://python-client.qdrant.tech/qdrant_client.local.qdrant_local.html
- Qdrant quickstart/local docs: https://qdrant.tech/documentation/quick-start/
- Chroma Python client docs: https://docs.trychroma.com/reference/python/client
