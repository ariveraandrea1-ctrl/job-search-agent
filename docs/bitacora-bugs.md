# Bitácora de bugs y hallazgos

Registro de los defectos y hallazgos encontrados mientras se construía el
proyecto: qué se vio, por qué pasaba, cómo se corrigió y cómo se evita que
vuelva a pasar. Se actualiza cada vez que aparece uno nuevo.

**Tipos:** 🐞 bug de código · ⚙️ configuración (n8n / Docker / Gmail) ·
🔍 hallazgo de prueba · 🧭 proceso

**Cómo se detectó:** prueba manual en Telegram · prueba con curl ·
revisión del JSON exportado · prueba automatizada (pytest) · observación de
datos reales · error en uso normal

---

## Resumen

| ID | Fecha | Tipo | Título | Estado |
|---|---|---|---|---|
| BUG-01 | 2026-09-23 | 🐞 | HTTP 500 en /documents después de que el Mac se duerme | Corregido |
| BUG-02 | 2026-09-24 | 🐞 | Mensaje "extraje  caracteres" sin número | Corregido |
| BUG-03 | 2026-09 | ⚙️ | Espacio escondido en expresiones de n8n rompía comparaciones y URLs | Corregido |
| BUG-04 | 2026-09 | 🧭 | Docker usaba código viejo (capas en caché) | Corregido (proceso) |
| BUG-05 | 2026-09-30 | ⚙️ | /perfil sin preferencias: el cambio no estaba publicado en n8n | Corregido (proceso) |
| BUG-06 | 2026-09-30 | 🐞 | /corregir sin tema fallaba en silencio | Corregido |
| BUG-07 | 2026-09-30 | ⚙️ | El If "¿Era corrección?" quedó conectado a la rama equivocada | Corregido |
| BUG-08 | 2026-09-30 | 🐞 | Lector de LinkedIn corría los campos (título = empresa) | Corregido + test |
| BUG-09 | 2026-10-01 | 🐞 | Aviso del radar no llegaba: correos de Indeed sin lector | Corregido + tests |
| BUG-10 | 2026-10-01 | 🐞 | Regresión: /perfil y /corregir dejaron de funcionar | Corregido |
| BUG-11 | 2026-10-01 | 🐞 | Get on Board traía vacantes de 24 a 43 días | Corregido + test |
| BUG-12 | 2026-10-03 | 🔍 | Pre-filtro por idioma no detectaba inglés exigido en el texto | Corregido (IA + regla fija) |
| BUG-13 | 2026-10-03 | 🔍 | Sospecha: la IA ponía 30 a todas las vacantes | Descartado (no era bug) |
| BUG-14 | 2026-10-03 | 🐞 | Listas de Telegram sin link a la vacante | Corregido + test |
| BUG-15 | 2026-10-03 | 🐞 | Texto "5 por hora" quedó desactualizado al cambiar el límite | Corregido |
| BUG-16 | 2026-10-01 / 10-03 | 🧭 | Archivo .git/index.lock bloqueaba los commits | Corregido (proceso) |
| BUG-17 | 2026-10-03 | 🐞 | Prueba de restauración daba PASO revisando solo 1 de 8 tablas (falso positivo) | Corregido + control |
| BUG-18 | 2026-10-03 | 🔍 | Llegaban vacantes de México por LinkedIn: no hay filtro de ubicación para fuentes de correo | Abierto |

---

## Detalle

### BUG-01 · HTTP 500 en /documents después de que el Mac se duerme
- **Síntoma:** al mandar el CV por Telegram después de una pausa, profile-api respondía 500 ("terminating connection due to administrator command").
- **Causa raíz:** al dormirse el Mac, Docker reinicia Postgres; profile-api seguía usando una conexión que ya estaba muerta.
- **Corrección:** `pool_pre_ping=True` en `app/db.py` (SQLAlchemy prueba la conexión antes de usarla y la renueva si murió).
- **Cómo se detectó:** error en uso normal.
- **Lección:** al volver de una pausa, correr `bash scripts/start-local.sh`.

### BUG-02 · Mensaje "extraje  caracteres" sin número
- **Síntoma:** el bot respondía "¡Recibí tu archivo y extraje  caracteres…" (sin el número).
- **Causa raíz:** el nodo usaba `{{ $json.char_count }}`, pero el nodo anterior (/documents) no devuelve ese campo; el dato venía de un nodo más atrás.
- **Corrección:** `{{ $('HTTP Request').item.json.char_count }}` (leer el dato del nodo que sí lo tiene).
- **Cómo se detectó:** prueba manual en Telegram.

### BUG-03 · Espacio escondido en expresiones de n8n
- **Síntoma:** comparaciones del If que nunca daban true; una URL que fallaba.
- **Causa raíz:** un espacio invisible antes del texto (`"= {{ $json.step }}"`, URL con espacios al inicio).
- **Corrección:** limpiar los campos; revisar el JSON del nodo (copiar el nodo y mirar el texto).
- **Cómo se detectó:** revisión del JSON exportado.

### BUG-04 · Docker usaba código viejo
- **Síntoma:** después de cambiar el código, la API seguía comportándose igual.
- **Causa raíz:** Docker reutilizaba capas en caché y el contenedor no se recreaba.
- **Corrección:** reconstruir siempre con `up -d --build --force-recreate profile-api`; verificar con `docker compose exec profile-api grep …` que el cambio está adentro.
- **Cómo se detectó:** prueba con curl.

### BUG-05 · /perfil sin preferencias (cambio no publicado)
- **Síntoma:** el editor de n8n tenía el cambio, pero el bot respondía como antes.
- **Causa raíz:** el workflow no se había publicado; el bot corre la última versión **publicada**.
- **Corrección:** publicar y verificar que el punto de Publish quede **verde**. Diagnóstico: pestaña Executions → abrir el nodo → OUTPUT real.
- **Cómo se detectó:** prueba manual en Telegram.

### BUG-06 · /corregir sin tema fallaba en silencio
- **Síntoma:** al escribir `/corregir` solo, el bot no respondía nada.
- **Causa raíz:** el parámetro de la consulta SQL quedaba vacío y el nodo Postgres fallaba sin mostrar error.
- **Corrección:** usar `|| 'ninguno'` cuando el tema queda vacío, para que la consulta corra y el flujo explique cómo usar /corregir.
- **Cómo se detectó:** prueba manual en Telegram (caso negativo).

### BUG-07 · If "¿Era corrección?" conectado a la rama equivocada
- **Síntoma:** después de una corrección, la entrevista seguía con la siguiente pregunta.
- **Causa raíz:** al insertar un If en una conexión, n8n conecta automáticamente el nodo siguiente a la salida **true**.
- **Corrección:** mover la conexión a la salida **false**.
- **Cómo se detectó:** prueba manual en Telegram.

### BUG-08 · Lector de LinkedIn corría los campos
- **Síntoma:** una vacante quedó guardada con título "Rappi" y empresa "Bogotá".
- **Causa raíz:** una línea extra del correo ("3 personas estudiaron en la misma institución…") se tomaba como título, y todo se corría una posición.
- **Corrección:** ampliar la regex de "ruido" (contactos, exalumnos, personas, solicitantes…). Se borró el registro malo y se reprocesó el correo.
- **Prueba de regresión:** `test_linkedin_ignora_personas_de_tu_institucion`.
- **Cómo se detectó:** observación de datos reales.

### BUG-09 · El aviso del radar no llegaba a Telegram
- **Síntoma:** al probar el workflow radar-correo no llegaba ningún aviso.
- **Causa raíz (dos):** (1) el trigger de correo solo reacciona a correos que **llegan nuevos**; marcar como no leído uno viejo no lo dispara. (2) El correo que sí llegó era de Indeed, que todavía no tenía lector (`source: null`).
- **Corrección:** se escribió `parse_indeed`. Para probar se usó *pin data* (fijar la salida de un nodo), porque "Execute step" reutiliza resultados viejos.
- **Pruebas:** 4 tests de Indeed (`test_indeed_*`).
- **Cómo se detectó:** prueba manual + Executions de n8n.

### BUG-10 · Regresión: /perfil y /corregir dejaron de funcionar
- **Síntoma:** las reglas 4 y 5 del Switch decían `perfil` y `corregir`, sin la barra `/`.
- **Causa raíz:** al ponerle nombre a las salidas, se escribió el nombre en la caja del **valor** en lugar de en "Output Name".
- **Corrección:** valor `/perfil` y `/corregir`; Output Name `perfil` y `corregir`.
- **Cómo se detectó:** revisión del JSON exportado **antes** de guardarlo en git.

### BUG-11 · Get on Board traía vacantes de 24 a 43 días
- **Síntoma:** en Telegram aparecían vacantes "nuevas" que en realidad eran viejas.
- **Causa raíz:** "nueva" significaba "nueva para el sistema", no "recién publicada". La API de Get on Board incluye vacantes antiguas entre las 50 que devuelve.
- **Corrección:** ignorar las publicadas hace más de 3 días (`published_at`); mostrar la antigüedad en las listas; Get on Board cada hora en vez de cada 4. Las viejas ya guardadas se descartaron con un `UPDATE`.
- **Prueba de regresión:** `test_getonbrd_ignora_las_publicadas_hace_mas_de_3_dias`.
- **Cómo se detectó:** observación de Andrea al usar el bot.
- **Limitación conocida:** los correos de LinkedIn e Indeed no traen fecha de publicación (solo se sabe cuándo llegaron).

### BUG-12 · El pre-filtro por idioma no detectaba inglés exigido en el texto
- **Síntoma:** "QA & Support Engineer" (Niuro) pasó el filtro aunque pide inglés C1.
- **Causa raíz:** el aviso no estaba marcado como "en inglés" (`lang`); el requisito estaba dentro de la descripción.
- **Corrección:** el puntaje con IA detecta el nivel de inglés exigido, y una **regla fija en código** limita el puntaje a 35 si piden inglés avanzado.
- **Prueba:** `test_tope_por_ingles_avanzado`.
- **Cómo se detectó:** revisión manual de los resultados del radar.

### BUG-13 · Sospecha: la IA ponía 30 a todas las vacantes (descartado)
- **Síntoma:** las 5 primeras vacantes puntuadas sacaron exactamente 30.
- **Hipótesis:** la IA no diferenciaba y repetía un valor.
- **Verificación:** se creó una vacante de prueba "ideal" (QA Junior en Medellín, sin inglés, 4 M COP). Resultado: **95**; otras sacaron 15 y 45.
- **Conclusión:** no era un bug. Las 5 primeras eran realmente malas para el perfil (senior, 4 años de experiencia, inglés C1). La vacante de prueba se borró.
- **Cómo se detectó:** observación de resultados + caso de prueba controlado.

### BUG-14 · Listas de Telegram sin link a la vacante
- **Síntoma:** /mejores, /nuevas y /guardadas mostraban la vacante pero no cómo abrirla.
- **Causa raíz:** el link solo se incluía en /detalle.
- **Corrección:** cada línea de las listas y del resumen diario trae el link debajo.
- **Prueba de regresión:** assert del link en `test_lista_muestra_numero_puntaje_y_ayuda`.
- **Cómo se detectó:** observación de Andrea al usar el bot.

### BUG-15 · Texto "5 por hora" desactualizado
- **Síntoma:** el resumen decía "va 5 por hora" cuando el límite ya era 10.
- **Causa raíz:** el número estaba escrito fijo en el texto, separado del lugar donde se configura (n8n).
- **Corrección:** texto genérico ("las va puntuando cada hora").
- **Cómo se detectó:** revisión del mensaje en Telegram.

### BUG-16 · .git/index.lock bloqueaba los commits
- **Síntoma:** git no dejaba hacer commit.
- **Causa raíz:** el asistente corrió `git status` desde su terminal; eso dejó el archivo de bloqueo y no lo pudo borrar.
- **Corrección:** `rm -f .git/index.lock`. Regla: el asistente no corre comandos de git; los corre Andrea.
- **Cómo se detectó:** error al hacer commit.

### BUG-17 · Prueba de restauración con falso positivo
- **Síntoma:** `probar-restauracion.sh` dijo "PASO: el respaldo se restaura completo", pero la tabla comparativa mostraba solo `opportunities`; faltaban 7 de las 8 tablas.
- **Causa raíz:** el ciclo `while read ... done < archivo.conteo` comparte la entrada con `docker compose exec -T`, que se leyó el resto del archivo en la primera vuelta. El ciclo terminó después de una tabla y, como esa coincidía, no había fallas.
- **Corrección:** `< /dev/null` en el comando de docker para que no lea la entrada del ciclo. Además, un control nuevo: si las tablas revisadas no son todas las del conteo, la prueba FALLA.
- **Lección:** una prueba que pasa también hay que revisarla; un PASO sin verificar cuánto se probó puede esconder el bug.
- **Cómo se detectó:** revisión de la salida de la prueba (Andrea la pegó y la tabla estaba incompleta).

### BUG-18 · Vacantes de otros países (México) en Telegram
- **Síntoma:** en /nuevas y en los avisos aparecían vacantes ubicadas en México.
- **Causa raíz:** el filtro de ubicación (remota o Colombia) solo existe para Get on Board. Lo que llega por correo (LinkedIn, Indeed, Workana) se guarda tal cual; depende de cómo esté configurada la alerta en cada portal. La IA baja el puntaje por ubicación pero no excluye.
- **Corrección:** (1) Andrea revisa la configuración de sus alertas de LinkedIn; (2) pendiente: regla fija en código como red de seguridad (otro país y no remota → descartada automáticamente).
- **Cómo se detectó:** observación de Andrea al revisar Telegram + consulta SQL por `location`.

---

## Riesgos y limitaciones conocidas (pendientes)

- **El sistema depende de que el Mac esté prendido.** Si está dormido a las 7 am, el resumen diario no se envía, y n8n no lo reenvía después. Mientras tanto: Mac conectado, Docker abierto y sin suspensión automática. Solución de fondo: servidor (Semana 7).
- **El túnel de Cloudflare cambia de URL** al reiniciarse; si se cae, el bot no recibe comandos (los avisos que salen sí funcionan).
- **LinkedIn por correo no trae descripción ni fecha** → el puntaje de esas vacantes es menos preciso.
- **`remote_local` de Get on Board** puede estar limitado a un país (no se lee `location_tenants`).
- **chat_id fijo (8553351572)** en varios workflows → decidir multiusuario en Semana 7.
- **Si falla n8n entero o Telegram, la alerta tampoco llega** (alertas-errores usa el mismo n8n y el mismo bot). Detecta fallas de un flujo, no caídas del sistema completo.
