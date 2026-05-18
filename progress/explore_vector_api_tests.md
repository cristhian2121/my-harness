# Hallazgos API/tests para soporte de documentos vectorizados

## Estado actual relevante

- La API hoy solo expone usuarios, `POST /ask`, historial por usuario y healthcheck en [back/app/entrypoints/api/routes.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/entrypoints/api/routes.py:40).
- Los contratos HTTP actuales están en [back/app/entrypoints/api/schemas.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/entrypoints/api/schemas.py:8) y no tienen noción de documentos, adjuntos, metadata ni fuentes recuperadas.
- El dominio solo modela `User` y `ChatInteraction` en [back/app/domain/entities.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/domain/entities.py:8), con puertos para `UserRepository`, `ChatRepository` y `ChatAgentPort` en [back/app/domain/ports.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/domain/ports.py:8).
- `AskUseCase` persiste una interacción y delega al agente con `username`, `role` y `message` en [back/app/application/use_cases.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/application/use_cases.py:45). No hay capa intermedia para recuperación documental.
- La cobertura backend hoy está concentrada en [back/tests/test_api.py](/Users/roshi/Dev/playGround/python_interviewI/back/tests/test_api.py:1) y solo valida el flujo actual de usuarios/chat.

## Restricción arquitectónica que conviene respetar

- No conviene “deformar” `POST /ask` para mezclar chat general con carga de archivos o Q&A documental.
- El encaje más limpio con la arquitectura actual es:
  - mantener `POST /ask` para chat general;
  - añadir nuevos casos de uso para documentos;
  - añadir nuevos puertos para almacenamiento de documentos, indexación/vector store y recuperación;
  - añadir endpoints específicos de documentos en la capa `entrypoints/api`.

## Endpoints a añadir o tocar

### 1. Carga de documentos

- Añadir `POST /documents`.
- Motivo:
  - subir archivo no encaja en JSON puro; debe usar `multipart/form-data`;
  - evita romper el contrato actual de `POST /ask`.
- Request esperado:
  - `file`;
  - `username`;
  - metadata opcional simple como `title`, `tags`, `source`.
- Response recomendada:
  - `document_id`;
  - `username`;
  - `filename`;
  - `content_type`;
  - `size_bytes`;
  - `status` tipo `uploaded | processing | ready | failed`;
  - `created_at`;
  - metadata útil ya normalizada.
- Códigos a cubrir:
  - `201` carga aceptada/creada;
  - `400` archivo vacío o tipo no soportado;
  - `404` usuario inexistente;
  - `409` duplicado si se decide deduplicar por checksum;
  - `422` payload inválido.

### 2. Listado de documentos por usuario

- Añadir `GET /documents`.
- Query params recomendados:
  - `username` obligatorio si se mantiene el modelo actual centrado en usuario;
  - `status` opcional;
  - `limit` y `offset`.
- Response recomendada:
  - lista de documentos con metadata resumida;
  - `total` para paginación simple.
- Esto cubre la necesidad de “listado/metadata útil” sin forzar a abrir cada documento.

### 3. Detalle/metadata de un documento

- Añadir `GET /documents/{document_id}`.
- Response recomendada:
  - mismos campos del listado;
  - metadata expandida: `page_count`, `chunk_count`, `checksum`, `storage_key`, `error_detail` si falló, `processed_at`.
- Este endpoint reduce acoplamiento: el frontend no tiene que inferir readiness o fallos desde la lista.

### 4. Preguntas sobre uno o múltiples documentos

- Añadir un endpoint nuevo y separado del chat general:
  - preferencia: `POST /documents/ask`.
- Request recomendado:
  - `username`;
  - `question`;
  - `document_ids: list[str]`.
- Regla:
  - permitir 1 o muchos `document_ids`; no hace falta un endpoint distinto para “single” y “multi”.
- Response recomendada:
  - `answer`;
  - `status` tipo `answered | blocked | no_context`;
  - `document_ids` usados;
  - `sources` con trazabilidad mínima por chunk;
  - `created_at`.
- `sources` debería incluir, como mínimo:
  - `document_id`;
  - `filename`;
  - `chunk_id` o identificador equivalente;
  - `snippet`;
  - `score` si existe ranking.
- Mantenerlo separado de `POST /ask` evita romper clientes existentes y conserva la semántica del flujo actual.

### 5. Posible ajuste menor al historial

- Si se quiere que las preguntas documentales también aparezcan en historial, hay dos caminos:
  - reutilizar `ChatInteraction` con metadata adicional;
  - crear un historial paralelo de “document interactions”.
- Para no romper el contrato actual de `GET /history/{username}`, conviene no tocarlo en una primera entrega.
- Si se amplía después, hacerlo añadiendo campos opcionales, no reemplazando `items`.

## Esquemas HTTP a añadir o tocar

### Nuevos esquemas

- `DocumentMetadataResponse`
- `DocumentUploadResponse`
- `DocumentListResponse`
- `DocumentDetailResponse`
- `DocumentQuestionRequest`
- `DocumentQuestionResponse`
- `DocumentSourceResponse`
- `DocumentErrorResponse` si se quiere distinguir errores de procesamiento/indexación

### Campos mínimos recomendados

- Para documento:
  - `id`
  - `username`
  - `filename`
  - `content_type`
  - `size_bytes`
  - `status`
  - `created_at`
- Para metadata útil:
  - `title`
  - `tags`
  - `source`
  - `page_count`
  - `chunk_count`
  - `checksum`
  - `processed_at`
  - `error_detail`
- Para pregunta documental:
  - request: `username`, `question`, `document_ids`
  - response: `answer`, `status`, `document_ids`, `sources`, `created_at`

### Esquemas actuales que conviene no romper

- `AskRequest` y `AskResponse` en [back/app/entrypoints/api/schemas.py](/Users/roshi/Dev/playGround/python_interviewI/back/app/entrypoints/api/schemas.py:35) deberían quedarse intactos.
- `HistoryItemResponse` solo debería tocarse si se acepta ampliar el historial; no parece necesario para la primera iteración.

## Pruebas backend que habría que añadir o tocar

### Archivo de tests actual

- [back/tests/test_api.py](/Users/roshi/Dev/playGround/python_interviewI/back/tests/test_api.py:1) hoy es el punto natural para arrancar cobertura de endpoints nuevos.
- Si el archivo crece demasiado, sería razonable dividirlo luego en:
  - `test_api_documents.py`
  - `test_api_document_qa.py`

### Tests de carga de documentos

- `test_upload_document_requires_existing_user`
- `test_upload_document_rejects_unsupported_extension_or_content_type`
- `test_upload_document_rejects_empty_file`
- `test_upload_document_returns_metadata_and_processing_status`
- `test_upload_document_can_record_optional_metadata`
- `test_upload_document_handles_duplicate_file_policy`

### Tests de listado/detalle

- `test_list_documents_returns_only_user_documents`
- `test_list_documents_supports_status_filter`
- `test_list_documents_includes_useful_metadata`
- `test_get_document_detail_returns_expanded_metadata`
- `test_get_document_detail_returns_404_for_unknown_document`
- `test_get_document_detail_rejects_access_to_other_user_document` si se añade ownership estricto

### Tests de preguntas sobre documentos

- `test_document_question_requires_existing_user`
- `test_document_question_requires_at_least_one_document_id`
- `test_document_question_rejects_unknown_document_id`
- `test_document_question_rejects_documents_owned_by_another_user`
- `test_document_question_rejects_documents_not_ready`
- `test_document_question_answers_using_single_document`
- `test_document_question_answers_using_multiple_documents`
- `test_document_question_returns_sources_metadata`
- `test_document_question_still_blocks_unsafe_prompt`
- `test_document_question_returns_no_context_when_retrieval_finds_nothing`

### Tests de no regresión del flujo actual

- Mantener sin tocar los tests actuales de:
  - creación/validación de usuario;
  - `POST /ask`;
  - `GET /history/{username}`;
  - `GET /health`.
- Añadir explícitamente una prueba de no regresión conceptual:
  - `test_general_ask_contract_is_unchanged_after_document_endpoints_exist`

## Dónde tocar la arquitectura, sin implementarla aquí

- `domain/entities.py`:
  - nuevas entidades tipo `Document`, `DocumentChunk` o equivalente liviano.
- `domain/ports.py`:
  - un puerto de repositorio documental;
  - un puerto de indexación/recuperación vectorial;
  - opcionalmente un puerto de extractor/parser de archivos.
- `application/use_cases.py`:
  - un caso de uso para upload/registro;
  - uno para listado/detalle;
  - uno para Q&A documental.
- `entrypoints/api/routes.py`:
  - endpoints nuevos, sin cambiar la firma de `POST /ask`.
- `entrypoints/api/schemas.py`:
  - contratos nuevos para documentos y respuestas con fuentes.
- `back/tests/conftest.py`:
  - habrá que extender los fakes actuales para simular indexación, recuperación y respuesta del agente con contexto documental.

## Recomendación concreta de diseño API para primera entrega

- Implementar exactamente cuatro endpoints nuevos:
  - `POST /documents`
  - `GET /documents`
  - `GET /documents/{document_id}`
  - `POST /documents/ask`
- No modificar `POST /ask` ni `GET /history/{username}` en la primera fase.
- Hacer que `POST /documents/ask` soporte uno o muchos documentos con el mismo campo `document_ids`.
- Exigir metadata y ownership por `username`, porque todo el backend actual ya pivota sobre usuario registrado.

## Riesgos a vigilar en tests

- `TestClient` actual en [back/tests/conftest.py](/Users/roshi/Dev/playGround/python_interviewI/back/tests/conftest.py:20) está preparado para JSON y un fake agent simple; para uploads habrá que cubrir `multipart/form-data`.
- Si el procesamiento documental se hace asíncrono, los tests del upload no deberían asumir que el documento queda `ready` inmediatamente; el contrato debería admitir `processing`.
- Si se decide persistir trazabilidad de fuentes en historial, eso merece tests separados para no romper el shape actual de `HistoryResponse`.
