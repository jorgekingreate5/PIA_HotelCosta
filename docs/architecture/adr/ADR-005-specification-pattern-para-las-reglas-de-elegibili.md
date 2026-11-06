# ADR-005: Specification Pattern para las reglas de elegibilidad

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Relacionado con:** N2, N15

## Contexto
Reglas como 'puede procesarse' o 'beneficio preferente' combinan varias condiciones y se reutilizan.

## Decisión
Cada condición es una especificación pequeña (HuespedActivo, DetalleNoVacio, ReservacionAutorizada, TotalMinimo...). Se combinan con Y (&), O (|) y No (~) en funciones con nombre de negocio: puede_procesarse, puede_confirmarse, beneficio_preferente y requiere_revision.

## Alternativas consideradas
Condiciones if anidadas dentro de los servicios.

## Consecuencias
Las reglas se leen como el negocio las dice y se prueban una por una y combinadas. Más clases pequeñas.
