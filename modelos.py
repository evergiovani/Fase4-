"""Clases de negocio: Entidad, Cliente, Servicio (y sus subclases) y Reserva."""

# Módulos estándar: expresiones regulares, clases abstractas y tipos.
import math
import re
from abc import ABC, abstractmethod
from typing import Any, Optional, overload

from excepciones import (
    LOGGER,
    CapacidadExcedidaError,
    ClienteInvalidoError,
    TransicionEstadoInvalidaError,
    ReservaError,
    ServicioNoDisponibleError,
    ValidacionError,
    error_registrado,
    numero_positivo,
    registrar_evento,
)


# Clase base abstracta para todas las entidades del sistema.
# Toda entidad debe poseer un identificador unico y una descripcion resumida.
class EntidadBase(ABC):
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


# Representa a una persona que puede reservar servicios del sistema.
# Las propiedades validan nombre, correo y teléfono antes de guardar la informacion.
class Cliente(EntidadBase):
    """Cliente cuyos datos personales se consultan y validan mediante propiedades."""

    def __init__(
        self, identificador: str, nombre: str, correo: str, telefono: str
    ) -> None:
        # Inicializa los atributos privados antes de pasar por sus validadores.
        if not isinstance(identificador, str) or not re.fullmatch(
            r"[0-9]{6,10}", identificador.strip()
        ):
            raise error_registrado(
                ClienteInvalidoError, "La cédula debe tener de 6 a 10 dígitos."
            )
        super().__init__(identificador)
        self._nombre = ""
        self._correo = ""
        self._telefono = ""
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono

    @property
    def nombre(self) -> str:
        """Lee el nombre almacenado en el atributo privado."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        """Valida y actualiza el nombre del cliente."""
        # Acepta letras, espacios, apóstrofos y guiones, con longitud razonable.
        if not isinstance(valor, str) or not re.fullmatch(
            r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]{3,80}", valor.strip()
        ):
            raise error_registrado(
                ClienteInvalidoError, "El nombre debe tener entre 3 y 80 letras."
            )
        self._nombre = valor.strip()

    @property
    def correo(self) -> str:
        """Lee el correo electrónico del cliente."""
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        """Valida el formato del correo y lo guarda normalizado."""
        # Comprueba un formato básico y normaliza el correo a minúsculas.
        if not isinstance(valor, str) or len(valor.strip()) > 254 or not re.fullmatch(
            r"[A-Za-z0-9_+%-]+(?:\.[A-Za-z0-9_+%-]+)*@"
            r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}", valor.strip()
        ):
            raise error_registrado(ClienteInvalidoError, "El correo no tiene formato válido.")
        self._correo = valor.strip().lower()

    @property
    def telefono(self) -> str:
        """Lee el teléfono del cliente."""
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        """Valida los caracteres y la cantidad de dígitos del teléfono."""
        telefono = valor.strip() if isinstance(valor, str) else ""
        if not re.fullmatch(r"\+?[0-9]{7,15}", telefono):
            raise error_registrado(
                ClienteInvalidoError, "El teléfono requiere de 7 a 15 dígitos y admite + inicial."
            )
        self._telefono = telefono

    def resumen(self) -> str:
        """Devuelve los datos principales del cliente para listados."""
        return f"{self.identificador} - {self.nombre} ({self.correo})"


# Clase abstracta para todos los servicios ofertados por la empresa.
# Define la logica comun de validacion, calculo de tarfa y presentacion,
# dejando a cada subclase su comportamiento particular.
class Servicio(EntidadBase, ABC):
    """Clase abstracta para los servicios; concentra reglas compartidas."""

    def __init__(
        self, identificador: str, nombre: str, tarifa: float, disponible: bool = True
    ) -> None:
        super().__init__(identificador)
        # El servicio necesita nombre, tarifa positiva y disponibilidad booleana.
        if not isinstance(nombre, str) or not nombre.strip():
            raise error_registrado(ValidacionError, "El nombre del servicio es obligatorio.")
        self.nombre = nombre.strip()
        self.tarifa = numero_positivo(tarifa, "La tarifa")
        if not isinstance(disponible, bool):
            raise error_registrado(ValidacionError, "La disponibilidad debe ser booleana.")
        self.disponible = disponible

    @abstractmethod
    def validar_parametros(self, duracion: float, **parametros: Any) -> None:
        """Cada servicio valida sus propias condiciones y disponibilidad."""

    @abstractmethod
    def calcular_tarifa(self, duracion: float, **parametros: Any) -> float:
        """Cada servicio implementa su fórmula de costo base."""

    @abstractmethod
    def describir(self) -> str:
        """Cada servicio construye su descripción de manera polimórfica."""

    # Las sobrecargas documentan tres formas de llamar el cálculo:
    # costo simple, costo con impuesto o costo con impuesto y descuento.
    @overload
    def calcular_costo(self, duracion: float) -> float:
        ...

    @overload
    def calcular_costo(self, duracion: float, impuesto: float) -> float:
        ...

    @overload
    def calcular_costo(
        self, duracion: float, impuesto: float, descuento: float
    ) -> float:
        ...

    def calcular_costo(self, duracion: float, *args: Any, **kwargs: Any) -> float:
        """Admite impuesto y descuento posicionales o por nombre."""
        return self._calcular_costo(duracion, *args, **kwargs)

    def _calcular_costo(
        self,
        duracion: float,
        impuesto: float = 0.19,
        descuento: float = 0.0,
        **parametros: Any,
    ) -> float:
        """Calcula el precio final aplicando impuesto y descuento opcionales."""
        # La clase concreta valida los datos particulares antes del cálculo.
        self.validar_parametros(duracion, **parametros)
        if isinstance(impuesto, bool) or not isinstance(impuesto, (int, float)):
            raise error_registrado(ValidacionError, "El impuesto debe ser numérico.")
        if isinstance(descuento, bool) or not isinstance(descuento, (int, float)):
            raise error_registrado(ValidacionError, "El descuento debe ser numérico.")
        if not 0 <= impuesto <= 1:
            raise error_registrado(
                ValidacionError, "El impuesto debe expresarse entre 0 y 1."
            )
        if not 0 <= descuento <= 1:
            raise error_registrado(
                ValidacionError, "El descuento debe expresarse entre 0 y 1."
            )
        # El descuento se aplica primero y el impuesto sobre el resultado.
        base = self.calcular_tarifa(duracion, **parametros)
        total = base * (1 - descuento) * (1 + impuesto)
        if not math.isfinite(total) or total < 0:
            raise error_registrado(
                ReservaError, "El cálculo produjo un costo inconsistente."
            )
        return round(total, 2)

    def resumen(self) -> str:
        """Reutiliza la descripción concreta como resumen del servicio."""
        return self.describir()


# Servicio concreto para alquiler de salas.
# Permite reservar espacio por horas y valida la capacidad maxima permitida.
class ReservaSala(Servicio):
    """Servicio concreto que alquila salas por hora y controla su capacidad."""

    # La interfaz usa esta unidad para mostrar la duración solicitada.
    unidad_duracion = "horas"

    def __init__(
        self,
        identificador: str,
        nombre: str,
        tarifa: float,
        capacidad_maxima: int = 20,
        disponible: bool = True,
    ) -> None:
        super().__init__(identificador, nombre, tarifa, disponible)
        # La capacidad debe ser un entero positivo, no un booleano.
        if isinstance(capacidad_maxima, bool) or not isinstance(capacidad_maxima, int):
            raise error_registrado(
                ValidacionError, "La capacidad máxima debe ser un número entero."
            )
        if capacidad_maxima < 1:
            raise error_registrado(
                ValidacionError, "La capacidad máxima debe ser al menos 1."
            )
        self.capacidad_maxima = capacidad_maxima

    def validar_parametros(self, duracion: float, **parametros: Any) -> None:
        """Comprueba duración, disponibilidad y cantidad de personas."""
        numero_positivo(duracion, "La duración")
        if not self.disponible:
            raise error_registrado(
                ServicioNoDisponibleError, f"El servicio {self.nombre} no está disponible."
            )
        # Si no se indica cantidad, se asume una persona.
        personas = parametros.get("personas", 1)
        if isinstance(personas, bool) or not isinstance(personas, int):
            raise error_registrado(
                ValidacionError, "La cantidad de personas debe ser un entero."
            )
        if personas < 1:
            raise error_registrado(ValidacionError, "Debe asistir al menos una persona.")
        if personas > self.capacidad_maxima:
            raise error_registrado(
                CapacidadExcedidaError, f"La sala admite hasta {self.capacidad_maxima} personas."
            )

    def calcular_tarifa(self, duracion: float, **parametros: Any) -> float:
        """Multiplica la tarifa por hora por la cantidad de horas."""
        return self.tarifa * numero_positivo(duracion, "La duración")

    def describir(self) -> str:
        """Devuelve el servicio con su precio, capacidad y disponibilidad."""
        estado = "Disponible" if self.disponible else "No disponible"
        return (
            f"{self.identificador} - Sala: {self.nombre} | "
            f"${self.tarifa:.2f}/hora | capacidad {self.capacidad_maxima} | {estado}"
        )


# Servicio concreto para alquiler de equipos.
# Se calcula por dias y controla cuantas unidades disponibles hay para prestar.
class AlquilerEquipo(Servicio):
    """Servicio concreto de alquiler diario con control de existencias."""

    # La duración de este servicio se mide en días.
    unidad_duracion = "días"

    def __init__(
        self,
        identificador: str,
        nombre: str,
        tarifa: float,
        existencias: int = 5,
        disponible: bool = True,
    ) -> None:
        super().__init__(identificador, nombre, tarifa, disponible)
        # Se evita registrar equipos con existencias inválidas.
        if isinstance(existencias, bool) or not isinstance(existencias, int):
            raise error_registrado(
                ValidacionError, "Las existencias deben ser un número entero."
            )
        if existencias < 1:
            raise error_registrado(ValidacionError, "Debe existir al menos un equipo.")
        self.existencias = existencias

    def validar_parametros(self, duracion: float, **parametros: Any) -> None:
        """Verifica disponibilidad, duración y unidades que se desean alquilar."""
        numero_positivo(duracion, "La duración")
        if not self.disponible:
            raise error_registrado(
                ServicioNoDisponibleError, f"El servicio {self.nombre} no está disponible."
            )
        # Cuando no se indica una cantidad, se solicita una unidad.
        cantidad = parametros.get("cantidad", 1)
        if isinstance(cantidad, bool) or not isinstance(cantidad, int):
            raise error_registrado(
                ValidacionError, "La cantidad de equipos debe ser un entero."
            )
        if cantidad < 1:
            raise error_registrado(ValidacionError, "Solicite al menos un equipo.")
        if cantidad > self.existencias:
            raise error_registrado(
                ServicioNoDisponibleError,
                f"Hay {self.existencias} unidades disponibles.",
            )

    def calcular_tarifa(self, duracion: float, **parametros: Any) -> float:
        """Calcula tarifa diaria por días de alquiler y cantidad de unidades."""
        cantidad = parametros.get("cantidad", 1)
        return (
            self.tarifa
            * numero_positivo(duracion, "La duración")
            * cantidad
        )

    def describir(self) -> str:
        """Devuelve el precio diario, las existencias y el estado del equipo."""
        estado = "Disponible" if self.disponible else "No disponible"
        return (
            f"{self.identificador} - Equipo: {self.nombre} | "
            f"${self.tarifa:.2f}/día | existencias {self.existencias} | {estado}"
        )


# Servicio concreto de asesoria profesional.
# Se ofrece por horas y se diferencia por la especialidad del experto.
class AsesoriaEspecializada(Servicio):
    """Servicio concreto de asesoría con especialidad y tarifa por hora."""

    # Las asesorías también se contabilizan por horas.
    unidad_duracion = "horas"

    def __init__(
        self,
        identificador: str,
        nombre: str,
        tarifa: float,
        especialidad: str = "General",
        disponible: bool = True,
    ) -> None:
        super().__init__(identificador, nombre, tarifa, disponible)
        # La especialidad se conserva sin espacios externos.
        if not isinstance(especialidad, str) or not especialidad.strip():
            raise error_registrado(
                ValidacionError, "La especialidad de la asesoría es obligatoria."
            )
        self.especialidad = especialidad.strip()

    def validar_parametros(self, duracion: float, **parametros: Any) -> None:
        """Verifica que la duración sea positiva y el servicio esté disponible."""
        numero_positivo(duracion, "La duración")
        if not self.disponible:
            raise error_registrado(
                ServicioNoDisponibleError, f"El servicio {self.nombre} no está disponible."
            )

    def calcular_tarifa(self, duracion: float, **parametros: Any) -> float:
        """Multiplica la tarifa por hora por la duración de la asesoría."""
        return self.tarifa * numero_positivo(duracion, "La duración")

    def describir(self) -> str:
        """Muestra el nombre de la asesoría, especialidad y tarifa."""
        estado = "Disponible" if self.disponible else "No disponible"
        return (
            f"{self.identificador} - Asesoría: {self.nombre} "
            f"({self.especialidad}) | ${self.tarifa:.2f}/hora | {estado}"
        )


# Representa la operacion de reservar un servicio por parte de un cliente.
# Controla el flujo de estados, el calculo del costo y la validacion del servicio.
class Reserva(EntidadBase):
    """Reserva que relaciona un cliente, un servicio y un estado de atención."""

    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"

    def __init__(
        self,
        identificador: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion: float,
        parametros: Optional[dict] = None,
    ) -> None:
        super().__init__(identificador)
        # Una reserva solo se crea con instancias válidas de Cliente y Servicio.
        if not isinstance(cliente, Cliente) or not isinstance(servicio, Servicio):
            raise error_registrado(
                ValidacionError, "La reserva requiere un cliente y un servicio válidos."
            )
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = numero_positivo(duracion, "La duración")
        # Se copia el diccionario para que cambios externos no alteren la reserva.
        if parametros is not None and not isinstance(parametros, dict):
            raise error_registrado(ValidacionError, "Los parámetros deben ser un diccionario.")
        self.parametros = parametros.copy() if parametros else {}
        # Se valida antes de guardar la reserva en el sistema.
        self.servicio.validar_parametros(self.duracion, **self.parametros)
        self._estado = self.PENDIENTE
        self.total: Optional[float] = None

    @property
    def estado(self) -> str:
        return self._estado

    def confirmar(self) -> None:
        """Confirma una reserva pendiente si el servicio sigue disponible."""
        if self.estado != self.PENDIENTE:
            raise error_registrado(
                TransicionEstadoInvalidaError,
                f"No se puede confirmar una reserva en estado {self.estado}.",
            )
        self.servicio.validar_parametros(self.duracion, **self.parametros)
        self._estado = self.CONFIRMADA
        registrar_evento(f"Reserva {self.identificador} confirmada.")

    def cancelar(self) -> None:
        """Cancela reservas pendientes o confirmadas, pero no procesadas."""
        if self.estado == self.CANCELADA or self.total is not None:
            raise error_registrado(
                TransicionEstadoInvalidaError,
                f"No se puede cancelar una reserva en estado {self.estado}.",
            )
        self._estado = self.CANCELADA
        registrar_evento(f"Reserva {self.identificador} cancelada.")

    def procesar(self, impuesto: float = 0.19, descuento: float = 0.0) -> float:
        """Calcula y guarda el total; encadena errores del cálculo como ReservaError."""
        if self.estado != self.CONFIRMADA or self.total is not None:
            raise error_registrado(
                TransicionEstadoInvalidaError,
                "La reserva debe estar confirmada y sin procesar.",
            )
        try:
            # El cálculo polimórfico usa la fórmula del tipo concreto de servicio.
            total = self.servicio.calcular_costo(
                self.duracion,
                impuesto,
                descuento,
                **self.parametros,
            )
        except (ValidacionError, ServicioNoDisponibleError, ReservaError) as exc:
            # "from exc" conserva el error original como causa de la excepción nueva.
            raise error_registrado(
                ReservaError,
                f"No se pudo procesar la reserva {self.identificador}.",
            ) from exc
        else:
            self.total = total
            registrar_evento(f"Reserva {self.identificador} procesada por ${total:.2f}.")
            return total
        finally:
            LOGGER.info("Fin del intento de cálculo de %s (%s).", self.identificador, self.estado)

    def resumen(self) -> str:
        """Genera una línea con el cliente, servicio, estado y costo de la reserva."""
        costo = f"${self.total:.2f}" if self.total is not None else "Pendiente"
        return (
            f"{self.identificador} | {self.cliente.nombre} | "
            f"{self.servicio.nombre} | {self.estado} | {costo}"
        )


# Nombres disponibles en versiones anteriores del módulo.
Entity = EntidadBase
Asesoria = AsesoriaEspecializada
