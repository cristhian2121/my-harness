## Resultado

Implementada la feature backend de documentos con base vectorial local y Q&A documental.

## Alcance entregado

- Endpoints nuevos:
  - `POST /documents`
  - `GET /documents`
  - `GET /documents/{document_id}`
  - `POST /documents/ask`
- Se mantuvieron sin romper contrato:
  - `POST /ask`
  - `GET /history/{username}`
- Metadata documental persistida en SQLite/SQLAlchemy.
- Vector store local persistido detrás de adapter usando `qdrant-client` local mode.
- Retrieval fuera del agente; el contexto se compone en un caso de uso documental dedicado.
- Formatos soportados en esta iteración:
  - `.pdf`
  - `.csv`
  - `.docx`
  - `.xlsx`
- Errores explícitos para formatos legacy no soportados:
  - `.doc`
  - `.xls`
- `POST /documents/ask` devuelve respuesta y fuentes útiles con `document_id`, `filename`, `snippet`, `score` y localización de chunk.
- Se reforzó el prompt documental indicando explícitamente que el contenido recuperado es no confiable y nunca debe sobreescribir instrucciones del sistema.

## Cambios principales

- Dominio:
  - nuevas entidades documentales y puertos de documentos/vector store/embeddings/parser/storage.
- Aplicación:
  - `IngestDocumentUseCase`
  - `ListDocumentsUseCase`
  - `GetDocumentDetailUseCase`
  - `AskDocumentsUseCase`
  - nuevas excepciones documentales
- Infraestructura:
  - modelos SQLAlchemy `documents` y `document_chunks`
  - repositorios SQLAlchemy para documentos y chunks
  - storage local en disco
  - parser local para `pdf/csv/docx/xlsx`
  - embeddings locales deterministas por hashing
  - adapter Qdrant local persistido con inicialización lazy para evitar locks en import-time
- API:
  - schemas y rutas nuevas para documentos
- Config:
  - settings para directorios de documentos/vector store y dimensiones de embeddings
- Dependencias mínimas añadidas en `back/pyproject.toml`:
  - `python-multipart`
  - `qdrant-client`
  - `pypdf`
  - `python-docx`
  - `openpyxl`

## Tests añadidos/validados

- upload requiere usuario existente
- rechazo explícito de `.doc`
- flujo upload/list/detail
- ingestión `.xlsx` con metadata de sheets
- ingestión `.docx`
- control de acceso en detalle
- document ask multi-documento con fuentes
- bloqueo de prompt inseguro en document ask
- no regresión del contrato de `/ask`

## Verificación ejecutada

- `python3 -m compileall back/app back/tests`
- `uv sync --directory back --dev`
- `uv run --directory back pytest`
- Resultado final: `20 passed`

## Bloqueos

- Ninguno.
