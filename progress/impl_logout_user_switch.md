Implementacion: logout de usuario actual para permitir cambiar de usuario sin limpiar storage manualmente.

Archivos tocados:
- `front/src/layouts/AppShell.tsx`
- `front/src/layouts/AppShell.test.tsx`
- `front/src/styles/global.css`
- `front/src/components/AssistantChat.test.tsx`

Comportamiento implementado:
- Se agrega boton `Cerrar sesion` en la topbar cuando hay usuario activo.
- El boton ejecuta `setCurrentUser(null)`, lo que elimina `pepe-grillo-user` de `localStorage`.
- Despues del logout, la app navega a `/`.
- Cuando no hay usuario activo, la topbar vuelve a mostrar `No user selected` y `ChatPage` ya queda libre para mostrar su estado vacio existente.

Verificacion:
- `pnpm --dir front test`
- `pnpm --dir front build`

Notas:
- Se agrego una prueba nueva de `AppShell` que valida logout, limpieza de `localStorage` y redireccion a registro.
- Se corrigio un mock tipado en `front/src/components/AssistantChat.test.tsx` para que `tsc` permita ejecutar `build`.

Riesgos:
- No se agrego confirmacion previa al logout; el flujo actual cierra sesion en un click.
