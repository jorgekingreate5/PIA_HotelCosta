"""Traducción de errores del dominio a códigos HTTP (función pura, fácil de probar)."""
from ..domain.errores import (ConflictoError, DatoInvalidoError, ErrorDeDominio, NoEncontradoError,
                              PermisoDenegadoError, PrecondicionNoCumplidaError,
                              ServicioExternoNoDisponibleError)

CODIGOS = (
    (DatoInvalidoError, 400),
    (PermisoDenegadoError, 403),
    (NoEncontradoError, 404),
    (ConflictoError, 409),
    (PrecondicionNoCumplidaError, 422),
    (ServicioExternoNoDisponibleError, 503),
)


def codigo_http(error):
    for tipo, codigo in CODIGOS:
        if isinstance(error, tipo):
            return codigo
    return 500


def cuerpo_de_error(error):
    return {"error": type(error).__name__, "detalle": str(error)}


def es_error_de_dominio(error):
    return isinstance(error, ErrorDeDominio)
