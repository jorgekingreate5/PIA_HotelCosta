# Contrato de la API

Documentación interactiva en `/docs` (Swagger UI) y `/openapi.json`. El archivo `openapi.yaml` es el contrato de diseño. Todas las rutas, salvo `/health`, requieren el encabezado `X-Rol`.

| Método | Ruta | Roles | Éxito | Errores |
|---|---|---|---|---|
| GET | `/health` | Público | 200 | — |
| GET | `/categorias` | Todos | 200 | 403 |
| POST | `/reservaciones` | RESERVACIONES | 201 | 403, 404, 422 |
| GET | `/reservaciones` | Todos | 200 | 403, 422 |
| GET | `/reservaciones/{reservacion_id}` | Todos | 200 | 403, 404 |
| POST | `/reservaciones/{reservacion_id}/autorizar` | RESERVACIONES | 200 | 403, 404, 409 |
| POST | `/reservaciones/{reservacion_id}/confirmar` | RESERVACIONES | 200 | 403, 404, 409, 422 |
| POST | `/reservaciones/{reservacion_id}/cancelar` | RESERVACIONES | 200 | 403, 404, 409 |
| POST | `/reservaciones/{reservacion_id}/no-show` | RESERVACIONES, RECEPCION | 200 | 403, 404, 409 |
| POST | `/reservaciones/{reservacion_id}/check-in` | RECEPCION | 200 | 403, 404, 409, 422, 503 |
| POST | `/reservaciones/{reservacion_id}/cargos` | RECEPCION | 201 | 403, 404, 409, 422 |
| GET | `/reservaciones/{reservacion_id}/cuenta` | RECEPCION, ADMINISTRACION | 200 | 403, 404 |
| POST | `/reservaciones/{reservacion_id}/cambio-habitacion` | RECEPCION | 200 | 403, 404, 409 |
| GET | `/reservaciones/{reservacion_id}/historial-cambios` | Todos | 200 | 403, 404 |
| POST | `/reservaciones/{reservacion_id}/check-out` | RECEPCION | 200 | 403, 404, 409 |
| GET | `/habitaciones` | Todos | 200 | 403 |
| POST | `/habitaciones/{habitacion_id}/limpieza-terminada` | LIMPIEZA | 200 | 403, 404, 409 |
| POST | `/habitaciones/{habitacion_id}/fuera-de-servicio` | ADMINISTRACION | 200 | 403, 404, 409 |
| POST | `/habitaciones/{habitacion_id}/reactivar` | ADMINISTRACION | 200 | 403, 404, 409 |
| GET | `/reportes/ocupacion` | ADMINISTRACION | 200 | 403 |
| GET | `/eventos` | ADMINISTRACION | 200 | 403 |

## Códigos de error

| Código | Cuándo |
|---|---|
| 400 | Valor inválido que detecta el dominio (por ejemplo, una cantidad no positiva). |
| 403 | El rol falta, no existe o no tiene permiso. |
| 404 | No existe la reservación, habitación, categoría, huésped o cuenta. |
| 409 | Conflicto con el estado: transición inválida, sin cupo, habitación no disponible, cuenta cerrada o con saldo. |
| 422 | El cuerpo no cumple el esquema, o la solicitud no cumple las condiciones del negocio (identidad, garantía, autorización). |
| 503 | Un servicio externo (pasarela de garantías) no respondió. |

Los errores del dominio responden `{"error": "Tipo", "detalle": "mensaje"}`.

## Ejemplo de flujo

```bash
curl -X POST localhost:8000/reservaciones -H 'X-Rol: RESERVACIONES' -H 'Content-Type: application/json' \
  -d '{"huesped_id":"HOT-C001","lineas":[{"categoria_id":"HOT-P001","cantidad":2}]}'
curl -X POST localhost:8000/reservaciones/RES-XXXX/autorizar -H 'X-Rol: RESERVACIONES'
curl -X POST localhost:8000/reservaciones/RES-XXXX/confirmar -H 'X-Rol: RESERVACIONES'
```