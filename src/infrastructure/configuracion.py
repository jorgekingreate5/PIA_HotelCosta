"""Configuración desde variables de entorno (12-Factor): nada de secretos en el código."""
import os
from dataclasses import dataclass
from decimal import Decimal


def normalizar_url_base_de_datos(url):
    """Render y otros proveedores entregan 'postgres://'; SQLAlchemy necesita el driver."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


@dataclass(frozen=True)
class Configuracion:
    database_url: str = "memory"
    umbral_beneficio_mxn: Decimal = Decimal("1500")
    cargar_datos_demo: bool = False
    ruta_datos: str = "datos"
    habitaciones_por_categoria: int = 6

    @classmethod
    def desde_entorno(cls, entorno=None):
        entorno = os.environ if entorno is None else entorno
        return cls(
            database_url=normalizar_url_base_de_datos(entorno.get("DATABASE_URL", "memory")),
            umbral_beneficio_mxn=Decimal(entorno.get("BENEFICIO_UMBRAL_MXN", "1500")),
            cargar_datos_demo=entorno.get("CARGAR_DATOS_DEMO", "0") in ("1", "true", "True"),
            ruta_datos=entorno.get("RUTA_DATOS", "datos"),
            habitaciones_por_categoria=int(entorno.get("HABITACIONES_POR_CATEGORIA", "6")),
        )
