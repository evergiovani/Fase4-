"""Sistema que coordina listas de clientes, servicios y reservas, además de la demostración."""

from typing import Any, List, Optional

from excepciones import (
    LOGGER,
    ReservaError,
    ServicioNoDisponibleError,
    SistemaError,
    ValidacionError,
    error_registrado,
    registrar_evento,
)
from modelos import (
    Asesoria,
    AlquilerEquipo,
    Cliente,
    Reserva,
    ReservaSala,
    Servicio,
)


class SistemaGestion:
    """Coordina clientes, servicios y reservas usando únicamente listas."""

    def __init__(self) -> None:
        self.clientes: List[Cliente] = []
        self.servicios: List[Servicio] = []
        self.reservas: List[Reserva] = []
        self._contador_cliente = 0
        self._contador_servicio = 0
        self._contador_reserva = 0

    def registrar_cliente(self, nombre: str, correo: str, telefono: str) -> Cliente:
        """Valida, asigna ID y registra un nuevo cliente."""
        if any(c.correo == correo.strip().lower() for c in self.clientes):
            raise error_registrado(
                ValidacionError, f"Ya existe un cliente con el correo {correo}."
            )
        # Validación agregada por Henry Fabián Rodríguez Centeno.
        # Evita registrar dos clientes con el mismo número de teléfono.
        if any(c.telefono == telefono for c in self.clientes):
            raise error_registrado(
                ValidacionError, "Ya existe un cliente con ese número de teléfono."
                )
        candidato = f"CLI-{self._contador_cliente + 1:03d}"
        cliente = Cliente(candidato, nombre, correo, telefono)
        self._contador_cliente += 1
        self.clientes.append(cliente)
        registrar_evento(f"Cliente {cliente.identificador} registrado.")
        return cliente

    def agregar_servicio(self, servicio: Servicio) -> Servicio:
        """Añade un servicio ya construido, evitando IDs duplicados."""
        if not isinstance(servicio, Servicio):
            raise error_registrado(
                ValidacionError, "Solo se pueden agregar servicios válidos."
            )
        if any(s.identificador == servicio.identificador for s in self.servicios):
            raise error_registrado(
                ValidacionError, f"El servicio {servicio.identificador} ya existe."
            )
        self.servicios.append(servicio)
        registrar_evento(f"Servicio {servicio.identificador} agregado.")
        return servicio

    def crear_servicio(
        self, tipo: str, nombre: str, tarifa: float, especificacion: Any = None
    ) -> Servicio:
        """Construye el subtipo solicitado usando su parámetro específico."""
        identificador = f"SER-{self._contador_servicio + 1:03d}"
        clases = {
            "Sala": lambda: ReservaSala(
                identificador, nombre, tarifa, capacidad_maxima=especificacion or 20
            ),
            "Equipo": lambda: AlquilerEquipo(
                identificador, nombre, tarifa, existencias=especificacion or 5
            ),
            "Asesoría": lambda: Asesoria(
                identificador, nombre, tarifa, especialidad=especificacion or "General"
            ),
        }
        if tipo not in clases:
            raise error_registrado(
                ValidacionError, "Tipo de servicio desconocido."
            )
        servicio = clases[tipo]()
        self._contador_servicio += 1
        return self.agregar_servicio(servicio)

    def buscar_cliente(self, identificador: str) -> Cliente:
        """Busca un cliente por ID o lanza un error de validación."""
        for cliente in self.clientes:
            if cliente.identificador == identificador:
                return cliente
        raise error_registrado(
            ValidacionError, f"No existe el cliente {identificador}."
        )

    def buscar_servicio(self, identificador: str) -> Servicio:
        """Busca un servicio por ID o indica que no está disponible."""
        for servicio in self.servicios:
            if servicio.identificador == identificador:
                return servicio
        raise error_registrado(
            ServicioNoDisponibleError, f"No existe el servicio {identificador}."
        )

    def crear_reserva(
        self,
        cliente_id: str,
        servicio_id: str,
        duracion: float,
        parametros: Optional[dict] = None,
    ) -> Reserva:
        """Busca sus dependencias, crea la reserva y la agrega a la lista."""
        cliente = self.buscar_cliente(cliente_id)
        servicio = self.buscar_servicio(servicio_id)
        identificador = f"RES-{self._contador_reserva + 1:03d}"
        reserva = Reserva(
            identificador, cliente, servicio, duracion, parametros=parametros
        )
        self._contador_reserva += 1
        self.reservas.append(reserva)
        registrar_evento(f"Reserva {reserva.identificador} creada.")
        return reserva

    def buscar_reserva(self, identificador: str) -> Reserva:
        """Busca una reserva por su ID y notifica si no existe."""
        for reserva in self.reservas:
            if reserva.identificador == identificador:
                return reserva
        raise error_registrado(ReservaError, f"No existe la reserva {identificador}.")


def ejecutar_demostracion() -> List[str]:
    """Ejecuta operaciones válidas e inválidas y devuelve su resultado como texto.

    Cada operación queda aislada para que un error no detenga las siguientes.
    """
    sistema = SistemaGestion()
    resultados: List[str] = []

    def probar(etiqueta: str, operacion: Any) -> Any:
        """Ejecuta una operación individual y registra éxito o excepción."""
        try:
            resultado = operacion()
        except SistemaError as exc:
            resultados.append(f"ERROR CONTROLADO: {etiqueta} -> {exc}")
            return None
        except Exception as exc:
            LOGGER.exception("Error inesperado en demostración: %s", etiqueta)
            resultados.append(f"ERROR INESPERADO: {etiqueta} -> {exc}")
            return None
        else:
            resultados.append(f"CORRECTO: {etiqueta}")
            return resultado
        finally:
            registrar_evento(f"Demostración ejecutada: {etiqueta}.")

    cliente = probar(
        "registrar cliente válido",
        lambda: sistema.registrar_cliente(
            "Laura Gómez", "laura@example.com", "3001234567"
        ),
    )
    probar(
        "rechazar correo inválido",
        lambda: sistema.registrar_cliente("Carlos Ruiz", "correo-invalido", "3011234567"),
    )
    cliente_dos = probar(
        "registrar segundo cliente",
        lambda: sistema.registrar_cliente(
            "Andrés Pérez", "andres@example.com", "3021234567"
        ),
    )
    probar(
        "rechazar correo duplicado",
        lambda: sistema.registrar_cliente(
            "Laura Gómez", "laura@example.com", "3001234567"
        ),
    )
    sala = probar(
        "crear servicio de sala",
        lambda: sistema.crear_servicio("Sala", "Sala ejecutiva", 50000, 12),
    )
    equipo = probar(
        "crear servicio de alquiler de equipos",
        lambda: sistema.crear_servicio("Equipo", "Proyector", 25000, 3),
    )
    asesoria = probar(
        "crear servicio de asesoría",
        lambda: sistema.crear_servicio("Asesoría", "Consultoría TI", 80000, "Tecnología"),
    )
    probar(
        "rechazar servicio con tarifa inválida",
        lambda: sistema.crear_servicio("Sala", "Sala inválida", -10, 10),
    )
    reserva = None
    if cliente is not None and sala is not None:
        reserva = probar(
            "crear reserva válida",
            lambda: sistema.crear_reserva(
                cliente.identificador, sala.identificador, 2, {"personas": 8}
            ),
        )
    if reserva is not None:
        probar("confirmar reserva", reserva.confirmar)
        probar(
            "procesar reserva con impuesto y descuento",
            lambda: reserva.procesar(0.19, 0.1),
        )
    if cliente_dos is not None and equipo is not None:
        probar(
            "rechazar reserva por exceder existencias",
            lambda: sistema.crear_reserva(
                cliente_dos.identificador,
                equipo.identificador,
                1,
                {"cantidad": 99},
            ),
        )
    if cliente_dos is not None and asesoria is not None:
        reserva_cancelable = probar(
            "crear reserva para cancelación",
            lambda: sistema.crear_reserva(
                cliente_dos.identificador, asesoria.identificador, 1
            ),
        )
        if reserva_cancelable is not None:
            probar("cancelar reserva", reserva_cancelable.cancelar)
            probar(
                "rechazar procesamiento de reserva cancelada",
                reserva_cancelable.procesar,
            )
    probar(
        "rechazar búsqueda de servicio inexistente",
        lambda: sistema.buscar_servicio("SER-999"),
    )
    registrar_evento(f"Demostración finalizada con {len(resultados)} operaciones.")
    return resultados
