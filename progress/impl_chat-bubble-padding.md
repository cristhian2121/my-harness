Archivos tocados
- `front/src/styles/global.css`

Cambio
- Se redujo el padding vertical de `.message-bubble` de `14px 16px` a `10px 16px` para compactar las cajas de mensajes sin alterar el padding horizontal.

Verificacion
- `pnpm --dir front test AssistantChat`
- Resultado: ok, `src/components/AssistantChat.test.tsx` paso (`1 test`, `1 passed`).

Riesgos
- Ajuste visual minimo. No se agrego prueba especifica de estilos porque el cambio afecta solo CSS y no modifica comportamiento del componente.
