"""Excepciones personalizadas, bitácora (logs) y validaciones generales.

Aquí está todo lo relacionado con el manejo de errores del sistema.
"""

# Módulos estándar: registro de eventos, validaciones, rutas y ventanas de Tkinter.
import logging
import math
from pathlib import Path
from typing import Any


# Se guarda la bitácora junto al archivo Python para facilitar su localización.
ARCHIVO_LOG = Path(__file__).with_name("software_fj.log")
LOGGER = logging.getLogger("SoftwareFJ")
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False
# Se evita agregar varios manejadores si el módulo se carga más de una vez.
if not LOGGER.handlers:
    manejador = logging.FileHandler(ARCHIVO_LOG, encoding="utf-8", delay=True)
    manejador.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    LOGGER.addHandler(manejador)


class SoftwareFJError(Exception):
    """Error base; permite capturar en conjunto los errores controlados."""


class DatoInvalidoError(SoftwareFJError):
    """Se usa cuando un dato ingresado no cumple las reglas del sistema."""


class TransicionEstadoInvalidaError(SoftwareFJError):
    """Se usa cuando se solicita una acción inválida para el estado actual."""


class ServicioNoDisponibleError(SoftwareFJError):
    """Se usa cuando un servicio no existe o no puede atender la solicitud."""


class ReservaError(SoftwareFJError):
    """Se usa para errores relacionados con las reservas."""


class ClienteInvalidoError(DatoInvalidoError):
    """Datos de cliente inválidos o cliente inexistente."""


class CapacidadExcedidaError(DatoInvalidoError):
    """La solicitud supera el aforo de la sala."""


# Nombres usados por la interfaz original.
SistemaError = SoftwareFJError
ValidacionError = DatoInvalidoError
OperacionNoPermitidaError = TransicionEstadoInvalidaError


def error_registrado(tipo_error: type, mensaje: str) -> Exception:
    """Registra el mensaje y construye una excepción del tipo indicado."""
    LOGGER.error("%s: %s", tipo_error.__name__, mensaje)
    return tipo_error(mensaje)


def registrar_evento(mensaje: str) -> None:
    """Escribe en la bitácora una operación que se realizó correctamente."""
    LOGGER.info(mensaje)


def numero_positivo(valor: Any, nombre: str) -> float:
    """Convierte un valor a número y rechaza booleanos, cero y valores inválidos."""
    # bool es una subclase de int en Python; se rechaza explícitamente.
    if isinstance(valor, bool):
        raise error_registrado(ValidacionError, f"{nombre} debe ser numérico.")
    try:
        # Encadenar la excepción original ayuda a identificar el dato mal formado.
        resultado = float(valor)
    except (TypeError, ValueError, OverflowError) as exc:
        raise error_registrado(
            ValidacionError, f"{nombre} debe ser un número válido."
        ) from exc
    # Se rechazan NaN e infinitos.
    if resultado <= 0 or not math.isfinite(resultado):
        raise error_registrado(
            ValidacionError, f"{nombre} debe ser un número mayor que cero."
        )
    return resultado
