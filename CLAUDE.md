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

## ▶ PRÓXIMA SESIÓN — empezar por aquí (actualizado 2026-10-01)

Arranque: `cd ~/projects/job-search-agent` → `bash scripts/start-local.sh`
(con Docker Desktop abierto). Si "Publish" falla con "Bad request" en el
Telegram Trigger, el túnel se cayó: volver a correr el script y recargar n8n.

Qué sigue, en orden:
1. **Semana 5: radar de vacantes** (decidido con Andrea 2026-09-30).
   Nueva rama `feature/radar-...`. 3 tipos de fuentes:
   a. **Alertas por correo → Gmail → n8n**: LinkedIn, Indeed, Computrabajo
      y **Workana** (freelance). Un "lector" por formato de correo.
      Upwork / Freelancer.com después (verificar primero qué avisos por
      correo ofrecen hoy).
   b. **APIs públicas Greenhouse / Lever** por empresa (revisar cuáles de
      las empresas objetivo de Andrea las usan).
   c. **URL manual** enviada por Telegram.
   NO scraping directo de LinkedIn/Indeed/Computrabajo (ToS).
   ESTADO 2026-10-01: (a) hecho para LinkedIn, Indeed, Workana (+aviso
   Telegram); Computrabajo resumen → []. Falta (b) y (c).
   Diseño freelance: cada oportunidad lleva `tipo` = empleo | freelance;
   freelance → aviso inmediato por Telegram (la velocidad importa);
   palabras clave extra: QA/testing, n8n, automatización, Zapier/Make,
   soporte administrativo. En Semana 6 (scoring) la IA marca señales de
   alerta (pedir documentos/KYC, probar cuentas financieras, pagos fuera
   de la plataforma) y criterios distintos para freelance (presupuesto,
   duración, reputación del cliente, nº de propuestas).
2. Limpiezas del perfil: duplicados en `habilidades.herramientas`
   ("REST"/"APIs REST"); fechas que no respetan "AAAA-MM"
   (ej. educación "jul. 2026").
3. Al terminar el Proyecto 1: actualizar el CV de Andrea.
4. **Al terminar el Proyecto 1 (pedido por Andrea 2026-09-30): sesión de
   REPASO** de todo lo construido y CÓMO se hizo, con PREGUNTAS DE
   ENTREVISTA posibles y cómo responderlas con sus palabras (ej.: cómo
   evitaste duplicados, qué hace la consulta con jsonb_array_elements_text,
   por qué IMAP y no OAuth, cómo probaste el bot, qué bug encontraste y cómo
   lo corregiste con test de regresión, por qué IA con respaldo, Gitflow,
   migraciones a mano). Andrea quiere poder explicar el proyecto en
   entrevistas. Formato acordado: (a) presentación corta del proyecto
   (pitch 1–2 min) y versión larga tipo exposición (arquitectura, decisiones,
   problemas y cómo se resolvieron, pruebas); (b) banco de preguntas de
   entrevista CON RESPUESTAS que ella pueda dar con sus palabras, incluyendo
   el manejo que le dio a todo (cómo probó, cómo depuró, decisiones de
   seguridad/ToS); (c) simulacro: Claude pregunta, Andrea responde, Claude
   da retroalimentación. Reforzar también: que ella escriba consultas SQL
   sencillas.

Pequeños arreglos pendientes:
- En n8n, Switch: la regla 4 (/perfil) tiene Output Name "corregir" y la
  regla 5 (/corregir) no tiene nombre → poner "perfil" y "corregir".
  (Funciona igual porque las conexiones van por posición; en el JSON del
  repo ya está corregido.)
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
- 2026-09-29 (rama `feature/entrevista-adaptativa`): **entrevista
  adaptativa**. Migración `0006`: columna `interview_questions.topic`
  (única) + 5 preguntas nuevas → 8 temas: rol_buscado, modalidad, ciudad,
  salario, disponibilidad, ingles, contrato, certificaciones. **Prompt v4**
  (`prompts/templates/extraer-cv-v4.txt`): `faltantes` = lista SOLO de esas
  claves (deben coincidir EXACTO con `topic`). n8n: la entrevista ya no sale
  de "Send a text message1" sino de "Guardar perfil" → "Buscar primera
  pregunta" (SQL: topic IN faltantes del último perfil del usuario, vía
  `jsonb_array_elements_text`; $1 = chat.id; Always Output Data) → If
  "¿Hay preguntas?" (true: "Enviar pregunta de entrevista"; false: "Avisar:
  perfil completo"). "Buscar siguiente pregunta": position > $1 AND topic
  IN faltantes ($2 = chat.id). "Guardar perfil" manda prompt_version "v4".
  Probado: CV real → 7 preguntas (se saltó `ingles`, que el CV ya tenía),
  coincide con faltantes en BD; CV ficticio completo
  (Laura Prueba Gómez) → faltantes [] → mensaje "perfil completo" sin
  preguntas. Ojo: el perfil vigente es el ÚLTIMO de `profiles`; después de
  probar con un CV ficticio, volver a mandar el CV real.
- 2026-09-30 (rama `feature/preferencias-perfil`): **preferencias en el
  perfil + comando /perfil**. Migración `0007`: `interview_answers.topic`
  (NULL en respuestas viejas). `POST /interview-answers` acepta `topic`
  opcional. Endpoints nuevos: `GET /profiles/{id}/current` (JSON: perfil +
  `preferencias` = respuesta más reciente por tema + `faltantes_sin_responder`;
  404 si no hay perfil) y `GET /profiles/{id}/summary` (texto plano listo
  para Telegram, siempre 200; si no hay perfil pide el CV). Ambos usan
  `_perfil_vigente()`. n8n: "Leer anotación" trae `q.topic`; "Guardar
  respuesta de entrevista" manda `topic`; Switch con 4ª salida `perfil`
  (`/perfil`) → "Pedir resumen del perfil" (GET /summary) → "Enviar resumen
  del perfil" (Append n8n Attribution apagado). Probado en Telegram.
  Lección: el editor tenía el cambio pero el bot usaba la versión vieja →
  SIEMPRE verificar que el Publish quedó en verde (si no, el bot corre la
  versión publicada anterior). Diagnóstico útil: pestaña Executions → abrir
  el nodo y mirar su OUTPUT real.
- 2026-09-30 (rama `feature/corregir-perfil`): **/corregir <tema>**. Switch
  regla 5 (starts with "/corregir") → "Buscar pregunta a corregir" (SQL:
  `topic LIKE $1 || '%'` AND `length($1) > 0`; $1 = texto sin "/corregir",
  trim, minúsculas, sin tildes, `|| 'ninguno'` si queda vacío — un parámetro
  vacío hacía fallar el nodo Postgres en silencio; Always Output Data) → If
  "¿Tema válido?" (true: "Enviar pregunta a corregir" → "Anotar:
  corrigiendo" con step='corrigiendo'; false: "Explicar /corregir").
  "¿Esperaba respuesta?" acepta step esperando_respuesta_entrevista OR
  corrigiendo. Después de "Guardar respuesta de entrevista": If "¿Era
  corrección?" (true: "Borrar anotación (corrección)" → "Confirmar
  corrección"; false: "Buscar siguiente pregunta"). Lección: al insertar un
  If en medio de una línea, n8n conecta lo que seguía a TRUE; revisar.
  `/summary` termina con ayuda de /corregir. "Confirmar fin de entrevista"
  invita a /perfil y /corregir (= confirmar o corregir inferencias, cierra
  Semana 4). Append n8n Attribution apagado en TODOS los nodos Telegram.
  Probado: tema válido, tema inválido, sin tema, libreta limpia después.
- 2026-09-30 (rama `feature/radar-vacantes`): **radar, sesión 1**.
  Migración `0008` tabla `opportunities` (tipo empleo|freelance, source,
  external_id, title, company, location, url, description, raw JSONB,
  status nueva|guardada|descartada, score, dedup_key; UNIQUE
  (telegram_user_id, dedup_key)). `POST /opportunities`: huella =
  "source:external_id" o URL normalizada (sin query/#/barra final);
  si ya existe → created=false (idempotente, también ante carreras con
  IntegrityError). Probado: nueva, duplicada con otro ?trk=, tipo inválido 422.
  **Gmail**: verificación en 2 pasos activada; contraseña de aplicación
  "n8n radar" guardada en n8n como credencial IMAP **"Gmail radar (IMAP)"**
  (imap.gmail.com:993 SSL). Etiqueta Gmail **"Radar"** + 2 filtros:
  from:(jobs-noreply@linkedin.com OR jobalerts-noreply@linkedin.com) y
  from:(donotreply@jobalert.indeed.com OR notification@notifications.workana.com
  OR empleos_co@computrabajo.com). n8n debe leer SOLO la carpeta/etiqueta
  Radar. Formatos vistos: LinkedIn "Alertas de empleo" (jobalerts: "X busca
  personal para el puesto de Y") + jobs-noreply (recomendaciones "solicita
  ya…" y AVISOS DE POSTULACIÓN "se ha enviado tu solicitud"/"ha visto tu
  solicitud" → ignorar en el radar, útiles en Proyecto 2); Indeed "Cargo en
  Empresa. N empleos más en …"; Computrabajo "Equipo de Computrabajo" y
  "Tu lista de empleos" (muchas son de Bogotá/senior → Andrea podría ajustar
  sus alertas a Medellín/QA Jr); Workana "Nuevos proyectos de Soporte
  Administrativo" (solo esa categoría → agregar QA/testing y automatización
  en las notificaciones de Workana). Lección: al crear etiqueta nueva desde
  el filtro quedó llamada "crear"; se renombró a "Radar".
  SIGUIENTE: nodo Email Trigger (IMAP) leyendo "Radar" → lector LinkedIn.
- 2026-09-30 (radar, sesión 2): workflow n8n nuevo **radar-correo**:
  "Timbre: correo en Radar" (Email Trigger IMAP, credencial Gmail radar,
  Mailbox "Radar", Action Nothing, Format Resolved; al probar trae los NO
  leídos de Radar) → "Leer vacantes del correo" (HTTP POST
  profile-api /radar/email con telegram_user_id fijo 8553351572 —cambiar al
  ser multiusuario—, from_address = $json.from.value[0].address, subject,
  text). profile-api: `app/parsers.py` (lectores puros: parse_linkedin —
  bloques hasta "Ver anuncio de empleo: URL", toma las ÚLTIMAS 3 líneas no
  ruido = título/empresa/ubicación, external_id = id de /jobs/view/;
  parse_workana — "Título / ---- / desc / Leer más: URL", tipo freelance;
  parse_computrabajo → [] porque los correos resumen no listan vacantes;
  Indeed pendiente sin muestra) + `elegir_lector(remitente)`.
  `_guardar_oportunidad()` compartida por POST /opportunities y
  POST /radar/email (responde found/created/duplicates/new_items).
  Tests: `services/profile-api/tests/test_parsers.py` (pytest, textos
  inventados sin datos personales; correr: cd services/profile-api &&
  python3 -m pytest tests -v). Bug encontrado y corregido con test de
  regresión: línea "N personas estudiaron en la misma institución…"
  corría los campos. Probado con 13 correos reales: 26 vacantes LinkedIn +
  2 Workana guardadas; re-ejecutar → todo duplicates (idempotente).
  SIGUIENTE: aviso por Telegram de las nuevas (freelance inmediato),
  lector Indeed (falta un correo de ejemplo), publicar el workflow.
- 2026-10-01 (radar, sesión 3): **aviso por Telegram + lector Indeed**.
  profile-api: POST /radar/email devuelve `telegram_text` (None si no hay
  nuevas; freelance primero con ⚡; tope 10 líneas / 4000 caracteres).
  n8n radar-correo: "¿Hay vacantes nuevas?" (If `created` > 0) → TRUE →
  "Avisar vacantes nuevas" (Telegram, chat fijo 8553351572, sin atribución,
  sin vista previa de links). Publicado y exportado. `parse_indeed`:
  bloques separados por línea en blanco "Título / Empresa - Ubicación /
  (salario, etiquetas) / descripción / fecha / URL con jk=<id>";
  external_id = jk; url limpia https://co.indeed.com/viewjob?jk=<id>;
  "Desde casa" → "Remoto"; empresa/ubicación cortadas en el ÚLTIMO " - ".
  4 tests nuevos (12 en total). Probado con correo real: 8/8 vacantes.
  Lecciones de prueba (para el repaso): (1) el Email Trigger solo se
  dispara con correos que LLEGAN nuevos; marcar como no leído uno viejo no
  lo dispara. (2) "Execute step" en n8n reutiliza resultados anteriores de
  los nodos padres → resultados confusos (duplicates / created 0). Solución:
  fijar (pin) la salida de "Leer vacantes del correo" con created > 0,
  ejecutar el nodo de Telegram, y luego QUITAR el pin. (3) SQL desde la
  terminal: `docker compose --env-file .env -f
  compose/docker-compose.local.yml exec postgres psql -U job_search_agent
  -d job_search_agent -c "<consulta>;"` (pegar SQL suelto en zsh falla).
  Nota: la alerta de Indeed de Andrea era "business analyst" → llegan
  vacantes fuera de QA; sugerido ajustar alertas en origen. El filtro por
  preferencias + scoring IA es Semana 6.
  SIGUIENTE: Greenhouse/Lever, URL manual por Telegram; luego Semana 6.

