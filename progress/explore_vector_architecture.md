# Exploracion de arquitectura backend para base vectorial de documentos

## Estado actual del backend

- La app backend es hexagonal liviana: HTTP en `back/app/entrypoints/api/routes.py`, reglas de negocio en `back/app/application/use_cases.py`, contratos en `back/app/domain/ports.py`, persistencia/integraciones en `back/app/infrastructure/`, wiring en `back/app/core/container.py`.
- Hoy solo existen tres capacidades persistidas:
  - usuarios (`UserModel` en `back/app/infrastructure/db/models.py`)
  - historial de chat (`ChatMessageModel` en `back/app/infrastructure/db/models.py`)
  - sesiones del agente ADK solo en memoria (`InMemorySessionService` dentro de `back/app/infrastructure/agent.py`)
- No existe soporte actual para upload de archivos, parsing documental, embeddings, vector store ni retrieval/RAG.
- No hay migraciones; el esquema se crea con `Base.metadata.create_all()` en startup desde `back/app/core/container.py`.
- `back/pyproject.toml` no incluye dependencias para parseo de PDF/Office, embeddings ni base vectorial.

## Flujo actual donde conviene integrarse

- El flujo relevante hoy es:
  - request HTTP -> `routes.py`
  - caso de uso -> `AskUseCase.execute()`
  - agente -> `ChatAgentPort.ask()`
  - persistencia del intercambio -> `SqlAlchemyChatRepository.create()`
- El punto exacto de integración para Q&A con documentos es `AskUseCase` en `back/app/application/use_cases.py`.
- Motivo:
  - ya valida existencia del usuario
  - ya aplica el `PromptSecurityFilter`
  - ya centraliza la llamada al agente
  - ya persiste el resultado final del intercambio
- La expansión correcta del flujo sería:
  - request HTTP con `username`, `message` y opcionalmente `document_ids`
  - `AskUseCase` o un caso derivado resuelve usuario
  - aplica seguridad al prompt
  - invoca un nuevo puerto de retrieval para obtener chunks relevantes del usuario
  - pasa `message + contexto recuperado + metadata de documentos` al agente
  - persiste la interacción de chat como hoy

## Punto exacto de integración por capa

### Entry point HTTP

- Archivo objetivo: `back/app/entrypoints/api/routes.py`
- Añadir dos capacidades nuevas:
  - endpoint de ingestión de documento(s)
  - endpoint de pregunta con alcance documental
- Recomendación de contratos:
  - `POST /documents/ingest`
  - `GET /documents`
  - `POST /ask_documents` o ampliar `POST /ask`
- Si se prioriza mínima ruptura de API, el mejor punto es ampliar `POST /ask` para aceptar `document_ids: list[str] | None`.
- Si se prefiere separar semánticas, `POST /ask_documents` evita mezclar chat general con RAG.

### Caso de uso de ingestión

- Archivo objetivo: `back/app/application/use_cases.py`
- Crear un caso de uso nuevo, por ejemplo `IngestDocumentsUseCase`.
- Responsabilidades:
  - validar usuario propietario
  - aceptar archivos soportados
  - delegar parsing/chunking/embedding a puertos
  - persistir documento, chunks y metadata
  - devolver IDs de documentos ingeridos y estado

### Caso de uso de retrieval para preguntas

- Archivo objetivo: `back/app/application/use_cases.py`
- Integración exacta:
  - o extender `AskUseCase`
  - o crear `AskWithDocumentsUseCase`
- Recomendación: crear `AskWithDocumentsUseCase` y dejar `AskUseCase` intacto.
- Razón:
  - `ChatAgentPort.ask()` actual solo acepta `username`, `role`, `message`
  - retrieval añade contexto, filtros por documento y metadata, una responsabilidad distinta del chat puro
  - reduce riesgo de regresión sobre el endpoint actual y sus tests

### Puertos de dominio nuevos

- Archivo objetivo: `back/app/domain/ports.py`
- Nuevos contratos recomendados:
  - `DocumentRepository`
  - `DocumentChunkRepository`
  - `DocumentStoragePort`
  - `DocumentParserPort`
  - `EmbeddingPort`
  - `DocumentRetrieverPort`
  - opcional: `DocumentAwareChatAgentPort`
- El puerto clave para Q&A sobre uno o múltiples documentos es `DocumentRetrieverPort`, con búsqueda por `username`, `query`, `document_ids opcionales` y `top_k`.

### Persistencia SQLAlchemy

- Archivos objetivo:
  - `back/app/infrastructure/db/models.py`
  - `back/app/infrastructure/repositories.py`
- La persistencia actual usa SQLAlchemy ORM y SQLite por defecto. La integración natural es agregar nuevas tablas ORM, no crear un almacén paralelo para metadata.

## Modelo de persistencia recomendado

- `DocumentModel`
  - `id`
  - `user_id`
  - `filename_original`
  - `storage_path` o `storage_uri`
  - `mime_type`
  - `extension`
  - `size_bytes`
  - `checksum_sha256`
  - `status` (`uploaded`, `parsed`, `indexed`, `failed`)
  - `page_count` nullable
  - `row_count` nullable
  - `sheet_names` nullable serializado
  - `created_at`
- `DocumentChunkModel`
  - `id`
  - `document_id`
  - `chunk_index`
  - `text`
  - `token_count` o `char_count`
  - `page_number` nullable
  - `sheet_name` nullable
  - `row_start` nullable
  - `row_end` nullable
  - `section_title` nullable
  - `metadata_json` o campos explícitos equivalentes
  - `created_at`
- `DocumentChunkEmbeddingModel` o embedding embebido en chunk
  - `chunk_id`
  - `embedding`
  - `embedding_model`
  - `created_at`

## Decisión importante sobre vector store

- SQLite sirve para metadata y texto fuente, pero no es un destino final ideal para similarity search seria.
- La arquitectura más limpia es separar:
  - metadata documental en SQLAlchemy/DB principal
  - embeddings y similarity search detrás de `DocumentRetrieverPort`
- Eso deja dos fases naturales:
  - fase 1: SQLite con embeddings serializados y reranking en aplicación
  - fase 2: mover solo `DocumentRetrieverPort` a una base vectorial real sin romper casos de uso
- El punto exacto de encapsulación es `DocumentRetrieverPort`, no `AskUseCase`.

## Recuperación para uno o múltiples documentos

- La recuperación debe filtrar siempre por `username` o `user_id`.
- Sobre un documento:
  - filtro por `document_id`
- Sobre múltiples documentos:
  - filtro por `document_ids IN (...)`
- El retrieval debe devolver no solo texto:
  - `chunk_text`
  - `document_id`
  - `filename_original`
  - ubicación interna (`page_number`, `sheet_name`, `row range`, etc.)
  - score de relevancia
- Ese payload debe alimentar al agente para que cite el origen del contexto y permita respuestas auditables.

## Integración con el agente actual

- Archivo actual: `back/app/infrastructure/agent.py`
- `AdkChatAgent.ask()` hoy arma un único prompt plano y no acepta contexto documental.
- El punto exacto para extenderlo es ese método, pero no conviene mezclar retrieval ahí.
- Recomendación:
  - mantener retrieval fuera del agente
  - hacer que el caso de uso entregue al agente un `message` enriquecido con contexto recuperado
- Si luego se quiere algo más limpio, crear un puerto nuevo tipo `ask_with_context(...)`.
- En la arquitectura actual, el cambio mínimo y consistente es:
  - `AskWithDocumentsUseCase` recupera chunks
  - compone un prompt estructurado
  - llama al agente ADK existente

## Pipeline de ingestión propuesto

- `POST /documents/ingest`
- validar usuario
- guardar archivo crudo mediante `DocumentStoragePort`
- crear `DocumentModel` en estado `uploaded`
- parsear según tipo:
  - `pdf`
  - `csv`
  - `doc/docx`
  - `xls/xlsx`
- normalizar a texto + unidades de origen
- chunkear preservando metadata de procedencia
- generar embeddings
- persistir chunks + embeddings + metadata
- actualizar `DocumentModel.status = indexed`

## Metadata mínima útil por tipo de archivo

- PDF:
  - `page_number`
  - encabezado/sección si puede inferirse
- CSV:
  - `row_start`, `row_end`
  - columnas presentes
- DOC/DOCX:
  - heading o bloque semántico
  - orden del bloque
- XLS/XLSX:
  - `sheet_name`
  - `row_start`, `row_end`
  - columnas presentes

## Restricciones y riesgos detectados

- `create_all()` en startup no es suficiente para una evolución de esquema compleja con documentos/chunks/embeddings; al implementar esto conviene introducir migraciones.
- `InMemorySessionService` implica que la memoria conversacional del agente se pierde al reiniciar; no bloquea retrieval, pero limita continuidad conversacional.
- `PromptSecurityFilter` hoy opera solo sobre el mensaje del usuario; al añadir contexto documental habrá que cuidar prompt injection desde el contenido recuperado.
- `docs/architecture.md` exige errores explícitos. La ingestión debe modelar excepciones nombradas para archivo inválido, formato no soportado, parseo fallido y documento no encontrado.

## Recomendación final de integración exacta

- Mantener la arquitectura hexagonal actual.
- Agregar la feature en estos puntos exactos:
  - `back/app/entrypoints/api/routes.py`: endpoints de ingestión y consulta documental
  - `back/app/entrypoints/api/schemas.py`: contratos para archivos, documentos y filtros
  - `back/app/application/use_cases.py`: `IngestDocumentsUseCase` y `AskWithDocumentsUseCase`
  - `back/app/domain/ports.py`: puertos de storage, parser, embeddings, repositorios documentales y retriever
  - `back/app/infrastructure/db/models.py`: tablas `documents`, `document_chunks` y soporte para embeddings
  - `back/app/infrastructure/repositories.py`: repositorios SQLAlchemy para documentos y chunks
  - `back/app/infrastructure/agent.py`: solo extensión de entrada para contexto, no retrieval
  - `back/app/core/container.py`: wiring de nuevos adapters

## Respuesta concreta a "dónde integrar"

- Ingestión de archivos:
  - nuevo endpoint en `routes.py`
  - caso de uso nuevo en `use_cases.py`
  - persistencia principal en `db/models.py` + `repositories.py`
- Persistencia de chunks/metadatos:
  - nuevas tablas SQLAlchemy en `db/models.py`
  - repositorios dedicados en `repositories.py`
- Recuperación para Q&A de uno o varios documentos:
  - nuevo `DocumentRetrieverPort` en `domain/ports.py`
  - llamado desde `AskWithDocumentsUseCase` en `application/use_cases.py`
  - paso del contexto recuperado al agente en `infrastructure/agent.py`

## Secuencia sugerida para el siguiente agente

- 1. Definir entidades y puertos documentales.
- 2. Crear modelos SQLAlchemy para `documents` y `document_chunks`.
- 3. Implementar endpoint y caso de uso de ingestión.
- 4. Implementar `DocumentRetrieverPort`.
- 5. Crear `AskWithDocumentsUseCase`.
- 6. Ampliar tests API y de repositorios.
