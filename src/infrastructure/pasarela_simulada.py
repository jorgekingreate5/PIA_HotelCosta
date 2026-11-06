"""Pasarela de garantías simulada (sustituye a un servicio externo real en la demostración)."""
from ..application.puertos import PasarelaDeGarantia


class PasarelaDeGarantiaSimulada(PasarelaDeGarantia):
    """Aprueba toda garantía, salvo referencias que terminan en -RECHAZADA o -TIMEOUT."""

    def validar(self, garantia):
        if garantia.referencia.endswith("-TIMEOUT"):
            raise TimeoutError("La pasarela no respondió")
        return not garantia.referencia.endswith("-RECHAZADA")
