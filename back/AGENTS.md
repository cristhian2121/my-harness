# Backend AGENTS Guide

## Objetivo

Este archivo existe para reducir tiempo de orientacion en `back/`.
Su meta es que un agente encuentre el modulo correcto rapido, lea menos archivos y gaste menos tokens.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2
- SQLite
- Google ADK
- Pytest
- `uv` como gestor principal

## Arquitectura real del backend

Este backend sigue una separacion cercana a hexagonal:

- `entrypoints/`: expone la API HTTP
- `application/`: contiene reglas de negocio y casos de uso
- `domain/`: define entidades y puertos
- `infrastructure/`: implementa persistencia, agente IA y filtros locales
- `core/`: configura settings y compone dependencias

Flujo habitual:

- request HTTP -> `routes.py` -> use case -> port -> infraestructura -> respuesta API

## Regla de navegacion rapida

Antes de abrir muchos archivos, sigue esta ruta:

1. Empieza por `app/main.py` si no conoces el entrypoint.
2. Si el problema es un endpoint, abre `app/entrypoints/api/routes.py`.
3. Desde la route, sigue el use case correspondiente en `app/application/use_cases.py`.
4. Si el caso de uso toca persistencia o servicios externos, sigue el port en `app/domain/ports.py` y luego la implementacion en `app/infrastructure/`.
5. Revisa el test mas cercano en `back/tests/` antes de asumir cobertura.

Esta secuencia suele bastar:

- endpoint -> route -> use case -> repo/agent -> model/schema -> test

## Metodo recomendado para encontrar el modulo correcto

Cuando el bug viene descrito desde comportamiento backend, usa este metodo:

1. Traduce el sintoma a palabras concretas.
   Ejemplos: `init_user`, `ask`, `history`, `health`, `session`, `settings`, `agent`, `sqlite`.
2. Busca primero en `back/app`, no en todo el repo.
   Ejemplo: `rg -n "ask|history|health" back/app`
3. Si el bug es HTTP o contrato API, abre primero:
   - `app/entrypoints/api/routes.py`
   - `app/entrypoints/api/schemas.py`
   - el test API correspondiente en `back/tests/`
4. Si el bug es de negocio, abre despues:
   - `app/application/use_cases.py`
   - `app/application/exceptions.py`
   - `app/domain/entities.py`
5. Si el bug es de persistencia o integracion, abre despues:
   - `app/infrastructure/repositories.py`
   - `app/infrastructure/db/models.py`
   - `app/infrastructure/agent.py`
   - `app/infrastructure/security.py`
6. Si el bug es de arranque, config o wiring, abre:
   - `app/main.py`
   - `app/core/config.py`
   - `app/core/container.py`
   - `app/entrypoints/api/dependencies.py`

## Metodo usado para entender este backend

La ruta eficiente para entender `back/` fue:

1. Leer `back/pyproject.toml` para confirmar stack y comandos.
2. Abrir `app/main.py` para identificar el entrypoint real y el lifespan.
3. Abrir `app/entrypoints/api/routes.py` para ver endpoints y casos de uso activos.
4. Seguir `app/core/container.py` para entender inyeccion de dependencias.
5. Leer `app/application/use_cases.py` para encontrar la logica central.
6. Validar contratos en `app/domain/entities.py` y `app/domain/ports.py`.
7. Confirmar implementaciones en `app/infrastructure/`.
8. Revisar `back/tests/` para ver cobertura real y fixtures.

Ese orden evita perder tiempo en archivos generados o capas no relevantes.

## Mapa de carpetas

### `app/main.py`

- Punto de entrada FastAPI.
- Crea la app, registra CORS, monta router y crea esquema en startup.
- Si no sabes como arranca el backend, empieza aqui.

### `app/entrypoints/api/`

- Capa HTTP.
- `routes.py`: endpoints reales.
- `schemas.py`: contratos request/response.
- `dependencies.py`: acceso a container y sesiones DB.

### `app/application/`

- Casos de uso y excepciones del negocio.
- `use_cases.py` concentra:
  - inicializacion de usuarios
  - chat
  - historial
  - healthcheck
- `exceptions.py` define errores que luego la capa API transforma.

### `app/domain/`

- Modelo de dominio y puertos.
- `entities.py`: `User`, `ChatInteraction`, `InteractionStatus`.
- `ports.py`: contratos para repositorios y agente.

### `app/infrastructure/`

- Implementaciones concretas.
- `repositories.py`: repositorios SQLAlchemy.
- `db/models.py`: tablas y relaciones SQLAlchemy.
- `agent.py`: integracion Google ADK y fallback cuando falta API key.
- `security.py`: filtro local de prompts inseguros.

### `app/core/`

- Wiring y configuracion.
- `config.py`: settings con `.env` y aliases.
- `container.py`: engine, session factory, security filter y chat agent.

### `tests/`

- Cobertura del backend.
- `conftest.py`: fixture principal con `TestClient`, DB temporal y fake chat agent.
- `test_api.py`: flujo HTTP y persistencia visibles desde la API.
- `test_config.py`: variables de entorno y wiring del agente ADK.

## Heuristicas para leer menos

- Si el problema es un status code o payload, empieza por `routes.py` y `schemas.py`.
- Si el problema es validacion o reglas de negocio, abre `use_cases.py` antes que repositorios.
- Si el problema es datos faltantes o desorden cronologico, abre `repositories.py` y `db/models.py`.
- Si el problema es que la IA no responde, abre `container.py`, `config.py` y `infrastructure/agent.py`.
- Si el problema es que una request se bloquea, abre `infrastructure/security.py` y luego `AskUseCase`.
- Si el problema es test-only, revisa primero `tests/conftest.py`; ahi se reemplaza el agente real por uno fake.

## Pistas especificas por endpoint

- `POST /init_user`
  - route: `app/entrypoints/api/routes.py`
  - negocio: `InitUserUseCase`
  - persistencia: `SqlAlchemyUserRepository`

- `POST /ask`
  - route: `app/entrypoints/api/routes.py`
  - negocio: `AskUseCase`
  - guardas locales: `PromptSecurityFilter`
  - agente IA: `AdkChatAgent` o `FallbackChatAgent`
  - persistencia: `SqlAlchemyChatRepository`

- `GET /history/{username}`
  - route: `app/entrypoints/api/routes.py`
  - negocio: `GetHistoryUseCase`
  - persistencia: `SqlAlchemyChatRepository`

- `GET /health`
  - route: `app/entrypoints/api/routes.py`
  - negocio: `HealthUseCase`
  - dependencias: `session_factory` + `chat_agent`

## Configuracion relevante

- Los settings viven en `app/core/config.py`.
- `.env` se lee automaticamente.
- Variables importantes:
  - `GOOGLE_API_KEY`
  - `GCP_PROJECT_ID`
  - `GEMINI_MODEL` o `WALT_MODEL`
  - `database_url`
- Si no hay `GOOGLE_API_KEY`, el container monta `FallbackChatAgent`.

## Convenciones utiles

- No uses `back/.venv/`, `back/.pytest_cache/` o `back/pepe_grillo.db` para entender arquitectura.
- La persistencia de tests usa una DB temporal creada desde `tests/conftest.py`.
- `create_schema()` se ejecuta al iniciar la app.
- La API hoy compone repositorios directamente en las routes; no hay capa extra de providers por caso de uso.

## Comandos utiles

- Buscar archivos: `rg --files back/app back/tests`
- Buscar texto: `rg -n "texto" back/app back/tests`
- Instalar deps: `uv sync --directory back --dev`
- Servidor dev: `uv run --directory back uvicorn app.main:app --reload`
- Tests backend: `uv run --directory back pytest`
- Test puntual API: `uv run --directory back pytest tests/test_api.py`

