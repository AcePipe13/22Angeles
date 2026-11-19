from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
)

from PySide6.QtCore import Qt

from interface.map_widget import MapWidget


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Silla Inteligente")
        self.resize(1024, 600)

        # =====================================================
        # WIDGET PRINCIPAL
        # =====================================================

        central = QWidget()
        self.setCentralWidget(central)

        layout_principal = QVBoxLayout(central)

        # =====================================================
        # TITULO
        # =====================================================

        titulo = QLabel("SILLA INTELIGENTE")
        titulo.setAlignment(Qt.AlignCenter)

        titulo.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
        """)

        layout_principal.addWidget(titulo)

        # =====================================================
        # ESTADOS
        # =====================================================

        layout_estado = QHBoxLayout()

        self.estado_esp32 = QLabel("ESP32 ● CONECTADA")
        self.estado_gps = QLabel("GPS ● ESPERANDO")

        self.estado_esp32.setStyleSheet("""
            font-size: 17px;
            font-weight: bold;
        """)

        self.estado_gps.setStyleSheet("""
            font-size: 17px;
            font-weight: bold;
        """)

        layout_estado.addWidget(self.estado_esp32)
        layout_estado.addStretch()
        layout_estado.addWidget(self.estado_gps)

        layout_principal.addLayout(layout_estado)

        # =====================================================
        # CONTENIDO CENTRAL
        # =====================================================

        layout_contenido = QHBoxLayout()

        # =====================================================
        # MAPA
        # =====================================================

        self.mapa = MapWidget()

        self.mapa.setMinimumWidth(650)

        layout_contenido.addWidget(
            self.mapa,
            stretch=3
        )

        # =====================================================
        # PANEL DERECHO
        # =====================================================

        panel_datos = QFrame()
        panel_datos.setFrameShape(QFrame.StyledPanel)

        grid = QGridLayout(panel_datos)

        self.latitud = QLabel("---")
        self.longitud = QLabel("---")
        self.altitud = QLabel("---")
        self.velocidad = QLabel("---")
        self.rumbo = QLabel("---")
        self.precision = QLabel("---")
        self.paquete = QLabel("---")

        datos = [
            ("Latitud", self.latitud),
            ("Longitud", self.longitud),
            ("Altitud", self.altitud),
            ("Velocidad", self.velocidad),
            ("Rumbo", self.rumbo),
            ("Precision", self.precision),
            ("Paquete", self.paquete),
        ]

        for fila, (nombre, valor) in enumerate(datos):

            etiqueta = QLabel(nombre)

            etiqueta.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
            """)

            valor.setStyleSheet("""
                font-size: 17px;
            """)

            grid.addWidget(
                etiqueta,
                fila,
                0
            )

            grid.addWidget(
                valor,
                fila,
                1
            )

        layout_contenido.addWidget(
            panel_datos,
            stretch=1
        )

        layout_principal.addLayout(
            layout_contenido
        )

    # =========================================================
    # ACTUALIZAR GPS
    # =========================================================

    def actualizar_gps(self, gps):

        self.latitud.setText(
            f"{gps.lat:.7f}"
        )

        self.longitud.setText(
            f"{gps.lon:.7f}"
        )

        self.altitud.setText(
            f"{gps.alt:.1f} m"
        )

        self.velocidad.setText(
            f"{gps.speed:.2f} km/h"
        )

        self.rumbo.setText(
            f"{gps.heading:.1f}°"
        )

        self.precision.setText(
            f"{gps.accuracy:.1f} m"
        )

        self.paquete.setText(
            str(gps.packet)
        )

        # MOVER MARCADOR EN EL MAPA
        self.mapa.actualizar_posicion(
            gps.lat,
            gps.lon
        )

        if gps.valid:
            self.estado_gps.setText(
                "GPS ● ACTIVO"
            )
        else:
            self.estado_gps.setText(
                "GPS ● SIN SEÑAL"
            )