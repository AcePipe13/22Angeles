import time

from smbus2 import SMBus, i2c_msg
from gpiozero import DigitalOutputDevice

import adafruit_vl53l1x


# =========================================================
# ADAPTADOR I2C PARA USAR /dev/i2c-0
# =========================================================

class I2C0:

    def __init__(self):

        self.bus = SMBus(0)

    def try_lock(self):

        return True

    def unlock(self):

        pass

    def scan(self):

        dispositivos = []

        for direccion in range(0x03, 0x78):

            try:

                mensaje = i2c_msg.write(
                    direccion,
                    [0]
                )

                self.bus.i2c_rdwr(mensaje)

                dispositivos.append(direccion)

            except Exception:

                pass

        return dispositivos

    def writeto(
        self,
        address,
        buffer,
        *,
        start=0,
        end=None
    ):

        if end is None:
            end = len(buffer)

        datos = list(
            buffer[start:end]
        )

        mensaje = i2c_msg.write(
            address,
            datos
        )

        self.bus.i2c_rdwr(mensaje)

    def readfrom_into(
        self,
        address,
        buffer,
        *,
        start=0,
        end=None
    ):

        if end is None:
            end = len(buffer)

        cantidad = end - start

        mensaje = i2c_msg.read(
            address,
            cantidad
        )

        self.bus.i2c_rdwr(mensaje)

        datos = list(mensaje)

        for i, valor in enumerate(datos):

            buffer[start + i] = valor

    def write_then_readinto(
        self,
        address,
        buffer_out,
        buffer_in,
        *,
        out_start=0,
        out_end=None,
        in_start=0,
        in_end=None
    ):

        if out_end is None:
            out_end = len(buffer_out)

        if in_end is None:
            in_end = len(buffer_in)

        datos_salida = list(
            buffer_out[out_start:out_end]
        )

        cantidad_entrada = (
            in_end - in_start
        )

        mensaje_write = i2c_msg.write(
            address,
            datos_salida
        )

        mensaje_read = i2c_msg.read(
            address,
            cantidad_entrada
        )

        self.bus.i2c_rdwr(
            mensaje_write,
            mensaje_read
        )

        datos_entrada = list(
            mensaje_read
        )

        for i, valor in enumerate(
            datos_entrada
        ):

            buffer_in[
                in_start + i
            ] = valor

    def close(self):

        self.bus.close()


# =========================================================
# CLASE DE LOS 4 VL53L1X
# =========================================================

class VL53L1X_4Sensores:

    # -----------------------------------------------------
    # BUS
    # -----------------------------------------------------

    DIRECCION_INICIAL = 0x29

    DIRECCIONES = [
        0x30,
        0x31,
        0x32,
        0x33
    ]

    # -----------------------------------------------------
    # XSHUT
    # -----------------------------------------------------

    PINES_XSHUT = [
        17,
        27,
        22,
        5
    ]


    # =====================================================
    # INICIALIZACIÓN
    # =====================================================

    def __init__(self):

        print()
        print("======================================")
        print("   INICIALIZANDO 4 VL53L1X")
        print("   BUS I2C-0")
        print("======================================")
        print()


        # -------------------------------------------------
        # I2C-0
        # -------------------------------------------------

        self.i2c = I2C0()


        # -------------------------------------------------
        # XSHUT
        # -------------------------------------------------

        self.xshut = []

        for pin in self.PINES_XSHUT:

            salida = DigitalOutputDevice(
                pin,
                active_high=True,
                initial_value=False
            )

            self.xshut.append(salida)


        # -------------------------------------------------
        # Apagar todos
        # -------------------------------------------------

        self.apagar_todos()

        time.sleep(0.5)


        # -------------------------------------------------
        # Lista de sensores
        # -------------------------------------------------

        self.sensores = []


        # -------------------------------------------------
        # Configurar sensores
        # -------------------------------------------------

        self.configurar()


    # =====================================================
    # APAGAR TODOS
    # =====================================================

    def apagar_todos(self):

        for sensor in self.xshut:

            sensor.off()

        time.sleep(0.5)


    # =====================================================
    # CONFIGURAR LOS 4 SENSORES
    # =====================================================

    def configurar(self):

        for i in range(4):

            print(
                f"Configurando Sensor {i + 1}..."
            )

            # ---------------------------------------------
            # Encender sensor
            # ---------------------------------------------

            self.xshut[i].on()

            time.sleep(0.5)


            # ---------------------------------------------
            # Crear sensor en 0x29
            # ---------------------------------------------

            try:

                sensor = adafruit_vl53l1x.VL53L1X(
                    self.i2c,
                    address=0x29
                )

                print(
                    f"  Sensor {i + 1} detectado en 0x29"
                )

            except Exception as e:

                print(
                    f"  ERROR detectando Sensor "
                    f"{i + 1}: {e}"
                )

                continue


            # ---------------------------------------------
            # Cambiar dirección
            # ---------------------------------------------

            nueva_direccion = (
                self.DIRECCIONES[i]
            )

            if i < 4:

                sensor.set_address(
                    nueva_direccion
                )

                print(
                    f"  Dirección: "
                    f"0x29 -> "
                    f"{hex(nueva_direccion)}"
                )


            # ---------------------------------------------
            # Configurar modo de distancia
            # ---------------------------------------------

            sensor.distance_mode = 2

            # 3 = LONG RANGE


            # ---------------------------------------------
            # Tiempo de medición
            # ---------------------------------------------

            sensor.timing_budget = 50


            # ---------------------------------------------
            # Iniciar medición
            # ---------------------------------------------

            sensor.start_ranging()


            # ---------------------------------------------
            # Guardar sensor
            # ---------------------------------------------

            self.sensores.append(
                sensor
            )

            time.sleep(0.2)


        print()
        print(
            "Sensores configurados:",
            len(self.sensores)
        )
        print()


    # =====================================================
    # LEER UN SENSOR
    # =====================================================

    def leer_sensor(self, numero):

        if numero >= len(self.sensores):

            return None


        sensor = self.sensores[numero]


        try:

            if sensor.data_ready:

                distancia = sensor.distance

                sensor.clear_interrupt()

                return distancia

            else:

                return None


        except Exception as e:

            print(
                f"Error Sensor {numero + 1}: "
                f"{e}"
            )

            return None


    # =====================================================
    # LEER LOS 4 SENSORES
    # =====================================================

    def leer_todos(self):

        datos = []

        for i in range(4):

            distancia = self.leer_sensor(i)

            datos.append(
                distancia
            )

        return datos


    # =====================================================
    # CERRAR
    # =====================================================

    def cerrar(self):

        print(
            "Deteniendo sensores..."
        )


        for sensor in self.sensores:

            try:

                sensor.stop_ranging()

            except Exception:

                pass


        for pin in self.xshut:

            pin.off()
            pin.close()


        self.i2c.close()


        print(
            "Sensores apagados."
        )