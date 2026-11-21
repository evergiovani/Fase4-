"""Registro en memoria y demostración reproducible de Software FJ."""

from excepciones import (
    LOGGER,
    CapacidadExcedidaError,
    ClienteInvalidoError,
    ReservaError,
    ServicioNoDisponibleError,
    SoftwareFJError,
    TransicionEstadoInvalidaError,
    ValidacionError,
    error_registrado,
    registrar_evento,
)
from modelos import AlquilerEquipo, AsesoriaEspecializada, Cliente, Reserva, ReservaSala, Servicio


class SistemaGestion:
    """Administra clientes, catálogo y reservas durante la sesión."""

    def __init__(self) -> None:
        self.clientes: list[Cliente] = []
        self.servicios: list[Servicio] = []
        self.reservas: list[Reserva] = []

    def registrar_cliente(self, nombre: str, correo: str, telefono: str, *, cedula: str) -> Cliente:
        cliente = Cliente(cedula, nombre, correo, telefono)
        if any(registro.identificador == cliente.identificador for registro in self.clientes):
            raise error_registrado(ClienteInvalidoError, "La cédula ya está registrada.")
        self.clientes.append(cliente)
        registrar_evento("Cliente registrado correctamente.")
        return cliente

    def crear_servicio(
        self, tipo: str, nombre: str, tarifa: float, detalle: int | str
    ) -> Servicio:
        clases = {
            "Sala": ReservaSala,
            "Equipo": AlquilerEquipo,
            "Asesoría": AsesoriaEspecializada,
        }
        if not isinstance(tipo, str) or tipo not in clases:
            raise error_registrado(ValidacionError, "El tipo de servicio no existe.")
        servicio = clases[tipo](f"S{len(self.servicios) + 1:03d}", nombre, tarifa, detalle)
        self.servicios.append(servicio)
        registrar_evento(f"Servicio {servicio.identificador} registrado ({tipo}).")
        return servicio

    def buscar_servicio(self, identificador: str) -> Servicio:
        for servicio in self.servicios:
            if servicio.identificador == identificador:
                return servicio
        raise error_registrado(ServicioNoDisponibleError, "El servicio solicitado no existe.")

    def buscar_reserva(self, identificador: str) -> Reserva:
        for reserva in self.reservas:
            if reserva.identificador == identificador:
                return reserva
        raise error_registrado(ReservaError, "La reserva solicitada no existe.")

    def crear_reserva(
        self, cliente_id: str, servicio_id: str, duracion: float, parametros: dict | None = None
    ) -> Reserva:
        cliente = next((c for c in self.clientes if c.identificador == cliente_id), None)
        if cliente is None:
            raise error_registrado(ClienteInvalidoError, "El cliente solicitado no existe.")
        servicio = self.buscar_servicio(servicio_id)
        reserva = Reserva(
            f"R{len(self.reservas) + 1:03d}", cliente, servicio, duracion, parametros
        )
        self.reservas.append(reserva)
        registrar_evento(f"Reserva {reserva.identificador} creada ({reserva.estado}).")
        return reserva


def ejecutar_demostracion() -> list[str]:
    """Ejecuta diez operaciones y comprueba sus resultados esperados."""
    sistema = SistemaGestion()
    sala = sistema.crear_servicio("Sala", "Sala de reuniones", 50000, 10)
    equipo = sistema.crear_servicio("Equipo", "Proyector", 25000, 2)
    asesoria = sistema.crear_servicio("Asesoría", "Edición digital", 80000, "Multimedia")
    cedula = "1234567890"
    resultados = []

    def ejecutar(descripcion, accion, esperado=None, mensaje="Operación completada"):
        try:
            accion()
        except SoftwareFJError as exc:
            if esperado is None or type(exc) is not esperado:
                raise
            LOGGER.warning("Rechazo controlado en %s (%s).", descripcion, type(exc).__name__)
            resultado = f"{type(exc).__name__}. {exc}"
        else:
            if esperado is not None:
                raise AssertionError(f"{descripcion} debía producir {esperado.__name__}.")
            resultado = mensaje
        resultados.append(f"{descripcion} | {resultado}")

    def procesar_asesoria():
        reserva = sistema.buscar_reserva("R002")
        total = reserva.procesar(impuesto=0.19, descuento=0.10)
        if total != 171360.0 or reserva.estado != Reserva.CONFIRMADA:
            raise AssertionError("El total o el estado final de la asesoría es incorrecto.")

    ejecutar("Alta de cliente válido", lambda: sistema.registrar_cliente(
        "Cliente de Prueba", "cliente@example.com", "+573001234567", cedula=cedula
    ), mensaje="Cliente registrado")
    ejecutar("Alta con correo inválido", lambda: sistema.registrar_cliente(
        "Cliente de Prueba", "correo-invalido", "3001234567", cedula="1234567891"
    ), ClienteInvalidoError)
    ejecutar("Sala para 11 personas", lambda: sistema.crear_reserva(
        cedula, sala.identificador, 2, {"personas": 11}
    ), CapacidadExcedidaError)
    ejecutar("Alquiler de 3 equipos", lambda: sistema.crear_reserva(
        cedula, equipo.identificador, 1, {"cantidad": 3}
    ), ServicioNoDisponibleError)
    ejecutar("Sala para 4 personas", lambda: sistema.crear_reserva(
        cedula, sala.identificador, 2, {"personas": 4}
    ), mensaje="R001 PENDIENTE")
    ejecutar("Cancelar R001", lambda: sistema.buscar_reserva("R001").cancelar(),
             mensaje="R001 CANCELADA")
    ejecutar("Cancelar R001 por segunda vez", lambda: sistema.buscar_reserva("R001").cancelar(),
             TransicionEstadoInvalidaError)
    ejecutar("Reservar 2 horas de asesoría", lambda: sistema.crear_reserva(
        cedula, asesoria.identificador, 2
    ), mensaje="R002 PENDIENTE")
    ejecutar("Confirmar R002", lambda: sistema.buscar_reserva("R002").confirmar(),
             mensaje="R002 CONFIRMADA")
    ejecutar("Procesar R002 con 19 % de impuesto y 10 % de descuento",
             procesar_asesoria, mensaje="Total de 171 360 COP")
    if len(sistema.clientes) != 1 or len(sistema.reservas) != 2:
        raise AssertionError("Las operaciones rechazadas alteraron el registro.")
    LOGGER.info("Demostración completada con %d operaciones.", len(resultados))
    return resultados
