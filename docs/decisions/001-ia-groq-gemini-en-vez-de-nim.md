# ADR 001 · IA: Groq + respaldo Gemini en vez de NVIDIA NIM

**Fecha:** 2026-09-25 · **Estado:** aceptada · **Decidió:** Andrea

## Contexto
La especificación propone NVIDIA NIM para prototipar, un modelo local
opcional y un GPT económico como respaldo, con alias (`fast`, `structured`,
`reasoning`, `embedding`) para no escribir nombres de modelos en cada
workflow (secciones 5, 8 y 11).

## Decisión
- Proveedor principal: **Groq**, modelo `openai/gpt-oss-120b` (plan gratis).
- Respaldo: **Gemini Flash-Lite** (`gemini-3.5-flash-lite`; la 2.5 ya no
  está disponible para cuentas nuevas).
- Todo pasa por un solo subworkflow, **`ai-model-router`**: si Groq falla,
  responde Gemini. Los demás flujos no saben qué proveedor contestó.
- Los prompts viven en `prompts/templates/` con versión (ej. `puntaje-v1`,
  `v4` del CV), no dentro de los nodos.
- Sin modelo local.

## Por qué
- **Costo USD 0:** Groq tiene plan gratis con límites claros (~1.000
  solicitudes/día, ~8.000 tokens/minuto) que alcanzan para el volumen del
  Proyecto 1 (puntaje de 10 vacantes por hora + CVs).
- **Rápido y con salida JSON:** `response_format: json_object` sirve para
  el CV y el puntaje, que profile-api valida.
- **Dos proveedores distintos** dan respaldo real: si cae uno, responde el
  otro (probado con falla simulada y con falla real; la telemetría del
  2026-10-06 mostró 4 de 20 llamadas resueltas por Gemini).
- **Sin modelo local:** el Mac de desarrollo tiene memoria limitada y ya
  corre Docker con n8n, Postgres y MinIO (la especificación misma dice "sin
  LLM local concurrente" con 8 GB).
- **Un solo punto de cambio:** `ai-model-router` cumple la idea de los
  alias: cambiar de proveedor es tocar un flujo, no todos.

## Consecuencias
- No hay alias separados (`fast`/`structured`/`reasoning`): hoy todas las
  tareas usan el mismo modelo. Si aparecen tareas con necesidades distintas,
  se agrega un campo `alias` a la entrada del router.
- **Privacidad:** el plan gratis de Gemini puede usar los datos para mejorar
  sus productos. Con usuarios reales hay que pasar a plan pago o quitar
  Gemini como respaldo de datos personales (CV).
- Cuotas gratis: si se superan, Groq responde error y todo cae a Gemini;
  la telemetría (`/telemetria/ia`) muestra el porcentaje de respaldo.

## Cuándo revisarla
- Si el respaldo (Gemini) pasa de ~30 % de las llamadas por varios días.
- Antes de abrir el bot a usuarios reales fuera de pruebas (privacidad).
- Si el costo deja de ser 0 (configurar `AI_PRECIOS_JSON`).
