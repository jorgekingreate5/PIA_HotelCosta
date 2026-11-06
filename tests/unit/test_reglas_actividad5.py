"""CAMBIO PIA: reglas del BRD/Actividad 5 integradas al proyecto final.

* Cancelación gratuita con >= 48 h; si no, cargo de 1 noche (excepción: Jefe/Administración).
* Tope de crédito de consumos de $3,000 MXN (pago parcial o autorización de Administración).
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.application.comandos import RegistrarCargo
from src.domain.cuenta_estancia import TOPE_CREDITO, CuentaEstancia
from src.domain.errores import ConflictoError, CreditoExcedidoError
from src.domain.eventos import ReservacionCancelada
from tests.helpers import contenedor_basico
from tests.unit.test_reservacion import AHORA, categorias, confirmada, reservacion
from tests.unit.test_servicios import ADM, REC, RES, en_estancia
from tests.unit.test_servicios import confirmada as confirmada_svc


# ----- cancelación 48 h
def test_cancelacion_con_48_horas_o_mas_es_gratuita():
    r, cats = confirmada()
    assert r.cancelar(cats, AHORA, AHORA + timedelta(hours=48)) == Decimal("0")


def test_cancelacion_con_menos_de_48_horas_cobra_una_noche():
    r, cats = confirmada()
    penalidad = r.cancelar(cats, AHORA, AHORA + timedelta(hours=47, minutes=59))
    assert penalidad == Decimal("1000")  # tarifa de la primera línea
    assert r.penalidad_cancelacion == Decimal("1000")
    evento = [e for e in r.sacar_eventos() if isinstance(e, ReservacionCancelada)][0]
    assert evento.penalidad == Decimal("1000")


def test_excepcion_de_jefe_o_administracion_exenta_la_penalidad():
    r, cats = confirmada()
    assert r.cancelar(cats, AHORA, AHORA + timedelta(hours=1), autorizacion_jefe=True) == 0


def test_solicitada_no_tiene_garantia_y_no_paga_penalidad():
    r, cats = reservacion(), categorias()
    assert r.cancelar(cats, AHORA, AHORA + timedelta(hours=1)) == Decimal("0")


def test_sin_fecha_de_llegada_no_hay_penalidad():
    r, cats = confirmada()
    assert r.cancelar(cats) == Decimal("0")


# ----- tope de crédito
def cuenta(hospedaje="5000"):
    return CuentaEstancia.abrir("C1", "R1", Decimal(hospedaje), datetime(2026, 10, 20))


def test_tope_es_3000():
    assert TOPE_CREDITO == Decimal("3000")


def test_consumos_hasta_el_tope_se_permiten_y_el_hospedaje_no_cuenta():
    c = cuenta("9000")
    c.registrar_cargo("Restaurante", Decimal("3000"), "E1", AHORA)
    assert c.credito_usado == Decimal("3000")


def test_consumo_que_supera_el_tope_se_rechaza():
    c = cuenta()
    c.registrar_cargo("Restaurante", Decimal("3000"), "E1", AHORA)
    with pytest.raises(CreditoExcedidoError):
        c.registrar_cargo("Minibar", Decimal("0.01"), "E1", AHORA)
    assert len(c.cargos) == 2  # hospedaje + restaurante; el rechazado no se guardó


def test_pago_parcial_libera_credito():
    c = cuenta()
    c.registrar_cargo("Restaurante", Decimal("3000"), "E1", AHORA)
    c.registrar_pago(Decimal("500"))
    c.registrar_cargo("Minibar", Decimal("500"), "E1", AHORA)
    with pytest.raises(CreditoExcedidoError):
        c.registrar_cargo("Minibar", Decimal("0.01"), "E1", AHORA)


def test_administracion_puede_autorizar_el_excedente():
    c = cuenta()
    c.registrar_cargo("Restaurante", Decimal("3000"), "E1", AHORA)
    c.registrar_cargo("Spa", Decimal("800"), "E1", AHORA, autorizacion_administracion=True)
    assert c.credito_usado == Decimal("3800")


def test_credito_excedido_es_un_conflicto_409():
    assert issubclass(CreditoExcedidoError, ConflictoError)


def test_servicio_aplica_tope_y_autorizacion():
    c = contenedor_basico()
    en_estancia(c)
    c.recepcion.registrar_cargo(REC, RegistrarCargo("R1", "Restaurante", Decimal("3000"), "E1"))
    with pytest.raises(CreditoExcedidoError):
        c.recepcion.registrar_cargo(REC, RegistrarCargo("R1", "Spa", Decimal("1"), "E1"))
    c.recepcion.registrar_cargo(
        REC, RegistrarCargo("R1", "Spa", Decimal("1"), "E1", autorizacion_administracion=True))
    assert c.consultas.cuenta_de_estancia(ADM, "R1").total == Decimal("5001")


def test_servicio_cancela_con_penalidad_tardia():
    c = contenedor_basico()
    confirmada_svc(c)
    r = c.reservaciones.cancelar_reservacion(RES, "R1", fecha_llegada=datetime(2026, 10, 20, 18))
    assert r.penalidad_cancelacion == Decimal("1000")
