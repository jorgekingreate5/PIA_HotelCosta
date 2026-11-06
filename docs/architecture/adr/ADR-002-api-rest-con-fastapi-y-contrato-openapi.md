# ADR-002: API REST con FastAPI y contrato OpenAPI

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Relacionado con:** RNF-06, RNF-07

## Contexto
Hace falta exponer los casos de uso a otros sistemas y documentar el contrato.

## Decisión
Se usa FastAPI: las rutas solo traducen HTTP a casos de uso, y la documentación OpenAPI se genera sola en /docs y /openapi.json. Los errores del dominio se convierten en 400, 403, 404, 409, 422 y 503 mediante una función pura (manejo_errores.py).

## Alternativas consideradas
Flask (sin validación ni documentación integradas) y Django REST (más pesado para este alcance).

## Consecuencias
Validación de entrada y documentación sin código extra. La API queda acoplada a Pydantic solo en la capa api.
