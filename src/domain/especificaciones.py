"""Specification: reglas de negocio pequeñas que se combinan con Y (&), O (|) y No (~)."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ContextoDeReservacion:
    """Lo que las especificaciones necesitan para evaluar una reservación."""

    reservacion: object
    huesped: object
    categorias: dict


class Especificacion:
    def es_satisfecha_por(self, contexto):
        raise NotImplementedError

    def __and__(self, otra):
        return Y(self, otra)

    def __or__(self, otra):
        return O(self, otra)

    def __invert__(self):
        return No(self)


class Y(Especificacion):
    def __init__(self, izquierda, derecha):
        self.izquierda, self.derecha = izquierda, derecha

    def es_satisfecha_por(self, contexto):
        return (self.izquierda.es_satisfecha_por(contexto)
                and self.derecha.es_satisfecha_por(contexto))


class O(Especificacion)#:
    def __init__(self, izquierda, derecha):
        self.izquierda, self.derecha = izquierda, derecha

    def es_satisfecha_por(self, contexto):
        return (self.izquierda.es_satisfecha_por(contexto)
                or self.derecha.es_satisfecha_por(contexto))


class No(Especificacion):
    def __init__(self, interna):
        self.interna = interna

    def es_satisfecha_por(self, contexto):
        return not self.interna.es_satisfecha_por(contexto)


class HuespedActivo(Especificacion):
    def es_satisfecha_por(self, contexto):
        return bool(contexto.huesped.activo)


class HuespedPreferente(Especificacion):
    def es_satisfecha_por(self, contexto):
        return bool(contexto.huesped.es_preferente)


class DetalleNoVacio(Especificacion):
    def es_satisfecha_por(self, contexto):
        return len(contexto.reservacion.lineas) > 0


class ReservacionAutorizada(Especificacion):
    def es_satisfecha_por(self, contexto):
        return bool(contexto.reservacion.autorizada)


class PromocionActiva(Especificacion):
    def es_satisfecha_por(self, contexto):
        return bool(contexto.reservacion.promocion_activa)


class TotalMinimo(Especificacion):
    def __init__(self, umbral):
        self.umbral = Decimal(umbral)

    def es_satisfecha_por(self, contexto):
        return contexto.reservacion.total >= self.umbral


class CategoriasHabilitadas(Especificacion):
    def es_satisfecha_por(self, contexto):
        for categoria_id in contexto.reservacion.cantidades_por_categoria():
            categoria = contexto.categorias.get(categoria_id)
            if categoria is None or not categoria.habilitada:
                return False
        return True


class CupoSuficiente(Especificacion):
    def es_satisfecha_por(self, contexto):
        for categoria_id, cantidad in contexto.reservacion.cantidades_por_categoria().items():
            categoria = contexto.categorias.get(categoria_id)
            if categoria is None or cantidad > categoria.cupo_disponible:
                return False
        return True


def puede_procesarse():
    """Huésped activo Y detalle no vacío Y reservación autorizada."""
    return HuespedActivo() & DetalleNoVacio() & ReservacionAutorizada()


def beneficio_preferente(umbral):
    """Huésped preferente Y total mínimo Y NO promoción activa."""
    return HuespedPreferente() & TotalMinimo(umbral) & ~PromocionActiva()


def requiere_revision():
    """NO huésped activo O NO autorizada: Reservaciones debe revisarla."""
    return ~HuespedActivo() | ~ReservacionAutorizada()


def puede_confirmarse():
    return puede_procesarse() & CategoriasHabilitadas() & CupoSuficiente()


_MOTIVOS = (
    (HuespedActivo(), "el huésped no está activo"),
    (DetalleNoVacio(), "la reservación no tiene detalle"),
    (ReservacionAutorizada(), "la reservación no está autorizada"),
    (CategoriasHabilitadas(), "hay categorías no habilitadas"),
)


def explicar_incumplimiento(contexto):
    """Lista en lenguaje del negocio qué condiciones básicas no se cumplen."""
    motivos = [texto for spec, texto in _MOTIVOS if not spec.es_satisfecha_por(contexto)]
    return "; ".join(motivos)
