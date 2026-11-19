
import time
import threading
import statistics
import tkinter as tk

from collections import deque

import board
import busio

from adafruit_bus_device.i2c_device import I2CDevice


# =====================================================
# CONFIGURACION GENERAL
# =====================================================

ADDRESS = 0x57

SAMPLE_RATE = 100

FINGER_THRESHOLD = 20000

MIN_BPM = 45
MAX_BPM = 150

# 4 intervalos = 5 pulsos
INTERVALOS_NECESARIOS = 4

# Actualizacion de interfaz
UI_INTERVAL = 100

# Actualizacion de grafica
GRAPH_INTERVAL = 200


# =====================================================
# REGISTROS MAX30102
# =====================================================

REG_FIFO_WR_PTR = 0x04
REG_OVF_COUNTER = 0x05
REG_FIFO_RD_PTR = 0x06
REG_FIFO_DATA = 0x07

REG_FIFO_CONFIG = 0x08
REG_MODE_CONFIG = 0x09
REG_SPO2_CONFIG = 0x0A

REG_LED_RED = 0x0C
REG_LED_IR = 0x0D

REG_PART_ID = 0xFF


# =====================================================
# CLASE MAX30102
# =====================================================

class MAX30102:

    def __init__(self):

        self.lock = threading.Lock()

        self.i2c = busio.I2C(
            board.SCL,
            board.SDA
        )

        self.sensor = I2CDevice(
            self.i2c,
            ADDRESS
        )

        self.reset_variables()

        self.setup()

    # =================================================
    # COMUNICACION I2C
    # =================================================

    def write(self, reg, value):

        with self.sensor as dev:

            dev.write(
                bytes([reg, value])
            )

    def read(self, reg):

        data = bytearray(1)

        with self.sensor as dev:

            dev.write_then_readinto(
                bytes([reg]),
                data
            )

        return data[0]

    # =================================================
    # CONFIGURAR SENSOR
    # =================================================

    def setup(self):

        # Verificar identificacion
        part_id = self.read(REG_PART_ID)

        if part_id != 0x15:

            raise RuntimeError(
                f"MAX30102 no identificado. "
                f"PART ID: 0x{part_id:02X}"
            )

        # Reset
        self.write(REG_MODE_CONFIG, 0x40)

        time.sleep(0.1)

        # FIFO sin promedio
        # Rollover habilitado
        self.write(REG_FIFO_CONFIG, 0x10)

        # 100 Hz
        # Resolucion 18 bits
        # Pulso 411 us
        self.write(REG_SPO2_CONFIG, 0x27)

        # Intensidad LED
        self.write(REG_LED_RED, 0x24)
        self.write(REG_LED_IR, 0x24)

        # Limpiar FIFO
        self.clear_fifo()

        # Activar modo RED + IR
        self.write(REG_MODE_CONFIG, 0x03)

    # =================================================
    # LIMPIAR FIFO
    # =================================================

    def clear_fifo(self):

        self.write(REG_FIFO_WR_PTR, 0)
        self.write(REG_OVF_COUNTER, 0)
        self.write(REG_FIFO_RD_PTR, 0)

    # =================================================
    # REINICIAR VARIABLES
    # =================================================

    def reset_variables(self):

        with self.lock:

            self.bpm = 0
            self.red = 0
            self.ir = 0

            self.dedo = False

            self.dc = None
            self.filtrada = 0

            self.anterior1 = 0
            self.anterior2 = 0

            self.historial = deque(maxlen=100)

            self.intervalos = deque(maxlen=5)

            self.grafica = deque(maxlen=400)

            self.ultimo_pico = None

            self.latidos = 0

            self.muestras = 0

            self.tiempo_muestra = None

            self.estado = "Sin dedo"

    # =================================================
    # LEER FIFO EN BLOQUE
    # =================================================

    def read_fifo(self, cantidad):

        if cantidad <= 0:
            return []

        data = bytearray(cantidad * 6)

        with self.sensor as dev:

            dev.write_then_readinto(
                bytes([REG_FIFO_DATA]),
                data
            )

        muestras = []

        for i in range(cantidad):

            p = i * 6

            red = (
                (data[p] << 16) |
                (data[p + 1] << 8) |
                data[p + 2]
            ) & 0x3FFFF

            ir = (
                (data[p + 3] << 16) |
                (data[p + 4] << 8) |
                data[p + 5]
            ) & 0x3FFFF

            muestras.append((red, ir))

        return muestras

    # =================================================
    # REINICIAR DETECTOR
    # =================================================

    def reset_detector(self):

        self.bpm = 0

        self.dc = None
        self.filtrada = 0

        self.anterior1 = 0
        self.anterior2 = 0

        self.historial.clear()
        self.intervalos.clear()
        self.grafica.clear()

        self.ultimo_pico = None

        self.latidos = 0

        self.muestras = 0

    # =================================================
    # CALCULAR BPM
    # Debe ejecutarse con lock adquirido
    # =================================================

    def calculate_bpm(self, ir, instante):

        # ---------------------------------------------
        # DETECTAR DEDO
        # ---------------------------------------------

        if ir < FINGER_THRESHOLD:

            if self.dedo:

                self.reset_detector()

            self.dedo = False

            self.estado = "Coloque el dedo"

            return 0

        if not self.dedo:

            self.reset_detector()

            self.dedo = True

            self.dc = float(ir)

            self.estado = "Estabilizando señal"

        # ---------------------------------------------
        # ELIMINAR COMPONENTE DC
        # ---------------------------------------------

        self.dc += 0.005 * (
            ir - self.dc
        )

        ac = ir - self.dc

        # ---------------------------------------------
        # FILTRO SUAVIZADO
        # ---------------------------------------------

        self.filtrada += 0.25 * (
            ac - self.filtrada
        )

        señal = self.filtrada

        self.historial.append(señal)

        self.grafica.append(señal)

        self.muestras += 1

        # Esperar ventana inicial
        if len(self.historial) < 80:

            self.anterior2 = self.anterior1
            self.anterior1 = señal

            return self.bpm

        # ---------------------------------------------
        # ESTADISTICAS DE LA SEÑAL
        # ---------------------------------------------

        promedio = (
            sum(self.historial)
            / len(self.historial)
        )

        desviacion = statistics.pstdev(
            self.historial
        )

        amplitud = (
            max(self.historial)
            - min(self.historial)
        )

        # Evitar señal demasiado pequeña
        if amplitud < 120:

            self.anterior2 = self.anterior1
            self.anterior1 = señal

            self.estado = "Señal insuficiente"

            return self.bpm

        # ---------------------------------------------
        # UMBRAL DINAMICO
        # ---------------------------------------------

        umbral = promedio + max(
            35,
            desviacion * 0.65
        )

        # ---------------------------------------------
        # DETECTAR PICO
        # ---------------------------------------------

        pico = (
            self.anterior1 > self.anterior2
            and
            self.anterior1 >= señal
            and
            self.anterior1 > umbral
        )

        if pico:

            tiempo_pico = instante - 0.01

            if self.ultimo_pico is None:

                self.ultimo_pico = tiempo_pico

                self.latidos = 1

            else:

                intervalo = (
                    tiempo_pico - self.ultimo_pico
                )

                # Ignorar picos demasiado cercanos
                if intervalo >= 0.40:

                    bpm_nuevo = 60 / intervalo

                    if (
                        MIN_BPM <= bpm_nuevo
                        <= MAX_BPM
                    ):

                        # Verificar regularidad
                        valido = True

                        if len(self.intervalos) >= 3:

                            mediana = statistics.median(
                                self.intervalos
                            )

                            diferencia = abs(
                                intervalo - mediana
                            )

                            if diferencia > mediana * 0.35:

                                valido = False

                        if valido:

                            self.intervalos.append(
                                intervalo
                            )

                            self.ultimo_pico = tiempo_pico

                            self.latidos = (
                                len(self.intervalos) + 1
                            )

                            # Calcular BPM
                            if len(self.intervalos) >= \
                                    INTERVALOS_NECESARIOS:

                                promedio_intervalos = (
                                    sum(self.intervalos)
                                    / len(self.intervalos)
                                )

                                self.bpm = (
                                    60 / promedio_intervalos
                                )

                                self.estado = (
                                    "Medicion activa"
                                )

                    # Si se pierde un pulso,
                    # iniciar nueva secuencia
                    if intervalo > 1.5:

                        self.intervalos.clear()

                        self.ultimo_pico = tiempo_pico

                        self.latidos = 1

                        self.bpm = 0

                        self.estado = (
                            "Recuperando señal"
                        )

        # ---------------------------------------------
        # GUARDAR SEÑAL ANTERIOR
        # ---------------------------------------------

        self.anterior2 = self.anterior1
        self.anterior1 = señal

        # ---------------------------------------------
        # DETECTAR PERDIDA DE PULSOS
        # ---------------------------------------------

        if self.ultimo_pico is not None:

            if instante - self.ultimo_pico > 2.5:

                self.ultimo_pico = None

                self.intervalos.clear()

                self.latidos = 0

                self.bpm = 0

                self.estado = (
                    "Buscando pulsos"
                )

        if self.bpm == 0 and self.dedo:

            if self.estado not in (
                "Señal insuficiente",
                "Recuperando señal",
                "Buscando pulsos"
            ):

                self.estado = (
                    "Detectando latidos"
                )

        return self.bpm

    # =================================================
    # ACTUALIZAR SENSOR
    # =================================================

    def update(self):

        wr = self.read(REG_FIFO_WR_PTR)
        rd = self.read(REG_FIFO_RD_PTR)

        overflow = self.read(REG_OVF_COUNTER)

        # Si se llena la FIFO, resincronizar
        if overflow > 0:

            self.clear_fifo()

            with self.lock:

                self.reset_detector()

                self.tiempo_muestra = None

                self.estado = (
                    "Recuperando adquisicion"
                )

            return 0

        cantidad = (wr - rd) & 0x1F

        if cantidad == 0:

            with self.lock:
                return self.bpm

        muestras = self.read_fifo(cantidad)

        ahora = time.monotonic()

        periodo = 1.0 / SAMPLE_RATE

        primero = ahora - (
            len(muestras) - 1
        ) * periodo

        with self.lock:

            # Recuperar sincronizacion temporal
            if self.tiempo_muestra is not None:

                if primero <= self.tiempo_muestra:

                    primero = (
                        self.tiempo_muestra + periodo
                    )

                # Si hubo una pausa prolongada
                if primero - self.tiempo_muestra > 0.3:

                    self.reset_detector()

            for i, (red, ir) in enumerate(muestras):

                self.red = red
                self.ir = ir

                instante = primero + i * periodo

                self.tiempo_muestra = instante

                self.calculate_bpm(
                    ir,
                    instante
                )

            return self.bpm

    # =================================================
    # DATOS PARA INTERFAZ
    # =================================================

    def get_data(self):

        with self.lock:

            return {
                "bpm": self.bpm,
                "ir": self.ir,
                "red": self.red,
                "dedo": self.dedo,
                "latidos": self.latidos,
                "estado": self.estado,
                "grafica": list(self.grafica)
            }


# =====================================================
# INTERFAZ TKINTER
# =====================================================

class Interfaz:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "MAX30102 - Monitor Cardiaco"
        )

        self.root.geometry("1100x650")

        self.root.minsize(900, 550)

        self.root.configure(bg="#101827")

        self.sensor = None

        self.activo = False

        self.hilo = None

        self.stop_event = threading.Event()

        self.error = None

        self.ultimo_bpm = 0

        self.ultimo_refresco_bpm = 0

        self.cerrando = False

        # =================================================
        # TITULO
        # =================================================

        titulo = tk.Frame(
            root,
            bg="#101827"
        )

        titulo.pack(
            fill="x",
            pady=(15, 10)
        )

        tk.Label(
            titulo,
            text="MONITOR CARDIACO",
            font=("Arial", 23, "bold"),
            fg="white",
            bg="#101827"
        ).pack()

        tk.Label(
            titulo,
            text="MAX30102 - Raspberry Pi",
            font=("Arial", 12),
            fg="#95A5B5",
            bg="#101827"
        ).pack(pady=5)

        # =================================================
        # BOTONES - SIEMPRE VISIBLES
        # =================================================

        barra_botones = tk.Frame(
            root,
            bg="#101827"
        )

        barra_botones.pack(
            side="bottom",
            fill="x",
            pady=15
        )

        self.boton_iniciar = tk.Button(
            barra_botones,
            text="INICIAR",
            font=("Arial", 14, "bold"),
            bg="#00B894",
            fg="white",
            width=17,
            height=2,
            command=self.iniciar
        )

        self.boton_iniciar.pack(
            side="left",
            expand=True,
            padx=20
        )

        self.boton_detener = tk.Button(
            barra_botones,
            text="DETENER",
            font=("Arial", 14, "bold"),
            bg="#D63031",
            fg="white",
            width=17,
            height=2,
            command=self.detener
        )

        self.boton_detener.pack(
            side="left",
            expand=True,
            padx=20
        )

        # =================================================
        # PANEL PRINCIPAL
        # =================================================

        principal = tk.Frame(
            root,
            bg="#101827"
        )

        principal.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        principal.grid_columnconfigure(
            0,
            weight=1
        )

        principal.grid_columnconfigure(
            1,
            weight=2
        )

        principal.grid_rowconfigure(
            0,
            weight=1
        )

        # =================================================
        # PANEL IZQUIERDO
        # =================================================

        izquierda = tk.Frame(
            principal,
            bg="#1D293B"
        )

        izquierda.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        tk.Label(
            izquierda,
            text="FRECUENCIA CARDIACA",
            font=("Arial", 13, "bold"),
            fg="white",
            bg="#1D293B"
        ).pack(pady=(25, 5))

        self.bpm_label = tk.Label(
            izquierda,
            text="--",
            font=("Arial", 85, "bold"),
            fg="#00E5A0",
            bg="#1D293B"
        )

        self.bpm_label.pack()

        tk.Label(
            izquierda,
            text="BPM",
            font=("Arial", 16),
            fg="white",
            bg="#1D293B"
        ).pack()

        self.estado_label = tk.Label(
            izquierda,
            text="Sensor detenido",
            font=("Arial", 12),
            fg="#FBC531",
            bg="#1D293B"
        )

        self.estado_label.pack(pady=20)

        self.ir_label = tk.Label(
            izquierda,
            text="IR: 0",
            font=("Arial", 13),
            fg="#00E5A0",
            bg="#1D293B"
        )

        self.ir_label.pack(pady=5)

        self.red_label = tk.Label(
            izquierda,
            text="RED: 0",
            font=("Arial", 13),
            fg="#FF7675",
            bg="#1D293B"
        )

        self.red_label.pack(pady=5)

        self.latidos_label = tk.Label(
            izquierda,
            text="Pulsos validos: 0/5",
            font=("Arial", 12),
            fg="white",
            bg="#1D293B"
        )

        self.latidos_label.pack(pady=15)

        # =================================================
        # PANEL DERECHO
        # =================================================

        derecha = tk.Frame(
            principal,
            bg="#1D293B"
        )

        derecha.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 0)
        )

        tk.Label(
            derecha,
            text="SEÑAL INFRARROJA (IR)",
            font=("Arial", 15, "bold"),
            fg="white",
            bg="#1D293B"
        ).pack(pady=20)

        self.canvas = tk.Canvas(
            derecha,
            bg="#182536",
            highlightthickness=0
        )

        self.canvas.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        # =================================================
        # CERRAR
        # =================================================

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.cerrar
        )

        # Actualizacion de interfaz
        self.root.after(
            UI_INTERVAL,
            self.actualizar_interfaz
        )

        # Actualizacion de grafica
        self.root.after(
            GRAPH_INTERVAL,
            self.actualizar_grafica
        )

    # =================================================
    # HILO DE ADQUISICION
    # =================================================

    def adquirir_datos(self):

        try:

            sensor = MAX30102()

            if self.stop_event.is_set():
                return

            self.sensor = sensor

            while not self.stop_event.is_set():

                sensor.update()

                # El hilo se puede interrumpir
                # inmediatamente al detener
                self.stop_event.wait(0.01)

        except Exception as e:

            self.error = str(e)

            self.stop_event.set()

    # =================================================
    # INICIAR
    # =================================================

    def iniciar(self):

        if self.activo:
            return

        if self.hilo is not None:

            if self.hilo.is_alive():
                return

        self.sensor = None

        self.error = None

        self.ultimo_bpm = 0

        self.ultimo_refresco_bpm = 0

        self.stop_event.clear()

        self.activo = True

        self.bpm_label.config(text="--")

        self.estado_label.config(
            text="Conectando sensor...",
            fg="#FBC531"
        )

        self.boton_iniciar.config(
            state="disabled"
        )

        self.hilo = threading.Thread(
            target=self.adquirir_datos,
            daemon=True
        )

        self.hilo.start()

    # =================================================
    # DETENER
    # =================================================

    def detener(self):

        self.activo = False

        self.stop_event.set()

        self.bpm_label.config(text="--")

        self.estado_label.config(
            text="Sensor detenido",
            fg="#FBC531"
        )

    # =================================================
    # ACTUALIZAR INTERFAZ
    # =================================================

    def actualizar_interfaz(self):

        if self.cerrando:
            return

        if not self.activo:

            if (
                self.hilo is None
                or not self.hilo.is_alive()
            ):

                self.boton_iniciar.config(
                    state="normal"
                )

        elif self.error is not None:

            self.activo = False

            self.estado_label.config(
                text=f"Error: {self.error}",
                fg="#FF7675"
            )

        elif self.sensor is not None:

            datos = self.sensor.get_data()

            bpm = datos["bpm"]
            ir = datos["ir"]
            red = datos["red"]

            dedo = datos["dedo"]
            latidos = datos["latidos"]

            estado = datos["estado"]

            # Valores IR y RED
            self.ir_label.config(
                text=f"IR: {ir}"
            )

            self.red_label.config(
                text=f"RED: {red}"
            )

            # Contador
            progreso = min(latidos, 5)

            self.latidos_label.config(
                text=(
                    f"Pulsos validos: "
                    f"{progreso}/5"
                )
            )

            # Estado
            if not dedo:

                self.bpm_label.config(
                    text="--"
                )

                self.estado_label.config(
                    text="Coloque el dedo",
                    fg="#FBC531"
                )

            elif bpm <= 0:

                self.bpm_label.config(
                    text="--"
                )

                self.estado_label.config(
                    text=estado,
                    fg="#FBC531"
                )

            else:

                self.estado_label.config(
                    text="Medicion activa",
                    fg="#00E5A0"
                )

                # Mostrar BPM nuevo cada segundo
                ahora = time.monotonic()

                if (
                    ahora - self.ultimo_refresco_bpm
                    >= 1
                ):

                    self.bpm_label.config(
                        text=str(round(bpm))
                    )

                    self.ultimo_refresco_bpm = ahora

        self.root.after(
            UI_INTERVAL,
            self.actualizar_interfaz
        )

    # =================================================
    # ACTUALIZAR GRAFICA
    # =================================================

    def actualizar_grafica(self):

        if self.cerrando:
            return

        self.canvas.delete("all")

        ancho = self.canvas.winfo_width()
        alto = self.canvas.winfo_height()

        if ancho > 20 and alto > 20:

            # Lineas de referencia
            for fraccion in (0.25, 0.5, 0.75):

                y = alto * fraccion

                self.canvas.create_line(
                    0,
                    y,
                    ancho,
                    y,
                    fill="#34495E",
                    dash=(4, 4)
                )

            if (
                self.sensor is not None
                and self.activo
            ):

                datos = self.sensor.get_data()

                valores = datos["grafica"]

                if len(valores) > 2:

                    minimo = min(valores)
                    maximo = max(valores)

                    rango = max(
                        maximo - minimo,
                        1
                    )

                    # Reducir puntos graficos
                    paso = max(
                        1,
                        len(valores) // 300
                    )

                    valores = valores[::paso]

                    puntos = []

                    total = len(valores)

                    for i, valor in enumerate(valores):

                        x = (
                            i / max(total - 1, 1)
                        ) * ancho

                        y = alto - 15 - (
                            (valor - minimo) / rango
                        ) * (alto - 30)

                        puntos.extend([x, y])

                    if len(puntos) >= 4:

                        self.canvas.create_line(
                            *puntos,
                            fill="#00E5A0",
                            width=2
                        )

        self.root.after(
            GRAPH_INTERVAL,
            self.actualizar_grafica
        )

    # =================================================
    # CERRAR
    # =================================================

    def cerrar(self):

        self.cerrando = True

        self.activo = False

        self.stop_event.set()

        self.root.destroy()


# =====================================================
# PROGRAMA PRINCIPAL
# =====================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = Interfaz(root)

    root.mainloop()

    