import json
import serial
import serial.tools.list_ports

from config import BAUDRATE, SERIAL_TIMEOUT
from gps_data import GPSData


class SerialReceiver:

    def __init__(self):
        self.serial = None

    # ============================================================
    # BUSCAR PUERTO SERIAL
    # ============================================================

    def buscar_puerto(self):

        puertos = list(serial.tools.list_ports.comports())

        if not puertos:
            return None

        print("Puertos seriales encontrados:")

        for puerto in puertos:
            print(
                f"  {puerto.device} - "
                f"{puerto.description}"
            )

        # Por ahora usamos el primer puerto encontrado
        return puertos[0].device

    # ============================================================
    # CONECTAR CON ESP32
    # ============================================================

    def conectar(self):

        puerto = self.buscar_puerto()

        if puerto is None:
            print("No se encontro ningun puerto serial.")
            return False

        try:
            self.serial = serial.Serial(
                port=puerto,
                baudrate=BAUDRATE,
                timeout=SERIAL_TIMEOUT,
            )

            print()
            print("==============================")
            print("     ESP32 CONECTADA")
            print("==============================")
            print(f"Puerto:   {puerto}")
            print(f"Baudrate: {BAUDRATE}")
            print()

            return True

        except serial.SerialException as error:

            print("Error abriendo puerto serial:")
            print(error)

            return False

    # ============================================================
    # LEER GPS
    # ============================================================

    def leer_gps(self):

        if self.serial is None:
            return None

        try:

            linea = self.serial.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            if not linea:
                return None

            # Ignorar mensajes de depuracion de la ESP32
            # y procesar solamente JSON
            if not (
                linea.startswith("{")
                and linea.endswith("}")
            ):
                return None

            datos_json = json.loads(linea)

            gps = GPSData.from_json(datos_json)

            return gps

        except json.JSONDecodeError:
            return None

        except serial.SerialException as error:

            print(f"Error serial: {error}")

            return None

    # ============================================================
    # CERRAR PUERTO
    # ============================================================

    def cerrar(self):

        if self.serial is not None:

            if self.serial.is_open:
                self.serial.close()

            print()
            print("Puerto serial cerrado.")