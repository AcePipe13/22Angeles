#include <Arduino.h>
#include <Wire.h>
#include <HardwareSerial.h>
#include <TinyGPSPlus.h>
#include <VL53L1X.h>


HardwareSerial GPS(2);
TinyGPSPlus gps;
VL53L1X sensor;

#define GPS_RX 16
#define GPS_TX 17

#define SDA_PIN 21
#define SCL_PIN 22

unsigned long tiempoAnterior = 0;
const unsigned long INTERVALO = 2000;


void mostrarGPS();
void mostrarTOF();
void setup()
{

    Serial.begin(9600);

    delay(1000);

    GPS.begin(
        9600,
        SERIAL_8N1,
        GPS_RX,
        GPS_TX
    );


    Serial.println();
    Serial.println("================================");
    Serial.println("       SISTEMA ESP32");
    Serial.println("================================");

    Serial.println("GPS iniciado");
    Serial.println("UART2 RX -> GPIO16");
    Serial.println("UART2 TX -> GPIO17");

    Wire.begin(
        SDA_PIN,
        SCL_PIN
    );


    Wire.setClock(100000);

    Serial.println();
    Serial.println("Inicializando VL53L1X...");

    sensor.setBus(&Wire);

    sensor.setTimeout(1000);

    if(!sensor.init())
    {

        Serial.println(
            "ERROR VL53L1X"
        );


        while(1)
        {
            delay(1000);
        }

    }

    Serial.println(
        "VL53L1X inicializado"
    );


    sensor.setDistanceMode(
        VL53L1X::Long
    );

    sensor.setMeasurementTimingBudget(
        50000
    );

    sensor.startContinuous(
        50
    );

    Serial.println();
    Serial.println("Sistema listo");
    Serial.println("================================");

}

void loop()
{

    while(GPS.available())
    {

        char dato = GPS.read();

        gps.encode(dato);

    }

    if(
        millis() - tiempoAnterior >= INTERVALO
      )
    {

        tiempoAnterior = millis();


        mostrarGPS();


        mostrarTOF();

    }


}

void mostrarGPS()
{

    Serial.println();
    Serial.println("-------------- GPS --------------");



    if(gps.location.isValid())
    {

        Serial.println(
            "Estado: GPS CON POSICION"
        );


        Serial.print(
            "Latitud:    "
        );

        Serial.println(
            gps.location.lat(),
            6
        );



        Serial.print(
            "Longitud:   "
        );

        Serial.println(
            gps.location.lng(),
            6
        );


    }

    else
    {

        Serial.println(
            "Estado: BUSCANDO SATELITES"
        );

        Serial.println(
            "Latitud:    ---"
        );

        Serial.println(
            "Longitud:   ---"
        );

    }

    Serial.print(
        "Altitud:    "
    );


    if(gps.altitude.isValid())
    {

        Serial.print(
            gps.altitude.meters(),
            2
        );

        Serial.println(
            " m"
        );

    }

    else
    {
        Serial.println("---");
    }




    Serial.print(
        "Satélites:  "
    );


    if(gps.satellites.isValid())
    {

        Serial.println(
            gps.satellites.value()
        );

    }

    else
    {

        Serial.println(
            "0"
        );

    }

}

void mostrarTOF()
{

    Serial.println();
    Serial.println("-------------- TOF VL53L1X --------------");



    uint16_t distancia = sensor.read();



    if(sensor.timeoutOccurred())
    {

        Serial.println(
            "Timeout sensor"
        );

        return;

    }



    Serial.print(
        "Distancia:  "
    );


    Serial.print(
        distancia
    );


    Serial.println(
        " mm"
    );



    Serial.print(
        "            "
    );


    Serial.print(
        distancia / 10.0
    );


    Serial.println(
        " cm"
    );



    Serial.println(
        "----------------------------------------"
    );


}