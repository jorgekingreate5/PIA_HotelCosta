import pytest

from src.domain.errores import TransicionInvalidaError
from src.domain.maquina_estados import MAQUINA_HABITACION, MAQUINA_RESERVACION, MaquinaDeEstados
from src.domain.valor import EstadoHabitacion as H
from src.domain.valor import EstadoReservacion as R

VALIDAS_RESERVACION = [
    (R.SOLICITADA, "confirmar", R.CONFIRMADA), (R.SOLICITADA, "cancelar", R.CANCELADA),
    (R.CONFIRMADA, "cancelar", R.CANCELADA), (R.CONFIRMADA, "no_show", R.NO_SHOW),
    (R.CONFIRMADA, "check_in", R.CHECK_IN), (R.CHECK_IN, "check_out", R.CHECK_OUT),
    (R.CHECK_IN, "cambiar_habitacion", R.CHECK_IN)]


@pytest.mark.parametrize("estado,accion,esperado", VALIDAS_RESERVACION)
def test_transiciones_validas_de_la_reservacion(estado, accion, esperado):
    assert MAQUINA_RESERVACION.siguiente(estado, accion) == esperado


def test_toda_otra_combinacion_de_la_reservacion_se_rechaza():
    validas = {(e, a) for e, a, _ in VALIDAS_RESERVACION}
    acciones = {a for _, a, _ in VALIDAS_RESERVACION}
    rechazadas = 0
    for estado in R:
        for accion in acciones:
            if (estado, accion) not in validas:
                with pytest.raises(TransicionInvalidaError):
                    MAQUINA_RESERVACION.siguiente(estado, accion)
                rechazadas += 1
    assert rechazadas == len(R) * len(acciones) - len(validas)


@pytest.mark.parametrize("estado", [R.CHECK_OUT, R.CANCELADA, R.NO_SHOW])
def test_los_estados_finales_no_admiten_acciones(estado):
    assert MAQUINA_RESERVACION.acciones_permitidas(estado) == []


def test_no_se_puede_confirmar_dos_veces():
    estado = MAQUINA_RESERVACION.siguiente(R.SOLICITADA, "confirmar")
    with pytest.raises(TransicionInvalidaError, match="confirmar"):
        MAQUINA_RESERVACION.siguiente(estado, "confirmar")


def test_no_se_puede_saltar_de_solicitada_a_check_out():
    with pytest.raises(TransicionInvalidaError):
        MAQUINA_RESERVACION.siguiente(R.SOLICITADA, "check_out")


def test_acciones_permitidas_desde_confirmada():
    assert MAQUINA_RESERVACION.acciones_permitidas(R.CONFIRMADA) == [
        "cancelar", "check_in", "no_show"]


def test_ciclo_de_la_habitacion():
    estado = H.DISPONIBLE
    for accion in ("entregar", "enviar_a_limpieza", "marcar_disponible"):
        estado = MAQUINA_HABITACION.siguiente(estado, accion)
    assert estado == H.DISPONIBLE


def test_habitacion_ocupada_no_puede_salir_de_servicio():
    with pytest.raises(TransicionInvalidaError):
        MAQUINA_HABITACION.siguiente(H.OCUPADA, "fuera_de_servicio")


def test_maquina_personalizada():
    maquina = MaquinaDeEstados({(R.SOLICITADA, "confirmar"): R.CONFIRMADA})
    assert maquina.siguiente(R.SOLICITADA, "confirmar") == R.CONFIRMADA
