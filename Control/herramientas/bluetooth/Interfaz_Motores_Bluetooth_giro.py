"""Monitor Bluetooth SPP / USB para el firmware ESP32/Cytron suministrado.
Instalar: python -m pip install pyserial matplotlib
Ejecutar: python Interfaz_Motores_Bluetooth_LEDS.py
START habilita a cero RPM; Aplicar RPM envía una sola línea RPM,x,x.
Adelante y Atrás son indicadores LED, sin acción. El signo del campo RPM define el sentido.
Giro derecha: RPM,0,x. Giro izquierdo: RPM,x,0. Conservan el signo del campo.
El indicador muestra referencias confirmadas, no una medición del rumbo físico.
Medidas: diámetro común en cm y vueltas del eje del encoder por vuelta
 de rueda. Solo afectan el cálculo local v = RPM*pi*D/(60*relación).
Firmware Bluetooth: KEEP cada 400 ms; parada por falta de contacto a los 2 s.
"""
from __future__ import annotations

import math
import queue
import threading
import time
import tkinter as tk
from collections import deque
from dataclasses import dataclass
from tkinter import messagebox, ttk

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# ============================================================
# CONFIGURACION GENERAL
# ============================================================
BAUDIOS = 57600
RPM_MAXIMAS = 120.0
VENTANA_GRAFICA_S = 30.0
MAX_MUESTRAS = 1200
ESPERA_ARRANQUE_S = 4.0

COLOR_PRIMARIO = "#2563eb"
COLOR_SECUNDARIO = "#059669"
COLOR_FONDO = "#eef2f7"
COLOR_PANEL = "#ffffff"
COLOR_BORDE = "#d8dee9"
COLOR_TEXTO = "#0f172a"
COLOR_TEXTO_SUAVE = "#475569"
COLOR_ALERTA = "#dc2626"
COLOR_INACTIVO = "#94a3b8"
COLOR_STATUS_OK = "#10b981"
COLOR_STATUS_WARN = "#f59e0b"
COLOR_STATUS_OFF = "#64748b"


# ============================================================
# MODELO DE DATOS
# ============================================================
@dataclass(frozen=True)
class Muestra:
    tiempo_s: float
    ref_izq: float
    rpm_izq: float
    pwm_izq: float
    cuentas_izq: int
    ref_der: float
    rpm_der: float
    pwm_der: float
    cuentas_der: int


def interpretar_data(linea: str) -> Muestra | None:
    partes = linea.split(",")
    if len(partes) != 10 or partes[0] != "DATA":
        return None
    try:
        tiempo_us = int(partes[1])
        valores = [float(partes[i]) for i in (2, 3, 4, 6, 7, 8)]
        if tiempo_us < 0 or not all(math.isfinite(v) for v in valores):
            return None
        return Muestra(
            tiempo_us / 1_000_000.0,
            valores[0], valores[1], valores[2], int(partes[5]),
            valores[3], valores[4], valores[5], int(partes[9]),
        )
    except (ValueError, OverflowError):
        return None


def comando_rpm(texto: str, modo: str = "ambos") -> str:
    valor = float(texto.strip().replace(",", "."))
    if not math.isfinite(valor) or abs(valor) > RPM_MAXIMAS:
        raise ValueError("RPM fuera de rango")
    if modo not in ("ambos", "izquierda", "derecha"):
        raise ValueError("Modo desconocido")
    izquierda = 0.0 if modo == "derecha" else valor
    derecha = 0.0 if modo == "izquierda" else valor
    return f"RPM,{izquierda:.3f},{derecha:.3f}"


def velocidad_lineal(rpm: float, diametro_m: float, relacion: float) -> float:
    return (rpm / relacion) * math.pi * diametro_m / 60.0


# ============================================================
# HILO DE COMUNICACION BLUETOOTH SPP / USB
# ============================================================
class EnlaceSerial(threading.Thread):
    def __init__(self, puerto: str):
        super().__init__(daemon=True)
        self.puerto = puerto
        self.eventos = queue.Queue()
        self.comandos = queue.Queue()
        self.cerrar = threading.Event()
        self.parar_motor = threading.Event()

    def enviar(self, comando: str):
        self.comandos.put(comando)

    def detener(self):
        self.parar_motor.set()

    def run(self):
        conexion = None
        activo = False
        try:
            if serial is None:
                raise RuntimeError("Instala pyserial: python -m pip install pyserial")

            conexion = serial.Serial(
                self.puerto, BAUDIOS, timeout=0.05, write_timeout=0.5
            )
            self.eventos.put(("estado", "Puerto abierto. Esperando a la ESP32..."))

            if self.cerrar.wait(ESPERA_ARRANQUE_S):
                return

            buffer = bytearray()
            listo = False
            limite = time.monotonic() + 10.0
            ultimo_ping = -math.inf
            ultimo_keep = time.monotonic()

            def escribir(comando: str):
                trama = (comando + "\n").encode("ascii")
                if conexion.write(trama) != len(trama):
                    raise IOError("Escritura USB incompleta")

            while not self.cerrar.is_set():
                ahora = time.monotonic()

                if self.parar_motor.is_set():
                    self.parar_motor.clear()
                    while True:
                        try:
                            self.comandos.get_nowait()
                        except queue.Empty:
                            break
                    escribir("STOP")
                    activo = False

                if not listo:
                    if ahora > limite:
                        raise RuntimeError("La ESP32 no respondio a PING a 115200 baudios.")
                    if ahora - ultimo_ping >= 1.0:
                        escribir("PING")
                        ultimo_ping = ahora
                else:
                    for _ in range(10):
                        try:
                            comando = self.comandos.get_nowait()
                        except queue.Empty:
                            break
                        if self.parar_motor.is_set():
                            break
                        escribir(comando)
                    if activo and ahora - ultimo_keep >= 0.4:
                        escribir("KEEP")
                        ultimo_keep = ahora

                bloque = conexion.read(min(max(conexion.in_waiting, 1), 4096))
                buffer.extend(bloque)

                while b"\n" in buffer:
                    linea_bytes, _, resto = buffer.partition(b"\n")
                    buffer = bytearray(resto)
                    linea = linea_bytes.decode("utf-8", errors="replace").strip()
                    if not linea:
                        continue

                    if linea == "READY":
                        listo = False
                        activo = False
                        ultimo_ping = -math.inf
                        limite = time.monotonic() + 10.0
                        while not self.comandos.empty():
                            try:
                                self.comandos.get_nowait()
                            except queue.Empty:
                                break
                        self.eventos.put(("reinicio", None))
                    elif linea in ("ACK,PONG", "PONG"):
                        listo = True
                        self.eventos.put(("listo", None))
                    elif linea == "ACK,START":
                        activo = True
                        self.eventos.put(("inicio", None))
                    elif linea == "ACK,STOP":
                        activo = False
                        self.eventos.put(("parada", None))
                    elif linea.startswith("DATA,"):
                        muestra = interpretar_data(linea)
                        if muestra is not None:
                            self.eventos.put(("dato", muestra))
                        else:
                            self.eventos.put(("mensaje", "Formato DATA distinto. Usa el firmware compatible."))
                    else:
                        self.eventos.put(("mensaje", linea))

                if len(buffer) > 8192:
                    buffer.clear()
                    self.eventos.put(("mensaje", "Se descarto una linea serial incompleta."))

        except Exception as error:
            self.eventos.put(("error", str(error)))
        finally:
            if conexion is not None:
                try:
                    if conexion.is_open:
                        try:
                            conexion.write(b"STOP\n")
                        except Exception:
                            pass
                        conexion.close()
                except Exception:
                    try:
                        conexion.close()
                    except Exception:
                        pass
            self.eventos.put(("cerrado", None))


# ============================================================
# WIDGETS VISUALES
# ============================================================
class TarjetaValor(tk.Frame):
    def __init__(self, master, titulo: str, color: str, icono: str = ""):
        super().__init__(master, bg=COLOR_PANEL, bd=0, highlightthickness=1, highlightbackground=COLOR_BORDE)
        self.configure(padx=14, pady=8)

        cab = tk.Frame(self, bg=COLOR_PANEL)
        cab.pack(fill="x")
        tk.Label(
            cab, text=f"{icono} {titulo}".strip(), bg=COLOR_PANEL,
            fg=color, font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")

        linea = tk.Frame(self, bg=color, height=3)
        linea.pack(fill="x", pady=(10, 12))

        self.valores = {}
        rejilla = tk.Frame(self, bg=COLOR_PANEL)
        rejilla.pack(fill="x")
        for i, (clave, texto) in enumerate([
            ("pwm", "PWM (%)"),
            ("rpm", "RPM medidas"),
            ("vel", "Velocidad (m/s)"),
        ]):
            celda = tk.Frame(rejilla, bg=COLOR_PANEL)
            celda.grid(row=0, column=i, padx=(0, 14 if i < 2 else 0), sticky="nsew")
            rejilla.grid_columnconfigure(i, weight=1)
            tk.Label(celda, text=texto, bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 10)).pack(anchor="w")
            var = tk.StringVar(value="--")
            tk.Label(celda, textvariable=var, bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 24, "bold")).pack(anchor="w", pady=(8, 0))
            self.valores[clave] = var

        self.extra = tk.StringVar(value="Referencia: -- RPM   |   Velocidad: -- km/h")
        tk.Label(self, textvariable=self.extra, bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 10)).pack(anchor="w", pady=(14, 0))

    def actualizar(self, pwm: str, rpm: str, vel: str, extra: str):
        self.valores["pwm"].set(pwm)
        self.valores["rpm"].set(rpm)
        self.valores["vel"].set(vel)
        self.extra.set(extra)

    def limpiar(self):
        self.actualizar("--", "--", "--", "Referencia: -- RPM   |   Velocidad: -- km/h")


# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
class InterfazMotores:
    def __init__(self, ventana: tk.Tk):
        self.ventana = ventana
        self.ventana.title("Cytron | Monitor Bluetooth SPP / USB de motores")
        self.ventana.geometry("1380x900")
        self.ventana.minsize(1180, 820)
        self.ventana.configure(bg=COLOR_FONDO)

        self.enlace = None
        self.listo = False
        self.activo = False
        self.ocupado = False
        self.cerrando = False
        self.historial = deque(maxlen=MAX_MUESTRAS)
        self.ultima = None
        self.ultima_recepcion = 0.0
        self.ultimo_dibujo = 0.0
        self.redibujar = False
        self.diametro_m = None
        self.relacion = 1.0

        self.puerto = tk.StringVar()
        self.referencia = tk.StringVar(value="0")
        self.plazo_orden = 0.0
        self.movimiento = tk.StringVar(value="SIN CONEXIÓN")
        self.esperando_stop = False
        self.diametro_cm = tk.StringVar(value="25.5")
        self.relacion_texto = tk.StringVar(value="1")
        self.estado = tk.StringVar(value="Desconectado")
        self.mensaje = tk.StringVar(value="Selecciona el puerto COM Bluetooth SPP / USB de la ESP32 para iniciar.")
        self.configuracion = tk.StringVar(value="Configura el diámetro de rueda y la relación eje/rueda para calcular la velocidad lineal.")
        self.estado_chip = tk.StringVar(value="DESCONECTADO")
        self.estado_chip_color = COLOR_STATUS_OFF

        self._configurar_estilos()
        self._crear_ui()
        self.actualizar_puertos()
        self.actualizar_botones()
        self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.ventana.after(50, self.actualizar)

    # -------------------------------
    # ESTILOS
    # -------------------------------
    def _configurar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure("TFrame", background=COLOR_FONDO)
        estilo.configure("TLabel", background=COLOR_FONDO, foreground=COLOR_TEXTO, font=("Segoe UI", 10))

        estilo.configure(
            "Card.TLabelframe",
            background=COLOR_PANEL,
            bordercolor=COLOR_BORDE,
            relief="solid",
            borderwidth=1,
            lightcolor=COLOR_BORDE,
            darkcolor=COLOR_BORDE,
        )
        estilo.configure(
            "Card.TLabelframe.Label",
            background=COLOR_PANEL,
            foreground=COLOR_TEXTO,
            font=("Segoe UI", 10, "bold"),
        )

        estilo.configure(
            "Modern.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
            background="#e2e8f0",
            foreground=COLOR_TEXTO,
            borderwidth=0,
        )
        estilo.map("Modern.TButton", background=[("active", "#cbd5e1")])

        estilo.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(14, 9),
            background=COLOR_PRIMARIO,
            foreground="white",
            borderwidth=0,
        )
        estilo.map("Primary.TButton",
                   background=[("active", "#1d4ed8"), ("disabled", "#93c5fd")],
                   foreground=[("disabled", "#eff6ff")])

        estilo.configure(
            "Success.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(14, 9),
            background=COLOR_SECUNDARIO,
            foreground="white",
            borderwidth=0,
        )
        estilo.map("Success.TButton",
                   background=[("active", "#047857"), ("disabled", "#a7f3d0")],
                   foreground=[("disabled", "#ecfdf5")])

        estilo.configure(
            "Danger.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(14, 9),
            background=COLOR_ALERTA,
            foreground="white",
            borderwidth=0,
        )
        estilo.map("Danger.TButton",
                   background=[("active", "#b91c1c"), ("disabled", "#fca5a5")],
                   foreground=[("disabled", "#fff1f2")])

        estilo.configure("Modern.TEntry", padding=6)
        estilo.configure("Modern.TCombobox", padding=5)

    # -------------------------------
    # UI
    # -------------------------------
    def _crear_ui(self):
        contenedor = tk.Frame(self.ventana, bg=COLOR_FONDO)
        contenedor.pack(fill="both", expand=True)

        self._crear_header(contenedor)

        cuerpo = tk.Frame(contenedor, bg=COLOR_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self._crear_panel_superior(cuerpo)
        self._crear_movimiento(cuerpo)
        self._crear_metricas(cuerpo)
        self._crear_graficas(cuerpo)
        self._crear_barra_estado(cuerpo)

    def _crear_header(self, parent):
        header = tk.Frame(parent, bg="#0f172a", height=84)
        header.pack(fill="x")
        header.pack_propagate(False)

        izq = tk.Frame(header, bg="#0f172a")
        izq.pack(side="left", fill="y", padx=18)
        tk.Label(
            izq,
            text="MONITOR DE MOTORES",
            bg="#0f172a",
            fg="white",
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w", pady=(12, 0))
        tk.Label(
            izq,
            text="Interfaz profesional para monitoreo y control por Bluetooth SPP / USB",
            bg="#0f172a",
            fg="#cbd5e1",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(2, 10))

        der = tk.Frame(header, bg="#0f172a")
        der.pack(side="right", padx=18)
        self.lbl_chip = tk.Label(
            der,
            textvariable=self.estado_chip,
            bg=COLOR_STATUS_OFF,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
            relief="flat"
        )
        self.lbl_chip.pack(anchor="e", pady=20)

    def _crear_panel_superior(self, parent):
        fila = tk.Frame(parent, bg=COLOR_FONDO)
        fila.pack(fill="x", pady=(16, 14))
        fila.grid_columnconfigure(0, weight=1)
        fila.grid_columnconfigure(1, weight=1)

        # Conexion
        card_con = tk.LabelFrame(fila, text="Conexión Bluetooth SPP / USB", bg=COLOR_PANEL, fg=COLOR_TEXTO,
                                 font=("Segoe UI", 10, "bold"), padx=14, pady=14,
                                 bd=1, relief="solid", highlightbackground=COLOR_BORDE)
        card_con.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(card_con, text="Puerto COM Bluetooth SPP / USB", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        self.combo = ttk.Combobox(card_con, textvariable=self.puerto, width=16, style="Modern.TCombobox")
        self.combo.grid(row=1, column=0, sticky="w", pady=(4, 10))

        botones_con = tk.Frame(card_con, bg=COLOR_PANEL)
        botones_con.grid(row=1, column=1, columnspan=3, sticky="w", padx=(12, 0), pady=(0, 10))
        self.b_actualizar = ttk.Button(botones_con, text="Actualizar", style="Modern.TButton", command=self.actualizar_puertos)
        self.b_actualizar.pack(side="left", padx=(0, 8))
        self.b_conectar = ttk.Button(botones_con, text="Conectar", style="Primary.TButton", command=self.conectar_desconectar)
        self.b_conectar.pack(side="left")

        tk.Label(card_con, text="Estado de enlace", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=(4, 0))
        tk.Label(card_con, textvariable=self.estado, bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 11, "bold")).grid(row=3, column=0, columnspan=4, sticky="w", pady=(4, 0))
        tk.Label(card_con, text="Bluetooth SPP / USB · 115200 baudios", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 9)).grid(row=0, column=1, columnspan=3, sticky="e")

        # Control y calculo
        card_ctrl = tk.LabelFrame(fila, text="Control y parámetros", bg=COLOR_PANEL, fg=COLOR_TEXTO,
                                  font=("Segoe UI", 10, "bold"), padx=14, pady=14,
                                  bd=1, relief="solid", highlightbackground=COLOR_BORDE)
        card_ctrl.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(card_ctrl, text="RPM para AMBOS motores (−120 a 120)", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 9)).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Entry(card_ctrl, textvariable=self.referencia, width=16, style="Modern.TEntry").grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 10))

        botones_ctrl = tk.Frame(card_ctrl, bg=COLOR_PANEL)
        botones_ctrl.grid(row=1, column=2, columnspan=3, sticky="w", padx=(16, 0), pady=(0, 10))
        self.b_iniciar = ttk.Button(botones_ctrl, text="START", style="Success.TButton", command=self.iniciar)
        self.b_iniciar.pack(side="left", padx=(0, 8))
        self.b_aplicar = ttk.Button(botones_ctrl, text="Aplicar RPM", style="Primary.TButton", command=self.aplicar_rpm)
        self.b_aplicar.pack(side="left", padx=(0, 8))
        self.b_stop = ttk.Button(botones_ctrl, text="STOP", style="Danger.TButton", command=self.detener)
        self.b_stop.pack(side="left")

        tk.Label(card_ctrl, text="Diámetro rueda (cm)", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w")
        ttk.Entry(card_ctrl, textvariable=self.diametro_cm, width=10, style="Modern.TEntry").grid(row=3, column=0, sticky="w", pady=(4, 0))
        tk.Label(card_ctrl, text="Relación eje/rueda", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 9)).grid(row=2, column=1, sticky="w", padx=(12, 0))
        ttk.Entry(card_ctrl, textvariable=self.relacion_texto, width=10, style="Modern.TEntry").grid(row=3, column=1, sticky="w", padx=(12, 0), pady=(4, 0))
        ttk.Button(card_ctrl, text="Aplicar medidas", style="Modern.TButton", command=self.aplicar_medidas).grid(row=3, column=2, sticky="w", padx=(16, 0))
        tk.Label(card_ctrl, textvariable=self.configuracion, bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, wraplength=520, justify="left", font=("Segoe UI", 9)).grid(row=4, column=0, columnspan=5, sticky="w", pady=(12, 0))

    def _crear_movimiento(self, parent):
        panel = tk.Frame(parent, bg=COLOR_PANEL, padx=12, pady=8)
        panel.pack(fill="x", pady=(0, 10))
        self.botones_movimiento = {}
        self.leds_sentido = {}
        for nombre in ("Adelante", "Atrás"):
            grupo = tk.Frame(panel, bg=COLOR_PANEL)
            grupo.pack(side="left", padx=(0, 18))
            led = tk.Label(grupo, text="●", fg=COLOR_INACTIVO, bg=COLOR_PANEL,
                           font=("Segoe UI", 20))
            led.pack(side="left")
            tk.Label(grupo, text=nombre, bg=COLOR_PANEL, fg=COLOR_TEXTO,
                     font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
            self.leds_sentido[nombre] = led
        self.movimiento.trace_add("write", self._apagar_leds_sentido)
        for modo, titulo in [("izquierda", "◀ Giro izquierdo"), ("derecha", "Giro derecha ▶")]:
            boton = ttk.Button(panel, text=titulo, style="Modern.TButton",
                               command=lambda m=modo: self.aplicar_rpm(m))
            boton.pack(side="left", padx=(0, 8))
            self.botones_movimiento[modo] = boton
        tk.Label(panel, textvariable=self.movimiento, bg="#e2e8f0", fg=COLOR_TEXTO,
                 font=("Segoe UI", 11, "bold"), padx=12, pady=8).pack(side="right")

    def _apagar_leds_sentido(self, *_):
        for led in self.leds_sentido.values():
            led.configure(fg=COLOR_INACTIVO)

    def indicar_referencias(self, izquierda, derecha):
        if not self.activo or self.esperando_stop:
            return
        if abs(izquierda) < 0.01 and abs(derecha) < 0.01:
            texto = "START · 0 RPM"
        elif abs(izquierda) < 0.01:
            texto = "GIRO DERECHA"
        elif abs(derecha) < 0.01:
            texto = "GIRO IZQUIERDO"
        elif izquierda > 0 and derecha > 0:
            texto = "ADELANTE"
        elif izquierda < 0 and derecha < 0:
            texto = "ATRÁS"
        else:
            texto = "REFERENCIAS DIFERENTES"
        self.movimiento.set(texto)
        # Indicar el signo de la referencia confirmada, también durante un giro.
        refs = [v for v in (izquierda, derecha) if abs(v) >= 0.01]
        if refs and all(v > 0 for v in refs):
            self.leds_sentido["Adelante"].configure(fg=COLOR_SECUNDARIO)
        elif refs and all(v < 0 for v in refs):
            self.leds_sentido["Atrás"].configure(fg=COLOR_PRIMARIO)

    def _crear_metricas(self, parent):
        fila = tk.Frame(parent, bg=COLOR_FONDO)
        fila.pack(fill="x", pady=(0, 14))
        fila.grid_columnconfigure(0, weight=1)
        fila.grid_columnconfigure(1, weight=1)

        self.card_izq = TarjetaValor(fila, "Motor izquierdo", COLOR_PRIMARIO, "◀")
        self.card_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_der = TarjetaValor(fila, "Motor derecho", COLOR_SECUNDARIO, "▶")
        self.card_der.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    def _crear_graficas(self, parent):
        panel = tk.Frame(parent, bg=COLOR_PANEL, bd=1, relief="solid", highlightbackground=COLOR_BORDE)
        panel.pack(fill="both", expand=True)

        top = tk.Frame(panel, bg=COLOR_PANEL)
        top.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(top, text="Tendencias en tiempo real", bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(top, text="Seguimiento de PWM, RPM y velocidad lineal estimada", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))

        self.figura = Figure(figsize=(12, 5.8), dpi=100, facecolor=COLOR_PANEL)
        self.ejes = self.figura.subplots(3, 3, sharex=True)
        self.comparadas = []
        self.lineas = []
        self.referencias = []
        for fila, etiqueta in enumerate(["PWM (%)", "RPM", "Velocidad (m/s)"]):
            par = []
            for col, (nombre, color) in enumerate([("Izquierdo", COLOR_PRIMARIO), ("Derecho", COLOR_SECUNDARIO)]):
                eje = self.ejes[fila, col]
                linea, = eje.plot([], [], color=color, linewidth=1.8, label=nombre)
                par.append(linea)
                if fila == 0:
                    eje.set_title("Motor " + nombre.lower(), fontsize=10)
                    eje.set_ylim(-105, 105)
                if fila == 1:
                    ref, = eje.plot([], [], '--', color="#94a3b8", linewidth=1, label="Referencia")
                    self.referencias.append(ref)
                    eje.legend(loc="upper right", fontsize=7)
                eje.set_ylabel(etiqueta, fontsize=8)
                eje.grid(True, alpha=0.18)
                eje.tick_params(labelsize=7)
                eje.set_xlim(0, VENTANA_GRAFICA_S)
                if fila == 2:
                    eje.set_xlabel("Tiempo ESP32 (s)", fontsize=8)
            self.lineas.append(par)
            eje = self.ejes[fila, 2]
            li, = eje.plot([], [], color=COLOR_PRIMARIO, linewidth=1.8, label="Izquierdo")
            ld, = eje.plot([], [], color=COLOR_SECUNDARIO, linewidth=1.8, linestyle="--", label="Derecho")
            self.comparadas.append((li, ld))
            eje.set_ylabel(etiqueta, fontsize=8)
            eje.grid(True, alpha=0.18)
            eje.tick_params(labelsize=7)
            eje.legend(loc="upper right", fontsize=7)
            if fila == 0:
                eje.set_title("Ambos motores", fontsize=10)
                eje.set_ylim(-105, 105)
            if fila == 2:
                eje.set_xlabel("Tiempo ESP32 (s)", fontsize=8)
        self.figura.subplots_adjust(left=0.07, right=0.98, bottom=0.13, top=0.92, hspace=0.40, wspace=0.36)

        self.canvas = FigureCanvasTkAgg(self.figura, master=panel)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 10))

    def _crear_barra_estado(self, parent):
        barra = tk.Frame(parent, bg=COLOR_PANEL, bd=1, relief="solid", highlightbackground=COLOR_BORDE)
        barra.pack(fill="x", pady=(14, 0))
        tk.Label(barra, text="Mensajes del sistema", bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
        tk.Label(barra, textvariable=self.mensaje, bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE,
                 wraplength=1260, justify="left", font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(4, 10))

    # -------------------------------
    # LOGICA DE UI
    # -------------------------------
    def actualizar_chip(self, texto: str, color: str):
        self.estado_chip.set(texto)
        self.lbl_chip.configure(bg=color)

    def actualizar_puertos(self):
        puertos = [p.device for p in list_ports.comports()] if list_ports else []
        self.combo["values"] = puertos
        if puertos and not self.puerto.get():
            self.puerto.set(puertos[0])

    def actualizar_botones(self):
        conectado = self.enlace is not None and self.enlace.is_alive()
        self.b_conectar.configure(text="Desconectar" if conectado else "Conectar")
        self.b_iniciar.configure(state="normal" if self.listo and not self.activo and not self.ocupado else "disabled")
        self.b_aplicar.configure(state="normal" if self.listo and self.activo and not self.ocupado else "disabled")
        self.b_stop.configure(state="normal" if conectado else "disabled")
        for boton in self.botones_movimiento.values():
            boton.configure(state="normal" if self.listo and self.activo and not self.ocupado else "disabled")
        self.combo.configure(state="disabled" if conectado else "normal")
        self.b_actualizar.configure(state="disabled" if conectado else "normal")

    def conectar_desconectar(self):
        if self.enlace is not None:
            self.listo = False
            self.enlace.cerrar.set()
            self.movimiento.set("DESCONECTANDO")
            self.estado.set("Desconectando...")
            self.mensaje.set("Cerrando enlace Bluetooth SPP / USB con la ESP32...")
            self.actualizar_chip("DESCONECTANDO", COLOR_STATUS_WARN)
            self.actualizar_botones()
            return

        puerto = self.puerto.get().strip()
        if not puerto:
            messagebox.showinfo("Puerto", "Selecciona o escribe el puerto COM de la ESP32.")
            return

        self.historial.clear()
        self.ultima = None
        self.borrar_tarjetas()
        self.redibujar = True
        self.enlace = EnlaceSerial(puerto)
        self.enlace.start()
        self.estado.set("Conectando...")
        self.mensaje.set(f"Abriendo {puerto} y esperando respuesta de la ESP32...")
        self.actualizar_chip("CONECTANDO", COLOR_STATUS_WARN)
        self.actualizar_botones()

    def iniciar(self):
        if self.listo and self.enlace:
            self.ocupado = True
            self.plazo_orden = time.monotonic() + 3.0
            self.enlace.enviar("START")
            self.mensaje.set("Enviando START. Esperando confirmación de la ESP32...")
            self.actualizar_botones()

    def aplicar_rpm(self, modo="ambos"):
        if not self.listo or not self.activo or not self.enlace or self.ocupado:
            return
        try:
            comando = comando_rpm(self.referencia.get(), modo)
        except ValueError:
            messagebox.showerror("Referencia", "Ingresa una RPM entre -120 y 120 para ambos motores.")
            return
        self.movimiento.set("ESPERANDO CONFIRMACIÓN")
        self.enlace.enviar(comando)
        self.ocupado = True
        self.plazo_orden = time.monotonic() + 3.0
        self.actualizar_botones()
        self.mensaje.set("Orden enviada. Esperando ACK,RPM...")

    def detener(self):
        if self.enlace:
            self.esperando_stop = True
            self.movimiento.set("STOP · pendiente")
            self.ocupado = True
            self.plazo_orden = time.monotonic() + 3.0
            self.enlace.detener()
            self.mensaje.set("Enviando STOP a la ESP32...")
            self.actualizar_botones()

    def aplicar_medidas(self):
        try:
            diametro = float(self.diametro_cm.get().replace(",", "."))
            relacion = float(self.relacion_texto.get().replace(",", "."))
            if not all(math.isfinite(v) and v > 0 for v in (diametro, relacion)):
                raise ValueError
        except ValueError:
            messagebox.showerror("Medidas", "Diametro y relación deben ser números mayores que cero. Para 1:1, escribe 1.")
            return
        self.diametro_m = diametro / 100.0
        self.relacion = relacion
        self.configuracion.set(
            f"Configuración activa: diámetro = {diametro:g} cm   |   relación eje/rueda = {relacion:g}."
        )
        self.redibujar = True
        if self.ultima:
            self.mostrar_tarjetas(self.ultima)

    def borrar_tarjetas(self):
        self.card_izq.limpiar()
        self.card_der.limpiar()

    def mostrar_tarjetas(self, muestra: Muestra):
        datos = []
        for sufijo in ("izq", "der"):
            rpm = getattr(muestra, f"rpm_{sufijo}")
            pwm = getattr(muestra, f"pwm_{sufijo}")
            ref = getattr(muestra, f"ref_{sufijo}")

            if self.diametro_m is None:
                vel_txt = "--"
                extra = f"Referencia: {ref:.1f} RPM   |   Velocidad: configura diámetro"
            else:
                velocidad = velocidad_lineal(rpm, self.diametro_m, self.relacion)
                vel_txt = f"{velocidad:.3f}"
                extra = f"Referencia: {ref:.1f} RPM   |   Velocidad: {velocidad * 3.6:.2f} km/h"

            datos.append((f"{pwm:.1f}", f"{rpm:.1f}", vel_txt, extra))

        self.card_izq.actualizar(*datos[0])
        self.card_der.actualizar(*datos[1])

    def dibujar(self):
        muestras = list(self.historial)
        tiempos = [m.tiempo_s for m in muestras]

        for indice, prefijo in enumerate(("pwm", "rpm", "vel")):
            for linea, sufijo in zip(self.lineas[indice], ("izq", "der")):
                if prefijo == "vel":
                    valores = [
                        velocidad_lineal(getattr(m, f"rpm_{sufijo}"), self.diametro_m, self.relacion)
                        if self.diametro_m is not None else math.nan
                        for m in muestras
                    ]
                else:
                    valores = [getattr(m, f"{prefijo}_{sufijo}") for m in muestras]
                linea.set_data(tiempos, valores)
            for origen, destino in zip(self.lineas[indice], self.comparadas[indice]):
                destino.set_data(origen.get_xdata(), origen.get_ydata())
            if indice:
                if indice == 1:
                    for linea_ref, sufijo in zip(self.referencias, ("izq", "der")):
                        linea_ref.set_data(tiempos, [getattr(m, f"ref_{sufijo}") for m in muestras])
                for eje in self.ejes[indice]:
                    eje.relim()
                    eje.autoscale_view(scalex=False, scaley=True)

        if tiempos:
            fin = tiempos[-1]
            self.ejes[-1, 0].set_xlim(max(0, fin - VENTANA_GRAFICA_S), max(VENTANA_GRAFICA_S, fin + 0.2))
        else:
            self.ejes[-1, 0].set_xlim(0, VENTANA_GRAFICA_S)

        self.canvas.draw_idle()

    def actualizar(self):
        if self.enlace:
            for _ in range(250):
                try:
                    tipo, valor = self.enlace.eventos.get_nowait()
                except queue.Empty:
                    break

                if tipo == "estado":
                    self.estado.set(valor)
                elif tipo == "listo":
                    self.listo = True
                    self.estado.set("Conectado")
                    self.mensaje.set("La ESP32 está lista. Presiona START y luego aplica las RPM deseadas.")
                    self.actualizar_chip("CONECTADO", COLOR_STATUS_OK)
                elif tipo == "reinicio":
                    self.listo = self.activo = self.ocupado = False
                    self.esperando_stop = False
                    self.movimiento.set("SIN CONEXIÓN / REINICIO")
                    self.ultima = None
                    self.historial.clear()
                    self.redibujar = True
                    self.borrar_tarjetas()
                    self.estado.set("ESP32 reiniciada. Comprobando conexión...")
                    self.mensaje.set("La ESP32 se reinició. La interfaz está esperando nuevamente la respuesta al PING.")
                    self.actualizar_chip("REINICIANDO", COLOR_STATUS_WARN)
                elif tipo == "inicio":
                    self.activo, self.ocupado = True, False
                    self.esperando_stop = False
                    self.movimiento.set("START · 0 RPM")
                    self.historial.clear()
                    self.ultima = None
                    self.redibujar = True
                    self.ultima_recepcion = time.monotonic()
                    self.estado.set("Control activo")
                    self.mensaje.set("Control activo en 0 RPM. Ahora puedes enviar referencias para mover los motores.")
                    self.actualizar_chip("CONTROL ACTIVO", COLOR_STATUS_OK)
                elif tipo == "parada":
                    self.activo = self.ocupado = False
                    self.esperando_stop = False
                    self.movimiento.set("STOP · confirmado")
                    self.ultima = None
                    self.referencia.set("0")
                    self.borrar_tarjetas()
                    self.estado.set("Conectado | control detenido")
                    self.mensaje.set("STOP confirmado. El control se detuvo correctamente.")
                    self.actualizar_chip("CONECTADO", COLOR_STATUS_OK)
                elif tipo == "dato":
                    if self.historial and valor.tiempo_s <= self.historial[-1].tiempo_s:
                        self.historial.clear()
                    self.historial.append(valor)
                    self.ultima = valor
                    self.ultima_recepcion = time.monotonic()
                    self.mostrar_tarjetas(valor)
                    self.indicar_referencias(valor.ref_izq, valor.ref_der)
                    self.redibujar = True
                    self.estado.set(f"En vivo | t = {valor.tiempo_s:.2f} s")
                elif tipo in ("mensaje", "error"):
                    self.mensaje.set(valor)
                    if tipo == "error":
                        self.listo = self.activo = self.ocupado = False
                        self.esperando_stop = False
                        self.movimiento.set("ERROR DE CONEXIÓN")
                        self.estado.set("Error de conexión")
                        self.actualizar_chip("ERROR", COLOR_ALERTA)
                    elif str(valor).startswith("ACK,RPM,"):
                        if not self.esperando_stop:
                            self.ocupado = False
                            try:
                                campos = str(valor).split(",")
                                if len(campos) != 4: raise ValueError
                                refs = [float(x) for x in campos[2:]]
                                if not all(math.isfinite(x) for x in refs): raise ValueError
                                self.indicar_referencias(*refs)
                            except ValueError:
                                self.movimiento.set("CONFIRMACIÓN INVÁLIDA")
                        self.mensaje.set("Referencia confirmada por ESP32: " + str(valor)[8:] + " RPM (izq., der.)")
                    elif str(valor).startswith("ERR,"):
                        self.ocupado = False
                elif tipo == "cerrado":
                    self.listo = self.activo = self.ocupado = False
                    self.esperando_stop = False
                    self.movimiento.set("SIN CONEXIÓN / REINICIO")
                    self.ultima = None
                    self.borrar_tarjetas()
                    self.enlace = None
                    self.estado.set("Desconectado")
                    self.mensaje.set("Sin conexión activa. Selecciona el COM Bluetooth SPP / USB y presiona Conectar.")
                    self.actualizar_chip("DESCONECTADO", COLOR_STATUS_OFF)
                    break
            self.actualizar_botones()

        ahora = time.monotonic()
        if self.ocupado and ahora > self.plazo_orden:
            self.ocupado = False
            self.movimiento.set("ESTADO SIN CONFIRMAR")
            self.mensaje.set("Sin confirmación de la orden. Comprueba el enlace; STOP sigue disponible.")
            self.actualizar_botones()
        if self.activo and ahora - self.ultima_recepcion > 1.5:
            self.movimiento.set("SIN DATOS RECIENTES")
            self.estado.set("Sin datos nuevos de la ESP32")
            self.actualizar_chip("SIN DATOS", COLOR_STATUS_WARN)
        if self.redibujar and ahora - self.ultimo_dibujo >= 0.15:
            self.dibujar()
            self.redibujar = False
            self.ultimo_dibujo = ahora
        if self.cerrando and self.enlace is None:
            self.ventana.destroy()
            return
        self.ventana.after(50, self.actualizar)

    def cerrar(self):
        self.cerrando = True
        if self.enlace:
            self.enlace.cerrar.set()
            self.listo = False
            self.estado.set("Cerrando conexión...")
            self.mensaje.set("Cerrando interfaz y liberando el puerto de comunicación...")
            self.actualizar_botones()
        else:
            self.ventana.destroy()


if __name__ == "__main__":
    ventana = tk.Tk()
    app = InterfazMotores(ventana)
    ventana.mainloop()
