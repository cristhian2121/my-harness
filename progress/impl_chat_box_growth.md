# Implementacion: chat box growth

## Causa raiz

El composer del chat ya autosizea su `textarea` via `ComposerPrimitive.Input` (`react-textarea-autosize`), pero el thread estaba montado con `ThreadPrimitive.Viewport turnAnchor="top"`. Ese modo agrega logica de reserva/inset extra en `assistant-ui` que no corresponde a un chat normal anclado abajo y amplificaba el crecimiento percibido del bloque de chat tras envios sucesivos. Ademas, el CSS local permitia `resize: vertical` sobre un input que ya autosizea, dejando una segunda via de crecimiento innecesaria.

## Archivos cambiados

- `front/src/components/AssistantChat.tsx`
  - Se removio `turnAnchor="top"` de `ThreadPrimitive.Viewport` para volver al comportamiento normal del chat.
- `front/src/styles/global.css`
  - Se cambio `.composer__input` de `resize: vertical` a `resize: none`.
- `front/src/components/AssistantChat.test.tsx`
  - Nueva prueba de regresion que monta `AssistantChat` real, envia dos preguntas y verifica que la altura del composer vuelve a su base tras cada envio y no sigue creciendo despues del segundo.
  - El test agrega solo los stubs minimos de jsdom: `ResizeObserver`, `scrollTo`, `getComputedStyle` para el autosize y `scrollHeight` del `textarea`.

## Pruebas ejecutadas

- `pnpm --dir front test -- src/components/AssistantChat.test.tsx`
  - Resultado: `3 passed (3)`; Vitest ejecuto la suite completa actual del frontend, incluyendo el nuevo test de `AssistantChat`.

