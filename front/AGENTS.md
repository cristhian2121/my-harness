# Frontend AGENTS Guide

## Objetivo

Este archivo reduce tiempo de orientacion para tareas en `front/`.
Usalo para encontrar rapido el componente correcto, leer menos archivos y gastar menos tokens.

## Stack

- React 19
- Vite
- TypeScript
- Vitest + Testing Library
- UI de chat con `@assistant-ui/react`

## Regla de navegacion rapida

Para ubicar el componente correcto, sigue esta ruta antes de abrir archivos de forma amplia:

1. Empieza en `src/App.tsx`.
2. Identifica la ruta que renderiza la pantalla afectada.
3. Abre la pagina correspondiente en `src/pages/`.
4. Desde esa pagina, sigue solo los imports reales hacia `src/components/`, `src/layouts/`, `src/context/`, `src/api/` y `src/styles/`.
5. Revisa tests de esa misma capa antes de asumir cobertura existente.

Esta secuencia suele bastar:

- ruta -> pagina -> componente -> estilos -> test

## Metodo recomendado para encontrar el componente correcto

Cuando el bug viene descrito desde la UI, usa este metodo:

1. Traduce el sintoma a palabras de busqueda concretas.
   Ejemplos: `chat`, `textarea`, `composer`, `message`, `history`, `register`, `health`.
2. Busca primero en `front/src/`, no en todo el repo.
   Ejemplo: `rg -n "chat|composer|textarea|message" front/src`
3. Si el bug parece visual, abre primero:
   - la pagina afectada en `src/pages/`
   - el componente principal en `src/components/`
   - `src/styles/global.css`
4. Si el bug parece de datos o side effects, abre despues:
   - `src/api/client.ts`
   - `src/context/UserContext.tsx`
   - `src/lib/types.ts`
5. Solo entra a `node_modules` si ya sospechas una libreria externa.
   En este proyecto eso aplica especialmente a `@assistant-ui/react`.

## Metodo usado en el bug del chat

Para encontrar el componente correcto del bug "el chat box crece mucho en la segunda pregunta", la ruta eficiente fue:

1. Buscar keywords de UI en `front/src`.
2. Confirmar la ruta en `src/App.tsx`.
3. Abrir `src/pages/ChatPage.tsx` para ver el ensamblaje de la pantalla.
4. Detectar que el chat real vive en `src/components/AssistantChat.tsx`.
5. Abrir `src/styles/global.css` para revisar clases `chat-*` y `composer_*`.
6. Revisar `src/pages/ChatPage.test.tsx` y notar que mockea `AssistantChat`, asi que no cubre el comportamiento real del composer.
7. Solo despues mirar `node_modules/@assistant-ui` para validar si el problema venia del primitive o de la integracion local.

Ese orden evito leer archivos no relacionados.

## Mapa de carpetas

### `src/App.tsx`

- Punto de entrada de rutas.
- Si no sabes que pagina se usa, empieza aqui.

### `src/pages/`

- Pantallas completas.
- Orquestan componentes, cargan datos y conectan contexto.
- En este repo:
  - `RegisterPage.tsx`: flujo de registro de usuario.
  - `ChatPage.tsx`: pantalla principal del chat.

### `src/components/`

- UI reutilizable o secciones grandes de una pagina.
- Componentes actuales importantes:
  - `AssistantChat.tsx`: runtime del chat, composer, mensajes.
  - `HistoryPanel.tsx`: historial persistido.
  - `HealthCard.tsx`: estado del backend.

### `src/layouts/`

- Estructura compartida de la app.
- `AppShell.tsx` define topbar y contenedor principal.

### `src/context/`

- Estado global ligero.
- `UserContext.tsx` guarda el usuario activo en `localStorage`.

### `src/api/`

- Cliente HTTP del frontend.
- `client.ts` concentra `registerUser`, `askQuestion`, `getHealth`, `getHistory`.

### `src/lib/`

- Tipos compartidos del frontend.
- Revisa `types.ts` antes de inventar nuevas formas de datos.

### `src/styles/`

- Estilos globales.
- Hoy casi toda la UI depende de `global.css`.
- Si un bug es visual, este archivo casi siempre entra en el primer corte de lectura.

### `src/test/`

- Setup global de Vitest.
- Abre esta carpeta si necesitas entender mocks o configuracion comun.

## Heuristicas para leer menos

- Si el problema es de navegacion o routing, empieza por `App.tsx` y `pages/`.
- Si el problema es visual, abre `components/` y `styles/global.css` antes que `api/`.
- Si el problema es datos faltantes o estado raro, abre `api/client.ts` y `context/UserContext.tsx`.
- Si un test de pagina mockea el componente hijo, no asumas que cubre bugs reales del hijo.
- Evita leer `dist/`; es output generado.
- Evita leer `node_modules/` al inicio; entra ahi solo cuando el comportamiento local ya apunte a una libreria.

## Pistas especificas del chat

- Ruta: `src/App.tsx` -> `/chat`
- Pagina: `src/pages/ChatPage.tsx`
- Componente central: `src/components/AssistantChat.tsx`
- Estilos principales: `src/styles/global.css`
- Cobertura actual:
  - `src/pages/ChatPage.test.tsx` valida wiring de pagina.
  - `src/components/AssistantChat.test.tsx` es donde debe vivir la cobertura del comportamiento real del chat.

## Convenciones utiles

- El alias `@/` apunta a `src/`.
- Los tests estan cerca de la unidad que prueban.
- El frontend tiene artefactos generados en `dist/`; no los uses para entender la arquitectura.

## Comandos utiles

- Buscar archivos: `rg --files front/src`
- Buscar texto: `rg -n "texto" front/src`
- Tests frontend: `pnpm --dir front test`
- Test puntual: `pnpm --dir front test -- src/components/AssistantChat.test.tsx`
- Build: `pnpm --dir front build`
