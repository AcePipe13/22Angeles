#include "gps_data.h"
#include "gps_input_wifi.h"
#include "gps_output_serial.h"

// ============================================================
// VARIABLE PRINCIPAL GPS
// ============================================================

GPSData gpsData;


// ============================================================
// SETUP
// ============================================================

void setup() {

  Serial.begin(115200);

  delay(1000);

  Serial.println();
  Serial.println("==============================");
  Serial.println("      SISTEMA GPS ESP32");
  Serial.println("==============================");

  iniciarGPSWiFi();
}


// ============================================================
// LOOP
// ============================================================

void loop() {

  // Si llega una nueva posicion desde el celular
  if (leerGPSWiFi(gpsData)) {

    // Enviar esa posicion al PC / Raspberry
    enviarGPSSerial(gpsData);
  }
}