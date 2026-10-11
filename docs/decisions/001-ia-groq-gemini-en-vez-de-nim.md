# ADR 001. IA: Groq con respaldo de Gemini en vez de NVIDIA NIM

Fecha: 2026-09-25. Estado: aceptada. Decidió: Andrea.

## Contexto

La especificación proponía NVIDIA NIM para el prototipo, un modelo local opcional y un GPT económico como respaldo. También proponía usar alias (`fast`, `structured`, `reasoning`, `embedding`) para no escribir el nombre del modelo en cada flujo (secciones 5, 8 y 11).

## Decisión

- El proveedor principal es Groq, con el modelo `openai/gpt-oss-120b` en el plan gratis.
- El respaldo es Gemini Flash-Lite (`gemini-3.5-flash-lite`, porque la 2.5 ya no está disponible para cuentas nuevas).
- Todas las llamadas pasan por un solo subflujo, `ai-model-router`. Si Groq falla, responde Gemini, y los demás flujos no se enteran de cuál de los dos contestó.
- Los prompts están en `prompts/templates/` con su versión (por ejemplo `puntaje-v1` o la `v4` del CV), no dentro de los nodos.
- No uso modelo local.

## Por qué

Con el plan gratis de Groq el costo es cero, y sus límites (unas 1.000 solicitudes y 8.000 tokens por minuto al día) alcanzan para el Proyecto 1: puntuar 10 vacantes por hora y leer algún CV.

Groq responde rápido y puede devolver JSON (`response_format: json_object`), que es lo que necesito para el CV y el puntaje, porque profile-api valida esa respuesta.

Tener dos proveedores distintos da un respaldo real. Lo probé con una falla simulada y también con fallas reales: en la telemetría del 2026-10-06, 4 de 20 llamadas las resolvió Gemini.

No uso un modelo local porque el Mac tiene poca memoria y ya corre Docker con n8n, Postgres y MinIO. La misma especificación dice que con 8 GB no conviene tener un LLM local al mismo tiempo.

Con `ai-model-router` se cumple la idea de los alias: si cambio de proveedor, toco un solo flujo y no todos.

## Consecuencias

Por ahora no hay alias separados: todas las tareas usan el mismo modelo. Si aparece una tarea con necesidades distintas, se agrega un campo `alias` a la entrada del router.

Hay un tema de privacidad: en el plan gratis, Gemini puede usar los datos para mejorar sus productos. Antes de tener usuarios reales hay que pasar a un plan pago o dejar de mandarle a Gemini datos personales como el CV.

Si se acaban las cuotas gratis, Groq responde con error y todo pasa a Gemini. La telemetría (`/telemetria/ia`) muestra qué porcentaje de llamadas está resolviendo el respaldo.

## Cuándo revisarla

- Si Gemini resuelve más del 30 % de las llamadas durante varios días seguidos. El 7 de octubre llegó al 30 % y en las pruebas del 8 estaba en 23 %.
- Antes de abrir el bot a usuarios reales, por el tema de privacidad.
- Si el costo deja de ser cero (en ese caso hay que configurar `AI_PRECIOS_JSON`).
