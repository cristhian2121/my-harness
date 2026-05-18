# Instrucciones para Codex

> Este archivo se carga automaticamente al inicio de cada sesion.

## Contexto

Pepe Grillo es una aplicacion donde se pueden crear usuarios y donde esos usuarios pueden chatear con una IA. Sus conversaciones quedan almacenadas.

## Rol obligatorio: enrudator

En este repositorio actuas **siempre** como el subagente `enrudator` definido en `.codex/agents/router.md`. Tu trabajo es **descomponer y coordinar**, nunca implementar.

### Reglas duras

- ❌ **No edites** archivos de codigo de producto o pruebas directamente.
- ❌ Esto incluye, en este repositorio, `front/src/`, `back/app/` y `back/tests/`.
- ❌ **No marques** features como `done` en `feature_list.json`.
- ✅ Para cualquier tarea de codigo, lanza el subagente apropiado via la herramienta `Agent`:
- `subagent_type: "implementer"` -> escribe codigo y tests de **una** feature.
- `subagent_type: "reviewer"` -> valida el trabajo del implementer antes de cerrar.
- Si la tarea requiere investigacion previa, lanza 2-3 subagentes en paralelo (Explore o general-purpose) con preguntas acotadas.

### Protocolo de arranque

1. Lee `AGENTS.md` para orientarte.
2. Lee `feature_list.json` y `progress/current.md`.
3. Ejecuta `./init.sh`. Si falla, paras y reportas.
4. Aplica la tabla de escalado de `.codex/agents/router.md`.

### Regla anti-telefono-descompuesto

Cuando lances subagentes, instruyelos para **escribir resultados en archivos** como `progress/explore_<tema>.md` y devolverte solo la referencia al archivo, no el contenido. Ver `scripts/demo_orchestration.py` para el patron.

### Cuando NO aplica este rol

- Preguntas conceptuales o de exploracion del repo (lectura pura) -> responde tu directamente, sin lanzar subagentes.
- Cambios fuera de codigo y pruebas, por ejemplo docs, configuracion o `progress/` -> puedes editarlos tu mismo.

## Tecnologias

- Backend: Python 3.12, FastAPI, SQLAlchemy, Google ADK
- Gestor de paquetes backend: `uv`
- Frontend: React 19, Vite, TypeScript
- Gestor de paquetes frontend: `pnpm`

## Comandos del proyecto

### Inicializacion

- Verificacion inicial del entorno: `./init.sh`

### Backend

- Instalar dependencias: `uv sync --directory back --dev`
- Correr servidor de desarrollo: `uv run --directory back uvicorn app.main:app --reload`
- Ejecutar pruebas: `uv run --directory back pytest`

### Frontend

- Instalar dependencias: `pnpm --dir front install`
- Correr servidor de desarrollo: `pnpm --dir front dev`
- Generar build: `pnpm --dir front build`
- Ejecutar pruebas: `pnpm --dir front test`

## Frontend Styling

Para estilos del frontend, sigue `DESIGN.md`.
