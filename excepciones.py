"""Excepciones personalizadas de Software FJ.

Todas heredan de ErrorSoftwareFJ, de esta forma la aplicación pueda obtener
cualquier error propio con un solo `except` y seguir funcionando.
"""


class ErrorSoftwareFJ(Exception):
    """Excepción base del sistema."""


class ClienteInvalidoError(ErrorSoftwareFJ):
    """Datos de cliente inválidos, duplicados o cliente inexistente."""


class ServicioInvalidoError(ErrorSoftwareFJ):
    """Datos de servicio inválidos o servicio inexistente."""


class ServicioNoDisponibleError(ErrorSoftwareFJ):
    """El servicio existe pero no está disponible para reservar."""


class ReservaInvalidaError(ErrorSoftwareFJ):
    """Intento de reserva incorrecto o reserva inexistente."""


class OperacionNoPermitidaError(ErrorSoftwareFJ):
    """Operación no permitida para el estado actual de la reserva."""


class ParametroFaltanteError(ErrorSoftwareFJ):
    """Faltan parámetros obligatorios (o sobran parámetros inesperados)."""


class CalculoInconsistenteError(ErrorSoftwareFJ):
    """Cálculo de costos con valores fuera de rango o resultado inválido."""
