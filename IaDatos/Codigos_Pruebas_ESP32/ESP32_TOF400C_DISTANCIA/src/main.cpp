#include <Arduino.h>
#include <Wire.h>
#include <VL53L1X.h>

VL53L1X sensor;

#define SDA_PIN 21
#define SCL_PIN 22

void setup()
{
    Serial.begin(9600);
    delay(1000);

    Wire.begin(SDA_PIN, SCL_PIN);
    Wire.setClock(100000);

    Serial.println("Inicializando VL53L1X...");

    sensor.setBus(&Wire);
    sensor.setTimeout(1000);

    if (!sensor.init())
    {
        Serial.println("ERROR al inicializar VL53L1X");
        while (1)
        {
            delay(1000);
        }
    }

    Serial.println("VL53L1X inicializado.");

    sensor.setDistanceMode(VL53L1X::Long);

    sensor.setMeasurementTimingBudget(50000);

    sensor.startContinuous(50);

    Serial.println("Midiendo...");
}

void loop()
{
    uint16_t distancia = sensor.read();

    if (sensor.timeoutOccurred())
    {
        Serial.println("Timeout");
        return;
    }

    Serial.print("Distancia: ");
    Serial.print(distancia);
    Serial.print(" mm  |  ");

    Serial.print(distancia / 10.0);
    Serial.println(" cm");

    delay(50);
}