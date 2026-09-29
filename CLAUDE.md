# Notas para Claude en este repo

Este archivo lo lee cualquier sesión de Claude que trabaje en esta carpeta,
sin importar si viene de una conversación nueva o de una que ya se resumió.
Antes de tocar código en `services/profile-api`, leer esto entero.

## Qué es este proyecto

Agente de búsqueda y postulación laboral orquestado con n8n (Andrea es la
dueña, junior QA aprendiendo n8n/backend). Visión completa y principios no
negociables: [`README.md`](README.md) y
[`docs/architecture/especificacion-tecnica.md`](docs/architecture/especificacion-tecnica.md).
Estamos en el Proyecto 1 (perfil + radar).

## Mapa rápido de rutas (Proyecto 1)

- Servicio FastAPI: `services/profile-api/`
  - Código: `services/profile-api/app/main.py`, `app/models.py`, `app/db.py`
  - Migraciones (Alembic, escritas a mano, NO autogenerar — ver abajo):
    `services/profile-api/migrations/versions/000N_*.py`
- Compose local: `compose/docker-compose.local.yml` (servicio se llama `profile-api`)
- Script de arranque real: `scripts/start-local.sh`
- Runbooks operativos: `docs/runbooks/` — **leer antes de correr comandos de docker/alembic a mano**

## Advertencias críticas (aprendidas el 2026-09-23, no repetir el error)

1. **Nunca correr `docker compose` sin `--env-file .env`.**
   Comando correcto, siempre desde la raíz del repo:
   ```
   docker compose --env-file .env -f compose/docker-compose.local.yml <comando>
   ```
   Sin `--env-file .env`, Docker interpola las `${VARIABLE}` del compose como
   vacías y recrea `postgres`/`minio` con credenciales en blanco (los datos no
   se pierden porque usan volúmenes con nombre, pero es innecesariamente
   arriesgado). Detalle: `docs/runbooks/entorno-local.md`.

2. **Postgres es compartido entre `profile-api` y n8n** (misma base de datos,
   mismo esquema `public`). Por eso: **JAMÁS correr
   `alembic revision --autogenerate`** sin revisar el archivo generado antes
   de aplicarlo — Alembic compara contra TODAS las tablas de la base, incluidas
   las de n8n, y genera `op.drop_table(...)` para cada tabla de n8n que no
   está en `app/models.py`. Si se aplica tal cual, borra el n8n del usuario.
   Método seguro (el que se usó para `interview_answers`): escribir la
   migración a mano, siguiendo el estilo de
   `migrations/versions/0001_create_documents_table.py` (revision numérica
   simple `"0001"`, `"0002"`, etc., solo con las tablas propias del servicio).
   Detalle paso a paso: `docs/runbooks/entorno-local.md`.

3. **Las migraciones se aplican SOLAS al arrancar profile-api**: el
   `CMD` del Dockerfile es `alembic upgrade head && uvicorn ...`. O sea,
   `build profile-api` + `up -d profile-api` ya crea las tablas nuevas; el
   `alembic upgrade head` manual no hace nada (no imprime "Running
   upgrade"). Verificar con `exec profile-api alembic current`. Por esto
   mismo una migración autogenerada sin revisar se aplicaría sola.

4. El servicio `profile-api` NO tiene bind mount en el compose local — el
   código se copia al construir la imagen. Cualquier cambio en `app/` requiere
   `docker compose ... build profile-api` + `up -d profile-api` para que
   tome efecto (no alcanza con reiniciar el contenedor).

## ▶ PRÓXIMA SESIÓN — empezar por aquí (actualizado 2026-09-29)

Arranque: `cd ~/projects/job-search-agent` → `bash scripts/start-local.sh`
(con Docker Desktop abierto). Si "Publish" falla con "Bad request" en el
Telegram Trigger, el túnel se cayó: volver a correr el script y recargar n8n.

Qué sigue, en orden:
1. **Entrevista adaptativa** (Semana 4 de la especificación): usar
   `faltantes` del último perfil guardado (tabla `profiles`) para que la
   entrevista pregunte solo lo que falta, en vez de las 3 preguntas fijas
   de `interview_questions`. Idea inicial: después de "Guardar perfil",
   convertir cada faltante en pregunta (o mapear faltantes → preguntas).
2. Guardar las respuestas de la entrevista en campos del perfil
   (hoy van sueltas a `interview_answers`).
3. Limpiezas menores del perfil: duplicados en `habilidades.herramientas`
   ("REST" y "APIs REST").
4. Al terminar el Proyecto 1: actualizar el CV de Andrea con todo lo
   construido (n8n, integración de APIs, SQL práctico con JSONB, Docker,
   Git con ramas, IA con respaldo entre proveedores).

Pequeños arreglos pendientes:
- En n8n, la URL del nodo "Guardar perfil" todavía tiene 1 espacio al
  inicio (" http://profile-api:8000/profiles"). Funciona igual, pero
  quitarlo: clic en la caja URL → Cmd+← (ir al inicio) → fn+Delete una
  vez. En el JSON del repo ya está limpio; al próximo export revisar.
- Carpeta `Claude outputs/` en la raíz del repo (imágenes de ayuda): no
  versionar; Andrea puede borrarla.
- Desactivar el traductor de Chrome en localhost:5678 (traduce nombres de
  campos en pantalla y confunde).

Forma de trabajo con Andrea (importante): está aprendiendo. Explicar UN
paso a la vez, corto, esperar su "listo" antes del siguiente. Decir
exactamente dónde hacer clic en n8n y qué pegar. Nada de listas largas de
pasos de golpe.

## Historial de cambios relevantes

- 2026-09-23: agregado endpoint `POST /interview-answers` + modelo
  `InterviewAnswer` + migración `0002`, para guardar la respuesta del usuario
  a la pregunta de entrevista posterior al CV (n8n: nodo después de "Enviar
  un mensaje de texto1"). (Ya commiteado y conectado en n8n.)
- 2026-09-23 (tarde): `interview-answers` terminado de punta a punta
  (nodos "Enviar pregunta de entrevista" → salida `respuesta` del Switch →
  "Guardar respuesta de entrevista" → "Confirmar respuesta guardada"),
  probado en Telegram y verificado en la tabla. Workflow exportado a
  `n8n/workflows/telegram-invitacion.json`. Notas de los nodos van en
  Ajustes → Notas (no sticky notes, que se desordenan al ordenar el lienzo).
- 2026-09-23: `app/db.py` usa `pool_pre_ping=True`. Motivo: si el Mac se
  duerme o Docker se reinicia, Postgres se reinicia y profile-api quedaba
  con una conexión muerta ("terminating connection due to administrator
  command") → HTTP 500 en `/documents`. Al volver de una pausa, correr
  primero `bash scripts/start-local.sh` (el túnel de Cloudflare también se cae).

## Estado y lecciones (actualizado 2026-09-24)

- 2026-09-23: estado de conversación terminado y mergeado a develop: tabla
  `conversation_state` (migración `0003`, modelo `ConversationState`) y
  nodos n8n "Anotar: esperando respuesta" → "Leer anotación" (Always Output
  Data) → If "¿Esperaba respuesta?" (true: guardar → "Borrar anotación" →
  confirmar; false: "Responder: no entendí"). Probado con 4 casos en
  Telegram + verificación en BD.
- 2026-09-24 (rama `fix/cv-char-count`): "Send a text message1" decía
  "extraje  caracteres" sin número porque usaba `{{ $json.char_count }}` y su
  nodo anterior es "HTTP Request1" (/documents), que solo devuelve id y
  created_at. Ahora usa `{{ $('HTTP Request').item.json.char_count }}`.
- 2026-09-25 (rama `feature/entrevista-varias-preguntas`): entrevista de
  varias preguntas. Migración `0004`: tabla `interview_questions`
  (position, question; 3 preguntas sembradas: rol, modalidad, ubicación) y
  columna `conversation_state.question_position`. Las preguntas viven SOLO en
  esa tabla (no escritas en nodos): para agregar una, insertar una fila.
  Flujo n8n — CV: "Buscar primera pregunta" → "Enviar pregunta de
  entrevista" ({{ $json.question }}) → "Anotar: esperando respuesta" (guarda
  position). Respuesta: "Leer anotación" (JOIN con interview_questions) →
  If → "Guardar respuesta" (question de Leer anotación) → "Buscar siguiente
  pregunta" (position > actual, Always Output Data) → If "¿Hay otra
  pregunta?" (true: "Enviar siguiente pregunta" → "Anotar: siguiente
  pregunta" UPDATE; false: "Borrar anotación" → "Confirmar fin de
  entrevista"). Probado con 5 casos + verificación en BD.
- Próximo (Semana 4, según la especificación): secciones de preguntas,
  entrevista adaptativa con IA (no preguntar lo que ya está en el CV),
  confirmar inferencias y guardar respuestas en campos del perfil.
- 2026-09-28 (rama `feature/ai-model-router`): workflow nuevo
  `ai-model-router` (n8n/workflows/ai-model-router.json). Timbre "When
  Executed by Another Workflow" recibe `system_prompt` + `user_text` →
  "Groq: preguntar a la IA" (HTTP a api.groq.com, credencial Groq,
  model `openai/gpt-oss-120b`, max_completion_tokens 4096,
  reasoning_effort low, response_format json_object; On Error = continue
  using error output) → "Respuesta limpia" {text, provider:"groq"}. Salida
  Error → "Gemini: respaldo" (models/gemini-3.5-flash-lite; 2.5 ya no está
  disponible para cuentas nuevas) → "Respuesta limpia (Gemini)" {text,
  provider:"gemini"}. Respaldo probado con falla simulada y con falla real.
  Ojo: response_format json_object obliga a responder JSON; si una tarea
  futura necesita texto libre, volverlo opcional.
  En telegram-invitacion: rama desde "Send a text message1" →
  "Instrucciones: extraer CV" (Set con system_prompt = prompt v2 y
  user_text = $('HTTP Request').item.json.text) → "Analizar CV con IA"
  (Execute Workflow → ai-model-router). Todavía NO se guarda el resultado.
  Lecciones: gpt-oss-20b se quedaba sin tokens (finish_reason "length",
  reasoning gastaba ~60%) y generaba JSON roto; 120b funciona. El nodo
  "When Executed by Another Workflow" no aparecía en el buscador de n8n:
  se creó importando el JSON.
- PENDIENTE próximo: prompt v3 (en `experiencia` los logros salen vacíos:
  pedir copiar todos los logros); luego guardar el JSON del perfil en BD;
  al final del proyecto, actualizar el CV de Andrea con todo lo construido
  (n8n, APIs, SQL práctico, Docker, IA con respaldo).
- Lección: en campos de expresión de n8n un espacio escondido tras el `=`
  (`"= {{ $json.step }}"`) rompe comparaciones del If. Revisar copiando el
  nodo (clic + Cmd+C) y mirando el JSON.
- Lección: el Telegram Trigger no permite ejecuciones de prueba mientras el
  workflow está publicado (hay que despublicar un momento). Sin datos de
  ejecución, el panel INPUT no muestra campos para arrastrar.
- Al descargar workflows, el navegador nombra `telegram-invitacion (N).json`;
  usar `ls -t ~/Downloads | head -3` para ver el nombre exacto y revisar que
  sea la versión nueva antes de moverla al repo.
- Decisión 2026-09-25 (Andrea): proveedor de IA principal = **Groq** (plan
  gratis, modelos gpt-oss; límites ~1.000 req/día, 8.000 tokens/min);
  respaldo = **Gemini Flash-Lite**. Todo pasa por un subworkflow
  `ai-model-router` para poder cambiar de proveedor en un solo lugar; los
  prompts van en `prompts/`, no dentro de los nodos. Ojo: Gemini gratis usa
  los datos para mejorar sus productos → con usuarios reales pasar a plan
  pago. (Hecho el 2026-09-28: credenciales Groq y Gemini creadas en n8n.)
- 2026-09-29 (rama `feature/prompt-cv-v3`): **prompt v3** del CV
  (`prompts/templates/extraer-cv-v3.txt`; v2 guardada al lado). Cambios:
  copiar TODOS los logros, copiar textos exactos, REST/JSON/HTTP van en
  `herramientas`, categoría nueva `habilidades.profesionales` (atención al
  cliente). Probado con el CV real: logros completos, clasificación bien.
  **Guardar perfil**: migración `0005` tabla `profiles` (telegram_user_id,
  document_id FK a documents, data JSONB, provider, prompt_version,
  created_at; una fila por CV = historial) + endpoint `POST /profiles`
  (valida que `text` sea JSON objeto; si no, 422 y no guarda; devuelve id,
  created_at y faltantes). n8n: nodo "Guardar perfil" (HTTP Request) después
  de "Analizar CV con IA", body con `$('Telegram Trigger')...chat.id`,
  `$('HTTP Request1').item.json.id`, `$json.text`, `$json.provider`,
  `"v3"`. Probado: curl positivo/negativo + Telegram + verificación en BD.
  Consulta útil: `data->'contacto'->>'nombre'`.
  También: `/extract-text` normaliza el texto del PDF con NFKC (las
  ligaduras "ﬁ" salían en el resumen: "ﬁnal" → "final").

