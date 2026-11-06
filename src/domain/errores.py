"""Errores del negocio. Cada familia se traduce a un código HTTP en la capa api."""


class ErrorDeDominio(Exception):
    """Base de todos los errores que producen las reglas del negocio."""


class DatoInvalidoError(ErrorDeDominio):
    """Un valor no es válido (cantidad, monto, texto vacío...)."""


class PermisoDenegadoError(ErrorDeDominio):
    """El rol no puede ejecutar la operación."""


class NoEncontradoError(ErrorDeDominio):
    """No existe el elemento solicitado."""


class ConflictoError(ErrorDeDominio):
    """La operación choca con el estado actual del negocio."""


class TransicionInvalidaError(ConflictoError):
    """El estado actual no permite la acción pedida."""


class SinCupoError(ConflictoError):
    """No hay cupo suficiente en la categoría de habitación."""


class HabitacionNoDisponibleError(ConflictoError):
    """La habitación no está disponible para entregarse."""


class CreditoExcedidoError(ConflictoError):
    """Los consumos superan el tope de crédito de la habitación (CAMBIO PIA: regla de la Act. 5)."""


class CuentaError(ConflictoError):
    """La cuenta de la estancia no permite la operación (cerrada o con saldo)."""


class PrecondicionNoCumplidaError(ErrorDeDominio):
    """Se entendió la solicitud, pero no cumple las condiciones del negocio."""


class ServicioExternoNoDisponibleError(ErrorDeDominio):
    """Un servicio externo (por ejemplo, la pasarela de garantías) no respondió."""
