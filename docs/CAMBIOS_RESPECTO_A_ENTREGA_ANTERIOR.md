# Cambios respecto a lo entregado anteriormente (PIA)

Todo lo que cambió respecto a `PIA_Hotel_Costa_Azul.zip` (entrega previa) está marcado con **[CAMBIO]** en los documentos y con `CAMBIO PIA` en el código.

| # | Qué cambió | Dónde | Motivo |
|---|---|---|---|
| 1 | **Tope de crédito de $3,000 MXN** por habitación (consumos sin hospedaje, menos pagos; se supera con pago parcial o autorización de Administración). Error nuevo `CreditoExcedidoError` (409). | `src/domain/cuenta_estancia.py`, `errores.py`, `comandos.py`, `servicios.py`, `api/app.py` | Regla del BRD del equipo y de la Actividad 5 que el PIA anterior no tenía. |
| 2 | **Penalidad de cancelación**: sin costo con ≥ 48 h; si no, una noche; excepción del Jefe de Reservaciones/Administración. Respuesta con `penalidad_cancelacion` y evento `ReservacionCancelada.penalidad`. | `src/domain/reservacion.py`, `eventos.py`, `servicios.py`, `api/app.py`, `serializadores.py` | Misma razón. La penalidad no se guarda en la base (se devuelve en la respuesta y el evento). |
| 3 | `POST /reservaciones/{id}/cancelar` acepta un cuerpo **opcional** (`fecha_llegada`, `autorizacion_jefe`); `POST .../cargos` acepta `autorizacion_administracion`. Sin cuerpo, todo funciona como antes. | `src/api/app.py`, `docs/api/openapi.yaml` | Compatibilidad hacia atrás. |
| 4 | BRD: RF-05, RF-08, alcance, supuestos, riesgos y pregunta abierta 1. | `docs/BRD.md` | Reflejar 1 y 2. |
| 5 | Historias US-05 y US-08: 5 escenarios Gherkin nuevos. | `docs/historias_usuario.md` | Reflejar 1 y 2. |
| 6 | Matriz de trazabilidad: pruebas nuevas en US-05 y US-08. Glosario: 2 términos. | `docs/matriz_trazabilidad.*`, `docs/glosario.md` | Reflejar 1 y 2. |
| 7 | Pruebas: +13 unitarias (`tests/unit/test_reglas_actividad5.py`) y +2 de integración de la API. Total unitarias: 186 (antes 173). | `tests/` | Probar 1 y 2. |
| 8 | **Informe** rehecho con la portada FIME y los tres integrantes; **presentación** rehecha con el formato FIME. | `entregables/` | Pedido del equipo. |

## Lo que NO cambió
Arquitectura, ADR, diagramas, máquina de estados, Specifications, persistencia, Docker, CI/CD y los 120 casos / 20 transiciones (mismos resultados).

## Lo que sigue sin implementarse
Expiración de la pre-reserva a 24 h (sí se hizo en el laboratorio de la Actividad 5, E9), no-show con cargo, salida anticipada, extensión y llegada anticipada.

## Pendiente de ejecutar en su equipo
Las pruebas de integración (FastAPI/SQLAlchemy), Ruff, cobertura oficial, Docker Compose, GitHub Actions y Render (ver `PASOS_PARA_EL_EQUIPO.md`).


## Pantalla sencilla (CAMBIO)
- Nuevo `src/api/static/panel.html` y ruta `GET /` en `src/api/app.py` (fuera del contrato OpenAPI).
- Nuevas pruebas: `tests/unit/test_panel.py` (2) y `test_pantalla_sencilla_en_la_raiz` en `tests/integration/test_api_http.py`.
