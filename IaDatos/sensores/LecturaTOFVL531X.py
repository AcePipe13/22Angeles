
import time
import board
import busio
import adafruit_vl53l1x


class VL53L1X:

    def __init__(self):

        # ==================================================
        # I2C
        # ==================================================

        self.i2c = busio.I2C(
            board.SCL,
            board.SDA
        )

        # ==================================================
        # SENSOR
        # ==================================================

        self.sensor = adafruit_vl53l1x.VL53L1X(
            self.i2c
        )

        # ==================================================
        # CONFIGURACIÓN
        # ==================================================

        # 2 = LONG
        self.sensor.distance_mode = 2

        # 50 ms
        self.sensor.timing_budget = 50

        # Iniciar medición continua
        self.sensor.start_ranging()


    # ======================================================
    # ACTUALIZAR
    # ======================================================

    def update(self):

        try:

            # Leer solamente cuando haya un dato nuevo
            if self.sensor.data_ready:

                distancia = self.sensor.distance

                # MUY IMPORTANTE:
                # limpiar la interrupción después de leer
                self.sensor.clear_interrupt()

                return distancia

            return None

        except Exception as e:

            print("Error VL53L1X:", e)

            return None


    # ======================================================
    # CERRAR
    # ======================================================

    def close(self):

        try:
            self.sensor.stop_ranging()
        except:
            pass
