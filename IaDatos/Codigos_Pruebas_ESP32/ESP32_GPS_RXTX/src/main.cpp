#include <Arduino.h>
#include <HardwareSerial.h>
#include <TinyGPSPlus.h>

HardwareSerial GPS(2);
TinyGPSPlus gps;

#define GPS_RX 16     // TX del GPS -> GPIO 16
#define GPS_TX 17     // RX del GPS -> GPIO 17

unsigned long tiempoAnterior = 0;

// Mostrar información cada 2 segundos
const unsigned long INTERVALO = 2000;

void mostrarGPS();

void setup()
{
    // Comunicación ESP32 -> PC
    Serial.begin(9600);

    delay(1000);


    // Comunicación ESP32 -> GPS
    // El GY-GPS6MV2 trabaja normalmente a 9600 baud

    GPS.begin(
        9600,
        SERIAL_8N1,
        GPS_RX,
        GPS_TX
    );


    Serial.println();
    Serial.println("================================");
    Serial.println("        GY-GPS6MV2");
    Serial.println("================================");
    Serial.println("GPS iniciado correctamente");
    Serial.println();
    Serial.println("GPS Baud: 9600");
    Serial.println("RX ESP32: GPIO16");
    Serial.println("TX ESP32: GPIO17");
    Serial.println();
    Serial.println("Esperando satelites...");
    Serial.println("================================");
}

void loop()
{

    while (GPS.available() > 0)
    {
        char dato = GPS.read();

        // TinyGPSPlus procesa los mensajes NMEA
        gps.encode(dato);
    }

    if (millis() - tiempoAnterior >= INTERVALO)
    {
        tiempoAnterior = millis();

        mostrarGPS();
    }
}

void mostrarGPS()
{

    Serial.println();
    Serial.println("================================");
    Serial.println("            GPS");
    Serial.println("================================");

    if (gps.location.isValid())
    {

        Serial.println("Estado: GPS CON POSICION");
        Serial.println();


        Serial.print("Latitud:     ");
        Serial.println(
            gps.location.lat(),
            6
        );


        Serial.print("Longitud:    ");
        Serial.println(
            gps.location.lng(),
            6
        );
    }

    else
    {

        Serial.println("Estado: BUSCANDO SATELITES");
        Serial.println();

        Serial.println("Latitud:     ---");
        Serial.println("Longitud:    ---");
    }

    Serial.print("Altitud:     ");

    if (gps.altitude.isValid())
    {

        Serial.print(
            gps.altitude.meters(),
            2
        );

        Serial.println(" m");
    }

    else
    {
        Serial.println("---");
    }

    Serial.print("Satelites:   ");

    if (gps.satellites.isValid())
    {
        Serial.println(
            gps.satellites.value()
        );
    }

    else
    {
        Serial.println("0");
    }

    Serial.print("Velocidad:   ");

    if (gps.speed.isValid())
    {

        Serial.print(
            gps.speed.kmph(),
            2
        );

        Serial.println(" km/h");
    }

    else
    {
        Serial.println("---");
    }

    Serial.print("Rumbo:       ");

    if (gps.course.isValid())
    {

        Serial.print(
            gps.course.deg(),
            2
        );

        Serial.println(" grados");
    }

    else
    {
        Serial.println("---");
    }

    Serial.print("Hora UTC:    ");

    if (gps.time.isValid())
    {

        if (gps.time.hour() < 10)
        {
            Serial.print("0");
        }

        Serial.print(
            gps.time.hour()
        );


        Serial.print(":");


        if (gps.time.minute() < 10)
        {
            Serial.print("0");
        }

        Serial.print(
            gps.time.minute()
        );


        Serial.print(":");


        if (gps.time.second() < 10)
        {
            Serial.print("0");
        }

        Serial.println(
            gps.time.second()
        );
    }

    else
    {
        Serial.println("--:--:--");
    }

    Serial.print("Fecha:       ");

    if (gps.date.isValid())
    {

        if (gps.date.day() < 10)
        {
            Serial.print("0");
        }

        Serial.print(
            gps.date.day()
        );

        Serial.print("/");


        if (gps.date.month() < 10)
        {
            Serial.print("0");
        }

        Serial.print(
            gps.date.month()
        );

        Serial.print("/");

        Serial.println(
            gps.date.year()
        );
    }

    else
    {
        Serial.println("--/--/----");
    }


    Serial.println("================================");
}