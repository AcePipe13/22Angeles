#include <Arduino.h>

unsigned long tiempoAnterior = 0;
const unsigned long INTERVALO = 5000;

void setup() {
  Serial.begin(9600);

  // Pequeña espera para iniciar el puerto serial
  delay(1000);

  Serial.println("ESP32 iniciada.");
}

void loop() {

  // ------------------------------------------------
  // ENVIAR SALUDO CADA 5 SEGUNDOS
  // ------------------------------------------------
  if (millis() - tiempoAnterior >= INTERVALO) {
    tiempoAnterior = millis();

    Serial.println("Hola Raspberry, soy ESP32");
  }


  // ------------------------------------------------
  // RECIBIR MENSAJES DE LA RASPBERRY
  // ------------------------------------------------
  if (Serial.available() > 0) {

    String mensaje = Serial.readStringUntil('\n');
    mensaje.trim();

    if (mensaje.length() > 0) {
      Serial.print("Raspberry me dijo: ");
      Serial.println(mensaje);
    }
  }
}