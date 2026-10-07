# ADR 002 · Fuente por API: Get on Board en vez de Greenhouse/Lever

**Fecha:** 2026-10-01 · **Estado:** aceptada · **Decidieron:** Andrea y Claude

## Contexto
La especificación pide tres tipos de fuentes: alertas por correo,
**APIs públicas de Greenhouse y Lever** por empresa, y URL manual.

## Decisión
Reemplazar Greenhouse/Lever por la **API pública de Get on Board**
(`https://www.getonbrd.com/api/v0/categories/{categoria}/jobs`), sin clave
y sin scraping. El flujo `radar-getonbrd` consulta cada 4 horas las
categorías de los usuarios activos, y profile-api filtra por palabras clave
del usuario, idioma (no inglés), ubicación (remota o Colombia) y nivel
(hasta Semi Senior).

## Por qué
- Se investigó: las empresas con vacantes de QA en Colombia que publican en
  Greenhouse/Lever son internacionales, piden nivel senior y entrevistas en
  inglés (ej. CI&T, Monks, Capco sin vacantes en Colombia). No encajan con
  el perfil objetivo (QA junior, español).
- Greenhouse/Lever exigen mantener una lista de empresas una por una; Get on
  Board es un portal tech de Latinoamérica, en español, con categorías
  (ej. `sysadmin-devops-qa`) y nivel de experiencia en los datos.
- Sigue cumpliendo el requisito de fondo: una fuente por **API oficial**,
  sin scraping (respeta términos de uso).

## Consecuencias
- Las tres fuentes quedan: correo (LinkedIn, Indeed, Workana), API (Get on
  Board) y URL manual (`/vacante`).
- Las categorías de Get on Board se derivan de las palabras clave de cada
  usuario (`/preferencias`).
- El lector de URL reconoce links de Get on Board (mismo id que la API, sin
  duplicados entre fuentes).

## Cuándo revisarla
- Si el perfil buscado cambia a roles donde Greenhouse/Lever sí tengan
  vacantes relevantes (ej. inglés avanzado, empresas internacionales):
  agregar un conector por empresa es compatible con el diseño actual
  (`_guardar_lote` en profile-api).
