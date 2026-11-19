from collections import deque

from adafruit_extended_bus import ExtendedI2C
from adafruit_ads1x15 import ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


class ADS1115:

    def __init__(self):

        # ==================================================
        # I2C-0 DE RASPBERRY PI 5
        # ==================================================

        self.i2c = ExtendedI2C(0)

        # ==================================================
        # ADS1115
        # ==================================================

        self.ads = ADS.ADS1115(
            self.i2c,
            address=0x48
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
            0
        )

        self.joystick_X = AnalogIn(
            self.ads,
            1
        )

        # ==================================================
        # FILTRO
        # ==================================================

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

        # Lectura ADC
        adc_x = self.joystick_X.value
        adc_y = self.joystick_Y.value

        # Guardar muestras
        self.buffer_x.append(adc_x)
        self.buffer_y.append(adc_y)

        # Promedio
        adc_x_filtrado = (
            sum(self.buffer_x)
            / len(self.buffer_x)
        )

        adc_y_filtrado = (
            sum(self.buffer_y)
            / len(self.buffer_y)
        )

        # Conversión a voltaje
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

        try:
            self.i2c.close()
        except:
            pass