# ADR-006: Máquina de estados explícita para reservaciones y habitaciones

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Relacionado con:** N2, N7

## Contexto
El ciclo de vida de una reservación y de una habitación tiene transiciones válidas y otras que deben rechazarse (confirmar dos veces, saltar al check-out).

## Decisión
Una tabla (estado, acción) → siguiente estado. Cualquier otra combinación lanza TransicionInvalidaError (409).

## Alternativas consideradas
Banderas booleanas sueltas en cada entidad.

## Consecuencias
Transiciones fáciles de revisar y de probar de forma exhaustiva. Agregar una acción requiere editar la tabla.
