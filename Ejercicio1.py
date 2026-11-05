"""Sistema de gestión de clientes, servicios y reservas para Software FJ."""
import logging
import re
import sys
import tkinter as tk
from abc import ABC, abstractmethod
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, List, Optional, overload


ARCHIVO_LOG = Path(__file__).with_name("software_fj.log")
LOGGER = logging.getLogger("SoftwareFJ")
LOGGER.setLevel(logging.INFO)
if not LOGGER.handlers:
    manejador = logging.FileHandler(ARCHIVO_LOG, encoding="utf-8")
    manejador.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    LOGGER.addHandler(manejador)


class SistemaError(Exception):
    """Error base de la aplicación."""


class ValidacionError(SistemaError):
    """Datos inválidos o incompletos."""


class OperacionNoPermitidaError(SistemaError):
    """Acción incompatible con el estado actual."""


class ServicioNoDisponibleError(SistemaError):
    """El servicio no está disponible para la operación solicitada."""


class ReservaError(SistemaError):
    """Error durante la creación o procesamiento de una reserva."""


def error_registrado(tipo_error: type, mensaje: str) -> Exception:
    LOGGER.error("%s: %s", tipo_error.__name__, mensaje)
    return tipo_error(mensaje)


def registrar_evento(mensaje: str) -> None:
    LOGGER.info(mensaje)


def numero_positivo(valor: Any, nombre: str) -> float:
    if isinstance(valor, bool):
        raise error_registrado(ValidacionError, f"{nombre} debe ser numérico.")
    try:
        resultado = float(valor)
    except (TypeError, ValueError) as exc:
        raise error_registrado(
            ValidacionError, f"{nombre} debe ser un número válido."
        ) from exc
    if resultado <= 0 or resultado == float("inf") or resultado != resultado:
        raise error_registrado(
            ValidacionError, f"{nombre} debe ser un número mayor que cero."
        )
    return resultado


class Entidad(ABC):
    """Entidad general identificada de forma única."""

    def __init__(self, identificador: str) -> None:
        if not isinstance(identificador, str) or not identificador.strip():
            raise error_registrado(
                ValidacionError, "El identificador de la entidad es obligatorio."
            )
        self._identificador = identificador.strip()

    @property
    def identificador(self) -> str:
        return self._identificador

    @abstractmethod
    def resumen(self) -> str:
        """Devuelve una descripción corta de la entidad."""

