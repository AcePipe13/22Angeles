
import tkinter as tk
from tkinter import ttk
from collections import deque
import serial
import serial.tools.list_ports
import math
import time

from LecturaADCJoystick import ADS1115


# ==========================================================
# CONFIGURACION GENERAL
# ==========================================================

RPM_MAX = 120
RANGO_ADC = 13000

ZONA_MUERTA = 0.18

BAUDIOS = 57600

PERIODO_MS = 10
PERIODO_VISUAL = 0.05
MUESTRAS_ADC = 3

# ==========================================================
# CURVA Y RAMPAS
# ==========================================================

CURVA_JOYSTICK = 2.0

ACELERACION_RPM_S = 24.0
DESACELERACION_RPM_S = 120.0

TIEMPO_MAX_ACTUALIZACION = 0.5

# ==========================================================
# MODOS
# ==========================================================

MODO_MANUAL = "MANUAL"
MODO_SENCILLO = "ASISTIDO SENCILLO"
MODO_DIRECCION = "ASISTIDO CON DIRECCION"

MODOS = [
    MODO_MANUAL,
    MODO_SENCILLO,
    MODO_DIRECCION
]

# ==========================================================
# VELOCIDADES ASISTIDAS
# ==========================================================

VELOCIDADES_REGION = (17, 40, 90)

LIMITE_REGION_1 = 0.35
LIMITE_REGION_2 = 0.68

HISTERESIS_REGION = 0.04

# Cambio de sector estable durante 100 ms
TIEMPO_CAMBIO_SECTOR = 0.10

# ==========================================================
# ASISTIDO CON DIRECCION
# ==========================================================

# Limites angulares expresados en grados.
# 0 grados = derecha
# 90 grados = adelante
# 180 grados = izquierda
# 270 grados = atras
#
# Adelante: 25 a 155
# Izquierda: 155 a 205
# Atras: 205 a 335
# Derecha: 335 a 25

# Subregiones delanteras
# Desde la derecha hacia la izquierda

LIMITES_ADELANTE = [
    25, 45, 65, 82,
    98, 115, 135, 155
]

# Intensidad de correccion
# 0 = recto
# 1 = ligera
# 2 = media
# 3 = pronunciada

CORRECCIONES = {
    0: 0.00,
    1: 0.18,
    2: 0.38,
    3: 0.60
}

# ==========================================================
# COLORES
# ==========================================================

FONDO = "#17202A"
PANEL = "#212F3D"

AZUL = "#3498DB"
VERDE = "#2ECC71"
ROJO = "#E74C3C"
AMARILLO = "#F1C40F"

BLANCO = "#FFFFFF"
GRIS = "#566573"


# ==========================================================
# INTERFAZ PRINCIPAL
# ==========================================================

class InterfazJoystick:

    def __init__(self, root):

        self.root = root
        self.root.title("Control de Motores - Joystick")

        self.ancho = root.winfo_screenwidth()
        self.alto = root.winfo_screenheight()

        self.root.geometry(
            f"{self.ancho}x{self.alto}+0+0"
        )

        self.root.configure(bg=FONDO)

        # ==================================================
        # ADC
        # ==========================================================

        self.adc = ADS1115()

        self.adc.ads.data_rate = 860

        self.adc.numero_muestras = MUESTRAS_ADC

        self.adc.buffer_x = deque(
            maxlen=MUESTRAS_ADC
        )

        self.adc.buffer_y = deque(
            maxlen=MUESTRAS_ADC
        )

        self.centro_x = None
        self.centro_y = None

        self.rango = RANGO_ADC

        self.pos_x = 0.0
        self.pos_y = 0.0

        # ==================================================
        # ESTADO DEL MODO
        # ==========================================================

        self.modo = MODO_MANUAL

        self.region_actual = 0
        self.direccion_actual = "CENTRO"

        self.sector_actual = "CENTRO"
        self.sector_pendiente = None
        self.tiempo_sector = 0.0

        # ==================================================
        # ESP32
        # ==========================================================

        self.esp32 = None
        self.conectado = False
        self.control_activo = False
        self.cerrando = False

        self.objetivo_izq = 0.0
        self.objetivo_der = 0.0

        self.rpm_izq = 0.0
        self.rpm_der = 0.0

        self.tiempo_anterior = time.monotonic()
        self.tiempo_visual = time.monotonic()

        # ==================================================
        # PANTALLA ADAPTABLE
        # ==========================================================

        self.escala = min(
            self.ancho / 1024,
            self.alto / 600
        )

        def px(valor):
            return max(1, int(valor * self.escala))

        self.px = px

        # ==================================================
        # TITULO
        # ==========================================================

        tk.Label(
            root,
            text="CONTROL DE MOTORES - JOYSTICK",
            font=("Arial", px(20), "bold"),
            bg=FONDO,
            fg=BLANCO
        ).pack(pady=(px(6), px(3)))

        # ==================================================
        # AREA PRINCIPAL
        # ==========================================================

        principal = tk.Frame(
            root,
            bg=FONDO
        )

        principal.pack(
            fill="both",
            expand=True,
            padx=px(12)
        )

        principal.grid_columnconfigure(0, weight=1)
        principal.grid_columnconfigure(1, weight=1)
        principal.grid_rowconfigure(0, weight=1)

        # ==================================================
        # PANEL IZQUIERDO
        # ==========================================================

        panel_izq = tk.Frame(
            principal,
            bg=PANEL
        )

        panel_izq.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=px(5),
            pady=px(3)
        )

        tk.Label(
            panel_izq,
            text="POSICION DEL JOYSTICK",
            font=("Arial", px(13), "bold"),
            fg=BLANCO,
            bg=PANEL
        ).pack(pady=px(4))

        # ==================================================
        # CANVAS
        # ==========================================================

        self.tamano = px(260)

        self.canvas = tk.Canvas(
            panel_izq,
            width=self.tamano,
            height=self.tamano,
            bg=PANEL,
            highlightthickness=0
        )

        self.canvas.pack()

        self.cx = self.tamano / 2
        self.cy = self.tamano / 2

        self.radio = self.tamano * 0.39
        self.radio_punto = px(9)

        self.radio_muerto = (
            self.radio * ZONA_MUERTA
        )

        # Elementos de cada modo
        self.elementos_manual = []
        self.elementos_sencillo = []
        self.elementos_direccion = []

        self.arcos_sencillo = {}
        self.arcos_direccion = {}

        # ==================================================
        # DIBUJAR MODOS
        # ==========================================================

        self.crear_joystick_manual()
        self.crear_joystick_sencillo()
        self.crear_joystick_direccion()

        # Punto movil
        self.punto = self.canvas.create_oval(
            self.cx - self.radio_punto,
            self.cy - self.radio_punto,
            self.cx + self.radio_punto,
            self.cy + self.radio_punto,
            fill=VERDE,
            outline=BLANCO
        )

        self.mostrar_modo_visual()

        # ==================================================
        # DATOS ADC
        # ==========================================================

        self.label_voltaje = tk.Label(
            panel_izq,
            text="X: 0.000 V     Y: 0.000 V",
            font=("Arial", px(11)),
            fg=BLANCO,
            bg=PANEL
        )

        self.label_voltaje.pack(pady=px(2))

        self.label_adc = tk.Label(
            panel_izq,
            text="ADC X: 0     ADC Y: 0",
            font=("Arial", px(11)),
            fg="#5DADE2",
            bg=PANEL
        )

        self.label_adc.pack(pady=px(2))

        self.label_posicion = tk.Label(
            panel_izq,
            text="X: +0.00     Y: +0.00",
            font=("Arial", px(11)),
            fg=BLANCO,
            bg=PANEL
        )

        self.label_posicion.pack(pady=px(2))

        # ==================================================
        # PANEL DERECHO
        # ==========================================================

        panel_der = tk.Frame(
            principal,
            bg=PANEL
        )

        panel_der.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=px(5),
            pady=px(3)
        )

        tk.Label(
            panel_der,
            text="VELOCIDAD DE LOS MOTORES",
            font=("Arial", px(13), "bold"),
            fg=BLANCO,
            bg=PANEL
        ).pack(pady=px(6))

        tk.Label(
            panel_der,
            text="MOTOR IZQUIERDO",
            font=("Arial", px(12), "bold"),
            fg=BLANCO,
            bg=PANEL
        ).pack(pady=(px(4), 0))

        self.label_rpm_izq = tk.Label(
            panel_der,
            text="0 RPM",
            font=("Arial", px(30), "bold"),
            fg=VERDE,
            bg=PANEL
        )

        self.label_rpm_izq.pack(pady=px(3))

        tk.Label(
            panel_der,
            text="MOTOR DERECHO",
            font=("Arial", px(12), "bold"),
            fg=BLANCO,
            bg=PANEL
        ).pack(pady=(px(6), 0))

        self.label_rpm_der = tk.Label(
            panel_der,
            text="0 RPM",
            font=("Arial", px(30), "bold"),
            fg=VERDE,
            bg=PANEL
        )

        self.label_rpm_der.pack(pady=px(3))

        # Region actual
        self.label_region = tk.Label(
            panel_der,
            text="CONTROL PROPORCIONAL",
            font=("Arial", px(11), "bold"),
            fg=AMARILLO,
            bg=PANEL
        )

        self.label_region.pack(pady=px(5))

        # Boton cambiar modo
        self.boton_modo = tk.Button(
            panel_der,
            text="MODO: MANUAL",
            command=self.cambiar_modo,
            font=("Arial", px(12), "bold"),
            bg=AZUL,
            fg=BLANCO,
            width=25,
            height=2
        )

        self.boton_modo.pack(pady=px(4))

        # ==================================================
        # PANEL INFERIOR
        # ==========================================================

        inferior = tk.Frame(
            root,
            bg=FONDO
        )

        inferior.pack(
            fill="x",
            padx=px(15),
            pady=px(3)
        )

        serial_frame = tk.Frame(
            inferior,
            bg=FONDO
        )

        serial_frame.pack(pady=px(2))

        tk.Label(
            serial_frame,
            text="ESP32:",
            font=("Arial", px(11), "bold"),
            fg=BLANCO,
            bg=FONDO
        ).grid(row=0, column=0, padx=px(5))

        self.puerto = ttk.Combobox(
            serial_frame,
            width=17,
            state="readonly",
            font=("Arial", px(11))
        )

        self.puerto.grid(
            row=0,
            column=1,
            padx=px(5)
        )

        tk.Button(
            serial_frame,
            text="BUSCAR",
            command=self.buscar_puertos,
            bg=GRIS,
            fg=BLANCO,
            font=("Arial", px(10), "bold"),
            width=9
        ).grid(row=0, column=2, padx=px(5))

        self.boton_conectar = tk.Button(
            serial_frame,
            text="CONECTAR",
            command=self.conectar,
            bg=AZUL,
            fg=BLANCO,
            font=("Arial", px(10), "bold"),
            width=12
        )

        self.boton_conectar.grid(
            row=0,
            column=3,
            padx=px(5)
        )

        # ==================================================
        # BOTONES PRINCIPALES
        # ==========================================================

        botones = tk.Frame(
            inferior,
            bg=FONDO
        )

        botones.pack(pady=px(5))

        self.boton_start = tk.Button(
            botones,
            text="START",
            command=self.start,
            bg=VERDE,
            fg="black",
            font=("Arial", px(13), "bold"),
            width=12,
            height=2
        )

        self.boton_start.grid(
            row=0, column=0, padx=px(10)
        )

        self.boton_stop = tk.Button(
            botones,
            text="STOP",
            command=self.stop,
            bg=ROJO,
            fg=BLANCO,
            font=("Arial", px(13), "bold"),
            width=12,
            height=2
        )

        self.boton_stop.grid(
            row=0, column=1, padx=px(10)
        )

        self.boton_calibrar = tk.Button(
            botones,
            text="CALIBRAR",
            command=self.calibrar,
            bg=AZUL,
            fg=BLANCO,
            font=("Arial", px(13), "bold"),
            width=12,
            height=2
        )

        self.boton_calibrar.grid(
            row=0, column=2, padx=px(10)
        )

        self.label_estado = tk.Label(
            inferior,
            text="ESP32 DESCONECTADA",
            font=("Arial", px(11), "bold"),
            fg=ROJO,
            bg=FONDO
        )

        self.label_estado.pack(pady=px(2))

        self.buscar_puertos()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.cerrar
        )

        self.actualizar()

    # ======================================================
    # FUNCIONES DE DIBUJO
    # ======================================================

    def agregar_arco(
        self, lista, diccionario,
        clave, inicio, extension,
        nivel
    ):

        ancho = (
            self.radio - self.radio_muerto
        ) / 3

        r = (
            self.radio_muerto
            + (nivel - 0.5) * ancho
        )

        arco = self.canvas.create_arc(
            self.cx - r,
            self.cy - r,
            self.cx + r,
            self.cy + r,
            start=inicio,
            extent=extension,
            style=tk.ARC,
            outline="#34495E",
            width=max(2, ancho - self.px(3))
        )

        lista.append(arco)
        diccionario[(clave, nivel)] = arco

    def dibujar_centro(self, lista):

        centro = self.canvas.create_oval(
            self.cx - self.radio_muerto,
            self.cy - self.radio_muerto,
            self.cx + self.radio_muerto,
            self.cy + self.radio_muerto,
            fill=FONDO,
            outline=ROJO,
            width=2
        )

        lista.append(centro)

        texto = self.canvas.create_text(
            self.cx,
            self.cy,
            text="0",
            fill=BLANCO,
            font=("Arial", self.px(11), "bold")
        )

        lista.append(texto)

    def crear_joystick_manual(self):

        self.elementos_manual.append(
            self.canvas.create_oval(
                self.cx - self.radio,
                self.cy - self.radio,
                self.cx + self.radio,
                self.cy + self.radio,
                outline=AZUL,
                width=3
            )
        )

        for x1, y1, x2, y2 in [
            (
                self.cx - self.radio,
                self.cy,
                self.cx + self.radio,
                self.cy
            ),
            (
                self.cx,
                self.cy - self.radio,
                self.cx,
                self.cy + self.radio
            )
        ]:

            linea = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=GRIS,
                dash=(5, 5)
            )

            self.elementos_manual.append(linea)

    def crear_joystick_sencillo(self):

        sectores = {
            "DERECHA": (-45, 90),
            "ADELANTE": (45, 90),
            "IZQUIERDA": (135, 90),
            "ATRAS": (225, 90)
        }

        for direccion, (inicio, extension) in sectores.items():

            for nivel in (1, 2, 3):

                self.agregar_arco(
                    self.elementos_sencillo,
                    self.arcos_sencillo,
                    direccion,
                    inicio,
                    extension,
                    nivel
                )

        self.dibujar_centro(
            self.elementos_sencillo
        )

    def crear_joystick_direccion(self):

        # ==============================================
        # SIETE SECTORES DELANTEROS
        # ==============================================

        nombres = [
            "D3", "D2", "D1",
            "RECTO",
            "I1", "I2", "I3"
        ]

        for i, nombre in enumerate(nombres):

            inicio = LIMITES_ADELANTE[i]

            extension = (
                LIMITES_ADELANTE[i + 1]
                - LIMITES_ADELANTE[i]
            )

            for nivel in (1, 2, 3):

                self.agregar_arco(
                    self.elementos_direccion,
                    self.arcos_direccion,
                    nombre,
                    inicio,
                    extension,
                    nivel
                )

        # ==============================================
        # GIROS SOBRE EL EJE MAS PEQUEÑOS
        # ==============================================

        sectores = {
            "IZQUIERDA": (155, 50),
            "ATRAS": (205, 130),
            "DERECHA": (335, 50)
        }

        for nombre, (inicio, extension) in sectores.items():

            for nivel in (1, 2, 3):

                self.agregar_arco(
                    self.elementos_direccion,
                    self.arcos_direccion,
                    nombre,
                    inicio,
                    extension,
                    nivel
                )

        # ==============================================
        # ETIQUETAS DE SECTORES
        # ==============================================

        etiquetas = [
            ("D3", 35),
            ("D2", 55),
            ("D1", 73),
            ("RECTO", 90),
            ("I1", 107),
            ("I2", 125),
            ("I3", 145)
        ]

        for texto, angulo in etiquetas:

            rad = math.radians(angulo)

            r = self.radio * 0.82

            x = self.cx + r * math.cos(rad)
            y = self.cy - r * math.sin(rad)

            etiqueta = self.canvas.create_text(
                x, y,
                text=texto,
                fill=BLANCO,
                font=("Arial", self.px(8), "bold")
            )

            self.elementos_direccion.append(etiqueta)

        self.dibujar_centro(
            self.elementos_direccion
        )

    def mostrar_modo_visual(self):

        grupos = [
            self.elementos_manual,
            self.elementos_sencillo,
            self.elementos_direccion
        ]

        for grupo in grupos:

            for elemento in grupo:
                self.canvas.itemconfig(
                    elemento,
                    state="hidden"
                )

        if self.modo == MODO_MANUAL:
            grupo_activo = self.elementos_manual

        elif self.modo == MODO_SENCILLO:
            grupo_activo = self.elementos_sencillo

        else:
            grupo_activo = self.elementos_direccion

        for elemento in grupo_activo:

            self.canvas.itemconfig(
                elemento,
                state="normal"
            )

        self.canvas.tag_raise(self.punto)

    # ======================================================
    # CAMBIAR MODO
    # ======================================================

    def cambiar_modo(self):

        if self.control_activo:
            self.stop()

        indice = MODOS.index(self.modo)

        indice = (indice + 1) % len(MODOS)

        self.modo = MODOS[indice]

        self.region_actual = 0
        self.direccion_actual = "CENTRO"

        self.sector_actual = "CENTRO"
        self.sector_pendiente = None

        if self.modo == MODO_MANUAL:

            color = AZUL
            texto = "MODO: MANUAL"

        elif self.modo == MODO_SENCILLO:

            color = "#8E44AD"
            texto = "MODO: ASISTIDO SENCILLO"

        else:

            color = "#117A65"
            texto = "MODO: ASISTIDO CON DIRECCION"

        self.boton_modo.config(
            text=texto,
            bg=color
        )

        self.mostrar_modo_visual()

        self.label_region.config(
            text="CENTRO - 0 RPM"
        )

        self.label_estado.config(
            text="MODO CAMBIADO - PRESIONE START",
            fg=AMARILLO
        )

    # ======================================================
    # DETECTAR VELOCIDAD POR REGION
    # ======================================================

    def detectar_nivel(self, distancia):

        if distancia <= 0:
            self.region_actual = 0
            return 0

        nivel = self.region_actual

        h = HISTERESIS_REGION

        if nivel == 0:
            nivel = 1

        if nivel == 1:

            if distancia >= LIMITE_REGION_2 + h:
                nivel = 3

            elif distancia >= LIMITE_REGION_1 + h:
                nivel = 2

        elif nivel == 2:

            if distancia >= LIMITE_REGION_2 + h:
                nivel = 3

            elif distancia < LIMITE_REGION_1 - h:
                nivel = 1

        elif nivel == 3:

            if distancia < LIMITE_REGION_1 - h:
                nivel = 1

            elif distancia < LIMITE_REGION_2 - h:
                nivel = 2

        self.region_actual = nivel

        return nivel

    # ======================================================
    # DETECTAR SECTOR SENCILLO
    # ======================================================

    def detectar_sector_sencillo(self, x, y):

        if x == 0 and y == 0:
            return "CENTRO"

        if abs(x) > abs(y):

            if x > 0:
                return "DERECHA"

            return "IZQUIERDA"

        if y > 0:
            return "ADELANTE"

        return "ATRAS"

    # ======================================================
    # DETECTAR SECTOR CON DIRECCION
    # ======================================================

    def detectar_sector_direccion(self, x, y):

        if x == 0 and y == 0:
            return "CENTRO"

        angulo = (
            math.degrees(math.atan2(y, x))
            + 360
        ) % 360

        # ==============================================
        # SECTOR DELANTERO
        # ==============================================

        if 25 <= angulo < 155:

            nombres = [
                "D3", "D2", "D1",
                "RECTO",
                "I1", "I2", "I3"
            ]

            for i in range(7):

                if (
                    LIMITES_ADELANTE[i]
                    <= angulo
                    < LIMITES_ADELANTE[i + 1]
                ):

                    return nombres[i]

        # ==============================================
        # GIRO IZQUIERDA
        # ==============================================

        if 155 <= angulo < 205:
            return "IZQUIERDA"

        # ==============================================
        # RETROCESO
        # ==============================================

        if 205 <= angulo < 335:
            return "ATRAS"

        # ==============================================
        # GIRO DERECHA
        # ==============================================

        return "DERECHA"

    # ======================================================
    # ESTABILIZAR CAMBIO DE SECTOR
    # ======================================================

    def estabilizar_sector(self, candidato):

        ahora = time.monotonic()

        # La zona muerta siempre tiene prioridad
        if candidato == "CENTRO":

            self.sector_actual = "CENTRO"
            self.sector_pendiente = None

            return "CENTRO"

        if candidato == self.sector_actual:

            self.sector_pendiente = None

            return self.sector_actual

        if candidato != self.sector_pendiente:

            self.sector_pendiente = candidato
            self.tiempo_sector = ahora

            return self.sector_actual

        if (
            ahora - self.tiempo_sector
            >= TIEMPO_CAMBIO_SECTOR
        ):

            self.sector_actual = candidato
            self.sector_pendiente = None

        return self.sector_actual

    # ======================================================
    # MODO ASISTIDO SENCILLO
    # ======================================================

    def calcular_sencillo(self, x, y):

        distancia = min(
            1.0,
            math.hypot(x, y)
        )

        candidato = self.detectar_sector_sencillo(
            x, y
        )

        sector = self.estabilizar_sector(candidato)

        self.direccion_actual = sector

        if sector == "CENTRO":
            self.region_actual = 0
            return 0.0, 0.0

        nivel = self.detectar_nivel(distancia)

        velocidad = VELOCIDADES_REGION[
            nivel - 1
        ]

        if sector == "ADELANTE":
            return velocidad, velocidad

        if sector == "ATRAS":
            return -velocidad, -velocidad

        if sector == "DERECHA":
            return velocidad, -velocidad

        if sector == "IZQUIERDA":
            return -velocidad, velocidad

        return 0.0, 0.0

    # ======================================================
    # MODO ASISTIDO CON DIRECCION
    # ======================================================

    def calcular_con_direccion(self, x, y):

        distancia = min(
            1.0,
            math.hypot(x, y)
        )

        candidato = self.detectar_sector_direccion(
            x, y
        )

        sector = self.estabilizar_sector(candidato)

        self.direccion_actual = sector

        if sector == "CENTRO":

            self.region_actual = 0
            return 0.0, 0.0

        nivel = self.detectar_nivel(distancia)

        velocidad = VELOCIDADES_REGION[
            nivel - 1
        ]

        # ==============================================
        # AVANCE RECTO
        # ==============================================

        if sector == "RECTO":

            return velocidad, velocidad

        # ==============================================
        # AVANCE CON CORRECCION
        # ==============================================

        if sector in (
            "D1", "D2", "D3",
            "I1", "I2", "I3"
        ):

            numero = int(sector[1])

            correccion = CORRECCIONES[numero]

            # Derecha:
            # motor izquierdo mas rapido
            # motor derecho mas lento

            if sector.startswith("D"):

                izquierda = velocidad * (
                    1 + correccion
                )

                derecha = velocidad * (
                    1 - correccion
                )

            # Izquierda:
            # motor derecho mas rapido
            # motor izquierdo mas lento

            else:

                izquierda = velocidad * (
                    1 - correccion
                )

                derecha = velocidad * (
                    1 + correccion
                )

            # Limitar a 120 RPM manteniendo
            # la proporcion entre los motores

            maximo = max(
                1.0,
                abs(izquierda) / RPM_MAX,
                abs(derecha) / RPM_MAX
            )

            izquierda /= maximo
            derecha /= maximo

            return izquierda, derecha

        # ==============================================
        # GIROS SOBRE EL EJE
        # ==============================================

        if sector == "DERECHA":

            return velocidad, -velocidad

        if sector == "IZQUIERDA":

            return -velocidad, velocidad

        # ==============================================
        # RETROCESO
        # ==============================================

        if sector == "ATRAS":

            return -velocidad, -velocidad

        return 0.0, 0.0

    # ======================================================
    # RESALTAR REGIONES
    # ======================================================

    def actualizar_regiones_visuales(self):

        if self.modo == MODO_MANUAL:

            self.label_region.config(
                text="CONTROL PROPORCIONAL"
            )

            return

        if self.modo == MODO_SENCILLO:

            arcos = self.arcos_sencillo

        else:

            arcos = self.arcos_direccion

        for (sector, nivel), arco in arcos.items():

            if nivel == 1:
                color = "#2471A3"

            elif nivel == 2:
                color = "#1E8449"

            else:
                color = "#AF601A"

            if (
                sector == self.direccion_actual
                and nivel == self.region_actual
            ):

                color = AMARILLO

            self.canvas.itemconfig(
                arco,
                outline=color
            )

        if self.region_actual == 0:

            texto = "CENTRO - 0 RPM"

        else:

            velocidad = VELOCIDADES_REGION[
                self.region_actual - 1
            ]

            texto = (
                f"{self.direccion_actual} | "
                f"R{self.region_actual} | "
                f"{velocidad} RPM"
            )

        self.label_region.config(
            text=texto
        )

    # ======================================================
    # PUERTOS SERIALES
    # ======================================================

    def buscar_puertos(self):

        puertos = [
            p.device
            for p in serial.tools.list_ports.comports()
        ]

        self.puerto["values"] = puertos

        if puertos:
            self.puerto.current(0)

    # ======================================================
    # CONECTAR
    # ======================================================

    def conectar(self):

        if self.conectado:

            self.desconectar()
            return

        puerto = self.puerto.get()

        if not puerto:

            self.label_estado.config(
                text="SELECCIONE UN PUERTO",
                fg=ROJO
            )

            return

        try:

            self.esp32 = serial.Serial(
                puerto,
                BAUDIOS,
                timeout=0,
                write_timeout=0.02
            )

            self.conectado = True
            self.control_activo = False

            self.boton_conectar.config(
                text="DESCONECTAR",
                bg=ROJO
            )

            self.label_estado.config(
                text="ESP32 CONECTADA - DETENIDO",
                fg=AZUL
            )

        except Exception as e:

            self.label_estado.config(
                text=f"ERROR: {e}",
                fg=ROJO
            )

    # ======================================================
    # ENVIAR
    # ======================================================

    def enviar(self, comando):

        if not self.conectado or self.esp32 is None:
            return False

        try:

            datos = (
                comando + "\n"
            ).encode("utf-8")

            enviados = self.esp32.write(datos)

            if enviados != len(datos):

                raise serial.SerialTimeoutException(
                    "Envio incompleto"
                )

            return True

        except (serial.SerialException, OSError) as e:

            print("ERROR SERIAL:", e)

            self.desconectar()

            return False

    # ======================================================
    # RECIBIR
    # ======================================================

    def leer_respuestas(self):

        if not self.conectado or self.esp32 is None:
            return

        try:

            disponibles = self.esp32.in_waiting

            if disponibles > 0:

                self.esp32.read(
                    min(disponibles, 4096)
                )

        except (serial.SerialException, OSError) as e:

            print("ERROR RECEPCION:", e)
            self.desconectar()

    # ======================================================
    # START
    # ======================================================

    def start(self):

        if not self.conectado:

            self.label_estado.config(
                text="CONECTE LA ESP32",
                fg=ROJO
            )

            return

        if self.centro_x is None:

            self.label_estado.config(
                text="CALIBRE EL JOYSTICK",
                fg=ROJO
            )

            return

        if self.control_activo:
            return

        if math.hypot(
            self.pos_x,
            self.pos_y
        ) > 0.01:

            self.label_estado.config(
                text="CENTRE EL JOYSTICK",
                fg=ROJO
            )

            return

        self.rpm_izq = 0.0
        self.rpm_der = 0.0

        self.objetivo_izq = 0.0
        self.objetivo_der = 0.0

        self.tiempo_anterior = time.monotonic()

        if not self.enviar("START"):
            return

        if not self.enviar("RPM,0,0"):
            return

        self.control_activo = True

        self.label_estado.config(
            text=f"CONTROL ACTIVO - {self.modo}",
            fg=VERDE
        )

    # ======================================================
    # STOP
    # ======================================================

    def stop(self):

        self.control_activo = False

        self.rpm_izq = 0.0
        self.rpm_der = 0.0

        self.objetivo_izq = 0.0
        self.objetivo_der = 0.0

        if self.conectado:
            self.enviar("STOP")

        self.label_rpm_izq.config(
            text="0 RPM"
        )

        self.label_rpm_der.config(
            text="0 RPM"
        )

        self.label_estado.config(
            text="CONTROL DETENIDO",
            fg=ROJO
        )

    # ======================================================
    # DESCONECTAR
    # ======================================================

    def desconectar(self):

        self.control_activo = False
        self.conectado = False

        self.rpm_izq = 0.0
        self.rpm_der = 0.0

        if self.esp32 is not None:

            try:
                self.esp32.write(b"STOP\n")
                self.esp32.flush()
            except Exception:
                pass

            try:
                self.esp32.close()
            except Exception:
                pass

        self.esp32 = None

        self.boton_conectar.config(
            text="CONECTAR",
            bg=AZUL
        )

        self.label_estado.config(
            text="ESP32 DESCONECTADA",
            fg=ROJO
        )

    # ======================================================
    # CALIBRAR
    # ======================================================

    def calibrar(self):

        if self.control_activo:
            self.stop()

        try:

            _, _, adc_x, adc_y = self.adc.update()

            self.centro_x = adc_x
            self.centro_y = adc_y

            self.pos_x = 0.0
            self.pos_y = 0.0

            self.region_actual = 0
            self.direccion_actual = "CENTRO"

            self.sector_actual = "CENTRO"
            self.sector_pendiente = None

            self.rpm_izq = 0.0
            self.rpm_der = 0.0

            self.label_estado.config(
                text="CENTRO CALIBRADO",
                fg=VERDE
            )

        except Exception as e:

            self.label_estado.config(
                text=f"ERROR ADC: {e}",
                fg=ROJO
            )

    # ======================================================
    # NORMALIZAR JOYSTICK
    # ======================================================

    def normalizar_joystick(self, adc_x, adc_y):

        x = (
            adc_x - self.centro_x
        ) / self.rango

        y = (
            adc_y - self.centro_y
        ) / self.rango

        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))

        magnitud = math.hypot(x, y)

        if magnitud <= ZONA_MUERTA:
            return 0.0, 0.0

        magnitud_normalizada = (
            min(magnitud, 1.0)
            - ZONA_MUERTA
        ) / (1.0 - ZONA_MUERTA)

        factor = (
            magnitud_normalizada / magnitud
        )

        return x * factor, y * factor

    # ======================================================
    # CURVA EXPONENCIAL
    # ======================================================

    def curva_joystick(self, valor):

        return math.copysign(
            abs(valor) ** CURVA_JOYSTICK,
            valor
        )

    # ======================================================
    # CONTROL MANUAL
    # ======================================================

    def calcular_manual(self, x, y):

        x = self.curva_joystick(x)
        y = self.curva_joystick(y)

        izquierda = y + x
        derecha = y - x

        maximo = max(
            1.0,
            abs(izquierda),
            abs(derecha)
        )

        return (
            izquierda / maximo * RPM_MAX,
            derecha / maximo * RPM_MAX
        )

    # ======================================================
    # RAMPA
    # ======================================================

    def aplicar_rampa(self, actual, objetivo, dt):

        dt = max(
            0.0,
            min(dt, 0.1)
        )

        # Primero pasar por cero al invertir
        if actual * objetivo < 0:

            objetivo_temporal = 0.0

        else:

            objetivo_temporal = objetivo

        if abs(objetivo_temporal) > abs(actual):

            tasa = ACELERACION_RPM_S

        else:

            tasa = DESACELERACION_RPM_S

        cambio_maximo = tasa * dt

        diferencia = (
            objetivo_temporal - actual
        )

        cambio = max(
            -cambio_maximo,
            min(cambio_maximo, diferencia)
        )

        nueva = actual + cambio

        if abs(nueva) < 0.001:
            nueva = 0.0

        return max(
            -RPM_MAX,
            min(RPM_MAX, nueva)
        )

    # ======================================================
    # ACTUALIZAR
    # ======================================================

    def actualizar(self):

        if self.cerrando:
            return

        try:

            ahora = time.monotonic()

            dt = ahora - self.tiempo_anterior
            self.tiempo_anterior = ahora

            # ==============================================
            # PROTECCION POR RETRASO
            # ==============================================

            if (
                self.control_activo
                and dt > TIEMPO_MAX_ACTUALIZACION
            ):

                self.stop()

                self.label_estado.config(
                    text="DETENIDO - RETRASO DE LECTURA",
                    fg=ROJO
                )

            # ==============================================
            # LEER ADC
            # ==============================================

            x, y, adc_x, adc_y = self.adc.update()

            if self.centro_x is None:

                self.centro_x = adc_x
                self.centro_y = adc_y

            self.pos_x, self.pos_y = (
                self.normalizar_joystick(
                    adc_x, adc_y
                )
            )

            # ==============================================
            # SELECCIONAR DIRECCION Y REGION
            # ==============================================

            if self.modo != MODO_MANUAL:

                distancia = min(
                    1.0,
                    math.hypot(
                        self.pos_x,
                        self.pos_y
                    )
                )

                if self.modo == MODO_SENCILLO:

                    candidato = (
                        self.detectar_sector_sencillo(
                            self.pos_x,
                            self.pos_y
                        )
                    )

                else:

                    candidato = (
                        self.detectar_sector_direccion(
                            self.pos_x,
                            self.pos_y
                        )
                    )

                sector = self.estabilizar_sector(
                    candidato
                )

                self.direccion_actual = sector

                if sector == "CENTRO":

                    self.region_actual = 0

                else:

                    self.detectar_nivel(distancia)

            # ==============================================
            # CONTROL
            # ==============================================

            if self.control_activo:

                if self.modo == MODO_MANUAL:

                    objetivos = self.calcular_manual(
                        self.pos_x,
                        self.pos_y
                    )

                elif self.modo == MODO_SENCILLO:

                    objetivos = self.calcular_sencillo(
                        self.pos_x,
                        self.pos_y
                    )

                else:

                    objetivos = self.calcular_con_direccion(
                        self.pos_x,
                        self.pos_y
                    )

                (
                    self.objetivo_izq,
                    self.objetivo_der
                ) = objetivos

                # Rampas independientes
                self.rpm_izq = self.aplicar_rampa(
                    self.rpm_izq,
                    self.objetivo_izq,
                    dt
                )

                self.rpm_der = self.aplicar_rampa(
                    self.rpm_der,
                    self.objetivo_der,
                    dt
                )

                # ==========================================
                # ENVIO PRIORITARIO
                # ==========================================

                comando = (
                    f"RPM,{self.rpm_izq:.2f},"
                    f"{self.rpm_der:.2f}"
                )

                if not self.enviar(comando):

                    raise RuntimeError(
                        "Fallo enviando RPM"
                    )

            else:

                self.rpm_izq = 0.0
                self.rpm_der = 0.0

                self.objetivo_izq = 0.0
                self.objetivo_der = 0.0

            # ==============================================
            # LEER ESP32
            # ==============================================

            self.leer_respuestas()

            # ==============================================
            # ACTUALIZACION VISUAL
            # ==============================================

            if (
                ahora - self.tiempo_visual
                >= PERIODO_VISUAL
            ):

                self.tiempo_visual = ahora

                self.label_voltaje.config(
                    text=(
                        f"X: {x:.3f} V     "
                        f"Y: {y:.3f} V"
                    )
                )

                self.label_adc.config(
                    text=(
                        f"ADC X: {adc_x}     "
                        f"ADC Y: {adc_y}"
                    )
                )

                self.label_posicion.config(
                    text=(
                        f"X: {self.pos_x:+.2f}     "
                        f"Y: {self.pos_y:+.2f}"
                    )
                )

                # Punto visual
                px = (
                    self.cx
                    + self.pos_x * self.radio
                )

                py = (
                    self.cy
                    - self.pos_y * self.radio
                )

                distancia = math.hypot(
                    self.pos_x,
                    self.pos_y
                )

                if distancia > 1:

                    px = (
                        self.cx
                        + self.pos_x / distancia
                        * self.radio
                    )

                    py = (
                        self.cy
                        - self.pos_y / distancia
                        * self.radio
                    )

                self.canvas.coords(
                    self.punto,
                    px - self.radio_punto,
                    py - self.radio_punto,
                    px + self.radio_punto,
                    py + self.radio_punto
                )

                self.canvas.tag_raise(self.punto)

                # Regiones resaltadas
                self.actualizar_regiones_visuales()

                # Referencias RPM
                self.label_rpm_izq.config(
                    text=f"{self.rpm_izq:+.1f} RPM"
                )

                self.label_rpm_der.config(
                    text=f"{self.rpm_der:+.1f} RPM"
                )

        except Exception as e:

            print("ERROR:", e)

            if self.control_activo:
                self.stop()

            self.label_estado.config(
                text=f"ERROR: {e}",
                fg=ROJO
            )

        if not self.cerrando:

            self.root.after(
                PERIODO_MS,
                self.actualizar
            )

    # ======================================================
    # CERRAR
    # ======================================================

    def cerrar(self):

        self.cerrando = True

        if self.conectado:

            self.stop()
            self.desconectar()

        self.adc.close()
        self.root.destroy()


# ==========================================================
# PROGRAMA PRINCIPAL
# ==========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = InterfazJoystick(root)

    root.mainloop()
