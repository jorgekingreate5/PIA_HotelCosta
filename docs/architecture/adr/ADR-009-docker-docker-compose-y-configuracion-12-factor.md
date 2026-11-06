# ADR-009: Docker, Docker Compose y configuración 12-Factor

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Relacionado con:** RNF-04, RNF-05

## Contexto
El sistema debe levantarse igual en cualquier equipo y en la nube.

## Decisión
Dockerfile de varias etapas (base, test, runtime), Docker Compose con db, api y pruebas, variables de entorno para toda la configuración y .env.example sin secretos. Render se configura con render.yaml y GitHub Actions dispara el despliegue.

## Alternativas consideradas
Instalar todo a mano en cada equipo.

## Consecuencias
Entornos reproducibles y secretos fuera del repositorio. Hay que mantener los archivos de despliegue.
