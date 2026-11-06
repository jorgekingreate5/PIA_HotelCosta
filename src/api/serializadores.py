"""Conversión de objetos del dominio a diccionarios JSON (los importes van como texto)."""
from decimal import Decimal

from ..domain.especificaciones import ContextoDeReservacion, requiere_revision


def dinero(valor):
    return f"{Decimal(valor):.2f}"


def reservacion_a_dict(reservacion):
    return {
        "id": reservacion.id,
        "huesped_id": reservacion.huesped_id,
        "referencia": reservacion.referencia,
        "fecha_solicitud": reservacion.fecha_solicitud.isoformat()
        if reservacion.fecha_solicitud else None,
        "estado": reservacion.estado.value,
        "autorizada": reservacion.autorizada,
        "promocion_activa": reservacion.promocion_activa,
        "beneficio_preferente": reservacion.beneficio_preferente,
        "total": dinero(reservacion.total),
        "penalidad_cancelacion": dinero(getattr(reservacion, "penalidad_cancelacion", 0)),
        "habitacion_id": reservacion.habitacion_id,
        "lineas": [{"categoria_id": x.categoria_id, "cantidad": x.cantidad,
                    "tarifa": dinero(x.tarifa), "subtotal": dinero(x.subtotal)}
                   for x in reservacion.lineas],
    }


def reservacion_con_revision(reservacion, huesped):
    datos = reservacion_a_dict(reservacion)
    contexto = ContextoDeReservacion(reservacion, huesped, {})
    datos["requiere_revision"] = requiere_revision().es_satisfecha_por(contexto)
    return datos


def categoria_a_dict(categoria):
    return {"id": categoria.id, "descripcion": categoria.descripcion,
            "tarifa": dinero(categoria.tarifa), "cupo_disponible": categoria.cupo_disponible,
            "habilitada": categoria.habilitada}


def habitacion_a_dict(habitacion):
    return {"id": habitacion.id, "numero": habitacion.numero,
            "categoria_id": habitacion.categoria_id, "estado": habitacion.estado.value}


def cuenta_a_dict(cuenta):
    return {"id": cuenta.id, "reservacion_id": cuenta.reservacion_id, "abierta": cuenta.abierta,
            "total": dinero(cuenta.total), "pagado": dinero(cuenta.pagado),
            "saldo": dinero(cuenta.saldo),
            "cargos": [{"fecha": c.fecha.isoformat(), "concepto": c.concepto,
                        "monto": dinero(c.monto), "empleado_id": c.empleado_id}
                       for c in cuenta.cargos]}


def cambio_a_dict(cambio):
    return {"fecha": cambio.fecha.isoformat(), "origen_id": cambio.origen_id,
            "destino_id": cambio.destino_id, "motivo": cambio.motivo,
            "responsable": cambio.responsable}


def evento_a_dict(evento):
    datos = {clave: (dinero(valor) if isinstance(valor, Decimal) else valor)
             for clave, valor in vars(evento).items()}
    return {"evento": type(evento).__name__, **datos}
