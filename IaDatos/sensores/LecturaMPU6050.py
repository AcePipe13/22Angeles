import math
import time

import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice


# ==========================================================
# MPU6050
# ==========================================================

ADDRESS = 0x68

WHO_AM_I = 0x75
PWR_MGMT_1 = 0x6B

ACCEL_XOUT_H = 0x3B


class MPU6050:

    def __init__(self):

        # --------------------------------------------------
        # I2C
        # --------------------------------------------------

        self.i2c = busio.I2C(
            board.SCL,
            board.SDA
        )

        self.sensor = I2CDevice(
            self.i2c,
            ADDRESS
        )

        # --------------------------------------------------
        # Despertar MPU6050
        # --------------------------------------------------

        self.write_register(
            PWR_MGMT_1,
            0x00
        )

        time.sleep(0.1)

        # --------------------------------------------------
        # Variables para filtro
        # --------------------------------------------------

        self.angle_x = 0.0
        self.angle_y = 0.0

        self.last_time = time.monotonic()


    # ======================================================
    # ESCRIBIR REGISTRO
    # ======================================================

    def write_register(self, register, value):

        with self.sensor as dev:

            dev.write(
                bytes([
                    register,
                    value
                ])
            )


    # ======================================================
    # LEER REGISTROS
    # ======================================================

    def read_registers(self, register, length):

        data = bytearray(length)

        with self.sensor as dev:

            dev.write_then_readinto(
                bytes([register]),
                data
            )

        return data


    # ======================================================
    # CONVERTIR 2 BYTES A ENTERO CON SIGNO
    # ======================================================

    def signed_value(self, high, low):

        value = (high << 8) | low

        if value >= 32768:

            value -= 65536

        return value


    # ======================================================
    # LEER ACELERÓMETRO
    # ======================================================

    def read_accelerometer(self):

        data = self.read_registers(
            ACCEL_XOUT_H,
            6
        )

        ax_raw = self.signed_value(
            data[0],
            data[1]
        )

        ay_raw = self.signed_value(
            data[2],
            data[3]
        )

        az_raw = self.signed_value(
            data[4],
            data[5]
        )

        # --------------------------------------------------
        # MPU6050 configurado por defecto:
        #
        # ±2g
        # 16384 LSB/g
        # --------------------------------------------------

        ax = ax_raw / 16384.0
        ay = ay_raw / 16384.0
        az = az_raw / 16384.0

        return ax, ay, az


    # ======================================================
    # CALCULAR INCLINACIÓN
    # ======================================================

    def read_inclinacion(self):

        ax, ay, az = self.read_accelerometer()

        # --------------------------------------------------
        # Ángulo X
        # --------------------------------------------------

        angle_x = math.degrees(
            math.atan2(
                ay,
                math.sqrt(
                    ax * ax +
                    az * az
                )
            )
        )

        # --------------------------------------------------
        # Ángulo Y
        # --------------------------------------------------

        angle_y = math.degrees(
            math.atan2(
                -ax,
                math.sqrt(
                    ay * ay +
                    az * az
                )
            )
        )

        return angle_x, angle_y


    # ======================================================
    # ACTUALIZAR
    # ======================================================

    def update(self):

        angle_x, angle_y = self.read_inclinacion()

        # --------------------------------------------------
        # Filtro suave
        # --------------------------------------------------

        alpha = 0.2

        self.angle_x = (
            alpha * angle_x +
            (1 - alpha) * self.angle_x
        )

        self.angle_y = (
            alpha * angle_y +
            (1 - alpha) * self.angle_y
        )

        return self.angle_x, self.angle_y