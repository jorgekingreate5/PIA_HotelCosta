from decimal import Decimal

import pytest

from src.domain.categoria import CategoriaHabitacion
from src.domain.especificaciones import (
    CategoriasHabilitadas, ContextoDeReservacion, CupoSuficiente, DetalleNoVacio, HuespedActivo,
    HuespedPreferente, PromocionActiva, ReservacionAutorizada, TotalMinimo, beneficio_preferente,
    explicar_incumplimiento, puede_confirmarse, puede_procesarse, requiere_revision)
from src.domain.huesped import Huesped
from src.domain.reservacion import Reservacion
from src.domain.valor import LineaReservacion


def contexto(activo=True, preferente=False, autorizada=True, promocion=False,
             lineas=((("C1", 2, "1000")),), cupo=5, habilitada=True):
    huesped = Huesped("H1", "Ana", es_preferente=preferente, activo=activo)
    reservacion = Reservacion(
        "R1", "H1", [LineaReservacion(c, n, Decimal(t)) for c, n, t in lineas],
        autorizada=autorizada, promocion_activa=promocion)
    categorias = {"C1": CategoriaHabitacion("C1", "Estándar", Decimal("1000"), cupo, habilitada)}
    return ContextoDeReservacion(reservacion, huesped, categorias)


# ----- reglas simples
def test_huesped_activo_y_preferente():
    assert HuespedActivo().es_satisfecha_por(contexto())
    assert not HuespedActivo().es_satisfecha_por(contexto(activo=False))
    assert HuespedPreferente().es_satisfecha_por(contexto(preferente=True))
    assert not HuespedPreferente().es_satisfecha_por(contexto())


def test_detalle_autorizacion_y_promocion():
    assert DetalleNoVacio().es_satisfecha_por(contexto())
    assert not DetalleNoVacio().es_satisfecha_por(contexto(lineas=()))
    assert ReservacionAutorizada().es_satisfecha_por(contexto())
    assert not ReservacionAutorizada().es_satisfecha_por(contexto(autorizada=False))
    assert PromocionActiva().es_satisfecha_por(contexto(promocion=True))
    assert not PromocionActiva().es_satisfecha_por(contexto())


# ----- composición Y (AND): tabla de verdad de puede_procesarse
@pytest.mark.parametrize("activo,con_detalle,autorizada", [
    (True, True, True), (True, True, False), (True, False, True), (True, False, False),
    (False, True, True), (False, True, False), (False, False, True), (False, False, False)])
def test_puede_procesarse_exige_las_tres_condiciones(activo, con_detalle, autorizada):
    lineas = (("C1", 1, "1000"),) if con_detalle else ()
    ctx = contexto(activo=activo, autorizada=autorizada, lineas=lineas)
    assert puede_procesarse().es_satisfecha_por(ctx) == (activo and con_detalle and autorizada)


# ----- beneficio preferente: preferente Y total >= umbral Y NO promoción
def test_beneficio_con_total_exactamente_en_el_umbral():
    ctx = contexto(preferente=True, lineas=(("C1", 3, "500"),))  # total 1500.00
    assert beneficio_preferente(Decimal("1500")).es_satisfecha_por(ctx)


def test_beneficio_no_aplica_un_centavo_debajo_del_umbral():
    ctx = contexto(preferente=True, lineas=(("C1", 1, "1499.99"),))
    assert not beneficio_preferente(Decimal("1500")).es_satisfecha_por(ctx)


def test_beneficio_no_aplica_con_promocion_o_sin_preferencia():
    assert not beneficio_preferente(1500).es_satisfecha_por(contexto(preferente=True, promocion=True))
    assert not beneficio_preferente(1500).es_satisfecha_por(contexto(preferente=False))


# ----- composición O (OR) y No (NOT)
def test_o_basta_con_una_condicion():
    spec = HuespedPreferente() | TotalMinimo(5000)
    assert spec.es_satisfecha_por(contexto(preferente=True))
    assert not spec.es_satisfecha_por(contexto(preferente=False))
    assert spec.es_satisfecha_por(contexto(preferente=False, lineas=(("C1", 5, "1000"),)))


def test_no_invierte_y_la_doble_negacion_regresa_al_valor():
    ctx = contexto(activo=True)
    assert not (~HuespedActivo()).es_satisfecha_por(ctx)
    assert (~~HuespedActivo()).es_satisfecha_por(ctx)


def test_requiere_revision_si_no_esta_activo_o_no_esta_autorizada():
    assert not requiere_revision().es_satisfecha_por(contexto())
    assert requiere_revision().es_satisfecha_por(contexto(activo=False))
    assert requiere_revision().es_satisfecha_por(contexto(autorizada=False))


# ----- cupo y categorías
def test_cupo_suficiente_en_el_limite_y_uno_mas():
    assert CupoSuficiente().es_satisfecha_por(contexto(lineas=(("C1", 5, "1000"),), cupo=5))
    assert not CupoSuficiente().es_satisfecha_por(contexto(lineas=(("C1", 6, "1000"),), cupo=5))


def test_cupo_suma_las_lineas_de_la_misma_categoria():
    ctx = contexto(lineas=(("C1", 3, "1000"), ("C1", 3, "1000")), cupo=5)
    assert not CupoSuficiente().es_satisfecha_por(ctx)


def test_categoria_desconocida_o_deshabilitada():
    desconocida = contexto(lineas=(("C9", 1, "1000"),))
    assert not CupoSuficiente().es_satisfecha_por(desconocida)
    assert not CategoriasHabilitadas().es_satisfecha_por(desconocida)
    assert not CategoriasHabilitadas().es_satisfecha_por(contexto(habilitada=False))


def test_puede_confirmarse_combina_todo():
    assert puede_confirmarse().es_satisfecha_por(contexto())
    assert not puede_confirmarse().es_satisfecha_por(contexto(cupo=1))
    assert not puede_confirmarse().es_satisfecha_por(contexto(autorizada=False))


def test_explicar_incumplimiento_nombra_cada_motivo():
    texto = explicar_incumplimiento(contexto(activo=False, autorizada=False, lineas=()))
    assert "no está activo" in texto
    assert "no tiene detalle" in texto
    assert "no está autorizada" in texto
    assert explicar_incumplimiento(contexto()) == ""


def test_la_especificacion_base_no_se_puede_evaluar_sin_subclase():
    from src.domain.especificaciones import Especificacion
    with pytest.raises(NotImplementedError):
        Especificacion().es_satisfecha_por(contexto())
