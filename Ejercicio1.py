"""Sistema de gestión de clientes, servicios y reservas para Software FJ.

La aplicación utiliza objetos y listas en memoria; no necesita una base de datos.
Al ejecutar el archivo se abre la interfaz gráfica. También se puede ejecutar
con la opción --demo para probar las operaciones desde la consola.
"""

import sys

from excepciones import ARCHIVO_LOG
from sistema import ejecutar_demostracion


def main() -> None:
    """Select between the graphical application and the console demo."""
    if "--demo" in sys.argv:
        # Este modo permite comprobar el flujo sin abrir la interfaz gráfica.
        resultados = ejecutar_demostracion()
        print("Demostración de Software FJ:")
        for indice, resultado in enumerate(resultados, start=1):
            print(f"{indice:02d}. {resultado}")
        print(f"\nLog: {ARCHIVO_LOG}")
        return
    # Se importa aquí para que el modo --demo funcione sin requerir tkinter.
    from interfaz import Application
    Application().mainloop()


if __name__ == '__main__':
    # Evita abrir la ventana si este archivo se importa desde otro módulo.
    main()
