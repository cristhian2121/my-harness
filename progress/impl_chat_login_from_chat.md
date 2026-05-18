Implementacion completada para la feature de login desde `/chat` sin sesion activa.

Cambios principales:
- Backend: agregado endpoint explicito `POST /validate_user` para validar `username` + `role` existentes.
- Backend: agregado `InvalidUserCredentialsError` y `ValidateUserUseCase`.
- Frontend: `/chat` sin usuario activo ahora mantiene `Ir a registro` y agrega formulario de autenticacion con `username` y `role`.
- Frontend: el formulario valida contra backend, guarda el usuario en `UserContext` al autenticar y muestra error visible cuando falla.
- Tests: agregados casos backend para validacion exitosa y fallo por role incorrecto.
- Tests: agregados casos frontend para login desde `/chat` y error visible al fallar la validacion.

Archivos tocados:
- `back/app/application/exceptions.py`
- `back/app/application/use_cases.py`
- `back/app/entrypoints/api/routes.py`
- `back/app/entrypoints/api/schemas.py`
- `back/tests/test_api.py`
- `front/src/api/client.ts`
- `front/src/pages/ChatPage.tsx`
- `front/src/pages/ChatPage.test.tsx`

Verificacion ejecutada:
- `uv run --directory back pytest tests/test_api.py` -> 9 passed
- `pnpm --dir front test -- --run front/src/pages/ChatPage.test.tsx` -> suite passed
- `./init.sh` -> OK

Notas:
- No se revirtieron cambios ajenos presentes en el worktree.
- No se marco nada como `done` en `feature_list.json`.
