# Spec: Vector Documents Review Fixes

## Goal

Address the four findings from `progress/review_vector_documents.md` without expanding feature scope.

## Required fixes

1. Persisted retrieval must still work after process restart.
   - Rehydrate vector collection metadata/state from persisted local storage.
   - Add a regression test that proves document Q&A still retrieves context from a fresh app/container instance.

2. Ingestion consistency between SQLite metadata and vector store.
   - Do not expose `indexed` before vectors are actually available.
   - Avoid losing already-computed document metadata when a later vector indexing step fails.
   - Add tests around vector-store or parser failure paths and final document status/metadata.

3. Stronger handling of untrusted document context.
   - Do better than a plain textual warning before concatenating raw chunks.
   - Reduce prompt-injection exposure from retrieved document content as much as is practical in the current architecture.
   - Keep the user prompt security check in place.

4. Coverage gaps from review.
   - Add happy-path `.pdf`
   - Add explicit `.xls` rejection
   - Add unsupported-format rejection
   - Add user-isolation checks for `POST /documents/ask`
   - Add restart persistence test
   - Add failure-path tests for parser/vector indexing
   - Add a no-contamination check that document operations do not break the existing chat/history flow

## Constraints

- Backend only.
- Keep `POST /ask` and `GET /history/{username}` contract unchanged.
- Do not broaden supported formats beyond the first iteration.
