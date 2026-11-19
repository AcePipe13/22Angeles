from PySide6.QtWebEngineWidgets import QWebEngineView


class MapWidget(QWebEngineView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lat = 4.6950169
        self.lon = -74.106194

        self.cargar_mapa()

    def cargar_mapa(self):

        html = f"""
        <!DOCTYPE html>
        <html>

        <head>

            <meta charset="utf-8">

            <meta name="viewport"
                  content="width=device-width, initial-scale=1.0">

            <link
                rel="stylesheet"
                href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
            />

            <script
                src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
            </script>

            <style>

                html, body {{
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }}

                #map {{
                    width: 100%;
                    height: 100%;
                }}

            </style>

        </head>


        <body>

            <div id="map"></div>

            <script>

                var map = L.map('map').setView(
                    [{self.lat}, {self.lon}],
                    17
                );

                L.tileLayer(
                    'https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
                    {{
                        maxZoom: 19,
                        attribution: '&copy; OpenStreetMap'
                    }}
                ).addTo(map);

                var marker = L.marker(
                    [{self.lat}, {self.lon}]
                ).addTo(map);

                marker
                    .bindPopup("Silla de ruedas")
                    .openPopup();


                function actualizarPosicion(lat, lon) {{

                    marker.setLatLng([lat, lon]);

                    map.panTo(
                        [lat, lon],
                        {{
                            animate: true
                        }}
                    );

                }}

            </script>

        </body>

        </html>
        """

        self.setHtml(html)

    def actualizar_posicion(self, lat, lon):

        self.lat = lat
        self.lon = lon

        javascript = f"""
        actualizarPosicion(
            {lat},
            {lon}
        );
        """

        self.page().runJavaScript(javascript)