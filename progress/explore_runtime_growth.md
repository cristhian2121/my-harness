# Investigacion: crecimiento o duplicacion del composer tras el segundo mensaje

## Arranque

- `./init.sh` ejecuto OK.
- `progress/current.md` no existe en este checkout; continue con el resto del protocolo.

## Conclusión

No encontre evidencia de que `front/src/components/AssistantChat.tsx` o su ciclo normal de rerender monten un segundo composer/input despues del segundo mensaje del usuario.

Por lectura de codigo, el path mas probable para un efecto visual de "crece" no es una duplicacion real del composer, sino:

1. la logica de `turnAnchor="top"` de `@assistant-ui/react`, que inserta una reserva vertical en el viewport y puede alterar el espacio visible entre turnos, o
2. el `TextareaAutosize` usado por `ComposerPrimitive.Input`, combinado con `resize: vertical` en CSS.

## Evidencia

- `AssistantChat` renderiza un solo `Composer` dentro de un solo `ThreadPrimitive.ViewportFooter`; no hay ramas condicionales que monten un segundo input en el segundo turno.
  - Referencias: `front/src/components/AssistantChat.tsx:18-37`, `front/src/components/AssistantChat.tsx:63-75`

- El rerender de `ChatPage` tras `onInteractionSaved()` no deberia recrear el runtime:
  - `loadHistory` esta memoizado por `currentUser`, no por `history`.
  - `adapter` en `AssistantChat` esta memoizado por `username` y `onInteractionSaved`.
  - Referencias: `front/src/pages/ChatPage.tsx:17-33`, `front/src/pages/ChatPage.tsx:77`, `front/src/components/AssistantChat.tsx:78-107`

- `useLocalRuntime` crea el `LocalRuntimeCore` una sola vez con `useState(...)`. En rerenders posteriores solo actualiza opciones y llama `__internal_load()`.
  - Referencias: `front/node_modules/.pnpm/@assistant-ui+core@0.2.2_@assistant-ui+store@0.2.10_@assistant-ui+tap@0.5.11_@types+rea_36f336e02ffe281bf2a33566cce35906/node_modules/@assistant-ui/core/src/react/runtimes/useLocalRuntime.ts:37-38`, `.../useLocalRuntime.ts:59-62`

- Ese `__internal_load()` no reimporta repetidamente el thread local: queda guardado por `_loadPromise`, asi que tras la primera carga se vuelve no-op.
  - Referencia: `front/node_modules/.pnpm/@assistant-ui+core@0.2.2_@assistant-ui+store@0.2.10_@assistant-ui+tap@0.5.11_@types+rea_36f336e02ffe281bf2a33566cce35906/node_modules/@assistant-ui/core/src/runtimes/local/local-thread-runtime-core.ts:144-146`

- El footer del viewport registra su altura para scroll/inset, pero el registro tiene cleanup explicito. No vi una fuga obvia que sume footers por rerender.
  - Referencias: `front/node_modules/.pnpm/@assistant-ui+react@0.14.5_@types+react-dom@19.2.3_@types+react@19.2.14__@types+react@1_ceebda073cb6f9fa27febe6ec6889dc3/node_modules/@assistant-ui/react/src/primitives/thread/ThreadViewportFooter.tsx:47-57`, `front/node_modules/.pnpm/@assistant-ui+react@0.14.5_@types+react-dom@19.2.3_@types+react@19.2.14__@types+react@1_ceebda073cb6f9fa27febe6ec6889dc3/node_modules/@assistant-ui/react/src/utils/hooks/useSizeHandle.ts:20-37`

- `React.StrictMode` esta activo, pero eso explica dobles mounts de desarrollo al inicio, no un sintoma ligado especificamente al segundo mensaje.
  - Referencia: `front/src/main.tsx:8-15`

## Focos plausibles dentro del runtime visual

### 1. `turnAnchor="top"` puede cambiar el espacio visible despues de cada turno

- `AssistantChat` activa `turnAnchor="top"` en el viewport.
  - Referencia: `front/src/components/AssistantChat.tsx:21`

- En assistant-ui, ese modo:
  - mantiene un `topAnchorTurn` en el store del viewport,
  - marca el ultimo user/assistant relevantes como anchor/target,
  - monta un `reserve` element al lado del mensaje assistant target para ajustar scroll y slack.
  - Referencias: `front/node_modules/.pnpm/@assistant-ui+react@0.14.5_@types+react-dom@19.2.3_@types+react@19.2.14__@types+react@1_ceebda073cb6f9fa27febe6ec6889dc3/node_modules/@assistant-ui/react/src/primitives/thread/ThreadViewport.tsx:103-139`, `.../ThreadViewport.tsx:165-168`, `front/node_modules/.pnpm/@assistant-ui+react@0.14.5_@types+react-dom@19.2.3_@types+react@19.2.14__@types+react@1_ceebda073cb6f9fa27febe6ec6889dc3/node_modules/@assistant-ui/react/src/primitives/message/MessageRoot.tsx:57-117`, `front/node_modules/.pnpm/@assistant-ui+react@0.14.5_@types+react-dom@19.2.3_@types+react@19.2.14__@types+react@1_ceebda073cb6f9fa27febe6ec6889dc3/node_modules/@assistant-ui/react/src/primitives/thread/topAnchor/mountTopAnchorReserve.ts:56-126`

- Ese flujo si puede hacer que el area inferior "crezca" visualmente entre turnos, porque la libreria agrega/reserva espacio en el viewport. No encontre evidencia de acumulacion infinita: el codigo reutiliza un solo `reserve` por viewport (`reserve ??=`), asi que esto parece mas un cambio de geometria que una duplicacion real.

### 2. El input es autosize y ademas el CSS permite resize manual

- `ComposerPrimitive.Input` termina renderizando `TextareaAutosize`.
  - Referencia: `front/node_modules/.pnpm/@assistant-ui+react@0.14.5_@types+react-dom@19.2.3_@types+react@19.2.14__@types+react@1_ceebda073cb6f9fa27febe6ec6889dc3/node_modules/@assistant-ui/react/src/primitives/composer/ComposerInput.tsx:392-393`

- El CSS del repo deja `resize: vertical` en `.composer__input`.
  - Referencia: `front/src/styles/global.css:291-295`

- Si el sintoma observado es "el area del input se vuelve mas alta", este camino es mas creible que una recreacion del runtime.

### 3. El autosize usa un textarea oculto fuera del chat

- `react-textarea-autosize` crea un `hiddenTextarea` y lo inserta en `document.body`, pero le fuerza estilos ocultos (`visibility: hidden`, `position: absolute`, `z-index: -1000`).
  - Referencias: `front/node_modules/.pnpm/react-textarea-autosize@8.5.9_@types+react@19.2.14_react@19.2.6/node_modules/react-textarea-autosize/dist/react-textarea-autosize.development.esm.js:9-20`, `.../react-textarea-autosize.development.esm.js:46-54`

- Eso no deberia verse como un segundo composer salvo que haya un problema externo de CSS/inspeccion.

## Dictamen

Mi lectura del repo no soporta la hipotesis de "AssistantChat duplica el composer por lifecycle" despues del segundo mensaje.

La hipotesis mas defendible es:

- no hay duplicacion real del composer en el arbol de React;
- el cambio visual probablemente viene del modo `turnAnchor="top"` de assistant-ui o del `TextareaAutosize` con `resize: vertical`.

Si se quiere confirmar en navegador, lo primero que inspeccionaria en DevTools es:

- cuantas instancias reales de `.composer` hay en el DOM,
- si aparece un sibling extra del mensaje assistant target por el top-anchor reserve,
- y si la altura efectiva del `<textarea>` cambia por autosize/manual resize aunque el composer siga siendo uno solo.
