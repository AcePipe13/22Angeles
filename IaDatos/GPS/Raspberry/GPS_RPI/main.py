import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from serial_receiver import SerialReceiver
from interface.main_window import MainWindow


def main():

    # ========================================================
    # CREAR APLICACION
    # ========================================================

    app = QApplication(sys.argv)

    # ========================================================
    # CONECTAR ESP32
    # ========================================================

    receptor = SerialReceiver()

    if not receptor.conectar():
        print("No fue posible conectar con la ESP32.")
        return

    # ========================================================
    # CREAR VENTANA
    # ========================================================

    ventana = MainWindow()
    ventana.show()

    # ========================================================
    # LEER SERIAL PERIODICAMENTE
    # ========================================================

    def actualizar():

        gps = receptor.leer_gps()

        if gps is not None:

            ventana.actualizar_gps(gps)

            print(
                f"GPS -> "
                f"{gps.lat}, "
                f"{gps.lon} | "
                f"Paquete {gps.packet}"
            )

    # Revisar serial cada 50 ms
    timer = QTimer()

    timer.timeout.connect(actualizar)

    timer.start(50)

    # ========================================================
    # EJECUTAR INTERFAZ
    # ========================================================

    resultado = app.exec()

    receptor.cerrar()

    sys.exit(resultado)


if __name__ == "__main__":
    main()