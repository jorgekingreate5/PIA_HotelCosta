from datetime import date, datetime
from decimal import Decimal

import pytest

from src.api.manejo_errores import codigo_http, cuerpo_de_error, es_error_de_dominio
from src.api.serializadores import (cambio_a_dict, categoria_a_dict, cuenta_a_dict, dinero,
                                    evento_a_dict, habitacion_a_dict, reservacion_a_dict,
                                    reservacion_con_revision)
from src.domain.categoria import CategoriaHabitacion
from src.domain.errores import (CuentaError, DatoInvalidoError, HabitacionNoDisponibleError,
                                NoEncontradoError, PermisoDenegadoError,
                                PrecondicionNoCumplidaError, ServicioExternoNoDisponibleError,
                                SinCupoError, TransicionInvalidaError)
from src.domain.eventos import CargoRegistrado, ReservacionConfirmada
from src.domain.habitacion import Habitacion
from src.domain.huesped import Huesped
from src.domain.reservacion import CambioDeHabitacion, Reservacion
from src.domain.valor import LineaReservacion
from src.infrastructure.configuracion import Configuracion, normalizar_url_base_de_datos


@pytest.mark.parametrize("error,codigo", [
    (DatoInvalidoError("x"), 400), (PermisoDenegadoError("x"), 403), (NoEncontradoError("x"), 404),
    (TransicionInvalidaError("x"), 409), (SinCupoError("x"), 409),
    (HabitacionNoDisponibleError("x"), 409), (CuentaError("x"), 409),
    (PrecondicionNoCumplidaError("x"), 422), (ServicioExternoNoDisponibleError("x"), 503),
    (RuntimeError("x"), 500)])
def test_cada_error_tiene_su_codigo_http(error, codigo):
    assert codigo_http(error) == codigo


def test_cuerpo_de_error_y_clasificacion():
    assert cuerpo_de_error(SinCupoError("sin cupo")) == {"error": "SinCupoError",
                                                         "detalle": "sin cupo"}
    assert es_error_de_dominio(SinCupoError("x")) and not es_error_de_dominio(ValueError("x"))


def reservacion_demo():
    r = Reservacion("R1", "H1", [LineaReservacion("C1", 2, Decimal("428"))],
                    fecha_solicitud=date(2026, 10, 1), autorizada=True)
    return r


def test_importes_como_texto_con_dos_decimales():
    assert dinero(Decimal("856")) == "856.00" and dinero(0) == "0.00"


def test_serializar_reservacion_y_requiere_revision():
    datos = reservacion_a_dict(reservacion_demo())
    assert datos["total"] == "856.00" and datos["estado"] == "SOLICITADA"
    assert datos["lineas"][0]["subtotal"] == "856.00"
    assert datos["fecha_solicitud"] == "2026-10-01"
    activo = reservacion_con_revision(reservacion_demo(), Huesped("H1", "Ana", activo=True))
    inactivo = reservacion_con_revision(reservacion_demo(), Huesped("H1", "Ana", activo=False))
    assert activo["requiere_revision"] is False and inactivo["requiere_revision"] is True
    sin_fecha = reservacion_a_dict(Reservacion("R2", "H1", []))
    assert sin_fecha["fecha_solicitud"] is None


def test_serializar_catalogo_habitacion_cambio_y_evento():
    assert categoria_a_dict(CategoriaHabitacion("C1", "Suite", Decimal("570"), 19))["tarifa"] == "570.00"
    assert habitacion_a_dict(Habitacion("A", "101", "C1"))["estado"] == "DISPONIBLE"
    cambio = CambioDeHabitacion(datetime(2026, 10, 1, 9, 30), "A", "B", "Ruido", "E1")
    assert cambio_a_dict(cambio)["fecha"] == "2026-10-01T09:30:00"
    assert evento_a_dict(ReservacionConfirmada("R1")) == {"evento": "ReservacionConfirmada",
                                                          "reservacion_id": "R1"}
    assert evento_a_dict(CargoRegistrado("R1", "Minibar", Decimal("50")))["monto"] == "50.00"


def test_serializar_cuenta():
    from src.domain.cuenta_estancia import CuentaEstancia
    cuenta = CuentaEstancia.abrir("CTA-1", "R1", Decimal("100"), datetime(2026, 10, 1, 9, 0))
    datos = cuenta_a_dict(cuenta)
    assert datos["saldo"] == "100.00" and datos["cargos"][0]["concepto"] == "Hospedaje"


# ----- configuración
def test_configuracion_por_omision():
    c = Configuracion.desde_entorno({})
    assert c.database_url == "memory" and c.umbral_beneficio_mxn == Decimal("1500")
    assert c.cargar_datos_demo is False and c.habitaciones_por_categoria == 6


def test_configuracion_desde_variables_de_entorno():
    c = Configuracion.desde_entorno({
        "DATABASE_URL": "postgres://u:p@host/db", "BENEFICIO_UMBRAL_MXN": "2000",
        "CARGAR_DATOS_DEMO": "1", "RUTA_DATOS": "otra", "HABITACIONES_POR_CATEGORIA": "3"})
    assert c.database_url == "postgresql+psycopg://u:p@host/db"
    assert c.umbral_beneficio_mxn == Decimal("2000") and c.cargar_datos_demo
    assert c.ruta_datos == "otra" and c.habitaciones_por_categoria == 3


@pytest.mark.parametrize("entrada,salida", [
    ("postgres://u@h/d", "postgresql+psycopg://u@h/d"),
    ("postgresql://u@h/d", "postgresql+psycopg://u@h/d"),
    ("postgresql+psycopg://u@h/d", "postgresql+psycopg://u@h/d"),
    ("sqlite+pysqlite:///:memory:", "sqlite+pysqlite:///:memory:"), ("memory", "memory")])
def test_normalizar_url_de_base_de_datos(entrada, salida):
    assert normalizar_url_base_de_datos(entrada) == salida
