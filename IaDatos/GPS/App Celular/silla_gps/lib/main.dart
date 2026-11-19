import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

void main() {
  runApp(const SillaGPSApp());
}

class SillaGPSApp extends StatelessWidget {
  const SillaGPSApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Silla GPS',
      theme: ThemeData(
        useMaterial3: true,
      ),
      home: const GPSPage(),
    );
  }
}

class GPSPage extends StatefulWidget {
  const GPSPage({super.key});

  @override
  State<GPSPage> createState() => _GPSPageState();
}

class _GPSPageState extends State<GPSPage> {
  // ============================================================
  // CONFIGURACION ESP32
  // ============================================================

  static const String esp32IP = "192.168.2.38";
  static const int esp32Puerto = 5000;

  // ============================================================
  // VARIABLES GPS
  // ============================================================

  Position? posicion;

  String estadoGPS = "GPS INACTIVO";
  String estadoESP32 = "Sin enviar";

  bool gpsActivo = false;

  // Contador de paquetes enviados
  int paquetesEnviados = 0;

  // Temporizador de envio
  Timer? timerEnvio;

  // Stream GPS
  StreamSubscription<Position>? gpsSubscription;

  // ============================================================
  // PREPARAR GPS
  // ============================================================

  Future<bool> prepararGPS() async {
    bool servicioActivo;
    LocationPermission permiso;

    // Verificar si la ubicacion esta activada
    servicioActivo = await Geolocator.isLocationServiceEnabled();

    if (!servicioActivo) {
      setState(() {
        estadoGPS = "ACTIVA LA UBICACION DEL CELULAR";
        gpsActivo = false;
      });

      return false;
    }

    // Revisar permisos
    permiso = await Geolocator.checkPermission();

    // Solicitar permiso si hace falta
    if (permiso == LocationPermission.denied) {
      permiso = await Geolocator.requestPermission();

      if (permiso == LocationPermission.denied) {
        setState(() {
          estadoGPS = "PERMISO DE UBICACION RECHAZADO";
          gpsActivo = false;
        });

        return false;
      }
    }

    // Permiso bloqueado permanentemente
    if (permiso == LocationPermission.deniedForever) {
      setState(() {
        estadoGPS = "PERMISO DE UBICACION BLOQUEADO";
        gpsActivo = false;
      });

      return false;
    }

    return true;
  }

  // ============================================================
  // ENVIAR GPS A ESP32 POR UDP
  // ============================================================

  Future<void> enviarUDP() async {
    // Si todavia no tenemos una posicion valida, no enviamos
    if (posicion == null) {
      setState(() {
        estadoESP32 = "Esperando GPS";
      });

      return;
    }

    RawDatagramSocket? socket;

    try {
      socket = await RawDatagramSocket.bind(
        InternetAddress.anyIPv4,
        0,
      );

      // Crear paquete
      final datos = {
        "lat": posicion!.latitude,
        "lon": posicion!.longitude,
        "alt": posicion!.altitude,

        // Convertir m/s a km/h
        "speed": posicion!.speed * 3.6,

        "accuracy": posicion!.accuracy,
        "heading": posicion!.heading,

        // Numero de paquete
        "packet": paquetesEnviados + 1,
      };

      // Convertir a JSON
      final String mensaje = jsonEncode(datos);

      // Enviar por UDP
      socket.send(
        utf8.encode(mensaje),
        InternetAddress(esp32IP),
        esp32Puerto,
      );

      paquetesEnviados++;

      if (mounted) {
        setState(() {
          estadoESP32 = "Enviando cada 1 s";
        });
      }

      print("");
      print("========== UDP ENVIADO ==========");
      print("Paquete: $paquetesEnviados");
      print("Destino: $esp32IP:$esp32Puerto");
      print(mensaje);
      print("=================================");
    } catch (e) {
      if (mounted) {
        setState(() {
          estadoESP32 = "Error de envio";
        });
      }

      print("ERROR UDP:");
      print(e);
    } finally {
      socket?.close();
    }
  }

  // ============================================================
  // INICIAR GPS
  // ============================================================

  Future<void> iniciarGPS() async {
    bool listo = await prepararGPS();

    if (!listo) {
      return;
    }

    setState(() {
      gpsActivo = true;
      estadoGPS = "GPS ACTIVO";
      estadoESP32 = "Esperando primera posicion";
    });

    // Configuracion GPS
    const configuracion = LocationSettings(
      accuracy: LocationAccuracy.high,

      // Queremos recibir cambios incluso con pequeños movimientos
      distanceFilter: 0,
    );

    // ==========================================================
    // LEER GPS
    // ==========================================================

    gpsSubscription = Geolocator.getPositionStream(
      locationSettings: configuracion,
    ).listen(
      (Position nuevaPosicion) {
        setState(() {
          posicion = nuevaPosicion;
        });

        print("");
        print("========== GPS ACTUALIZADO ==========");
        print("Latitud: ${nuevaPosicion.latitude}");
        print("Longitud: ${nuevaPosicion.longitude}");
        print("Altitud: ${nuevaPosicion.altitude} m");
        print(
          "Velocidad: ${(nuevaPosicion.speed * 3.6).toStringAsFixed(2)} km/h",
        );
        print("Precision: ${nuevaPosicion.accuracy} m");
        print("Rumbo: ${nuevaPosicion.heading} grados");
        print("=====================================");
      },
      onError: (error) {
        setState(() {
          estadoGPS = "ERROR DE GPS";
        });

        print("ERROR GPS:");
        print(error);
      },
    );

    // ==========================================================
    // ENVIO EXACTAMENTE CADA 1 SEGUNDO
    // ==========================================================

    timerEnvio?.cancel();

    timerEnvio = Timer.periodic(
      const Duration(seconds: 1),
      (timer) {
        enviarUDP();
      },
    );
  }

  // ============================================================
  // DETENER GPS
  // ============================================================

  Future<void> detenerGPS() async {
    timerEnvio?.cancel();
    timerEnvio = null;

    await gpsSubscription?.cancel();
    gpsSubscription = null;

    setState(() {
      gpsActivo = false;
      estadoGPS = "GPS DETENIDO";
      estadoESP32 = "Envio detenido";
    });
  }

  // ============================================================
  // LIBERAR RECURSOS
  // ============================================================

  @override
  void dispose() {
    timerEnvio?.cancel();
    gpsSubscription?.cancel();

    super.dispose();
  }

  // ============================================================
  // INTERFAZ
  // ============================================================

  @override
  Widget build(BuildContext context) {
    double velocidadKmh = (posicion?.speed ?? 0) * 3.6;

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "Silla GPS",
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
      ),

      body: Padding(
        padding: const EdgeInsets.all(20),

        child: Column(
          children: [
            const Icon(
              Icons.location_on,
              size: 65,
            ),

            const SizedBox(height: 5),

            // ==================================================
            // ESTADO GPS
            // ==================================================

            Text(
              estadoGPS,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: gpsActivo ? Colors.green : Colors.red,
              ),
            ),

            const SizedBox(height: 8),

            // ==================================================
            // ESTADO ESP32
            // ==================================================

            Text(
              "ESP32: $estadoESP32",
              style: const TextStyle(
                fontSize: 15,
              ),
            ),

            Text(
              "$esp32IP:$esp32Puerto",
              style: const TextStyle(
                fontSize: 13,
              ),
            ),

            Text(
              "Paquetes enviados: $paquetesEnviados",
              style: const TextStyle(
                fontSize: 13,
              ),
            ),

            const SizedBox(height: 12),

            // ==================================================
            // DATOS GPS
            // ==================================================

            tarjetaDato(
              "Latitud",
              posicion == null
                  ? "---"
                  : posicion!.latitude.toStringAsFixed(6),
            ),

            tarjetaDato(
              "Longitud",
              posicion == null
                  ? "---"
                  : posicion!.longitude.toStringAsFixed(6),
            ),

            tarjetaDato(
              "Altitud",
              posicion == null
                  ? "---"
                  : "${posicion!.altitude.toStringAsFixed(1)} m",
            ),

            tarjetaDato(
              "Precision",
              posicion == null
                  ? "---"
                  : "${posicion!.accuracy.toStringAsFixed(1)} m",
            ),

            tarjetaDato(
              "Velocidad",
              posicion == null
                  ? "---"
                  : "${velocidadKmh.toStringAsFixed(2)} km/h",
            ),

            tarjetaDato(
              "Rumbo",
              posicion == null
                  ? "---"
                  : "${posicion!.heading.toStringAsFixed(1)} grados",
            ),

            const Spacer(),

            // ==================================================
            // BOTONES
            // ==================================================

            SizedBox(
              width: double.infinity,
              height: 55,

              child: ElevatedButton.icon(
                onPressed: gpsActivo ? null : iniciarGPS,

                icon: const Icon(
                  Icons.gps_fixed,
                ),

                label: const Text(
                  "INICIAR GPS",
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 8),

            SizedBox(
              width: double.infinity,
              height: 55,

              child: ElevatedButton.icon(
                onPressed: gpsActivo ? detenerGPS : null,

                icon: const Icon(
                  Icons.stop,
                ),

                label: const Text(
                  "DETENER GPS",
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // TARJETA DE DATOS
  // ============================================================

  Widget tarjetaDato(
    String nombre,
    String valor,
  ) {
    return Card(
      child: ListTile(
        title: Text(nombre),

        trailing: Text(
          valor,

          style: const TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}