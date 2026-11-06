"""Integración con SQLAlchemy sobre SQLite en memoria (cada prueba crea su propia base)."""
import os
from datetime import date, datetime
from decimal import Decimal

import pytest

from src.application.comandos import RealizarCheckIn, RealizarCheckOut, SolicitarReservacion
from src.domain.categoria import CategoriaHabitacion
from src.domain.cuenta_estancia import CuentaEstancia
from src.domain.errores import NoEncontradoError, SinCupoError
from src.domain.habitacion import Habitacion
from src.domain.huesped import Huesped
from src.domain.reservacion import Reservacion
from src.domain.valor import EstadoHabitacion, EstadoReservacion, Garantia, LineaReservacion
from src.infrastructure.composicion import crear_contenedor
from src.infrastructure.configuracion import Configuracion
from src.infrastructure.sql import Base, UnidadDeTrabajoSql, crear_fabrica, crear_motor

URL = os.environ.get("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
AHORA = datetime(2026, 10, 20, 12, 0)
GARANTIA = Garantia("tarjeta", "TC-0001")


def motor_limpio():
    """Base vacía en cada prueba (SQLite en memoria o PostgreSQL si hay TEST_DATABASE_URL)."""
    motor = crear_motor(URL)
    Base.metadata.drop_all(motor)
    Base.metadata.create_all(motor)
    return motor


def nueva_uow():
    fabrica = crear_fabrica(motor_limpio())
    return lambda: UnidadDeTrabajoSql(fabrica)


def sembrar(nueva):
    with nueva() as uow:
        uow.huespedes.guardar(Huesped("H1", "Ana", es_preferente=True, activo=True, ciudad="MTY"))
        uow.categorias.guardar(CategoriaHabitacion("C1", "Estándar", Decimal("428.00"), 5))
        uow.habitaciones.guardar(Habitacion("HAB-101", "101", "C1"))
        uow.habitaciones.guardar(Habitacion("HAB-102", "102", "C1"))
        uow.guardar_cambios()


def test_guardar_y_recuperar_huesped_categoria_y_habitacion():
    nueva = nueva_uow()
    sembrar(nueva)
    with nueva() as uow:
        assert uow.huespedes.obtener("H1").es_preferente is True
        assert uow.categorias.obtener("C1").tarifa == Decimal("428.00")
        assert [h.numero for h in uow.habitaciones.listar()] == ["101", "102"]
        assert [c.id for c in uow.categorias.listar()] == ["C1"]


def test_elementos_inexistentes_lanzan_no_encontrado():
    nueva = nueva_uow()
    with nueva() as uow:
        for buscar in (lambda: uow.huespedes.obtener("X"), lambda: uow.categorias.obtener("X"),
                       lambda: uow.habitaciones.obtener("X"), lambda: uow.reservaciones.obtener("X"),
                       lambda: uow.cuentas.obtener_por_reservacion("X")):
            with pytest.raises(NoEncontradoError):
                buscar()


def test_reservacion_con_lineas_garantia_y_cambios_se_recupera_completa():
    nueva = nueva_uow()
    sembrar(nueva)
    reservacion = Reservacion("R1", "H1", [LineaReservacion("C1", 2, Decimal("428.00"))],
                              referencia="REF-1", fecha_solicitud=date(2026, 10, 1),
                              autorizada=True, estado=EstadoReservacion.CHECK_IN)
    reservacion.garantia, reservacion.habitacion_id = GARANTIA, "HAB-102"
    reservacion.beneficio_preferente = True
    from src.domain.reservacion import CambioDeHabitacion
    reservacion.cambios.append(CambioDeHabitacion(AHORA, "HAB-101", "HAB-102", "Ruido", "E1"))
    with nueva() as uow:
        uow.reservaciones.guardar(reservacion)
        uow.guardar_cambios()
    with nueva() as uow:
        leida = uow.reservaciones.obtener("R1")
        assert leida.total == Decimal("856.00") and leida.estado == EstadoReservacion.CHECK_IN
        assert leida.garantia == GARANTIA and leida.habitacion_id == "HAB-102"
        assert leida.beneficio_preferente and leida.fecha_solicitud == date(2026, 10, 1)
        assert [(c.origen_id, c.destino_id) for c in leida.cambios] == [("HAB-101", "HAB-102")]
        assert [r.id for r in uow.reservaciones.listar()] == ["R1"]


def test_actualizar_una_reservacion_no_duplica_sus_lineas():
    nueva = nueva_uow()
    sembrar(nueva)
    reservacion = Reservacion("R1", "H1", [LineaReservacion("C1", 1, Decimal("428.00"))])
    for _ in range(2):
        with nueva() as uow:
            uow.reservaciones.guardar(reservacion)
            uow.guardar_cambios()
    with nueva() as uow:
        assert len(uow.reservaciones.obtener("R1").lineas) == 1


def test_cuenta_con_cargos_se_guarda_y_se_recupera():
    nueva = nueva_uow()
    sembrar(nueva)
    with nueva() as uow:
        uow.reservaciones.guardar(Reservacion("R1", "H1", []))
        cuenta = CuentaEstancia.abrir("CTA-R1", "R1", Decimal("856.00"), AHORA)
        cuenta.registrar_cargo("Restaurante", Decimal("250.00"), "E1", AHORA)
        cuenta.registrar_pago(Decimal("100.00"))
        uow.cuentas.guardar(cuenta)
        uow.guardar_cambios()
    with nueva() as uow:
        leida = uow.cuentas.obtener_por_reservacion("R1")
        assert leida.total == Decimal("1106.00") and leida.pagado == Decimal("100.00")
        assert [c.concepto for c in leida.cargos] == ["Hospedaje", "Restaurante"]


def test_sin_guardar_cambios_se_hace_rollback():
    nueva = nueva_uow()
    sembrar(nueva)
    with nueva() as uow:
        uow.huespedes.guardar(Huesped("H2", "Beto"))
    with nueva() as uow:
        with pytest.raises(NoEncontradoError):
            uow.huespedes.obtener("H2")


def test_flujo_completo_de_servicios_sobre_sql():
    motor_limpio()
    c = crear_contenedor(Configuracion(database_url=URL), reloj=lambda: AHORA)
    sembrar(c.nueva_uow)
    c.reservaciones.solicitar_reservacion("RESERVACIONES", SolicitarReservacion(
        "H1", [("C1", 2)], reservacion_id="R1", autorizada=True))
    c.reservaciones.confirmar_reservacion("RESERVACIONES", "R1")
    assert c.consultas.consultar_categorias("RECEPCION")[0].cupo_disponible == 3
    c.recepcion.realizar_check_in("RECEPCION", RealizarCheckIn("R1", "HAB-101", True, GARANTIA))
    c.recepcion.realizar_check_out("RECEPCION", RealizarCheckOut("R1", Decimal("856.00")))
    c.limpieza.marcar_habitacion_disponible("LIMPIEZA", "HAB-101")
    estados = {h.id: h.estado for h in c.consultas.estatus_de_habitaciones("RECEPCION")}
    assert estados["HAB-101"] == EstadoHabitacion.DISPONIBLE
    assert c.consultas.consultar_reservacion("RECEPCION", "R1").estado == EstadoReservacion.CHECK_OUT


def test_un_rechazo_sobre_sql_no_deja_cambios():
    motor_limpio()
    c = crear_contenedor(Configuracion(database_url=URL), reloj=lambda: AHORA)
    sembrar(c.nueva_uow)
    c.reservaciones.solicitar_reservacion("RESERVACIONES", SolicitarReservacion(
        "H1", [("C1", 9)], reservacion_id="R1", autorizada=True))
    with pytest.raises(SinCupoError):
        c.reservaciones.confirmar_reservacion("RESERVACIONES", "R1")
    assert c.consultas.consultar_categorias("RECEPCION")[0].cupo_disponible == 5
    assert c.consultas.consultar_reservacion("RECEPCION", "R1").estado == EstadoReservacion.SOLICITADA
