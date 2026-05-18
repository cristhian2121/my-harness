# Spec: Vector Documents Backend

## Goal

Add backend support for user-owned document ingestion and question answering over one or multiple stored documents.

## Scope

- Backend only.
- Keep general chat endpoints unchanged.
- Add document-specific endpoints and persistence.

## Decisions

- Keep document metadata in the existing SQLAlchemy database.
- Use a local persisted vector store adapter for similarity search.
- Prefer `qdrant-client` local mode for vectors.
- Keep retrieval outside the chat agent; compose retrieved context in a dedicated document Q&A use case.
- Support these first-class formats in this iteration:
  - `.pdf`
  - `.csv`
  - `.docx`
  - `.xlsx`
- Treat legacy `.doc` and `.xls` as unsupported in this first iteration, but return explicit errors.

## API

- `POST /documents`
  - multipart upload with `username` and `file`
  - stores metadata and indexes content
- `GET /documents`
  - list documents for a `username`
- `GET /documents/{document_id}`
  - document detail and useful metadata
- `POST /documents/ask`
  - JSON with `username`, `question`, `document_ids`
  - answers from one or multiple documents and returns sources

## Architecture

- Add document entities and ports in `back/app/domain/`.
- Add document use cases in `back/app/application/use_cases.py`.
- Add SQLAlchemy document models and repositories in `back/app/infrastructure/`.
- Add parser/storage/vector adapters in `back/app/infrastructure/`.
- Wire everything from `back/app/core/container.py`.

## Retrieval behavior

- Always filter by owning user.
- Support one or many `document_ids`.
- Return answer plus source metadata.
- Preserve prompt-security checks for document questions too.

## Testing

- Add backend tests for upload, list, detail, and document Q&A.
- Preserve all existing tests for `/ask`, `/history/{username}`, and `/health`.
- Use test doubles where needed for embeddings or vector retrieval.
