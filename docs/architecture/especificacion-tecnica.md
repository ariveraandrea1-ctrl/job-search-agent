# Hoja de ruta técnica: agente de búsqueda y postulación laboral con n8n

Este es el plan técnico con el que arranqué el proyecto. Describe las tres etapas, desde un laboratorio local hasta un producto para varios usuarios. Durante la construcción del Proyecto 1 tomé algunas decisiones distintas a las que dice este documento; cada una está explicada en `docs/decisions/`.

- Estado: estrategia lista para implementar.
- Horizonte inicial: una beta de 5 usuarios, con un máximo de 30 durante los primeros 3 meses.
- Método: primero defino el producto final y después construyo por etapas, de lo más básico a lo más completo.
- Núcleo: n8n coordina toda la automatización.

## 1. Visión del producto

No se construirán tres aplicaciones aisladas. Cada proyecto será una versión más capaz del mismo producto:

1. Proyecto 1, perfil inteligente y radar: crea el núcleo de datos, la entrevista profesional y la búsqueda en varias fuentes.
2. Proyecto 2, copiloto de postulaciones: agrega la adaptación de documentos, las aprobaciones, la navegación asistida y el seguimiento.
3. Proyecto 3, agente laboral para varios usuarios: completa la automatización autorizada, la operación continua y el despliegue comercial.

El producto final deberá analizar CV, entrevistar al usuario, mantener un perfil versionado, generar filtros, buscar en distintas fuentes, puntuar vacantes, preparar documentos, solicitar autorización, postular cuando esté permitido y seguir las respuestas de reclutadores.

Telegram será el canal principal; el correo será complementario para alertas, respuestas y resúmenes.

### 1.1 Diseño regresivo

Primero se define el producto final y después sus prerrequisitos. La construcción ocurre en el sentido contrario:

~~~mermaid
flowchart RL
    P3["Proyecto 3: agente completo"] --> P2["Proyecto 2: copiloto"]
    P2 --> P1["Proyecto 1: núcleo y radar"]
~~~

| Diseño desde el resultado | Ejecución | Resultado acumulado |
|---|---:|---|
| Agente multiusuario comercial | 3 | Automatización controlada y producción |
| Copiloto de postulaciones | 2 | Preparación, aprobación y seguimiento |
| Perfil y radar | 1 | Datos confiables y oportunidades |

## 2. Principios no negociables

### 2.1 n8n como protagonista

n8n será el orquestador central:

- Recibe eventos de Telegram, correo, cron y webhooks.
- Coordina subworkflows y servicios especializados.
- Ejecuta reglas, esperas, aprobaciones, reintentos y compensaciones.
- Invoca modelos mediante un router común.
- Elige API, extracción permitida, navegador asistido o intervención humana.
- Registra ejecuciones, notifica y genera resúmenes.

FastAPI y Playwright complementan a n8n; no sustituyen su función de plano de control.

### 2.2 Supervisión humana

El agente puede buscar, analizar, priorizar y preparar. Ninguna postulación real se envía sin autorización explícita, vigente y vinculada al contenido exacto.

### 2.3 Veracidad y evidencia

| Estado | Significado |
|---|---|
| CV_EXTRACTED | Dato explícito en el CV |
| USER_CONFIRMED | Confirmado por el usuario |
| INFERRED | Inferencia pendiente; no puede enviarse como hecho |
| MISSING | Información todavía ausente |
| CONFLICTING | Contradicción que exige aclaración |

La IA no inventará experiencia, estudios, certificaciones, idiomas, salario, disponibilidad ni logros.

### 2.4 Integración responsable

Orden de preferencia:

1. API oficial o integración autorizada.
2. Alertas oficiales por correo o RSS.
3. Página pública cuya extracción esté permitida.
4. Navegación asistida y visible.
5. Preparación de materiales y proceso manual.

No se evadirán CAPTCHA, MFA, controles de acceso, límites ni mecanismos anti-bot.

### 2.5 Multiusuario desde el inicio

Aunque el Proyecto 1 sea local, las tablas funcionales tendrán tenant_id y user_id. Esto evita reconstruir la persistencia al migrar a beta.

### 2.6 Portabilidad

- La lógica de dominio vive en servicios y esquemas versionados.
- n8n concentra la orquestación, no todos los algoritmos.
- Los prompts se versionan fuera de los nodos.
- Los conectores implementan un contrato común.
- Los modelos se consumen mediante alias y un router.
- Los secretos no aparecen en workflows exportados.

## 3. Comparación de los tres proyectos

| Dimensión | Proyecto 1, Básico | Proyecto 2, Intermedio | Proyecto 3, Completo |
|---|---|---|---|
| Producto | Perfil + radar | Copiloto de postulación | Agente laboral SaaS |
| Usuarios | 1 local; preparado para 5 | 5 beta; hasta 30 | Multiusuario comercial |
| Entorno | Docker Compose local | Local + beta económica | Producción escalable |
| Fuentes | Correo, Greenhouse, Lever, URL | HTML permitido + Playwright | Catálogo gobernado |
| Acción | Descubrir y priorizar | Preparar, aprobar y asistir | Aplicar cuando esté autorizado |
| Persistencia | PostgreSQL, pgvector, MinIO | Núcleo + aplicaciones | Servicios administrados + colas |
| IA | Extracción, entrevista, scoring | Documentos y correo | Agente, evaluación y aprendizaje |
| n8n | Modo regular | Esperas y compensaciones | Queue mode y workers |
| Navegador | No | Playwright aislado | Pool de browser workers |
| Redis | No | Opcional por carga | Sí para colas |

### 3.1 Arquitectura acumulativa

~~~mermaid
flowchart TB
    U["Telegram, correo y panel futuro"] --> N["n8n: plano de control"]
    N --> S["Servicios de dominio"]
    N --> C["Conectores de empleo"]
    N --> A["Router de IA"]
    S --> D["PostgreSQL + pgvector"]
    S --> O["Objetos S3/MinIO"]
    C --> B["APIs, correo, HTML y navegador"]
    N --> Q["Colas y workers"]
~~~

En el Proyecto 1 no se despliegan colas ni navegador. En el Proyecto 2 se añade el navegador. En el Proyecto 3 se activan colas, workers y operación productiva.

# Proyecto 1: Perfil inteligente y radar multifuente

## 4. Resultado funcional

Al finalizar, un usuario podrá:

1. Registrarse mediante invitación desde Telegram.
2. Cargar un CV PDF o DOCX.
3. Recibir un análisis estructurado.
4. Completar una entrevista adaptativa.
5. Confirmar o corregir inferencias.
6. Obtener un perfil maestro versionado.
7. Configurar roles, modalidad, ubicación, idioma, salario y exclusiones.
8. Buscar en al menos tres tipos de fuentes.
9. Recibir vacantes normalizadas, deduplicadas y puntuadas.
10. Consultar, guardar o descartar oportunidades por Telegram.
11. Recibir un resumen diario por Telegram y correo.

Todavía no se implementan postulaciones ni navegador. Primero se construye una base confiable.

## 5. Arquitectura del Proyecto 1

~~~mermaid
flowchart TB
    T["Telegram / cron / correo"] --> N["n8n"]
    N --> P["Profile API"]
    N --> R["Router de IA"]
    N --> J["Conectores"]
    P --> DB["PostgreSQL + pgvector"]
    P --> M["MinIO"]
    J --> DB
    R --> L["NIM / local / GPT"]
~~~

| Componente | Responsabilidad |
|---|---|
| n8n | Canales, reglas, programación, reintentos y auditoría |
| Profile API | Dominio, extracción, versiones y consultas complejas |
| PostgreSQL | Usuarios, perfiles, vacantes, ejecuciones y auditoría |
| pgvector | Similitud semántica entre perfil y vacantes |
| MinIO | CV originales y artefactos derivados |
| Router de IA | Proveedor, modelo, salida estructurada, costo y fallback |
| Conectores | Conversión de cada fuente al esquema canónico |
| Telegram | Comandos, entrevista, consultas y notificaciones |
| Correo | Alertas de entrada y resumen diario |
| Mailpit | Captura local de correos durante desarrollo |

## 6. Stack completo del Proyecto 1

| Capa | Tecnología | Decisión |
|---|---|---|
| Contenedores | Docker Compose v2 | Entorno reproducible |
| Orquestación | n8n Community autoalojado | Núcleo de automatización |
| API | Python 3.12 + FastAPI | Servicios pequeños y comprobables |
| Contratos | Pydantic 2 | Validación estricta |
| ORM/migraciones | SQLAlchemy 2 + Alembic | Evolución segura |
| Datos | PostgreSQL 17 | Fuente de verdad |
| Vectores | pgvector | Evita otra base |
| Archivos | MinIO | Compatible con S3 |
| PDF/DOCX | PyMuPDF + python-docx | Extracción documental |
| OCR opcional | OCRmyPDF/Tesseract | CV escaneados |
| IA de desarrollo | NVIDIA NIM | Prototipado alojado |
| IA local opcional | Ollama | Privacidad y experimentación |
| Fallback/comparación | GPT económico | Calidad y resiliencia |
| Embeddings | Modelo multilingüe local | Bajo costo |
| Canales | Telegram + IMAP/SMTP | Interacción y correo |
| Correo de pruebas | Mailpit | Evita envíos reales |
| Túnel opcional | Cloudflare Tunnel | Webhooks en desarrollo |
| Pruebas | Pytest | Servicios y contratos |
| Versionado | Git | Workflows, prompts y migraciones |

Servicios obligatorios: n8n, postgres, profile-api, minio y mailpit. Opcionales: ollama, cloudflared y pgadmin.

No se añaden Redis, Playwright, Grafana ni panel web en este proyecto.

### 6.1 Capacidad local

| Memoria | Docker | IA |
|---|---|---|
| 8 GB | Aproximadamente 4 GB | NIM alojado; sin LLM local concurrente |
| 16 GB o más | 6–8 GB | NIM + modelo local pequeño opcional |

Reservar aproximadamente 25–30 GB para imágenes, volúmenes, documentos y respaldos.

## 7. Persistencia del Proyecto 1

| Grupo | Tablas |
|---|---|
| Identidad | tenants, users, tenant_members, consents |
| Perfil | profiles, profile_versions, profile_evidence, experiences, skills |
| Documentos | documents |
| Entrevista | interview_sessions, interview_questions, interview_answers |
| Búsqueda | job_sources, connectors, search_profiles, jobs, job_occurrences |
| Evaluación | job_scores, saved_jobs |
| Operación | notifications, ai_calls, workflow_events, failed_executions |

Todas las tablas funcionales incluirán tenant_id. Las restricciones únicas lo combinarán con las claves naturales.

### 7.1 Objetos en MinIO

~~~text
tenants/{tenant_id}/users/{user_id}/
├── cv/original/
├── cv/extracted/
├── profile/exports/
└── diagnostics/
~~~

PostgreSQL guarda metadatos, hashes y referencias; MinIO conserva archivos.

### 7.2 Versionado e idempotencia

- Cada corrección crea una versión inmutable.
- Toda ejecución usa idempotency_key.
- La vacante canónica combina URL, empresa, cargo y ubicación.
- Los callbacks de Telegram se consumen una vez.
- Un reintento no crea una segunda vacante o notificación.

## 8. IA del Proyecto 1

Casos de uso:

- Extracción estructurada del CV.
- Contradicciones y vacíos.
- Siguiente pregunta de entrevista.
- Normalización de cargos y habilidades.
- Preferencias en lenguaje natural.
- Clasificación y explicación de vacantes.
- Embeddings y resumen diario.

n8n invoca el subworkflow ai-model-router:

| Nivel | Tarea | Estrategia |
|---|---|---|
| Determinístico | Fechas, salario, ubicación, deduplicación | Código/SQL |
| Ligero | Clasificación simple | NIM o modelo local |
| Estructurado | CV, entrevista y explicación | NIM; GPT económico como fallback |
| Embeddings | Perfil y vacantes | Modelo multilingüe local |

Se registran proveedor, alias, prompt, tokens, latencia, costo y fallback.

Control de costo: primero filtros fijos, después embeddings y al final una evaluación con IA generativa solo para las mejores vacantes. Meta local: USD 0–5 al mes, como estimación y no como tarifa garantizada.

## 9. Workflows de n8n del Proyecto 1

| Familia | Workflows |
|---|---|
| Sistema | sys-global-error-handler, sys-audit-execution, sys-retry-failed, sys-daily-maintenance |
| Perfil | profile-onboarding, profile-cv-upload, profile-cv-extraction, profile-analysis, profile-interview-next-question, profile-answer-processing, profile-confirmation, profile-versioning |
| Búsqueda | search-orchestrator, connector-email-alerts, connector-greenhouse, connector-lever, connector-company-page, connector-manual-url, job-normalizer, job-deduplicator, job-hard-filters, job-ai-scoring |
| Comunicación | telegram-command-router, telegram-notification, summary-daily-telegram, summary-daily-email |

Comandos: /start, /perfil, /subir_cv, /completar_perfil, /preferencias, /buscar, /nuevas, /mejores, /detalle, /guardar, /descartar, /resumen y /pausar.

## 10. Plan de 7 semanas

| Semana | Incremento | Aprendizaje n8n |
|---:|---|---|
| 1 | Compose, servicios y health checks | Credenciales, variables y ejecuciones |
| 2 | Invitaciones y Telegram | Triggers, Switch y subworkflows |
| 3 | Carga, extracción y análisis | Webhooks, binarios, HTTP y JSON |
| 4 | Entrevista y perfil versionado | Wait, callbacks y estados |
| 5 | Tres conectores | Schedule, paginación y rate limits |
| 6 | Deduplicación, scoring y resúmenes | Merge, Code, SQL y errores |
| 7 | Pruebas, respaldo, métricas y demo | Idempotencia y depuración |

### 10.1 Definición de terminado

- Cinco usuarios aislados pueden registrarse.
- Se procesa un PDF y un DOCX reales.
- Toda inferencia puede confirmarse o corregirse.
- Perfil estructurado y versionado.
- Tres tipos de fuentes y 100 vacantes de prueba.
- Deduplicación entre fuentes.
- Consulta, guardado y descarte por Telegram.
- Resumen por Telegram y correo.
- Telemetría de IA.
- Fallos recuperables sin duplicados.
- Respaldo restaurable de PostgreSQL y MinIO.
- Reconstrucción desde repositorio y .env.example.

Puerta al Proyecto 2: no automatizar postulaciones hasta validar perfil, evidencia, deduplicación, idempotencia, secretos y restauración.

# Proyecto 2: Copiloto de postulaciones y seguimiento

## 11. Resultado funcional

Conserva el Proyecto 1 y añade:

- Adaptación contextual del CV y carta.
- Respuestas respaldadas por evidencia.
- Aprobación vinculada a versiones exactas.
- Scraping estático permitido.
- Playwright en modo asistido.
- Envío directo solo mediante integración autorizada.
- Seguimiento de confirmaciones, entrevistas, pruebas, rechazos y ofertas.
- Borradores de respuesta sujetos a aprobación.
- Beta en nube para 5 usuarios y crecimiento hasta 30.

## 12. Arquitectura del Proyecto 2

~~~mermaid
flowchart TB
    T["Telegram y correo"] --> N["n8n"]
    N --> D["Servicios de dominio"]
    N --> P["Playwright aislado"]
    N --> R["Router de IA"]
    D --> DB["PostgreSQL + pgvector"]
    D --> O["S3 / MinIO"]
    N --> H["Aprobación y espera durable"]
~~~

Playwright recibe tareas limitadas y devuelve evidencia; no toma decisiones de negocio.

## 13. Stack incremental

| Capa | Tecnología | Propósito |
|---|---|---|
| Navegador | Playwright | Formularios dinámicos permitidos |
| Browser service | Node.js o Python | Sesiones, capturas y trazas |
| Documentos | DOCX/HTML + PDF | CV y cartas versionados |
| Correo entrante | IMAP IDLE o polling | Respuestas |
| Objetos nube | S3 compatible | Documentos externos |
| Entrada | Caddy, Traefik o Nginx | TLS y proxy |
| Backups | Copias cifradas | Datos y objetos |
| Redis | Opcional | Cuando la concurrencia lo exija |

## 14. Modos de integración

| Modo | Alcance |
|---|---|
| API | API oficial; aprobación antes del envío |
| EMAIL_ALERT | Búsqueda con alertas nativas |
| STATIC_SCRAPER | Lectura de HTML público permitida |
| BROWSER_ASSISTED | Completa hasta revisión |
| DIRECT_AUTHORIZED | Incluye envío con permiso |
| MANUAL_ONLY | Prepara; el usuario envía |

Cada fuente registra términos revisados, fecha, autenticación, límites, frecuencia, campos, modo y alternativa.

## 15. Preparación y aprobación

~~~mermaid
stateDiagram-v2
    [*] --> Descubierta
    Descubierta --> Evaluada
    Evaluada --> Preparando
    Preparando --> PendienteAprobacion
    PendienteAprobacion --> Autorizada
    PendienteAprobacion --> Descartada
    Autorizada --> Asistida
    Autorizada --> Enviada
    Asistida --> Enviada
    Enviada --> Confirmada
    Confirmada --> Entrevista
    Confirmada --> Rechazada
    Entrevista --> Oferta
~~~

La autorización incluye tenant, usuario, vacante, versiones de perfil/CV/carta, respuestas, modo, hash, creador y expiración. Si cambia un elemento, expira.

## 16. Workflows nuevos

- application-prepare
- application-document-tailoring
- application-question-resolver
- application-request-approval
- application-wait-approval
- application-executor
- browser-task-dispatcher
- browser-result-handler
- email-response-monitor
- email-response-classifier
- reply-draft-generator
- application-timeline
- application-reminders

## 17. Persistencia incremental

Tablas: document_versions, applications, application_packages, application_answers, approvals, application_events, browser_tasks, browser_artifacts, messages, message_classifications, reply_drafts y connector_policies.

Applications tendrá una restricción única por tenant, usuario, vacante y tipo. El ejecutor verifica idempotencia antes y después de cada llamada externa.

## 18. IA del Proyecto 2

Nuevas tareas:

- Comparar requisitos con evidencias.
- Seleccionar y adaptar el CV.
- Generar carta verificable.
- Detectar preguntas sin respuesta.
- Clasificar correo y proponer contestaciones.

Reglas:

- Ningún hecho sin profile_evidence.
- Validador determinístico posterior.
- Modelo y prompt versionados.
- Baja confianza deriva al usuario.
- El correo saliente no se envía automáticamente.

## 19. Despliegue beta

### 19.1 Cinco usuarios

- Una VM con Docker Compose.
- n8n, API y proxy en contenedores.
- PostgreSQL en la VM durante beta temprana.
- Objetos S3 y backups cifrados fuera de la VM.
- Playwright aislado y con baja concurrencia.

### 19.2 Crecimiento hasta 30

| Señal | Acción |
|---|---|
| CPU/RAM sostenida | Aumentar VM o separar navegador |
| Ejecuciones acumuladas | Redis + n8n queue mode |
| Base crítica | PostgreSQL administrado |
| Playwright bloquea | Browser workers dedicados |
| Restauración lenta | Servicios administrados |

Cuotas iniciales por usuario:

- 2–3 búsquedas al día.
- 3–5 fuentes.
- 30 vacantes nuevas al día.
- 10 evaluaciones profundas al día.
- 5 paquetes por semana.
- 3 procesos de navegador por semana.
- 250 MB de documentos.

Presupuesto orientativo: USD 25–70/mes para 5 usuarios, sujeto a proveedor, región y precios vigentes.

## 20. Plan de 7–9 semanas

1. Aplicaciones, eventos y autorizaciones.
2. CV, carta y respuestas versionadas.
3. Aprobación por Telegram con expiración.
4. Scraper permitido y Playwright de prueba.
5. Flujo asistido, barreras y recuperación.
6. Monitor de correo y línea de tiempo.
7. Despliegue, backups y observabilidad.
8. Pruebas con usuarios y correcciones.

### 20.1 Definición de terminado

- Paquete versionado y verificable.
- Aprobación exacta y con expiración.
- Conector estático y flujo dinámico de prueba.
- CAPTCHA/MFA provoca pausa, no evasión.
- Flujo directo autorizado y asistido demostrados.
- Línea de tiempo completa.
- Clasificación de correo.
- Respuestas sugeridas requieren aprobación.
- Cinco usuarios operan aislados.
- Ruta probada hasta 30.
- Cero duplicados en E2E y restauración documentada.

# Proyecto 3: Agente laboral multiusuario completo

## 21. Resultado funcional

- Conversación natural desde Telegram.
- Búsqueda, preparación, aprobación, envío autorizado y seguimiento.
- Colas y workers.
- Aislamiento fuerte de tenants.
- Credenciales seguras por usuario.
- Catálogo gobernado de conectores.
- Métricas, trazas y alertas.
- Planes, cuotas, consentimiento y eliminación.
- Aprendizaje supervisado.
- Despliegue, rollback y recuperación.

## 22. Arquitectura de producción

~~~mermaid
flowchart TB
    E["Telegram, correo y API"] --> G["Entrada segura"]
    G --> N["n8n main"]
    N --> Q["Redis / cola"]
    Q --> W["n8n workers"]
    W --> S["Servicios de dominio"]
    W --> B["Browser workers"]
    S --> P["PostgreSQL administrado"]
    S --> O["Objetos S3"]
    W --> A["Router de IA"]
~~~

| Capa | Responsabilidad |
|---|---|
| Entrada | TLS, rate limit, autenticación y webhooks |
| n8n main | Webhooks, programación y distribución |
| Redis | Cola y coordinación |
| n8n workers | Ejecución horizontal |
| Dominio | Reglas, autorización, credenciales y datos |
| Browser workers | Sesiones efímeras por usuario |
| PostgreSQL | Fuente transaccional |
| S3 | Documentos y evidencias cifradas |
| Observabilidad | Logs, métricas, trazas y alertas |

## 23. Stack de producción

| Capa | Tecnología sugerida |
|---|---|
| Orquestación | n8n queue mode |
| Cola | Redis administrado o compatible |
| Datos | PostgreSQL administrado + pgvector |
| Objetos | S3 con cifrado/versionado |
| Dominio | FastAPI |
| Navegador | Pool aislado de Playwright |
| Entrada | Gateway/proxy con TLS |
| Identidad | OIDC |
| Secretos | Gestor externo |
| Métricas/logs | Prometheus compatible + logs estructurados |
| CI/CD | Pruebas, migraciones y despliegue versionado |

Kubernetes no se recomienda para los primeros 30 usuarios.

## 24. Organización de n8n

~~~text
system/          profile/          search/
  error-handler   onboarding        orchestrator
  audit            cv-ingestion      connector-*
  retry            interview         normalize
  health           versioning        score

application/     communications/   ai/
  prepare          telegram-router   model-router
  approval         email-monitor     extraction
  execute          notifications     evaluation
  timeline         summaries         fallback
~~~

Reglas:

- Workflows públicos pequeños que delegan.
- Propagar tenant_id, user_id, correlation_id e idempotency_key.
- Timeout, reintentos limitados y compensación.
- Procesos prolongados modelados como estados.
- Workflows, prompts y migraciones versionados juntos.
- Errores sin CV ni secretos en logs.

## 25. Agente conversacional

Ejemplos:

- "Busca vacantes Java remotas en español".
- "No muestres posiciones que exijan inglés C1".
- "¿Por qué esta vacante tiene 82 %?".
- "Prepara la vacante 235".
- "¿Qué falta para autorizarla?".
- "Muéstrame procesos sin respuesta durante diez días".

Flujo: primero se entiende la intención, luego se revisan permisos y contexto, se pide confirmación si la acción es sensible, se ejecuta un flujo fijo, se deja registro y al final se responde. El LLM interpreta y explica; no ejecuta por sí solo acciones irreversibles.

## 26. Credenciales y aislamiento

Se propone un credential broker:

- n8n recibe una referencia opaca.
- El servicio valida tenant, usuario, propósito y vigencia.
- Descifra solo durante la operación.
- Emite token temporal cuando sea posible.
- Audita sin registrar el secreto.

Controles: filtro obligatorio por tenant, Row-Level Security, prefijos por tenant, sesiones efímeras, URLs firmadas, exportación/eliminación y rotación.

## 27. IA avanzada

| Tarea | Estrategia |
|---|---|
| Extracción rutinaria | Modelo pequeño |
| Perfil vs. vacante | Modelo de mayor calidad bajo demanda |
| Embeddings | Multilingüe local o servicio económico |
| Conversación | Modelo rápido con herramientas limitadas |
| Evaluación offline | Modelo juez + referencia humana |

Usar alias fast, structured, reasoning y embedding; no codificar nombres concretos en todos los workflows.

Conjunto de evaluación: 30 CV, 100 vacantes, 50 preguntas, 50 correos, casos adversos y ejemplos bilingües. Medir exactitud, precisión/recall, correlación del ranking, hechos sin evidencia, costo, latencia y revisión humana.

## 28. Observabilidad

Técnica: ejecuciones, p50/p95, reintentos, cola, errores por conector, recursos, sesiones de navegador y costo de IA.

Producto: vacantes, descartes, aplicaciones, respuestas, entrevistas, ofertas, tiempo de respuesta, rendimiento por fuente/CV, intervenciones y costo unitario.

No se fijan SLA comerciales hasta medir 30 días de beta.

## 29. Despliegue productivo progresivo

1. Local: desarrollo y datos sintéticos.
2. Beta de 5: una VM, PostgreSQL local, objetos externos y backups.
3. 10–20 usuarios: PostgreSQL administrado y navegador separado.
4. Cerca de 30: queue mode, Redis y workers.
5. Comercial: servicios críticos administrados, secretos externos y monitoreo.

| Estrategia | Ventaja | Riesgo | Uso |
|---|---|---|---|
| Una VM | Bajo costo | Punto único de fallo | Beta |
| Administrada | Disponibilidad | Mayor costo | Producción |
| Híbrida | Equilibrio | Migraciones | Recomendación |

## 30. Licencia de n8n

Antes de vender:

- Revisar la [Sustainable Use License](https://docs.n8n.io/n8n-community-license/).
- Documentar uso de n8n y credenciales de clientes.
- Solicitar confirmación comercial cuando corresponda.
- Mantener dominio, datos y credential broker fuera de n8n.
- Presupuestar licencia comercial si es necesaria.

La decisión continúa como investigación. No debe asumirse que Community cubre automáticamente el servicio comercial.

## 31. Definición de terminado

- Operación E2E para múltiples tenants.
- Conectores independientes y desactivables.
- Autorización verificable.
- Modos API, asistido y manual.
- Sin mezcla de credenciales, cookies, documentos o sesiones.
- Queue mode sin duplicados.
- Métricas y alertas.
- Calidad de IA evaluada.
- Costos y cuotas documentados.
- Backup, restauración, despliegue y rollback probados.
- Decisión formal de licencia.
- Políticas de privacidad y retención.

## 32. Repositorio objetivo

~~~text
job-search-agent/
├── compose/
│   ├── docker-compose.local.yml
│   ├── docker-compose.beta.yml
│   └── docker-compose.production.yml
├── n8n/workflows/
├── services/
│   ├── profile-api/
│   ├── credential-broker/
│   └── browser-worker/
├── database/{migrations,seeds,backups}/
├── prompts/{schemas,templates,evaluations}/
├── connectors/{policies,fixtures}/
├── tests/{unit,integration,e2e}/
├── docs/{architecture,decisions,runbooks,threat-model}/
├── .env.example
└── README.md
~~~

## 33. Seguridad y privacidad

- Cifrado en tránsito y reposo.
- N8N_ENCRYPTION_KEY estable y respaldada.
- .env fuera de Git.
- Invitaciones y autorización de Telegram.
- Validación de archivos.
- Sin CV, tokens o cookies en logs.
- Retención y eliminación.
- Separación de entornos.
- Mínimo privilegio y auditoría.
- Respuesta a incidentes.

## 34. Pruebas acumulativas

Unitarias: extracción, normalización, duplicados, filtros, comandos, evidencia, correo y autorizaciones.

Integración: Telegram–n8n–PostgreSQL; documento–perfil; fuente–deduplicación; aprobación–ejecutor; correo–estado; n8n–browser; fallo–reintento.

E2E: alta y CV; vacante duplicada; postulación autorizada; CAPTCHA/MFA; autorización expirada; formulario modificado; reintento sin duplicado; rechazo/entrevista; exportación y eliminación.

## 35. Riesgos

| Riesgo | Mitigación |
|---|---|
| Bloqueo de cuenta | Política y modo asistido/manual |
| Cambio de HTML | Adaptadores, fixtures y circuit breaker |
| Experiencia inventada | Evidencia y aprobación |
| Duplicados | Idempotencia y restricciones |
| Exposición | Aislamiento, cifrado y minimización |
| Costos de IA | Filtros, caché, modelos y cuotas |
| Clasificación errónea | Confianza mínima y revisión |
| Fallo de infraestructura | Backups y restauración |
| Dependencia de n8n | Dominio externo y contratos |
| Licencia incompatible | Revisión antes de vender |
| Complejidad prematura | Componentes por señal real |

## 36. Entregables por proyecto

Cada Work Item tendrá objetivo, alcance, contratos, datos, workflows, errores, aceptación, pruebas, métricas y riesgos.

Cada proyecto entregará workflows n8n, servicios, migraciones, .env.example, README, diagramas, catálogo de conectores, pruebas, video demostrativo, decisiones, costos y runbook de restauración.

## 37. Decisiones

### Tomadas

- Un producto en tres proyectos acumulativos.
- n8n como orquestador.
- Telegram como interfaz.
- PostgreSQL + pgvector y MinIO/S3 desde el inicio.
- FastAPI solo para especialización.
- Multiusuario desde el esquema.
- Aprobación humana para toda postulación.
- NIM para prototipos, local opcional y GPT económico como fallback.
- Local primero; nube tras cerrar E2E.
- Infraestructura híbrida progresiva.

### Pendientes

- Proveedor de nube, región y S3.
- Momento de PostgreSQL administrado.
- Identidad/OIDC.
- Modelos concretos según evaluación y precio.
- Licencia comercial de n8n.
- Plataformas con postulación directa permitida.
- Panel web frente a Telegram.
- Requisitos legales por país.

## 38. Próximo paso

Comenzar solo el Proyecto 1:

1. Repositorio y Compose.
2. Esquema multiusuario.
3. Invitación por Telegram.
4. Carga segura del CV.
5. Extracción y evidencias.
6. Entrevista adaptativa.
7. Perfil versionado.
8. Primer conector.
9. Normalización, deduplicación y scoring.
10. Resumen y recuperación de fallos.

Regla: no automatizar postulaciones hasta demostrar que perfil, evidencia, deduplicación y autorización son confiables.

## 39. Referencias

- [Documentación de n8n](https://docs.n8n.io/)
- [Docker Compose para n8n](https://docs.n8n.io/hosting/installation/server-setups/docker-compose/)
- [Queue mode](https://docs.n8n.io/hosting/scaling/queue-mode/)
- [Community Edition](https://docs.n8n.io/hosting/community-edition-features/)
- [Monitoreo](https://docs.n8n.io/hosting/logging-monitoring/monitoring/)
- [Licencia de n8n](https://docs.n8n.io/n8n-community-license/)
- [Telegram Trigger](https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.telegramtrigger/)
- [Playwright](https://playwright.dev/docs/input)
- [Greenhouse Job Board API](https://developer.greenhouse.io/job-board.html)
- [Lever Postings API](https://github.com/lever/postings-api)
- [NVIDIA NIM](https://developer.nvidia.com/nim)
- [API de NVIDIA NIM](https://docs.nvidia.com/nim/large-language-models/latest/api-reference.html)
- [Precios de OpenAI](https://developers.openai.com/api/docs/pricing)
- [Acuerdo de LinkedIn](https://www.linkedin.com/legal/user-agreement)
- [Términos de Indeed](https://www.indeed.com/legal)
