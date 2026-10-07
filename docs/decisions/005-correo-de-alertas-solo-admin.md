# ADR 005 · El radar por correo lee solo el buzón de la admin

**Fecha:** 2026-10-05 · **Estado:** aceptada para el Proyecto 1

## Contexto
El radar por correo (`radar-correo`) lee por IMAP la etiqueta "Radar" de un
Gmail donde llegan las alertas de LinkedIn, Indeed y Workana. Con
multiusuario, cada usuario tiene sus propias vacantes.

## Decisión
El buzón conectado es **el de la admin**. `POST /radar/email` guarda esas
vacantes a nombre de la admin (si no se indica otro usuario) y les aplica
sus palabras clave. Los demás usuarios reciben vacantes de **Get on Board**
(según sus palabras y categorías) y pueden agregar las suyas con
`/vacante <link>`.

## Por qué
- Leer el correo de otra persona exige su contraseña de aplicación de Gmail
  o OAuth por usuario: más permisos, más secretos que proteger y un riesgo
  de privacidad que no se justifica para un proyecto de práctica.
- LinkedIn e Indeed no tienen API pública para alertas; el correo es la
  única forma sin scraping, y es personal.

## Consecuencias
- Los invitados no reciben vacantes de LinkedIn/Indeed/Workana.
- El código ya acepta `telegram_user_id` en `/radar/email`: conectar otro
  buzón es agregar otro flujo (o credencial) que mande ese id.

## Cuándo revisarla
- Si el bot se abre a más usuarios reales: evaluar OAuth de Gmail por
  usuario o una dirección de reenvío propia por usuario.
