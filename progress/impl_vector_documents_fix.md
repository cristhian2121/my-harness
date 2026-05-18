## Resultado

Corregida la segunda pasada de la feature backend de documentos vectoriales enfocada exclusivamente en los hallazgos de `progress/review_vector_documents.md`.

## Cambios aplicados

1. Persistencia de retrieval tras restart
   - `LocalQdrantVectorStore.search()` ya no depende de `_vector_size` inicializado en memoria.
   - La colección persistida se rehidrata desde disco antes de consultar y valida el tamaño del vector configurado.
   - Se añadió cierre explícito del cliente Qdrant en shutdown para liberar locks locales en recreaciones de app dentro del mismo proceso.

2. Consistencia SQLite/vector store
   - La ingestión ya no marca el documento como `indexed` antes de que el vector store confirme la indexación.
   - Primero se persisten chunks y metadata documental manteniendo `status=uploaded`.
   - Solo después de indexar vectores correctamente se actualiza a `status=indexed`.
   - Si fallan embeddings o vector store, el documento queda en `failed` preservando `chunk_count`, `page_count`, `row_count` y `sheet_names`.

3. Endurecimiento del contexto documental no confiable
   - `AskDocumentsUseCase` ahora compone el contexto recuperado como JSON estructurado en vez de concatenar texto crudo libre.
   - Se sanitizan fragmentos recuperados con redacción de patrones claros de prompt injection antes de enviarlos al modelo.
   - Se mantuvo el filtro previo sobre la pregunta del usuario.

4. Cobertura de tests añadida
   - happy path `.pdf`
   - rechazo explícito `.xls`
   - rechazo de formato no soportado
   - aislamiento por usuario en `POST /documents/ask`
   - retrieval persistido tras restart
   - sanitización de contenido documental malicioso
   - fallo de parser con persistencia de documento `failed`
   - fallo de vector store preservando metadata y sin indexar prematuramente
   - no contaminación de `POST /ask` / `GET /history/{username}` por el flujo documental

## Archivos tocados

- `back/app/application/use_cases.py`
- `back/app/core/container.py`
- `back/app/infrastructure/documents.py`
- `back/app/main.py`
- `back/tests/conftest.py`
- `back/tests/test_api.py`

## Verificación

- `python3 -m compileall back/app back/tests`
- `uv run --directory back pytest`
- Resultado: `29 passed`

## Riesgo residual honesto

La mitigación de prompt injection mejora materialmente el aislamiento, pero no convierte la arquitectura en inmune: el modelo sigue razonando sobre contenido proveniente del documento. En la arquitectura actual, la reducción real proviene de dos capas concretas:

- redacción preventiva de patrones de instrucción maliciosa en los fragmentos recuperados
- encapsulado estructurado del contexto como datos JSON no confiables

Para un aislamiento más fuerte haría falta una arquitectura separada de extracción/normalización de hechos o un modelo/pipeline dedicado a clasificación y limpieza previa del contenido.
