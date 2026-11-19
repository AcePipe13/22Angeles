
import board
import busio
from collections import deque

from adafruit_ads1x15 import ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


class ADS1115:

    def __init__(self):

        # ==================================================
        # I2C
        # ==================================================

        self.i2c = busio.I2C(
            board.SCL,
            board.SDA
        )

        # ==================================================
        # ADS1115
        # ==================================================

        self.ads = ADS.ADS1115(
            self.i2c
        )

        # Ganancia
        self.ads.gain = 1

        # ==================================================
        # JOYSTICK
        # ==================================================

        # A0 = Y
        # A1 = X

        self.joystick_Y = AnalogIn(
            self.ads,
            2
        )

        self.joystick_X = AnalogIn(
            self.ads,
            1
        )

        # ==================================================
        # FILTRO
        # ==================================================

        # Número de muestras utilizadas
        self.numero_muestras = 10

        self.buffer_x = deque(
            maxlen=self.numero_muestras
        )

        self.buffer_y = deque(
            maxlen=self.numero_muestras
        )


    # ======================================================
    # ACTUALIZAR
    # ======================================================

    def update(self):

        # --------------------------------------------------
        # Lectura actual
        # --------------------------------------------------

        x = self.joystick_X.voltage
        y = self.joystick_Y.voltage

        adc_x = self.joystick_X.value
        adc_y = self.joystick_Y.value


        # --------------------------------------------------
        # Guardar muestras
        # --------------------------------------------------

        self.buffer_x.append(adc_x)
        self.buffer_y.append(adc_y)


        # --------------------------------------------------
        # Promedio
        # --------------------------------------------------

        adc_x_filtrado = sum(
            self.buffer_x
        ) / len(self.buffer_x)

        adc_y_filtrado = sum(
            self.buffer_y
        ) / len(self.buffer_y)


        # --------------------------------------------------
        # Convertir nuevamente a voltaje
        # --------------------------------------------------

        # ADS1115 gain = 1
        #
        # 1 cuenta ≈ 125 uV
        #
        # Pero usamos la conversión del ADS1115
        # para mantener el mismo comportamiento.

        x_filtrado = (
            adc_x_filtrado
            * 0.125
            / 1000
        )

        y_filtrado = (
            adc_y_filtrado
            * 0.125
            / 1000
        )


        return (
            x_filtrado,
            y_filtrado,
            int(adc_x_filtrado),
            int(adc_y_filtrado)
        )


    # ======================================================
    # CERRAR
    # ======================================================

    def close(self):

        pass

