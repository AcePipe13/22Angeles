#ifndef GPS_OUTPUT_SERIAL_H
#define GPS_OUTPUT_SERIAL_H

#include <ArduinoJson.h>
#include "gps_data.h"

// ============================================================
// ENVIAR GPS AL PC / RASPBERRY POR SERIAL
// ============================================================

void enviarGPSSerial(const GPSData& datos) {

  StaticJsonDocument<512> json;

  json["lat"] = datos.lat;
  json["lon"] = datos.lon;
  json["alt"] = datos.alt;
  json["speed"] = datos.speed;
  json["accuracy"] = datos.accuracy;
  json["heading"] = datos.heading;
  json["packet"] = datos.packet;
  json["valid"] = datos.valid;

  serializeJson(json, Serial);

  Serial.println();
}

#endif