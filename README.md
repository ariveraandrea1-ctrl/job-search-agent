# job-search-agent

Agente de búsqueda y postulación laboral orquestado con **n8n**, construido en tres proyectos acumulativos: no son tres aplicaciones separadas, sino versiones cada vez más completas del mismo producto.

## Visión del producto

1. **Proyecto 1 — Perfil inteligente y radar**: núcleo de datos, entrevista de perfil y búsqueda multifuente (sin postulaciones ni navegador).
2. **Proyecto 2 — Copiloto de postulaciones**: adaptación documental, aprobación humana, navegación asistida (Playwright) y seguimiento de procesos.
3. **Proyecto 3 — Agente laboral multiusuario**: automatización autorizada, operación continua (queue mode, workers) y despliegue comercial.

Telegram es el canal principal de interacción; el correo es complementario para alertas, respuestas y resúmenes.

## Principios no negociables

- **n8n es el plano de control** de toda la automatización (eventos, subworkflows, reintentos, notificaciones). FastAPI y Playwright lo complementan, no lo reemplazan.
- **Supervisión humana obligatoria**: ninguna postulación real se envía sin autorización explícita, vigente y vinculada al contenido exacto.
- **Veracidad y evidencia**: todo dato tiene un estado (`CV_EXTRACTED`, `USER_CONFIRMED`, `INFERRED`, `MISSING`, `CONFLICTING`). La IA no inventa experiencia, estudios, certificaciones, idiomas, salario, disponibilidad ni logros.
- **Integración responsable**: se prefiere siempre, en este orden, API oficial > alertas oficiales por correo/RSS > scraping permitido > navegación asistida y visible > proceso manual. No se evaden CAPTCHA, MFA ni mecanismos anti-bot.
- **Multiusuario desde el inicio**: aunque el Proyecto 1 corra local, las tablas funcionales incluyen `tenant_id` y `user_id` desde el esquema.
- **Portabilidad**: dominio en servicios versionados, prompts versionados fuera de los nodos de n8n, conectores con contrato común, modelos consumidos por alias mediante un router, secretos fuera de los workflows exportados.

Detalle completo de los tres proyectos, arquitectura, stack, persistencia, workflows de n8n, plan semanal y riesgos: ver [`docs/architecture/especificacion-tecnica.md`](docs/architecture/especificacion-tecnica.md).

## Estructura del repositorio

```text
job-search-agent/
├── compose/                 # docker-compose por entorno (local, beta, production)
├── n8n/workflows/           # workflows de n8n exportados (JSON)
├── services/
│   ├── profile-api/         # FastAPI: dominio, extracción, versiones de perfil
│   ├── credential-broker/   # Gestión y aislamiento de credenciales por tenant
│   └── browser-worker/      # Automatización con Playwright (Proyecto 2+)
├── database/{migrations,seeds,backups}/
├── prompts/{schemas,templates,evaluations}/   # Prompts versionados fuera de n8n
├── connectors/{policies,fixtures}/            # Políticas de uso y fixtures de prueba por fuente
├── tests/{unit,integration,e2e}/
├── docs/{architecture,decisions,runbooks,threat-model}/
├── .env.example
└── README.md
```

## Cómo levantar el entorno local (Proyecto 1)

> Estado actual: andamiaje del repositorio. El `docker-compose.local.yml` es un esqueleto — los servicios (n8n, postgres, profile-api, minio, mailpit) se implementan en el siguiente incremento (Semana 1 del plan).

1. Copiar `.env.example` a `.env` y completar los valores (nunca se commitea `.env`).
2. `docker compose -f compose/docker-compose.local.yml up -d`
3. n8n queda disponible en `http://localhost:5678`.

## Stack (Proyecto 1)

Docker Compose · n8n Community autoalojado · Python 3.12 + FastAPI · Pydantic 2 · SQLAlchemy 2 + Alembic · PostgreSQL 17 + pgvector · MinIO · PyMuPDF / python-docx · NVIDIA NIM (con Ollama y GPT económico como alternativas) · Telegram + IMAP/SMTP · Mailpit · Pytest · Git.

## Flujo de trabajo (Gitflow)

- `main`: siempre desplegable/estable.
- `develop`: integración de features completadas.
- `feature/{nombre-funcionalidad}`: una rama por funcionalidad, creada desde `develop`, con Pull Request de vuelta a `develop`.

Commits progresivos por fase lógica, push frecuente. Ver [`docs/decisions/`](docs/decisions/) para decisiones técnicas registradas.

## Seguridad

- `.env` fuera de Git (ver `.gitignore`).
- `N8N_ENCRYPTION_KEY` estable y respaldada.
- Sin CVs, tokens ni cookies en logs.
- Ver [`docs/threat-model/`](docs/threat-model/) para el modelo de amenazas.
