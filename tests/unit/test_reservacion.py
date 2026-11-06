from datetime import datetime
from decimal import Decimal

import pytest

from src.domain.categoria import CategoriaHabitacion
from src.domain.errores import (ConflictoError, DatoInvalidoError, PrecondicionNoCumplidaError,
                                SinCupoError, TransicionInvalidaError)
from src.domain.eventos import (BeneficioPreferenteOtorgado, ReservacionConfirmada,
                                ReservacionSolicitada)
from src.domain.habitacion import Habitacion
from src.domain.huesped import Huesped
from src.domain.reservacion import Reservacion
from src.domain.valor import EstadoHabitacion, EstadoReservacion, Garantia, LineaReservacion

AHORA = datetime(2026, 10, 20, 12, 0)
UMBRAL = Decimal("1500")
GARANTIA = Garantia("tarjeta", "TC-0001")


def reservacion(lineas=(("C1", 2),), autorizada=True, promocion=False):
    return Reservacion.solicitar(
        "R1", "H1", [LineaReservacion(c, n, Decimal("1000")) for c, n in lineas],
        autorizada=autorizada, promocion_activa=promocion)


def huesped(activo=True, preferente=False):
    return Huesped("H1", "Ana", es_preferente=preferente, activo=activo)


def categorias(cupo=5, habilitada=True):
    return {"C1": CategoriaHabitacion("C1", "Estándar", Decimal("1000"), cupo, habilitada)}


def confirmada(**kwargs):
    r = reservacion(**kwargs)
    cats = categorias()
    r.confirmar(huesped(), cats, UMBRAL)
    return r, cats


def en_estancia():
    r, cats = confirmada()
    h = Habitacion("A", "101", "C1")
    r.registrar_check_in(h, True, GARANTIA)
    return r, cats, h


# ----- solicitud y total
def test_solicitar_registra_evento_y_calcula_total():
    r = reservacion()
    assert r.estado == EstadoReservacion.SOLICITADA
    assert r.total == Decimal("2000")
    assert [type(e) for e in r.sacar_eventos()] == [ReservacionSolicitada]


def test_reservacion_sin_lineas_tiene_total_cero():
    assert reservacion(lineas=()).total == 0


# ----- confirmar
def test_confirmar_descuenta_cupo_y_cambia_estado():
    r, cats = confirmada()
    assert r.estado == EstadoReservacion.CONFIRMADA
    assert cats["C1"].cupo_disponible == 3


def test_confirmar_dos_veces_es_una_transicion_invalida_y_no_toca_el_cupo():
    r, cats = confirmada()
    with pytest.raises(TransicionInvalidaError):
        r.confirmar(huesped(), cats, UMBRAL)
    assert cats["C1"].cupo_disponible == 3


@pytest.mark.parametrize("kwargs", [{"autorizada": False}, {"lineas": ()}])
def test_confirmar_sin_autorizacion_o_sin_detalle_se_rechaza(kwargs):
    r = reservacion(**kwargs)
    with pytest.raises(PrecondicionNoCumplidaError):
        r.confirmar(huesped(), categorias(), UMBRAL)
    assert r.estado == EstadoReservacion.SOLICITADA


def test_confirmar_con_huesped_inactivo_se_rechaza():
    with pytest.raises(PrecondicionNoCumplidaError, match="no está activo"):
        reservacion().confirmar(huesped(activo=False), categorias(), UMBRAL)


def test_confirmar_con_categoria_deshabilitada_se_rechaza():
    with pytest.raises(PrecondicionNoCumplidaError, match="no habilitadas"):
        reservacion().confirmar(huesped(), categorias(habilitada=False), UMBRAL)


def test_confirmar_sin_cupo_suficiente_es_un_conflicto():
    cats = categorias(cupo=1)
    with pytest.raises(SinCupoError):
        reservacion().confirmar(huesped(), cats, UMBRAL)
    assert cats["C1"].cupo_disponible == 1


def test_confirmar_otorga_beneficio_preferente_en_el_umbral():
    r = reservacion(lineas=(("C1", 2),))  # total 2000
    r.confirmar(huesped(preferente=True), categorias(), UMBRAL)
    assert r.beneficio_preferente
    assert BeneficioPreferenteOtorgado in [type(e) for e in r.sacar_eventos()]


def test_confirmar_no_otorga_beneficio_con_promocion_o_total_menor():
    r = reservacion(promocion=True)
    r.confirmar(huesped(preferente=True), categorias(), UMBRAL)
    assert not r.beneficio_preferente
    chica = reservacion(lineas=(("C1", 1),))  # total 1000 < 1500
    chica.confirmar(huesped(preferente=True), categorias(), UMBRAL)
    assert not chica.beneficio_preferente


def test_autorizar_una_reservacion_solicitada():
    r = reservacion(autorizada=False)
    r.autorizar()
    r.autorizar()  # repetir no genera otro evento
    assert r.autorizada
    assert len([e for e in r.sacar_eventos() if "Autorizada" in type(e).__name__]) == 1


def test_no_se_autoriza_una_reservacion_ya_confirmada():
    r, _ = confirmada()
    with pytest.raises(ConflictoError):
        r.autorizar()


# ----- cancelar y no-show
def test_cancelar_confirmada_libera_el_cupo():
    r, cats = confirmada()
    r.cancelar(cats)
    assert r.estado == EstadoReservacion.CANCELADA
    assert cats["C1"].cupo_disponible == 5


def test_cancelar_solicitada_no_toca_el_cupo():
    r, cats = reservacion(), categorias()
    r.cancelar(cats)
    assert r.estado == EstadoReservacion.CANCELADA
    assert cats["C1"].cupo_disponible == 5


def test_no_se_cancela_una_reservacion_en_estancia():
    r, cats, _ = en_estancia()
    with pytest.raises(TransicionInvalidaError):
        r.cancelar(cats)


def test_no_show_libera_el_cupo_y_solo_aplica_a_confirmadas():
    r, cats = confirmada()
    r.registrar_no_show(cats)
    assert r.estado == EstadoReservacion.NO_SHOW and cats["C1"].cupo_disponible == 5
    with pytest.raises(TransicionInvalidaError):
        reservacion().registrar_no_show(categorias())


# ----- check-in
def test_check_in_entrega_la_habitacion():
    r, _, h = en_estancia()
    assert r.estado == EstadoReservacion.CHECK_IN
    assert r.habitacion_id == "A" and h.estado == EstadoHabitacion.OCUPADA
    assert r.garantia == GARANTIA


def test_check_in_sin_identidad_o_sin_garantia_no_ocupa_la_habitacion():
    for identidad, garantia in ((False, GARANTIA), (True, None)):
        r, _ = confirmada()
        h = Habitacion("A", "101", "C1")
        with pytest.raises(PrecondicionNoCumplidaError):
            r.registrar_check_in(h, identidad, garantia)
        assert h.estado == EstadoHabitacion.DISPONIBLE
        assert r.estado == EstadoReservacion.CONFIRMADA


def test_check_in_desde_solicitada_es_una_transicion_invalida():
    with pytest.raises(TransicionInvalidaError):
        reservacion().registrar_check_in(Habitacion("A", "101", "C1"), True, GARANTIA)


def test_check_in_en_habitacion_de_otra_categoria_se_rechaza():
    r, _ = confirmada()
    with pytest.raises(ConflictoError, match="categoría"):
        r.registrar_check_in(Habitacion("B", "201", "C2"), True, GARANTIA)


# ----- cambio de habitación
def test_cambio_de_habitacion_deja_historial_y_manda_la_anterior_a_limpieza():
    r, _, actual = en_estancia()
    nueva = Habitacion("B", "102", "C1")
    r.cambiar_habitacion(actual, nueva, "Ruido", "recepcion-1", AHORA)
    assert r.habitacion_id == "B" and nueva.estado == EstadoHabitacion.OCUPADA
    assert actual.estado == EstadoHabitacion.PENDIENTE_DE_LIMPIEZA
    assert (r.cambios[0].origen_id, r.cambios[0].destino_id) == ("A", "B")


def test_cambio_a_habitacion_no_disponible_no_deja_rastro():
    r, _, actual = en_estancia()
    nueva = Habitacion("B", "102", "C1", EstadoHabitacion.FUERA_DE_SERVICIO)
    with pytest.raises(ConflictoError):
        r.cambiar_habitacion(actual, nueva, "Ruido", "recepcion-1", AHORA)
    assert r.cambios == [] and r.habitacion_id == "A"
    assert actual.estado == EstadoHabitacion.OCUPADA


def test_cambio_a_la_misma_habitacion_o_fuera_de_estancia_se_rechaza():
    r, _, actual = en_estancia()
    with pytest.raises(DatoInvalidoError):
        r.cambiar_habitacion(actual, actual, "x", "y", AHORA)
    with pytest.raises(ConflictoError):
        r.cambiar_habitacion(Habitacion("Z", "999", "C1"), Habitacion("B", "102", "C1"),
                             "x", "y", AHORA)
    with pytest.raises(TransicionInvalidaError):
        reservacion().cambiar_habitacion(actual, Habitacion("B", "102", "C1"), "x", "y", AHORA)


# ----- check-out
def test_check_out_libera_la_habitacion_a_limpieza():
    r, _, h = en_estancia()
    r.registrar_check_out(h)
    assert r.estado == EstadoReservacion.CHECK_OUT
    assert h.estado == EstadoHabitacion.PENDIENTE_DE_LIMPIEZA


def test_check_out_desde_confirmada_es_una_transicion_invalida():
    r, _ = confirmada()
    with pytest.raises(TransicionInvalidaError):
        r.registrar_check_out(Habitacion("A", "101", "C1"))


def test_check_out_con_otra_habitacion_se_rechaza():
    r, _, _ = en_estancia()
    with pytest.raises(ConflictoError):
        r.registrar_check_out(Habitacion("B", "102", "C1", EstadoHabitacion.OCUPADA))


def test_eventos_de_la_confirmacion():
    r = reservacion()
    r.sacar_eventos()
    r.confirmar(huesped(), categorias(), UMBRAL)
    assert ReservacionConfirmada in [type(e) for e in r.sacar_eventos()]
