# Hotel Costa Azul – API de Reservaciones (PIA CLN, Caso 09)

Sistema de reservación, check-in, estancia, check-out y limpieza de Hotel Costa Azul. Arquitectura por capas con diseño guiado por el dominio (DDD), API REST con FastAPI, persistencia en PostgreSQL, Docker y CI/CD con GitHub Actions.

**Repositorio:** https://github.com/jorgekingreate5/hotel-costa-azul-cln  ·  **URL desplegada (Render):** _pegar aquí al desplegar_ (`/` = pantalla sencilla para clientes, `/docs` = Swagger, `/health` = estado)

**Equipo:** Jorge Luis Molina García (2147723), Jonathan Alexander Reyes Garcia (2146387) y Leonardo Davila Gongora (2145945) · UANL-FIME · Componentes de Lógica de Negocios.

## Qué problema resuelve
Recepción no veía de inmediato lo que Limpieza liberaba, la disponibilidad podía ser inconsistente, los cambios de habitación no se rastreaban y los cargos estaban dispersos. Aquí cada habitación tiene un solo estatus que cambia solo por operaciones del negocio, el cupo se descuenta al confirmar y se devuelve al cancelar, cada cambio de habitación queda en un historial y cada estancia tiene una cuenta única.

## Arranque rápido
```bash
cp .env.example .env
docker compose up --build        # API en http://localhost:8000/docs
```
Sin Docker:
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
CARGAR_DATOS_DEMO=1 uvicorn src.api.app:obtener_app --factory --reload
```
Todas las rutas (salvo `/health`) usan el encabezado `X-Rol`: `RESERVACIONES`, `RECEPCION`, `LIMPIEZA` o `ADMINISTRACION`.

## Pruebas y calidad
```bash
python -m pytest -v --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=80
python -m ruff check src tests scripts
python scripts/ejecutar_casos_pia.py      # 120 casos y 20 transiciones del PIA -> docs/evidencias/
```
Con Docker y PostgreSQL: `docker compose --profile pruebas run --rm pruebas`.

## Estructura
```
src/domain/          agregados, value objects, specifications, máquina de estados, eventos
src/application/     servicios (un método por caso de uso), comandos, permisos, puertos
src/infrastructure/  repositorios SQL y en memoria, Unit of Work, pasarela simulada, datos del PIA
src/api/             FastAPI, errores HTTP, serializadores
tests/unit           pruebas de dominio, servicios, datos del PIA y trazabilidad
tests/integration    pruebas con SQLAlchemy y con la API (TestClient)
datos/               datos ficticios del paquete del PIA (huéspedes, catálogo, operaciones, casos)
docs/                BRD, historias, glosario, trazabilidad, arquitectura, ADR, diagramas, API, despliegue
```

## Documentación
| Documento | Archivo |
|---|---|
| Requerimientos de negocio | `docs/BRD.md` |
| Historias de usuario con Gherkin | `docs/historias_usuario.md` |
| Glosario | `docs/glosario.md` |
| Matriz de trazabilidad | `docs/matriz_trazabilidad.md` y `.csv` |
| Arquitectura y patrones | `docs/architecture/arquitectura.md` |
| Decisiones (10 ADR) | `docs/architecture/adr/` |
| Diagramas (BPMN, dominio, clases, estados, secuencias, capas) | `docs/architecture/diagramas/` |
| Contrato de la API | `docs/api/` |
| Despliegue y CI/CD | `docs/despliegue.md` |
| Resultados de los casos del PIA | `docs/evidencias/` |

## Reglas del hotel que protege el dominio (resumen)
Cupo sin sobreventa; check-in con identidad y garantía validada; cuenta única por estancia; **tope de crédito de $3,000 MXN** en consumos (pago parcial o autorización de Administración); **cancelación gratuita con ≥ 48 h**, si no una noche de penalidad (excepción del Jefe de Reservaciones/Administración); cambio de habitación con historial; habitación liberada solo por Limpieza.

## Demo rápida (con la API levantada)
1. `GET /categorias` con `X-Rol: RESERVACIONES` → catálogo con cupo.
2. `POST /reservaciones` → 201 (SOLICITADA); `/autorizar` y `/confirmar` → CONFIRMADA.
3. `POST /reservaciones/{id}/check-in` (`X-Rol: RECEPCION`) → CHECK_IN.
4. `POST /reservaciones/{id}/cargos` con monto mayor al tope → 409; con `autorizacion_administracion: true` → 201.
5. `POST /reservaciones/{id}/cancelar` con `fecha_llegada` próxima → penalidad de una noche.

## Pantalla sencilla para clientes y jefes (CAMBIO)
Al abrir la raíz `/` aparece un panel con botones grandes y mensajes en español simple (disponibilidad, nueva reservación, check-in, consumos, check-out, limpieza y resumen). Usa la misma API y las mismas reglas; no es parte del contrato REST (`include_in_schema=False`).

## Cambios respecto a la entrega anterior
Ver `docs/CAMBIOS_RESPECTO_A_ENTREGA_ANTERIOR.md` (todo lo nuevo está marcado como **[CAMBIO]**).

## Limitaciones
La autenticación es un encabezado de rol, los eventos viven en memoria, no hay migraciones, la pasarela de garantías es simulada y la penalidad de cancelación no se guarda en la base. Siguen sin implementarse la expiración de la pre-reserva a 24 h, el no-show con cargo, la salida anticipada, la extensión y la llegada anticipada (ver BRD, sección 12).
