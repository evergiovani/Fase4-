"""Interfaz gráfica (Tkinter) del sistema Software FJ."""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Optional

from excepciones import (
    ARCHIVO_LOG,
    LOGGER,
    ReservaError,
    SistemaError,
    ValidacionError,
)
from modelos import AlquilerEquipo, Reserva, ReservaSala
from sistema import SistemaGestion, ejecutar_demostracion


class Application(tk.Tk):
    """Ventana principal de Tkinter para administrar los objetos del sistema."""

    def __init__(self) -> None:
        """Configura la ventana, crea los datos iniciales y prepara las pestañas."""
        super().__init__()
        # Tamaño inicial y mínimo para que los formularios sigan siendo legibles.
        self.title("Software FJ | Gestión integral")
        self.geometry("1000x700")
        self.minsize(820, 580)
        self.sistema = SistemaGestion()
        self.reserva_seleccionada: Optional[str] = None
        self._cargar_servicios_iniciales()
        self._crear_interfaz()
        self._actualizar_vistas()

    def _cargar_servicios_iniciales(self) -> None:
        """Agrega tres servicios de ejemplo al iniciar la aplicación."""
        self.sistema.crear_servicio("Sala", "Sala de reuniones", 50000, 20)
        self.sistema.crear_servicio("Equipo", "Proyector", 25000, 5)
        self.sistema.crear_servicio("Asesoría", "Asesoría especializada", 80000, "General")

    def _crear_interfaz(self) -> None:
        """Construye el encabezado y las cuatro pestañas principales."""
        # Cada pestaña separa una parte de la aplicación para facilitar su uso.
        encabezado = ttk.Label(
            self,
            text="Software FJ — Clientes, servicios y reservas",
            font=("Segoe UI", 16, "bold"),
        )
        encabezado.pack(pady=(12, 4))
        ttk.Label(
            self,
            text="Los datos se mantienen en memoria y los eventos se guardan en software_fj.log.",
        ).pack(pady=(0, 10))
        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(fill="both", expand=True, padx=12, pady=8)
        self.tab_clientes = ttk.Frame(self.pestanas, padding=10)
        self.tab_servicios = ttk.Frame(self.pestanas, padding=10)
        self.tab_reservas = ttk.Frame(self.pestanas, padding=10)
        self.tab_eventos = ttk.Frame(self.pestanas, padding=10)
        self.pestanas.add(self.tab_clientes, text="Clientes")
        self.pestanas.add(self.tab_servicios, text="Servicios")
        self.pestanas.add(self.tab_reservas, text="Reservas")
        self.pestanas.add(self.tab_eventos, text="Bitácora")
        self._crear_pestana_clientes()
        self._crear_pestana_servicios()
        self._crear_pestana_reservas()
        self._crear_pestana_eventos()

    def _crear_tabla(
        self, contenedor: ttk.Frame, columnas: tuple, encabezados: tuple, altura: int = 12
    ) -> ttk.Treeview:
        """Crea una tabla reutilizable con encabezados y columnas configuradas."""
        tabla = ttk.Treeview(
            contenedor, columns=columnas, show="headings", height=altura
        )
        for columna, encabezado in zip(columnas, encabezados):
            tabla.heading(columna, text=encabezado)
            tabla.column(columna, width=145, anchor="w")
        tabla.pack(fill="both", expand=True, pady=8)
        return tabla

    def _crear_pestana_clientes(self) -> None:
        """Crea el formulario de clientes y la tabla con sus registros."""
        formulario = ttk.LabelFrame(self.tab_clientes, text="Registrar cliente", padding=10)
        formulario.pack(fill="x")
        self.cedula_cliente = tk.StringVar()
        self.nombre_cliente = tk.StringVar()
        self.correo_cliente = tk.StringVar()
        self.telefono_cliente = tk.StringVar()
        # Las variables de Tkinter conectan las cajas de texto con el código Python.
        campos = (
            ("Cédula", self.cedula_cliente),
            ("Nombre", self.nombre_cliente),
            ("Correo", self.correo_cliente),
            ("Teléfono", self.telefono_cliente),
        )
        for indice, (etiqueta, variable) in enumerate(campos):
            ttk.Label(formulario, text=etiqueta).grid(row=0, column=indice, sticky="w", padx=5)
            ttk.Entry(formulario, textvariable=variable, width=22).grid(
                row=1, column=indice, padx=5, pady=4
            )
        ttk.Button(
            formulario, text="Guardar cliente", command=self._accion(self._registrar_cliente)
        ).grid(row=2, column=0, columnspan=4, pady=8)
        self.tabla_clientes = self._crear_tabla(
            self.tab_clientes,
            ("id", "nombre", "correo", "telefono"),
            ("ID", "Nombre", "Correo", "Teléfono"),
        )

    def _crear_pestana_servicios(self) -> None:
        """Crea los campos para registrar y consultar servicios."""
        formulario = ttk.LabelFrame(self.tab_servicios, text="Crear servicio", padding=10)
        formulario.pack(fill="x")
        self.tipo_servicio = tk.StringVar(value="Sala")
        self.nombre_servicio = tk.StringVar()
        self.tarifa_servicio = tk.StringVar()
        self.detalle_servicio = tk.StringVar(value="20")
        ttk.Label(formulario, text="Tipo").grid(row=0, column=0, sticky="w", padx=4)
        # La lista desplegable limita la selección a los tres subtipos existentes.
        ttk.Combobox(
            formulario,
            textvariable=self.tipo_servicio,
            values=("Sala", "Equipo", "Asesoría"),
            state="readonly",
            width=14,
        ).grid(row=1, column=0, padx=4)
        ttk.Label(formulario, text="Nombre").grid(row=0, column=1, sticky="w", padx=4)
        ttk.Entry(formulario, textvariable=self.nombre_servicio, width=25).grid(
            row=1, column=1, padx=4
        )
        ttk.Label(formulario, text="Tarifa").grid(row=0, column=2, sticky="w", padx=4)
        ttk.Entry(formulario, textvariable=self.tarifa_servicio, width=14).grid(
            row=1, column=2, padx=4
        )
        ttk.Label(formulario, text="Capacidad / existencias / especialidad").grid(
            row=0, column=3, sticky="w", padx=4
        )
        ttk.Entry(formulario, textvariable=self.detalle_servicio, width=24).grid(
            row=1, column=3, padx=4
        )
        ttk.Button(
            formulario,
            text="Crear servicio",
            command=self._accion(self._crear_servicio),
        ).grid(row=1, column=4, padx=6)
        self.tabla_servicios = self._crear_tabla(
            self.tab_servicios,
            ("id", "tipo", "nombre", "tarifa", "estado"),
            ("ID", "Tipo / detalle", "Nombre", "Tarifa", "Estado"),
        )
        ttk.Label(
            self.tab_servicios,
            text="Sala: tarifa por hora y capacidad máxima. Equipo: tarifa por día y existencias. Asesoría: tarifa por hora y especialidad.",
            wraplength=900,
        ).pack(anchor="w")

    def _crear_pestana_reservas(self) -> None:
        """Crea el formulario, tabla y botones para operar las reservas."""
        formulario = ttk.LabelFrame(self.tab_reservas, text="Crear reserva", padding=10)
        formulario.pack(fill="x")
        self.cliente_reserva = tk.StringVar()
        self.servicio_reserva = tk.StringVar()
        self.duracion_reserva = tk.StringVar(value="1")
        self.cantidad_reserva = tk.StringVar(value="1")
        self.combo_clientes = ttk.Combobox(
            formulario, textvariable=self.cliente_reserva, state="readonly", width=25
        )
        self.combo_servicios = ttk.Combobox(
            formulario, textvariable=self.servicio_reserva, state="readonly", width=42
        )
        # El cliente y el servicio se eligen de listas ya registradas.
        for columna, texto, widget in (
            (0, "Cliente", self.combo_clientes),
            (1, "Servicio", self.combo_servicios),
        ):
            ttk.Label(formulario, text=texto).grid(row=0, column=columna, sticky="w", padx=4)
            widget.grid(row=1, column=columna, padx=4)
        ttk.Label(formulario, text="Duración (horas o días)").grid(
            row=0, column=2, sticky="w", padx=4
        )
        ttk.Entry(formulario, textvariable=self.duracion_reserva, width=14).grid(
            row=1, column=2, padx=4
        )
        ttk.Label(formulario, text="Personas / unidades").grid(
            row=0, column=3, sticky="w", padx=4
        )
        ttk.Entry(formulario, textvariable=self.cantidad_reserva, width=14).grid(
            row=1, column=3, padx=4
        )
        ttk.Button(
            formulario, text="Crear reserva", command=self._accion(self._crear_reserva)
        ).grid(row=1, column=4, padx=6)
        self.tabla_reservas = self._crear_tabla(
            self.tab_reservas,
            ("id", "cliente", "servicio", "duracion", "estado", "total"),
            ("ID", "Cliente", "Servicio", "Duración", "Estado", "Total"),
        )
        self.tabla_reservas.bind("<<TreeviewSelect>>", self._seleccionar_reserva)
        botones = ttk.Frame(self.tab_reservas)
        botones.pack(fill="x")
        for texto, accion in (
            ("Confirmar", self._confirmar_reserva),
            ("Procesar", self._procesar_reserva),
            ("Cancelar", self._cancelar_reserva),
        ):
            ttk.Button(botones, text=texto, command=self._accion(accion)).pack(
                side="left", padx=4
            )
        ttk.Label(
            botones, text="Seleccione una reserva de la tabla antes de ejecutar una acción."
        ).pack(side="left", padx=10)

    def _crear_pestana_eventos(self) -> None:
        """Muestra la bitácora y permite ejecutar la demostración del ejercicio."""
        controles = ttk.Frame(self.tab_eventos)
        controles.pack(fill="x")
        ttk.Button(
            controles, text="Actualizar bitácora", command=self._accion(self._mostrar_log)
        ).pack(side="left")
        ttk.Button(
            controles,
            text="Ejecutar demostración (10+ operaciones)",
            command=self._accion(self._demostrar),
        ).pack(side="left", padx=8)
        self.texto_log = tk.Text(self.tab_eventos, height=25, wrap="word", state="disabled")
        self.texto_log.pack(fill="both", expand=True, pady=8)

    def _accion(self, funcion: Any) -> Any:
        """Envuelve acciones de botones para presentar errores sin cerrar la app."""

        def ejecutar() -> None:
            try:
                # Ejecuta la acción vinculada al botón.
                funcion()
            except SistemaError as exc:
                # Los errores de negocio se muestran con el mensaje específico.
                messagebox.showerror("Operación no realizada", str(exc), parent=self)
            except Exception:
                # Un error inesperado se registra con traceback y no cierra la ventana.
                LOGGER.exception("Error inesperado en la interfaz.")
                messagebox.showerror(
                    "Error inesperado",
                    "La operación falló. El detalle se guardó en la bitácora.",
                    parent=self,
                )
            finally:
                # Refresca las tablas incluso cuando la operación produjo un error.
                self._actualizar_vistas()

        return ejecutar

    def _registrar_cliente(self) -> None:
        """Lee el formulario, registra al cliente y limpia los campos."""
        cliente = self.sistema.registrar_cliente(
            self.nombre_cliente.get(),
            self.correo_cliente.get(),
            self.telefono_cliente.get(),
            cedula=self.cedula_cliente.get(),
        )
        self.cedula_cliente.set("")
        self.nombre_cliente.set("")
        self.correo_cliente.set("")
        self.telefono_cliente.set("")
        messagebox.showinfo(
            "Cliente registrado", f"Se registró a {cliente.nombre}.", parent=self
        )

    def _crear_servicio(self) -> None:
        """Convierte los datos del formulario y crea el subtipo seleccionado."""
        tipo = self.tipo_servicio.get()
        detalle: Any = self.detalle_servicio.get().strip()
        # Capacidad y existencias son enteros; la especialidad es texto.
        if tipo in ("Sala", "Equipo"):
            try:
                detalle = int(detalle)
            except ValueError as exc:
                raise ValidacionError(
                    "La capacidad o las existencias deben ser un número entero."
                ) from exc
        self.sistema.crear_servicio(
            tipo,
            self.nombre_servicio.get(),
            self.tarifa_servicio.get(),
            detalle,
        )
        self.nombre_servicio.set("")
        self.tarifa_servicio.set("")
        messagebox.showinfo("Servicio creado", "El servicio se agregó correctamente.", parent=self)

    def _crear_reserva(self) -> None:
        """Obtiene IDs del formulario y crea una reserva con los datos requeridos."""
        cliente_id = self.cliente_reserva.get().split(" | ", 1)[0]
        servicio_id = self.servicio_reserva.get().split(" | ", 1)[0]
        if not cliente_id or not servicio_id:
            raise ValidacionError("Seleccione un cliente y un servicio.")
        servicio = self.sistema.buscar_servicio(servicio_id)
        # Los parámetros cambian según el servicio: personas o cantidad de equipos.
        parametros: dict = {}
        if isinstance(servicio, (ReservaSala, AlquilerEquipo)):
            try:
                cantidad = int(self.cantidad_reserva.get())
            except ValueError as exc:
                raise ValidacionError("La cantidad debe ser un entero.") from exc
            clave = "personas" if isinstance(servicio, ReservaSala) else "cantidad"
            parametros[clave] = cantidad
        reserva = self.sistema.crear_reserva(
            cliente_id,
            servicio_id,
            self.duracion_reserva.get(),
            parametros,
        )
        messagebox.showinfo(
            "Reserva creada",
            f"{reserva.identificador} quedó en estado Pendiente.",
            parent=self,
        )

    def _seleccionar_reserva(self, _evento: Any) -> None:
        """Recuerda el ID de la fila seleccionada en la tabla de reservas."""
        seleccion = self.tabla_reservas.selection()
        self.reserva_seleccionada = seleccion[0] if seleccion else None

    def _reserva_actual(self) -> Reserva:
        """Devuelve la reserva seleccionada o indica que falta seleccionarla."""
        if not self.reserva_seleccionada:
            raise ReservaError("Seleccione una reserva de la tabla.")
        return self.sistema.buscar_reserva(self.reserva_seleccionada)

    def _confirmar_reserva(self) -> None:
        """Confirma la reserva seleccionada."""
        reserva = self._reserva_actual()
        reserva.confirmar()
        messagebox.showinfo("Reserva confirmada", reserva.identificador, parent=self)

    def _procesar_reserva(self) -> None:
        """Procesa la reserva seleccionada y muestra el costo calculado."""
        reserva = self._reserva_actual()
        total = reserva.procesar()
        messagebox.showinfo(
            "Reserva procesada", f"Costo total: ${total:.2f}", parent=self
        )

    def _cancelar_reserva(self) -> None:
        """Cancela la reserva seleccionada."""
        reserva = self._reserva_actual()
        reserva.cancelar()
        messagebox.showinfo("Reserva cancelada", reserva.identificador, parent=self)

    def _demostrar(self) -> None:
        """Ejecuta los casos de prueba de demostración y actualiza la bitácora."""
        resultados = ejecutar_demostracion()
        self._mostrar_log()
        messagebox.showinfo(
            "Demostración finalizada",
            f"Se ejecutaron {len(resultados)} operaciones. "
            "Consulte el detalle en la pestaña Bitácora y en software_fj.log.",
            parent=self,
        )

    def _mostrar_log(self) -> None:
        """Lee el archivo de bitácora y muestra su contenido en la pestaña."""
        contenido = ARCHIVO_LOG.read_text(encoding="utf-8") if ARCHIVO_LOG.exists() else ""
        # El widget de texto se habilita temporalmente para actualizarlo.
        self.texto_log.configure(state="normal")
        self.texto_log.delete("1.0", "end")
        self.texto_log.insert("end", contenido or "Todavía no hay eventos registrados.")
        self.texto_log.see("end")
        self.texto_log.configure(state="disabled")

    def _actualizar_vistas(self) -> None:
        """Reconstruye tablas y opciones desplegables desde las listas en memoria."""
        # Se borran las filas anteriores para mostrar el estado más reciente.
        for fila in self.tabla_clientes.get_children():
            self.tabla_clientes.delete(fila)
        # Carga los clientes.
        for cliente in self.sistema.clientes:
            self.tabla_clientes.insert(
                "", "end",
                values=(cliente.identificador, cliente.nombre, cliente.correo, cliente.telefono),
            )
        # Carga los servicios con su tarifa y unidad de tiempo.
        for fila in self.tabla_servicios.get_children():
            self.tabla_servicios.delete(fila)
        for servicio in self.sistema.servicios:
            self.tabla_servicios.insert(
                "",
                "end",
                values=(
                    servicio.identificador,
                    type(servicio).__name__,
                    servicio.nombre,
                    f"${servicio.tarifa:.2f}/{servicio.unidad_duracion}",
                    "Disponible" if servicio.disponible else "No disponible",
                ),
            )
        # Carga las reservas e indica el total cuando ya fueron procesadas.
        for fila in self.tabla_reservas.get_children():
            self.tabla_reservas.delete(fila)
        for reserva in self.sistema.reservas:
            total = f"${reserva.total:.2f}" if reserva.total is not None else "—"
            self.tabla_reservas.insert(
                "",
                "end",
                iid=reserva.identificador,
                values=(
                    reserva.identificador,
                    reserva.cliente.nombre,
                    reserva.servicio.nombre,
                    f"{reserva.duracion:g} {reserva.servicio.unidad_duracion}",
                    reserva.estado,
                    total,
                ),
            )
        # Las listas desplegables muestran ID y nombre, pero conservan el ID al guardar.
        self.combo_clientes["values"] = [
            f"{cliente.identificador} | {cliente.nombre}" for cliente in self.sistema.clientes
        ]
        self.combo_servicios["values"] = [
            f"{servicio.identificador} | {servicio.nombre}"
            for servicio in self.sistema.servicios
        ]
        self._mostrar_log()
