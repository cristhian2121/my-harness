# Implementacion de variables de entorno backend

## Cambios

- `back/app/core/config.py`
  - `google_api_key` ahora acepta explicitamente `GOOGLE_API_KEY`.
  - se agrego `gcp_project_id` con soporte para `GCP_PROJECT_ID`.
  - `gemini_model` ahora acepta `WALT_MODEL` y mantiene compatibilidad con nombres previos.
  - se activo `populate_by_name=True` para conservar compatibilidad al instanciar `Settings(...)` desde codigo/tests.

- `back/app/infrastructure/agent.py`
  - `AdkChatAgent` sigue funcionando en modo API key.
  - si existe `gcp_project_id`, lo propaga al runtime via `GCP_PROJECT_ID` y `GOOGLE_CLOUD_PROJECT`.
  - si no existe, limpia esas variables para evitar estado residual entre instancias.

- `back/tests/test_config.py`
  - prueba de carga desde `GOOGLE_API_KEY`, `GCP_PROJECT_ID` y `WALT_MODEL`.
  - prueba de propagacion de proyecto/modelo al runtime del agente sin depender de servicios externos.

## Verificacion

- Ejecutado: `uv run --directory back pytest tests/test_config.py tests/test_api.py`
- Resultado: `9 passed`

## Alcance

- No se tocaron archivos de frontend.
- Se mantuvo el uso interno existente de `settings.google_api_key` y `settings.gemini_model`.
