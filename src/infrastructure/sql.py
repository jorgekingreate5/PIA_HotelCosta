"""Persistencia con SQLAlchemy 2.x (PostgreSQL en Docker/Render, SQLite en pruebas)."""
from decimal import Decimal

from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String,
                        create_engine, delete, select)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ..application.puertos import UnidadDeTrabajo
from ..domain.categoria import CategoriaHabitacion
from ..domain.cuenta_estancia import Cargo, CuentaEstancia
from ..domain.errores import NoEncontradoError
from ..domain.habitacion import Habitacion
from ..domain.huesped import Huesped
from ..domain.repositorios import (RepositorioDeCategorias, RepositorioDeCuentas,
                                   RepositorioDeHabitaciones, RepositorioDeHuespedes,
                                   RepositorioDeReservaciones)
from ..domain.reservacion import CambioDeHabitacion, Reservacion
from ..domain.valor import EstadoHabitacion, EstadoReservacion, Garantia, LineaReservacion

DINERO = Numeric(12, 2)


class Base(DeclarativeBase):
    pass


class HuespedFila(Base):
    __tablename__ = "huespedes"
    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    es_preferente = Column(Boolean, nullable=False, default=False)
    activo = Column(Boolean, nullable=False, default=True)
    ciudad = Column(String, nullable=False, default="")


class CategoriaFila(Base):
    __tablename__ = "categorias"
    id = Column(String, primary_key=True)
    descripcion = Column(String, nullable=False)
    tarifa = Column(DINERO, nullable=False)
    cupo_disponible = Column(Integer, nullable=False)
    habilitada = Column(Boolean, nullable=False, default=True)


class HabitacionFila(Base):
    __tablename__ = "habitaciones"
    id = Column(String, primary_key=True)
    numero = Column(String, nullable=False, unique=True)
    categoria_id = Column(String, ForeignKey("categorias.id"), nullable=False)
    estado = Column(String, nullable=False)


class ReservacionFila(Base):
    __tablename__ = "reservaciones"
    id = Column(String, primary_key=True)
    huesped_id = Column(String, ForeignKey("huespedes.id"), nullable=False)
    referencia = Column(String, nullable=False, default="")
    fecha_solicitud = Column(Date, nullable=True)
    autorizada = Column(Boolean, nullable=False, default=False)
    promocion_activa = Column(Boolean, nullable=False, default=False)
    estado = Column(String, nullable=False)
    garantia_tipo = Column(String, nullable=True)
    garantia_referencia = Column(String, nullable=True)
    habitacion_id = Column(String, nullable=True)
    beneficio_preferente = Column(Boolean, nullable=False, default=False)


class LineaFila(Base):
    __tablename__ = "lineas_reservacion"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reservacion_id = Column(String, ForeignKey("reservaciones.id"), nullable=False)
    categoria_id = Column(String, ForeignKey("categorias.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    tarifa = Column(DINERO, nullable=False)


class CambioFila(Base):
    __tablename__ = "cambios_habitacion"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reservacion_id = Column(String, ForeignKey("reservaciones.id"), nullable=False)
    fecha = Column(DateTime, nullable=False)
    origen_id = Column(String, nullable=False)
    destino_id = Column(String, nullable=False)
    motivo = Column(String, nullable=False)
    responsable = Column(String, nullable=False)


class CuentaFila(Base):
    __tablename__ = "cuentas"
    id = Column(String, primary_key=True)
    reservacion_id = Column(String, ForeignKey("reservaciones.id"), nullable=False, unique=True)
    abierta = Column(Boolean, nullable=False, default=True)
    pagado = Column(DINERO, nullable=False, default=0)


class CargoFila(Base):
    __tablename__ = "cargos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cuenta_id = Column(String, ForeignKey("cuentas.id"), nullable=False)
    fecha = Column(DateTime, nullable=False)
    concepto = Column(String, nullable=False)
    monto = Column(DINERO, nullable=False)
    empleado_id = Column(String, nullable=False)


def _no_encontrado(nombre, clave):
    return NoEncontradoError(f"No existe {nombre} '{clave}'")


class RepositorioDeHuespedesSql(RepositorioDeHuespedes):
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener(self, huesped_id):
        fila = self.sesion.get(HuespedFila, huesped_id)
        if fila is None:
            raise _no_encontrado("el huésped", huesped_id)
        return Huesped(fila.id, fila.nombre, fila.es_preferente, fila.activo, fila.ciudad)

    def guardar(self, huesped):
        self.sesion.merge(HuespedFila(id=huesped.id, nombre=huesped.nombre,
                                      es_preferente=huesped.es_preferente, activo=huesped.activo,
                                      ciudad=huesped.ciudad))


class RepositorioDeCategoriasSql(RepositorioDeCategorias):
    def __init__(self, sesion: Session):
        self.sesion = sesion

    @staticmethod
    def _a_dominio(fila):
        return CategoriaHabitacion(fila.id, fila.descripcion, Decimal(fila.tarifa),
                                   fila.cupo_disponible, fila.habilitada)

    def obtener(self, categoria_id):
        fila = self.sesion.get(CategoriaFila, categoria_id)
        if fila is None:
            raise _no_encontrado("la categoría", categoria_id)
        return self._a_dominio(fila)

    def guardar(self, categoria):
        self.sesion.merge(CategoriaFila(id=categoria.id, descripcion=categoria.descripcion,
                                        tarifa=categoria.tarifa,
                                        cupo_disponible=categoria.cupo_disponible,
                                        habilitada=categoria.habilitada))

    def listar(self):
        filas = self.sesion.scalars(select(CategoriaFila).order_by(CategoriaFila.id))
        return [self._a_dominio(fila) for fila in filas]


class RepositorioDeHabitacionesSql(RepositorioDeHabitaciones):
    def __init__(self, sesion: Session):
        self.sesion = sesion

    @staticmethod
    def _a_dominio(fila):
        return Habitacion(fila.id, fila.numero, fila.categoria_id, EstadoHabitacion(fila.estado))

    def obtener(self, habitacion_id):
        fila = self.sesion.get(HabitacionFila, habitacion_id)
        if fila is None:
            raise _no_encontrado("la habitación", habitacion_id)
        return self._a_dominio(fila)

    def guardar(self, habitacion):
        self.sesion.merge(HabitacionFila(id=habitacion.id, numero=habitacion.numero,
                                         categoria_id=habitacion.categoria_id,
                                         estado=habitacion.estado.value))

    def listar(self):
        filas = self.sesion.scalars(select(HabitacionFila).order_by(HabitacionFila.numero))
        return [self._a_dominio(fila) for fila in filas]


class RepositorioDeReservacionesSql(RepositorioDeReservaciones):
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def _a_dominio(self, fila):
        lineas = self.sesion.scalars(
            select(LineaFila).where(LineaFila.reservacion_id == fila.id).order_by(LineaFila.id))
        reservacion = Reservacion(
            fila.id, fila.huesped_id,
            [LineaReservacion(x.categoria_id, x.cantidad, Decimal(x.tarifa)) for x in lineas],
            referencia=fila.referencia, fecha_solicitud=fila.fecha_solicitud,
            autorizada=fila.autorizada, promocion_activa=fila.promocion_activa,
            estado=EstadoReservacion(fila.estado))
        if fila.garantia_tipo:
            reservacion.garantia = Garantia(fila.garantia_tipo, fila.garantia_referencia)
        reservacion.habitacion_id = fila.habitacion_id
        reservacion.beneficio_preferente = fila.beneficio_preferente
        cambios = self.sesion.scalars(
            select(CambioFila).where(CambioFila.reservacion_id == fila.id).order_by(CambioFila.id))
        reservacion.cambios = [CambioDeHabitacion(c.fecha, c.origen_id, c.destino_id, c.motivo,
                                                  c.responsable) for c in cambios]
        return reservacion

    def obtener(self, reservacion_id):
        fila = self.sesion.get(ReservacionFila, reservacion_id)
        if fila is None:
            raise _no_encontrado("la reservación", reservacion_id)
        return self._a_dominio(fila)

    def guardar(self, reservacion):
        garantia = reservacion.garantia
        self.sesion.merge(ReservacionFila(
            id=reservacion.id, huesped_id=reservacion.huesped_id,
            referencia=reservacion.referencia, fecha_solicitud=reservacion.fecha_solicitud,
            autorizada=reservacion.autorizada, promocion_activa=reservacion.promocion_activa,
            estado=reservacion.estado.value,
            garantia_tipo=garantia.tipo if garantia else None,
            garantia_referencia=garantia.referencia if garantia else None,
            habitacion_id=reservacion.habitacion_id,
            beneficio_preferente=reservacion.beneficio_preferente))
        self.sesion.flush()
        self.sesion.execute(delete(LineaFila).where(LineaFila.reservacion_id == reservacion.id))
        self.sesion.execute(delete(CambioFila).where(CambioFila.reservacion_id == reservacion.id))
        for linea in reservacion.lineas:
            self.sesion.add(LineaFila(reservacion_id=reservacion.id,
                                      categoria_id=linea.categoria_id, cantidad=linea.cantidad,
                                      tarifa=linea.tarifa))
        for cambio in reservacion.cambios:
            self.sesion.add(CambioFila(reservacion_id=reservacion.id, fecha=cambio.fecha,
                                       origen_id=cambio.origen_id, destino_id=cambio.destino_id,
                                       motivo=cambio.motivo, responsable=cambio.responsable))

    def listar(self):
        filas = self.sesion.scalars(select(ReservacionFila).order_by(ReservacionFila.id))
        return [self._a_dominio(fila) for fila in filas]


class RepositorioDeCuentasSql(RepositorioDeCuentas):
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener_por_reservacion(self, reservacion_id):
        fila = self.sesion.scalar(
            select(CuentaFila).where(CuentaFila.reservacion_id == reservacion_id))
        if fila is None:
            raise _no_encontrado("la cuenta de la reservación", reservacion_id)
        cuenta = CuentaEstancia(fila.id, fila.reservacion_id)
        cuenta.abierta = fila.abierta
        cuenta.pagado = Decimal(fila.pagado)
        cargos = self.sesion.scalars(
            select(CargoFila).where(CargoFila.cuenta_id == fila.id).order_by(CargoFila.id))
        cuenta.cargos = [Cargo(c.fecha, c.concepto, Decimal(c.monto), c.empleado_id)
                         for c in cargos]
        return cuenta

    def guardar(self, cuenta):
        self.sesion.merge(CuentaFila(id=cuenta.id, reservacion_id=cuenta.reservacion_id,
                                     abierta=cuenta.abierta, pagado=cuenta.pagado))
        self.sesion.flush()
        self.sesion.execute(delete(CargoFila).where(CargoFila.cuenta_id == cuenta.id))
        for cargo in cuenta.cargos:
            self.sesion.add(CargoFila(cuenta_id=cuenta.id, fecha=cargo.fecha,
                                      concepto=cargo.concepto, monto=cargo.monto,
                                      empleado_id=cargo.empleado_id))


class UnidadDeTrabajoSql(UnidadDeTrabajo):
    def __init__(self, fabrica_de_sesiones):
        self._fabrica = fabrica_de_sesiones
        self._sesion = None
        self._confirmado = False

    def __enter__(self):
        self._sesion = self._fabrica()
        self._confirmado = False
        self.huespedes = RepositorioDeHuespedesSql(self._sesion)
        self.categorias = RepositorioDeCategoriasSql(self._sesion)
        self.habitaciones = RepositorioDeHabitacionesSql(self._sesion)
        self.reservaciones = RepositorioDeReservacionesSql(self._sesion)
        self.cuentas = RepositorioDeCuentasSql(self._sesion)
        return self

    def guardar_cambios(self):
        self._sesion.commit()
        self._confirmado = True

    def __exit__(self, tipo, valor, traza):
        if not self._confirmado:
            self._sesion.rollback()
        self._sesion.close()
        return False


def crear_motor(url="sqlite+pysqlite:///:memory:"):
    if url.startswith("sqlite") and ":memory:" in url:
        motor = create_engine(url, connect_args={"check_same_thread": False},
                              poolclass=StaticPool)
    else:
        motor = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(motor)
    return motor


def crear_fabrica(motor):
    return sessionmaker(bind=motor, expire_on_commit=False)
