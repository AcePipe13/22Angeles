#ifndef GPS_INPUT_WIFI_H
#define GPS_INPUT_WIFI_H

#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

#include "gps_data.h"

// ============================================================
// CONFIGURACION WIFI
// ============================================================

#include "gps_secrets.h"

// ============================================================
// CONFIGURACION UDP
// ============================================================

const int GPS_UDP_PORT = 5000;

WiFiUDP gpsUdp;


// ============================================================
// INICIAR WIFI Y RECEPTOR UDP
// ============================================================

void iniciarGPSWiFi() {

  Serial.println();
  Serial.println("================================");
  Serial.println("     GPS INPUT - WIFI / UDP");
  Serial.println("================================");

  WiFi.mode(WIFI_STA);

  WiFi.begin(
    WIFI_SSID,
    WIFI_PASSWORD
  );

  Serial.print("Conectando a WiFi");

  while (WiFi.status() != WL_CONNECTED) {

    delay(500);

    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi conectado correctamente.");

  Serial.print("IP de la ESP32: ");
  Serial.println(WiFi.localIP());

  // Iniciar receptor UDP
  gpsUdp.begin(GPS_UDP_PORT);

  Serial.print("Puerto UDP: ");
  Serial.println(GPS_UDP_PORT);

  Serial.println();
  Serial.println("Esperando datos GPS del celular...");
}


// ============================================================
// LEER GPS RECIBIDO POR WIFI
// ============================================================

bool leerGPSWiFi(GPSData& datos) {

  // Revisar si llego un paquete UDP
  int packetSize = gpsUdp.parsePacket();

  if (packetSize <= 0) {
    return false;
  }

  // ==========================================================
  // LEER PAQUETE
  // ==========================================================

  char buffer[512];

  int len = gpsUdp.read(
    buffer,
    sizeof(buffer) - 1
  );

  if (len <= 0) {
    return false;
  }

  // Terminar correctamente el String recibido
  buffer[len] = '\0';


  // ==========================================================
  // DECODIFICAR JSON
  // ==========================================================

  StaticJsonDocument<512> json;

  DeserializationError error =
      deserializeJson(json, buffer);

  if (error) {

    Serial.print("ERROR JSON: ");
    Serial.println(error.c_str());

    return false;
  }


  // ==========================================================
  // GUARDAR LOS DATOS EN GPSData
  // ==========================================================

  datos.lat =
      json["lat"] | 0.0;

  datos.lon =
      json["lon"] | 0.0;

  datos.alt =
      json["alt"] | 0.0;

  datos.speed =
      json["speed"] | 0.0;

  datos.accuracy =
      json["accuracy"] | 0.0;

  datos.heading =
      json["heading"] | 0.0;

  datos.packet =
      json["packet"] | 0;

  datos.valid = true;


  // ==========================================================
  // PAQUETE RECIBIDO CORRECTAMENTE
  // ==========================================================

  return true;
}

#endif
