"""Gestor central: mantiene las listas internas (sin base de datos) y registra
en el log cada error ocurrido."""
import functools
import logging

from excepciones import (
    ClienteInvalidoError,
    ErrorSoftwareFJ,
    ParametroFaltanteError,
    ReservaInvalidaError,
    ServicioInvalidoError,
)
from modelos import Asesoria, AlquilerEquipo, Cliente, Reserva, ReservaSala

log = logging.getLogger("software_fj")


def registrar_errores(func):
    """Decorador: escribe en el log cualquier ErrorSoftwareFJ y lo vuelve a lanzar."""
    @functools.wraps(func)
    def envoltura(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ErrorSoftwareFJ as e:
            causa = f" | causa: {e.__cause__!r}" if e.__cause__ else ""
            log.error("%s -> %s: %s%s", func.__name__, type(e).__name__, e, causa)
            raise
    return envoltura


class GestorFJ:
    TIPOS_SERVICIO = {"sala": ReservaSala, "equipo": AlquilerEquipo, "asesoria": Asesoria}

    def __init__(self):
        self.clientes: list[Cliente] = []
        self.servicios: list = []
        self.reservas: list[Reserva] = []

    # búsquedas
    @staticmethod
    def _buscar(lista, id_, error, nombre):
        for item in lista:
            if item.id == id_:
                return item
        raise error(f"{nombre} '{id_}' no existe.")

    def buscar_cliente(self, id_):
        return self._buscar(self.clientes, id_, ClienteInvalidoError, "Cliente")

    def buscar_servicio(self, id_):
        return self._buscar(self.servicios, id_, ServicioInvalidoError, "Servicio")

    def buscar_reserva(self, id_):
        return self._buscar(self.reservas, id_, ReservaInvalidaError, "Reserva")

    #  clientes 
    @registrar_errores
    def registrar_cliente(self, nombre, documento, email, telefono) -> Cliente:
        cliente = Cliente(nombre, documento, email, telefono)
        if any(c.documento == cliente.documento for c in self.clientes):
            raise ClienteInvalidoError(f"Ya existe un cliente con documento {cliente.documento}.")
        self.clientes.append(cliente)
        log.info("Cliente registrado: %s", cliente.describir())
        return cliente

    #  servicios 
    @registrar_errores
    def crear_servicio(self, tipo, **datos):
        clase = self.TIPOS_SERVICIO.get(str(tipo).strip().lower())
        if clase is None:
            raise ServicioInvalidoError(f"Tipo de servicio desconocido: '{tipo}'.")
        try:
            servicio = clase(**datos)
        except TypeError as e:
            raise ParametroFaltanteError(f"Parámetros faltantes o inesperados: {e}") from e
        self.servicios.append(servicio)
        log.info("Servicio creado: %s", servicio.describir())
        return servicio

    @registrar_errores
    def cambiar_disponibilidad(self, id_servicio, disponible: bool):
        servicio = self.buscar_servicio(id_servicio)
        servicio.disponible = disponible
        log.info("Servicio %s disponible=%s", id_servicio, disponible)
        return servicio

    # reservas
    @registrar_errores
    def crear_reserva(self, id_cliente, id_servicio, horas) -> Reserva:
        reserva = Reserva(self.buscar_cliente(id_cliente), self.buscar_servicio(id_servicio), horas)
        self.reservas.append(reserva)
        log.info("Reserva creada: %s", reserva.describir())
        return reserva

    @registrar_errores
    def confirmar_reserva(self, id_reserva):
        reserva = self.buscar_reserva(id_reserva)
        reserva.confirmar()
        return reserva

    @registrar_errores
    def cancelar_reserva(self, id_reserva):
        reserva = self.buscar_reserva(id_reserva)
        reserva.cancelar()
        return reserva

    @registrar_errores
    def procesar_reserva(self, id_reserva, impuesto=0.19, descuento=0.0) -> float:
        return self.buscar_reserva(id_reserva).procesar(impuesto, descuento)
