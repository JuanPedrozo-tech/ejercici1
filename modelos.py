"""Modelo de dominio de Software FJ (POO: abstracción, herencia, polimorfismo,
encapsulación y manejo avanzado de excepciones)."""
import logging
import math
import re
from abc import ABC, abstractmethod
from enum import Enum

from excepciones import (
    CalculoInconsistenteError,
    ClienteInvalidoError,
    OperacionNoPermitidaError,
    ReservaInvalidaError,
    ServicioInvalidoError,
    ServicioNoDisponibleError,
    ErrorSoftwareFJ,
)

log = logging.getLogger("software_fj")
IVA = 0.19

#se utilizo el iva actual de colombia

# Clase abstracta general

class EntidadBase(ABC):
    """Entidad general del sistema: todas tienen un id único y se describen."""

    _PREFIJO = "ENT"
    _secuencias: dict = {}

    def __init__(self):
        # Se llama al final de cada constructor, de esta forma un objeto inválido no consume id.
        n = EntidadBase._secuencias.get(self._PREFIJO, 0) + 1
        EntidadBase._secuencias[self._PREFIJO] = n
        self._id = f"{self._PREFIJO}-{n:03d}"

    @property
    def id(self) -> str:
        return self._id

    @abstractmethod
    def describir(self) -> str:
        """Descripción de la entidad."""

    def __str__(self) -> str:
        return self.describir()


# Cliente (encapsulación + validaciones)

class Cliente(EntidadBase):
    _PREFIJO = "CLI"

    def __init__(self, nombre, documento, email, telefono):
        self.__nombre = self._validar_nombre(nombre)
        self.__documento = self._validar_documento(documento)
        self.__email = self._validar_email(email)
        self.__telefono = self._validar_telefono(telefono)
        super().__init__()

    #  validaciones de métodos estáticos reutilizados por los setters
    @staticmethod
    def _texto(valor, campo):
        valor = str(valor if valor is not None else "").strip()
        if not valor:
            raise ClienteInvalidoError(f"El campo '{campo}' es obligatorio.")
        return valor

    @staticmethod
    def _validar_nombre(valor):
        valor = Cliente._texto(valor, "nombre")
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]{3,60}", valor):
            raise ClienteInvalidoError("El nombre debe tener 3-60 letras (sin números ni símbolos).")
        return valor.title()

    @staticmethod
    def _validar_documento(valor):
        valor = Cliente._texto(valor, "documento")
        if not re.fullmatch(r"\d{5,12}", valor):
            raise ClienteInvalidoError("El documento debe tener entre 5 y 12 dígitos.")
        return valor

    @staticmethod
    def _validar_email(valor):
        valor = Cliente._texto(valor, "email")
        if not re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", valor):
            raise ClienteInvalidoError(f"Email con formato inválido: '{valor}'.")
        return valor.lower()

    @staticmethod
    def _validar_telefono(valor):
        valor = Cliente._texto(valor, "teléfono")
        if not re.fullmatch(r"\d{7,10}", valor):
            raise ClienteInvalidoError("El teléfono debe tener entre 7 y 10 dígitos.")
        return valor

    # propiedades de acceso controlado a los datos personales
    @property
    def nombre(self): return self.__nombre

    @nombre.setter
    def nombre(self, v): self.__nombre = self._validar_nombre(v)

    @property
    def documento(self): return self.__documento

    @property
    def email(self): return self.__email

    @email.setter
    def email(self, v): self.__email = self._validar_email(v)

    @property
    def telefono(self): return self.__telefono

    @telefono.setter
    def telefono(self, v): self.__telefono = self._validar_telefono(v)

    def describir(self) -> str:
        return f"{self.id} - {self.nombre} (CC {self.documento}, {self.email}, {self.telefono})"



# Servicio abstracto + 3 servicios especializados

class Servicio(EntidadBase, ABC):
    _PREFIJO = "SRV"
    TIPO = "Servicio"

    def __init__(self, nombre, tarifa_hora):
        nombre = str(nombre if nombre is not None else "").strip()
        if len(nombre) < 3:
            raise ServicioInvalidoError("El nombre del servicio debe tener al menos 3 caracteres.")
        try:
            tarifa = float(tarifa_hora)
        except (TypeError, ValueError) as e:
            raise ServicioInvalidoError("La tarifa por hora debe ser numérica.") from e
        if not math.isfinite(tarifa) or tarifa <= 0:
            raise ServicioInvalidoError("La tarifa por hora debe ser mayor que cero.")
        self._nombre = nombre
        self._tarifa_hora = tarifa
        self._disponible = True
        super().__init__()

    @property
    def nombre(self): return self._nombre

    @property
    def tarifa_hora(self): return self._tarifa_hora

    @property
    def disponible(self): return self._disponible

    @disponible.setter
    def disponible(self, valor):
        if not isinstance(valor, bool):
            raise ServicioInvalidoError("La disponibilidad debe ser True o False.")
        self._disponible = valor

    # métodos abstractos: cada servicio los sobrescribe (polimorfismo) 
    @abstractmethod
    def validar_parametros(self, horas) -> float:
        """Valida la duración solicitada y la devuelve como float."""
        try:
            h = float(horas)
        except (TypeError, ValueError) as e:
            raise ServicioInvalidoError("La duración debe ser numérica.") from e
        if not math.isfinite(h) or h <= 0:
            raise ServicioInvalidoError("La duración debe ser mayor que cero.")
        return h

    @abstractmethod
    def calcular_costo_base(self, horas: float) -> float:
        """Costo sin impuestos ni descuentos."""

    # "sobrecarga" con parámetros opcionales (Python no tiene overloading nativo) 
    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0) -> float:
        """Variantes: calcular_costo(h) | calcular_costo(h, iva) | calcular_costo(h, iva, desc)."""
        h = self.validar_parametros(horas)
        try:
            imp, desc = float(impuesto), float(descuento)
        except (TypeError, ValueError) as e:
            raise CalculoInconsistenteError("Impuesto y descuento deben ser numéricos.") from e
        if not 0 <= imp <= 1:
            raise CalculoInconsistenteError(f"Impuesto fuera de rango (0-1): {imp}")
        if not 0 <= desc < 1:
            raise CalculoInconsistenteError(f"Descuento fuera de rango (0-1): {desc}")
        total = self.calcular_costo_base(h) * (1 - desc) * (1 + imp)
        if not math.isfinite(total) or total < 0:
            raise CalculoInconsistenteError(f"Resultado inconsistente: {total}")
        return round(total, 2)

    def calcular_costo_con_iva(self, horas) -> float:
        """Variante: costo con IVA del 19 %."""
        return self.calcular_costo(horas, impuesto=IVA)

    def __str__(self) -> str:
        return self.describir()


class ReservaSala(Servicio):
    TIPO = "Sala"

    def __init__(self, nombre, tarifa_hora, capacidad):
        try:
            cap = int(capacidad)
        except (TypeError, ValueError) as e:
            raise ServicioInvalidoError("La capacidad debe ser un entero.") from e
        if cap <= 0:
            raise ServicioInvalidoError("La capacidad debe ser mayor que cero.")
        self._capacidad = cap
        super().__init__(nombre, tarifa_hora)

    def validar_parametros(self, horas) -> float:
        h = super().validar_parametros(horas)
        if h > 12:
            raise ServicioInvalidoError("Una sala no se puede reservar más de 12 horas.")
        return h

    def calcular_costo_base(self, horas):
        costo = horas * self._tarifa_hora
        return costo * 0.90 if horas >= 4 else costo  # 10 % por bloques de 4 h o más

    def describir(self):
        return f"{self.id} - Sala '{self.nombre}' (cap. {self._capacidad}) ${self.tarifa_hora:,.0f}/h"


class AlquilerEquipo(Servicio):
    TIPO = "Equipo"

    def __init__(self, nombre, tarifa_hora, deposito):
        try:
            dep = float(deposito)
        except (TypeError, ValueError) as e:
            raise ServicioInvalidoError("El depósito debe ser numérico.") from e
        if dep < 0:
            raise ServicioInvalidoError("El depósito no puede ser negativo.")
        self._deposito = dep
        super().__init__(nombre, tarifa_hora)

    def validar_parametros(self, horas) -> float:
        h = super().validar_parametros(horas)
        if h > 72:
            raise ServicioInvalidoError("Un equipo no se puede alquilar más de 72 horas.")
        return h

    def calcular_costo_base(self, horas):
        return horas * self._tarifa_hora + self._deposito  # el depósito se cobra una vez

    def describir(self):
        return (f"{self.id} - Equipo '{self.nombre}' ${self.tarifa_hora:,.0f}/h "
                f"+ depósito ${self._deposito:,.0f}")


class Asesoria(Servicio):
    TIPO = "Asesoría"
    NIVELES = {"junior": 1.0, "senior": 1.25}

    def __init__(self, nombre, tarifa_hora, nivel):
        nivel = str(nivel if nivel is not None else "").strip().lower()
        if nivel not in self.NIVELES:
            raise ServicioInvalidoError("El nivel debe ser 'junior' o 'senior'.")
        self._nivel = nivel
        super().__init__(nombre, tarifa_hora)

    def validar_parametros(self, horas) -> float:
        h = super().validar_parametros(horas)
        if h > 8:
            raise ServicioInvalidoError("Una asesoría no puede superar 8 horas.")
        return h

    def calcular_costo_base(self, horas):
        return horas * self._tarifa_hora * self.NIVELES[self._nivel]

    def describir(self):
        return f"{self.id} - Asesoría '{self.nombre}' ({self._nivel}) ${self.tarifa_hora:,.0f}/h"


# Reserva

class EstadoReserva(Enum):
    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"
    PROCESADA = "Procesada"
    FALLIDA = "Fallida"


class Reserva(EntidadBase):
    _PREFIJO = "RES"

    def __init__(self, cliente, servicio, horas):
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un servicio válido.")
        if not servicio.disponible:
            raise ServicioNoDisponibleError(f"El servicio {servicio.id} no está disponible.")
        try:
            h = servicio.validar_parametros(horas)
        except ServicioInvalidoError as e:  # encadenamiento de excepciones
            raise ReservaInvalidaError(f"Duración inválida para {servicio.id}: {e}") from e
        self._cliente, self._servicio, self._horas = cliente, servicio, h
        self._estado = EstadoReserva.PENDIENTE
        self._costo_total = None
        super().__init__()

    @property
    def cliente(self): return self._cliente

    @property
    def servicio(self): return self._servicio

    @property
    def horas(self): return self._horas

    @property
    def estado(self): return self._estado

    @property
    def costo_total(self): return self._costo_total

    def confirmar(self):
        if self._estado is not EstadoReserva.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"Solo se confirman reservas pendientes (estado actual: {self._estado.value}).")
        if not self._servicio.disponible:
            raise ServicioNoDisponibleError(f"El servicio {self._servicio.id} ya no está disponible.")
        self._estado = EstadoReserva.CONFIRMADA
        log.info("Reserva %s confirmada", self.id)

    def cancelar(self):
        if self._estado in (EstadoReserva.CANCELADA, EstadoReserva.PROCESADA):
            raise OperacionNoPermitidaError(
                f"No se puede cancelar una reserva {self._estado.value.lower()}.")
        self._estado = EstadoReserva.CANCELADA
        log.info("Reserva %s cancelada", self.id)

    def procesar(self, impuesto=IVA, descuento=0.0) -> float:
        """Calcula el costo final. Usa try/except/else/finally y encadena excepciones."""
        if self._estado is not EstadoReserva.CONFIRMADA:
            raise OperacionNoPermitidaError(
                f"Solo se procesan reservas confirmadas (estado actual: {self._estado.value}).")
        try:
            costo = self._servicio.calcular_costo(self._horas, impuesto, descuento)
        except ErrorSoftwareFJ as e:
            self._estado = EstadoReserva.FALLIDA
            raise ReservaInvalidaError(f"No se pudo procesar {self.id}: {e}") from e
        else:
            self._costo_total = costo
            self._estado = EstadoReserva.PROCESADA
            log.info("Reserva %s procesada. Total: $%s", self.id, f"{costo:,.2f}")
            return costo
        finally:
            log.debug("Fin del intento de procesamiento de %s (estado: %s)", self.id, self._estado.value)

    def describir(self):
        total = f" | total ${self._costo_total:,.2f}" if self._costo_total is not None else ""
        return (f"{self.id} - {self._cliente.nombre} -> {self._servicio.nombre} "
                f"({self._horas:g} h) [{self._estado.value}]{total}")
