# job-search-agent

Este es un agente que me ayuda a buscar trabajo. Revisa varias fuentes de vacantes, las compara con mi perfil, me avisa por Telegram de las que valen la pena y me manda un resumen cada mañana. Toda la automatización la orquesta n8n.

Lo estoy construyendo en tres etapas. No son tres aplicaciones distintas: cada etapa amplía la anterior.

## Video demo

Un recorrido de 3 minutos por el bot funcionando y por cómo lo probé: [ver en YouTube](https://youtu.be/1OXVT5XA_Fo).

## Las tres etapas

1. **Proyecto 1, perfil y radar.** El bot lee mi hoja de vida, me hace unas preguntas para completar el perfil y busca vacantes en varias fuentes. En esta etapa no postula a nada ni abre el navegador. Terminado y probado en octubre de 2026.
2. **Proyecto 2, copiloto de postulaciones.** Adaptar la hoja de vida a cada vacante, pedirme aprobación antes de enviar algo, ayudar a llenar formularios con Playwright y llevar el seguimiento de cada proceso.
3. **Proyecto 3, agente para varios usuarios.** Que funcione de forma continua para más personas, con colas de trabajo y un despliegue real.

Telegram es el canal principal. El correo lo uso para el resumen diario y algunas alertas.

Lo construí con apoyo de IA (Claude) para escribir buena parte del código. El diseño y la ejecución de las pruebas, las decisiones del proyecto y los flujos de n8n son míos; los flujos los armé yo misma en el editor. El archivo `CLAUDE.md` es el registro de contexto que uso para trabajar con la IA entre sesiones.

## Reglas que sigo en el proyecto

- n8n coordina todo: los eventos, los reintentos y las notificaciones. FastAPI y Playwright hacen el trabajo pesado, pero las decisiones de flujo están en n8n.
- Nada se envía a una empresa sin que yo lo apruebe, y la aprobación vale solo para el contenido exacto que revisé.
- La IA no se inventa datos. Cada dato del perfil tiene un estado (`CV_EXTRACTED`, `USER_CONFIRMED`, `INFERRED`, `MISSING`, `CONFLICTING`), y si algo falta, el bot pregunta en lugar de suponer experiencia, estudios, idiomas o salario.
- Para traer vacantes prefiero, en este orden: API oficial, alertas oficiales por correo o RSS, scraping permitido, navegación asistida y, al final, el proceso manual. No intento saltarme CAPTCHA, verificaciones en dos pasos ni protecciones contra bots.
- Desde el principio las tablas tienen `tenant_id` y `user_id`, para que el paso a varios usuarios no obligue a rehacer la base de datos.
- Los prompts, los conectores y los secretos viven fuera de los flujos de n8n, para poder cambiar de modelo de IA o de servidor sin reescribir todo.

El detalle de las tres etapas, la arquitectura, el plan semanal y los riesgos está en [`docs/architecture/especificacion-tecnica.md`](docs/architecture/especificacion-tecnica.md).

## Cómo está organizado el repositorio

```text
job-search-agent/
├── compose/                 # docker-compose por entorno (local, beta, producción)
├── n8n/workflows/           # flujos de n8n exportados en JSON
├── services/
│   ├── profile-api/         # FastAPI: perfil, extracción del CV, radar y comandos
│   ├── credential-broker/   # credenciales por usuario (planeado para el Proyecto 2)
│   └── browser-worker/      # automatización con Playwright (Proyecto 2)
├── database/{migrations,seeds,backups}/
├── prompts/{schemas,templates,evaluations}/
├── connectors/{policies,fixtures}/
├── scripts/                 # arranque local, respaldos y pruebas de punta a punta
├── tests/{unit,integration,e2e}/
├── docs/                    # arquitectura, decisiones, runbooks, pruebas y bitácora de bugs
├── .env.example
└── README.md
```

## Cómo levantarlo en local

1. Copia `.env.example` a `.env` y completa los valores. El `.env` nunca se sube a Git.
2. Cada vez que retomes el trabajo, por ejemplo después de cerrar el Mac o reiniciar Docker, corre:
   ```
   bash scripts/start-local.sh
   ```
   El script levanta los contenedores, crea un túnel nuevo de Cloudflare (la URL cambia cada vez que se reinicia) y la guarda en el `.env`.
3. n8n queda en `http://localhost:5678` y Mailpit, donde caen los correos de prueba, en `http://localhost:8025`.

Si después de arrancar el bot no responde en Telegram, revisa que Telegram tenga registrada la URL nueva (está explicado en [`docs/runbooks/entorno-local.md`](docs/runbooks/entorno-local.md)). Desde la corrección del BUG-36 el script lo revisa al arrancar y avisa si Telegram no quedó con la URL nueva.

Para levantar los contenedores sin tocar el túnel:
```
docker compose --env-file .env -f compose/docker-compose.local.yml up -d
```
El `--env-file .env` hace falta porque el `.env` está en la raíz y no junto al archivo de compose.

## Tecnologías del Proyecto 1

Docker Compose, n8n autoalojado, Python 3.12 con FastAPI, Pydantic 2, SQLAlchemy 2 y Alembic, PostgreSQL 17 con pgvector, MinIO para guardar los CV, PyMuPDF y python-docx para leerlos, Groq como IA principal y Gemini como respaldo, Telegram, IMAP y SMTP para el correo, Mailpit en local y Pytest para las pruebas.

## Pruebas

Así quedó el Proyecto 1 al cerrar las pruebas, el 11 de octubre de 2026:

- 30 casos de punta a punta y 2 pruebas exploratorias, ejecutados con el bot real en Telegram. Los 32 pasan. Cinco fallaron en la primera ejecución (BUG-32 a BUG-36); los corregí y volví a probar cada uno, con su regresión.
- 182 pruebas unitarias y de integración, todas en verde.
- 36 bugs y hallazgos anotados en la bitácora desde que empecé el proyecto, cada uno con su causa y cómo lo corregí.
- 31 observaciones de la ejecución: 9 quedaron corregidas con 8 cambios, y las demás quedaron decididas para el Proyecto 2 o sin cambio.

Dónde está cada cosa:

- Pruebas unitarias y de integración con Pytest en `services/profile-api/tests`.
- Plan de pruebas de punta a punta, con los resultados de cada caso y su evidencia: [`docs/testing/plan-pruebas-e2e.md`](docs/testing/plan-pruebas-e2e.md).
- Los mismos casos en Excel, con resumen de resultados y lista de defectos: [`docs/testing/casos-de-prueba-proyecto1.xlsx`](docs/testing/casos-de-prueba-proyecto1.xlsx).
- Todo lo que he encontrado y corregido está en [`docs/bitacora-bugs.md`](docs/bitacora-bugs.md).

## Cómo trabajo con Git

Uso Gitflow:

- `main` siempre tiene una versión estable.
- `develop` junta las funcionalidades terminadas.
- Cada funcionalidad va en su rama `feature/{nombre}`, sale de `develop` y vuelve a `develop` con un Pull Request.

Hago commits pequeños, uno por paso lógico. Las decisiones técnicas importantes quedan en [`docs/decisions/`](docs/decisions/).

## Seguridad

- El `.env` está en `.gitignore`.
- La `N8N_ENCRYPTION_KEY` no cambia y tiene respaldo.
- Ni los CV, ni los tokens, ni las cookies se escriben en los logs.
