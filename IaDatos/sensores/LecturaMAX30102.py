import time
import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice


ADDRESS = 0x57

REG_FIFO_WR_PTR = 0x04
REG_OVF_COUNTER = 0x05
REG_FIFO_RD_PTR = 0x06
REG_FIFO_DATA = 0x07

REG_FIFO_CONFIG = 0x08
REG_MODE_CONFIG = 0x09
REG_SPO2_CONFIG = 0x0A

REG_LED_RED = 0x0C
REG_LED_IR = 0x0D


class MAX30102:

    def __init__(self):

        # I2C
        self.i2c = busio.I2C(
            board.SCL,
            board.SDA
        )

        self.sensor = I2CDevice(
            self.i2c,
            ADDRESS
        )

        self.setup()

        # Variables para BPM
        self.buffer = []
        self.last_peak = None
        self.beats = []
        self.bpm = 0
        self.last_value = 0
        self.last_beat_time = 0

    # ======================================================
    # I2C
    # ======================================================

    def write_register(self, reg, value):

        with self.sensor as dev:
            dev.write(
                bytes([reg, value])
            )


    def read_register(self, reg):

        data = bytearray(1)

        with self.sensor as dev:

            dev.write_then_readinto(
                bytes([reg]),
                data
            )

        return data[0]


    # ======================================================
    # LEER FIFO
    # ======================================================

    def read_fifo(self):

        data = bytearray(6)

        with self.sensor as dev:

            dev.write_then_readinto(
                bytes([REG_FIFO_DATA]),
                data
            )

        red = (
            (data[0] << 16) |
            (data[1] << 8) |
            data[2]
        ) & 0x3FFFF

        ir = (
            (data[3] << 16) |
            (data[4] << 8) |
            data[5]
        ) & 0x3FFFF

        return red, ir


    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    def setup(self):

        # Reset
        self.write_register(
            REG_MODE_CONFIG,
            0x40
        )

        time.sleep(0.1)

        # Limpiar FIFO
        self.write_register(
            REG_FIFO_WR_PTR,
            0x00
        )

        self.write_register(
            REG_OVF_COUNTER,
            0x00
        )

        self.write_register(
            REG_FIFO_RD_PTR,
            0x00
        )

        # FIFO
        self.write_register(
            REG_FIFO_CONFIG,
            0x4F
        )

        # RED + IR
        self.write_register(
            REG_MODE_CONFIG,
            0x03
        )

        # 100 Hz
        self.write_register(
            REG_SPO2_CONFIG,
            0x27
        )

        # LEDs
        self.write_register(
            REG_LED_RED,
            0x24
        )

        self.write_register(
            REG_LED_IR,
            0x24
        )


    # ======================================================
    # CALCULAR BPM
    # ======================================================

    def calculate_bpm(self, ir):

        now = time.monotonic()

        # -----------------------------------------------
        # Detectar dedo
        # -----------------------------------------------

        FINGER_THRESHOLD = 20000

        if ir < FINGER_THRESHOLD:

            self.buffer.clear()
            self.beats.clear()

            self.bpm = 0

            self.last_peak = None
            self.last_value = 0

            return 0


        # -----------------------------------------------
        # Guardar señal
        # -----------------------------------------------

        self.buffer.append(ir)

        if len(self.buffer) > 100:

            self.buffer.pop(0)


        if len(self.buffer) < 20:

            return self.bpm


        # -----------------------------------------------
        # Media
        # -----------------------------------------------

        mean = sum(self.buffer) / len(self.buffer)


        # -----------------------------------------------
        # Desviación estándar
        # -----------------------------------------------

        variance = sum(
            (x - mean) ** 2
            for x in self.buffer
        ) / len(self.buffer)

        std = variance ** 0.5


        # -----------------------------------------------
        # Umbral
        # -----------------------------------------------

        threshold = mean + std * 0.35


        # -----------------------------------------------
        # Detectar latido
        # -----------------------------------------------

        if ir > threshold and self.last_value <= threshold:

            if now - self.last_beat_time > 0.35:

                if self.last_peak is not None:

                    intervalo = now - self.last_peak

                    if 0.35 < intervalo < 1.5:

                        nuevo_bpm = 60 / intervalo

                        if 40 <= nuevo_bpm <= 180:

                            self.beats.append(
                                nuevo_bpm
                            )

                            if len(self.beats) > 3:

                                self.beats.pop(0)

                            self.bpm = (
                                sum(self.beats)
                                / len(self.beats)
                            )

                self.last_peak = now
                self.last_beat_time = now


        self.last_value = ir

        return self.bpm


    # ======================================================
    # ACTUALIZAR SENSOR
    # ======================================================

    def update(self):

        wr_ptr = self.read_register(
            REG_FIFO_WR_PTR
        )

        rd_ptr = self.read_register(
            REG_FIFO_RD_PTR
        )

        samples = (wr_ptr - rd_ptr) & 0x1F

        if samples == 0:

            return self.bpm

        bpm = self.bpm

        for _ in range(min(samples, 10)):

            red, ir = self.read_fifo()

            bpm = self.calculate_bpm(ir)

        return bpm