"""Sistema de gestión de clientes, servicios y reservas para Software FJ.

La aplicación utiliza objetos y listas en memoria; no necesita una base de datos.
Al ejecutar el archivo se abre la interfaz gráfica. También se puede ejecutar
con la opción --demo para probar las operaciones desde la consola.
"""

# Módulos estándar: registro de eventos, validaciones, rutas y ventanas Tkinter.
import logging
import re
import sys
import tkinter as tk
from abc import ABC, abstractmethod
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, List, Optional, overload


# Se guarda la bitácora junto al archivo Python para facilitar su localización.
ARCHIVO_LOG = Path(__file__).with_name("software_fj.log")
LOGGER = logging.getLogger("SoftwareFJ")
LOGGER.setLevel(logging.INFO)
# Se evita agregar varios manejadores si el módulo se carga más de una vez.
if not LOGGER.handlers:
    manejador = logging.FileHandler(ARCHIVO_LOG, encoding="utf-8")
    manejador.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    LOGGER.addHandler(manejador)


class SistemaError(Exception):
    """Error base; permite capturar en conjunto los errores controlados."""


class ValidacionError(SistemaError):
    """Se usa cuando un dato ingresado no cumple las reglas del sistema."""


class OperacionNoPermitidaError(SistemaError):
    """Se usa cuando se solicita una acción inválida para el estado actual."""


class ServicioNoDisponibleError(SistemaError):
    """Se usa cuando un servicio no existe o no puede atender la solicitud."""


class ReservaError(SistemaError):
    """Se usa para errores relacionados con las reservas."""


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
    except (TypeError, ValueError) as exc:
        raise error_registrado(
            ValidacionError, f"{nombre} debe ser un número válido."
        ) from exc
    # La última condición detecta NaN; la anterior impide usar infinito.
    if resultado <= 0 or resultado == float("inf") or resultado != resultado:
        raise error_registrado(
            ValidacionError, f"{nombre} debe ser un número mayor que cero."
        )
    return resultado


class Entidad(ABC):
    """Clase abstracta común con identificador y método resumen obligatorio."""

    def __init__(self, identificador: str) -> None:
        # Todas las entidades del sistema deben tener un ID no vacío.
        if not isinstance(identificador, str) or not identificador.strip():
            raise error_registrado(
                ValidacionError, "El identificador de la entidad es obligatorio."
            )
        self._identificador = identificador.strip()

    @property
    def identificador(self) -> str:
        """Expone el identificador sin permitir cambiarlo desde la interfaz."""
        return self._identificador

    @abstractmethod
    def resumen(self) -> str:
        """Obliga a cada clase concreta a definir una descripción corta."""


class Cliente(Entidad):
    """Cliente cuyos datos personales se consultan y validan mediante propiedades."""

    def __init__(
        self, identificador: str, nombre: str, correo: str, telefono: str
    ) -> None:
        # Inicializar los atributos privados antes de pasar por sus validadores.
        super().__init__(identificador)
        self._nombre = ""
        self._correo = ""
        self._telefono = ""
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono
