# ADR 005. El radar por correo lee solo el buzón de la admin

Fecha: 2026-10-05. Estado: aceptada para el Proyecto 1. Decidió: Andrea.

## Contexto

El radar por correo (`radar-correo`) lee por IMAP la etiqueta "Radar" de un Gmail al que llegan las alertas de LinkedIn, Indeed y Workana. Con varios usuarios, cada uno tiene sus propias vacantes.

## Decisión

El único buzón conectado es el de la admin. `POST /radar/email` guarda esas vacantes a nombre de la admin (si no se indica otro usuario) y les aplica sus palabras clave. Los demás usuarios reciben vacantes de Get on Board, según sus palabras y categorías, y pueden agregar las suyas con `/vacante <link>`.

## Por qué

Para leer el correo de otra persona se necesita su contraseña de aplicación de Gmail o un permiso OAuth por usuario. Son más permisos, más secretos que cuidar y un riesgo de privacidad que no se justifica en un proyecto de práctica.

LinkedIn e Indeed no tienen una API pública para las alertas. El correo es la única forma de recibirlas sin scraping, y el correo es personal.

## Consecuencias

Los usuarios invitados no reciben vacantes de LinkedIn, Indeed ni Workana.

El código ya acepta `telegram_user_id` en `/radar/email`, así que conectar otro buzón sería agregar otro flujo (o credencial) que mande ese id.

Ojo: como este camino no pasa por la lista de usuarios activos, hoy no respeta la pausa (BUG-34).

## Cuándo revisarla

Si el bot se abre a más usuarios reales. Ahí habría que evaluar OAuth de Gmail por usuario o una dirección de reenvío propia para cada uno.
