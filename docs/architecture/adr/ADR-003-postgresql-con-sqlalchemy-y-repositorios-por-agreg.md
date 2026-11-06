# ADR-003: PostgreSQL con SQLAlchemy y repositorios por agregado

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Relacionado con:** RNF-02

## Contexto
Los datos deben persistir entre reinicios y el dominio no debe conocer la base de datos.

## Decisión
Se usa PostgreSQL en Docker y Render, SQLAlchemy 2.x para el mapeo manual entre filas y objetos de dominio, y un repositorio por agregado (contratos en el dominio, implementaciones en infraestructura). Las pruebas usan SQLite en memoria y, en CI, PostgreSQL.

## Alternativas consideradas
ORM declarativo directo sobre las entidades (mezcla dominio y persistencia) y una base NoSQL (el modelo es relacional).

## Consecuencias
El dominio permanece limpio y se puede cambiar de motor. Hay código de conversión que mantener.
