# Hallazgos composer/chat growth

## Resumen

El crecimiento del input/chat box no parece venir de una sola regla CSS. La combinacion mas sospechosa es:

1. `ComposerPrimitive.Input` ya autosizea el `textarea` con `react-textarea-autosize`.
2. `ThreadPrimitive.ViewportFooter` mide cualquier cambio de altura del footer con `ResizeObserver` y lo suma como `content inset` del viewport.
3. El chat usa `turnAnchor="top"`, lo que activa la logica de `assistant-ui` que inserta un `reserve` adicional despues del turno activo para mantener el ultimo mensaje del usuario anclado arriba.

Cuando el composer crece, no solo crece visualmente el footer: tambien crece el inset que `assistant-ui` reserva y puede crecer el `reserve` del top-anchor. Eso cuadra con el sintoma de que el area del chat/composer parece agrandarse despues de interacciones sucesivas.

## Evidencia principal

### 1. El input ya es autosizing; el CSS local lo deja crecer mas

- En `front/src/components/AssistantChat.tsx:65-70`, `ComposerPrimitive.Input` se renderiza con `rows={1}`.
- En `@assistant-ui/react`, `ComposerPrimitive.Input` renderiza `TextareaAutosize` de `react-textarea-autosize`, no un `textarea` plano:
  - `front/node_modules/.../ComposerInput.tsx:18-20`
  - `front/node_modules/.../ComposerInput.tsx:94`
  - `front/node_modules/.../ComposerInput.tsx:307-313`
  - `front/node_modules/.../ComposerInput.tsx:371-373`
- El CSS local ademas le impone:
  - `min-height: 56px` en `front/src/styles/global.css:291-292`
  - `resize: vertical` en `front/src/styles/global.css:293`
  - sin `max-height` ni `overflow-y` local en esa clase

Impacto:

- `TextareaAutosize` ya cambia altura segun contenido.
- `resize: vertical` agrega otra via de crecimiento y hace que la altura del composer no este controlada solo por el primitive.
- Sin `max-height`, cualquier prompt largo o newline repetido puede inflar bastante el footer.

### 2. El sticky footer no es pasivo; assistant-ui mide su altura y la usa en el layout

- El footer se monta dentro del viewport scrollable:
  - `front/src/components/AssistantChat.tsx:21`
  - `front/src/components/AssistantChat.tsx:35-37`
- `ThreadPrimitive.ViewportFooter` esta hecho precisamente para medir su propia altura y reportarla al viewport:
  - `front/node_modules/.../ThreadViewportFooter.tsx:20-29`
  - `front/node_modules/.../ThreadViewportFooter.tsx:47-53`
- Usa `ResizeObserver` via `useSizeHandle`, asi que cualquier cambio de altura del footer/composer actualiza el inset:
  - `front/node_modules/.../useSizeHandle.ts:11-31`

Impacto:

- Si el composer crece, `assistant-ui` interpreta que ahora necesita mas espacio reservado en el viewport.
- El efecto visible no es solo "textarea mas alto"; tambien aparece mas espacio util/reservado alrededor del footer.

### 3. `turnAnchor="top"` activa una reserva extra por turno

- El viewport se usa con `turnAnchor="top"` en `front/src/components/AssistantChat.tsx:21`.
- En `assistant-ui`, `turnAnchor="top"` habilita logica especifica:
  - `front/node_modules/.../ThreadViewport.tsx:165-168`
- Esa logica monta un `reserve` DOM despues del mensaje activo:
  - `front/node_modules/.../mountTopAnchorReserve.ts:80-94`
- El `reserve` cambia de altura dinamicamente para hacer alcanzable el target anclado:
  - `front/node_modules/.../mountTopAnchorReserve.ts:91-99`
  - `front/node_modules/.../computeTopAnchorSlack.ts:72-81`

Impacto:

- Con top anchoring, el layout no funciona como un chat clasico "anclado abajo".
- Un footer mas alto reduce viewport util y puede requerir mas `reserve`.
- Eso hace que, tras nuevos turnos, el chat parezca dejar cada vez mas espacio debajo del contenido.

## Reglas CSS locales que amplifican el problema

- `front/src/styles/global.css:244-249`
  - `position: sticky`
  - `bottom: 0`
  - `padding: 16px 0 20px`
  - `margin-top: auto`
- `front/src/styles/global.css:281-289`
  - el composer agrega mas padding y borde sobre el textarea autosizing
- `front/src/styles/global.css:200-208` y `291-295`
  - `.composer__input` recibe dos bloques de estilos; el segundo sobreescribe parte del primero. No parece ser la causa principal, pero complica razonar el alto efectivo del textarea.

Observaciones:

- El footer ya es alto incluso en estado base: padding del footer + padding del composer + `min-height` del input + fila de acciones.
- `margin-top: auto` dentro de un contenedor flex scrollable puede introducir espacio elastico cuando hay pocos mensajes. No parece explicar crecimiento acumulativo por si solo, pero si contribuye a que el bloque se sienta "grande".

## Causa mas probable

La causa mas probable es la combinacion de `TextareaAutosize` + `resize: vertical` + `ViewportFooter` medido por `assistant-ui`, agravada por `turnAnchor="top"`.

En otras palabras: el composer no solo cambia de tamaño visualmente; ese cambio retroalimenta el sistema de scroll/inset/reserve del thread.

## Causas secundarias o menos probables

- La duplicacion de reglas de `.composer__input` puede hacer mas dificil predecir el alto base, pero no parece explicar por si sola el crecimiento tras interacciones.
- `margin-top: auto` en el footer probablemente agrega percepcion de hueco extra cuando el thread aun tiene poco contenido.

## Conclusión operativa

Si el objetivo es eliminar el crecimiento notable tras varios turnos, los puntos a revisar primero son:

1. Si `resize: vertical` debe existir en un `ComposerPrimitive.Input` que ya autosizea.
2. Si el footer sticky debe seguir dentro de `ThreadPrimitive.ViewportFooter`.
3. Si `turnAnchor="top"` es realmente deseado para este chat, porque introduce reserva dinamica extra ademas del footer medido.
