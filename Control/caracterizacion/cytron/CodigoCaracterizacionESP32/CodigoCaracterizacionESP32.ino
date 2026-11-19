
#include <Arduino.h>
#include "CytronMotorDriver.h"
#include "driver/gpio.h"


// =====================================================
// CONFIGURACION GENERAL
// =====================================================

const uint32_t BAUDIOS = 57600;
const uint32_t PERIODO_MUESTREO_US = 50000;
const uint32_t TIMEOUT_COMUNICACION_MS = 1500;


// =====================================================
// CYTRON MDDS30
// =====================================================

// Motor izquierdo 150 RPM
// PWM = GPIO 18 (U31: jumper 1-2)
// DIR = GPIO 23

CytronMD motorIzquierdo(PWM_DIR, 18, 23);


// Motor derecho 300 RPM
// PWM = GPIO 21 (U32: jumper 1-2)
// DIR = GPIO 22

CytronMD motorDerecho(PWM_DIR, 21, 22);


// =====================================================
// ENCODERS
// =====================================================

const uint8_t PIN_ENCODER_IZQUIERDO_A = 33;
const uint8_t PIN_ENCODER_IZQUIERDO_B = 32;

const uint8_t PIN_ENCODER_DERECHO_A = 26;
const uint8_t PIN_ENCODER_DERECHO_B = 25;


// =====================================================
// RESOLUCION DE ENCODERS
// =====================================================

const int32_t PPR_ENCODER_IZQUIERDO = 360;
const int32_t PPR_ENCODER_DERECHO = 360;

// Convencion de avance igual al codigo de probar movimiento.
const int8_t SIGNO_ENCODER_IZQUIERDO = -1;
const int8_t SIGNO_ENCODER_DERECHO = 1;

const int32_t CUENTAS_REV_IZQUIERDO =
    PPR_ENCODER_IZQUIERDO * 4;

const int32_t CUENTAS_REV_DERECHO =
    PPR_ENCODER_DERECHO * 4;


// =====================================================
// VARIABLES DE LOS MOTORES
// =====================================================

float comandoMotorIzquierdo = 0;
float comandoMotorDerecho = 0;

float rpmMotorIzquierdo = 0;
float rpmMotorDerecho = 0;


// =====================================================
// VARIABLES DE LOS ENCODERS
// =====================================================

volatile int32_t conteoIzquierdo = 0;
volatile int32_t conteoDerecho = 0;

volatile uint8_t estadoAnteriorIzquierdo = 0;
volatile uint8_t estadoAnteriorDerecho = 0;

portMUX_TYPE muxEncoders = portMUX_INITIALIZER_UNLOCKED;


// Tabla de decodificacion en cuadratura x4

const int8_t TABLA_CUADRATURA[16] = {
     0,  1, -1,  0,
    -1,  0,  0,  1,
     1,  0,  0, -1,
     0, -1,  1,  0
};


// =====================================================
// VARIABLES DE ADQUISICION
// =====================================================

bool adquisicionActiva = false;

uint32_t tiempoInicioUs = 0;
uint32_t tiempoMuestreoAnteriorUs = 0;
uint32_t ultimoContactoMs = 0;

int32_t conteoAnteriorIzquierdo = 0;
int32_t conteoAnteriorDerecho = 0;

char bufferComando[64];
size_t indiceBufferComando = 0;


// =====================================================
// PROTOTIPOS
// =====================================================

void leerPuertoSerial();
void procesarComando(const char *comando);

void escribirMotorIzquierdo(float comando);
void escribirMotorDerecho(float comando);
void detenerMotores();

void aplicarComandosPWM(float izquierdo, float derecho);

void iniciarAdquisicion();
void finalizarAdquisicion(const char *respuesta);
void verificarTimeoutComunicacion();
void actualizarTelemetria();

void inicializarEncoders();
void reiniciarConteos();

void IRAM_ATTR actualizarEncoderIzquierdo();
void IRAM_ATTR actualizarEncoderDerecho();

void leerConteosCorregidos(int32_t &izq, int32_t &der);


// =====================================================
// CONTROL DE MOTORES
// =====================================================

void escribirMotorIzquierdo(float comando)
{
    comando = constrain(comando, -100.0f, 100.0f);

    motorIzquierdo.setSpeed((int16_t)(comando * 2.55f));
}


void escribirMotorDerecho(float comando)
{
    comando = constrain(comando, -100.0f, 100.0f);

    motorDerecho.setSpeed((int16_t)(comando * 2.55f));
}


void detenerMotores()
{
    comandoMotorIzquierdo = 0;
    comandoMotorDerecho = 0;

    motorIzquierdo.setSpeed(0);
    motorDerecho.setSpeed(0);
}


// =====================================================
// SETUP
// =====================================================

void setup()
{
    Serial.begin(BAUDIOS);

    detenerMotores();

    inicializarEncoders();

    Serial.println("READY");
}


// =====================================================
// LOOP
// =====================================================

void loop()
{
    leerPuertoSerial();

    verificarTimeoutComunicacion();

    if (adquisicionActiva)
    {
        actualizarTelemetria();
    }
}


// =====================================================
// COMUNICACION SERIAL
// =====================================================

void leerPuertoSerial()
{
    while (Serial.available())
    {
        char c = Serial.read();

        if (c == '\r')
        {
            continue;
        }

        if (c == '\n')
        {
            bufferComando[indiceBufferComando] = '\0';

            procesarComando(bufferComando);

            indiceBufferComando = 0;
        }
        else
        {
            if (indiceBufferComando < sizeof(bufferComando) - 1)
            {
                bufferComando[indiceBufferComando++] = c;
            }
            else
            {
                indiceBufferComando = 0;
            }
        }
    }
}


void procesarComando(const char *comando)
{
    if (strcmp(comando, "PING") == 0)
    {
        ultimoContactoMs = millis();

        Serial.println("ACK,PONG");
        return;
    }


    if (strcmp(comando, "RESET") == 0)
    {
        detenerMotores();

        Serial.println("ACK,RESET");
        return;
    }


    if (strcmp(comando, "START") == 0)
    {
        iniciarAdquisicion();
        return;
    }


    if (strcmp(comando, "KEEP") == 0)
    {
        ultimoContactoMs = millis();
        return;
    }


    if (strcmp(comando, "STOP") == 0)
    {
        finalizarAdquisicion("ACK,STOP");
        return;
    }


    if (strncmp(comando, "PWM,", 4) == 0)
    {
        float izq = 0;
        float der = 0;

        if (sscanf(comando + 4, "%f,%f", &izq, &der) != 2)
        {
            Serial.println("ERR,BAD_PWM");
            return;
        }

        aplicarComandosPWM(izq, der);

        ultimoContactoMs = millis();

        Serial.print("ACK,PWM,");
        Serial.print(comandoMotorIzquierdo);
        Serial.print(",");
        Serial.println(comandoMotorDerecho);

        return;
    }

    Serial.println("ERR,UNKNOWN_COMMAND");
}


// =====================================================
// APLICAR PWM
// =====================================================

void aplicarComandosPWM(float izquierdo, float derecho)
{
    comandoMotorIzquierdo = constrain(izquierdo, -100.0f, 100.0f);
    comandoMotorDerecho = constrain(derecho, -100.0f, 100.0f);

    escribirMotorIzquierdo(comandoMotorIzquierdo);
    escribirMotorDerecho(comandoMotorDerecho);
}


// =====================================================
// INICIAR ADQUISICION
// =====================================================

void iniciarAdquisicion()
{
    detenerMotores();

    reiniciarConteos();

    conteoAnteriorIzquierdo = 0;
    conteoAnteriorDerecho = 0;

    tiempoInicioUs = micros();
    tiempoMuestreoAnteriorUs = tiempoInicioUs;

    ultimoContactoMs = millis();

    adquisicionActiva = true;

    Serial.println("ACK,START");
}


// =====================================================
// FINALIZAR ADQUISICION
// =====================================================

void finalizarAdquisicion(const char *respuesta)
{
    detenerMotores();

    adquisicionActiva = false;

    Serial.println(respuesta);
}


// =====================================================
// SEGURIDAD DE COMUNICACION
// =====================================================

void verificarTimeoutComunicacion()
{
    if (!adquisicionActiva)
    {
        return;
    }

    if (millis() - ultimoContactoMs > TIMEOUT_COMUNICACION_MS)
    {
        finalizarAdquisicion("ERR,COMM_TIMEOUT");
    }
}


// =====================================================
// TELEMETRIA PARA PYTHON
// =====================================================

void actualizarTelemetria()
{
    uint32_t ahora = micros();
    uint32_t dt = ahora - tiempoMuestreoAnteriorUs;

    if (dt < PERIODO_MUESTREO_US)
    {
        return;
    }

    int32_t cuentaI;
    int32_t cuentaD;

    leerConteosCorregidos(cuentaI, cuentaD);

    int32_t deltaI = cuentaI - conteoAnteriorIzquierdo;
    int32_t deltaD = cuentaD - conteoAnteriorDerecho;

    rpmMotorIzquierdo =
        (deltaI * 60000000.0f) /
        (CUENTAS_REV_IZQUIERDO * (float)dt);

    rpmMotorDerecho =
        (deltaD * 60000000.0f) /
        (CUENTAS_REV_DERECHO * (float)dt);

    conteoAnteriorIzquierdo = cuentaI;
    conteoAnteriorDerecho = cuentaD;

    tiempoMuestreoAnteriorUs = ahora;

    uint32_t tiempo = ahora - tiempoInicioUs;

    Serial.print("DATA,");
    Serial.print(tiempo);
    Serial.print(",");

    Serial.print(comandoMotorIzquierdo);
    Serial.print(",");

    Serial.print(cuentaI);
    Serial.print(",");

    Serial.print(rpmMotorIzquierdo);
    Serial.print(",");

    Serial.print(comandoMotorDerecho);
    Serial.print(",");

    Serial.print(cuentaD);
    Serial.print(",");

    Serial.println(rpmMotorDerecho);
}


// =====================================================
// INICIALIZAR ENCODERS
// =====================================================

void inicializarEncoders()
{
    pinMode(PIN_ENCODER_IZQUIERDO_A, INPUT_PULLUP);
    pinMode(PIN_ENCODER_IZQUIERDO_B, INPUT_PULLUP);

    pinMode(PIN_ENCODER_DERECHO_A, INPUT_PULLUP);
    pinMode(PIN_ENCODER_DERECHO_B, INPUT_PULLUP);

    reiniciarConteos();

    attachInterrupt(
        PIN_ENCODER_IZQUIERDO_A,
        actualizarEncoderIzquierdo,
        CHANGE
    );

    attachInterrupt(
        PIN_ENCODER_IZQUIERDO_B,
        actualizarEncoderIzquierdo,
        CHANGE
    );

    attachInterrupt(
        PIN_ENCODER_DERECHO_A,
        actualizarEncoderDerecho,
        CHANGE
    );

    attachInterrupt(
        PIN_ENCODER_DERECHO_B,
        actualizarEncoderDerecho,
        CHANGE
    );
}


// =====================================================
// INTERRUPCION ENCODER IZQUIERDO
// =====================================================

// CORRECCION: A es el bit mas significativo y B el menos significativo.

void IRAM_ATTR actualizarEncoderIzquierdo()
{
    uint8_t estado =
        (gpio_get_level((gpio_num_t)PIN_ENCODER_IZQUIERDO_A) << 1) |
         gpio_get_level((gpio_num_t)PIN_ENCODER_IZQUIERDO_B);

    portENTER_CRITICAL_ISR(&muxEncoders);

    uint8_t indice = (estadoAnteriorIzquierdo << 2) | estado;

    conteoIzquierdo += TABLA_CUADRATURA[indice];

    estadoAnteriorIzquierdo = estado;

    portEXIT_CRITICAL_ISR(&muxEncoders);
}


// =====================================================
// INTERRUPCION ENCODER DERECHO
// =====================================================

void IRAM_ATTR actualizarEncoderDerecho()
{
    uint8_t estado =
        (gpio_get_level((gpio_num_t)PIN_ENCODER_DERECHO_A) << 1) |
         gpio_get_level((gpio_num_t)PIN_ENCODER_DERECHO_B);

    portENTER_CRITICAL_ISR(&muxEncoders);

    uint8_t indice = (estadoAnteriorDerecho << 2) | estado;

    conteoDerecho += TABLA_CUADRATURA[indice];

    estadoAnteriorDerecho = estado;

    portEXIT_CRITICAL_ISR(&muxEncoders);
}


// =====================================================
// LEER CONTEOS
// =====================================================

void leerConteosCorregidos(int32_t &izq, int32_t &der)
{
    portENTER_CRITICAL(&muxEncoders);

    izq = conteoIzquierdo;
    der = conteoDerecho;

    portEXIT_CRITICAL(&muxEncoders);

    izq *= SIGNO_ENCODER_IZQUIERDO;
    der *= SIGNO_ENCODER_DERECHO;
}


// =====================================================
// REINICIAR CONTEOS
// =====================================================

void reiniciarConteos()
{
    portENTER_CRITICAL(&muxEncoders);

    conteoIzquierdo = 0;
    conteoDerecho = 0;

    // CORRECCION: el estado inicial izquierdo debe usar A/B,
    // igual que la interrupcion del encoder izquierdo.

    estadoAnteriorIzquierdo =
        (digitalRead(PIN_ENCODER_IZQUIERDO_A) << 1) |
         digitalRead(PIN_ENCODER_IZQUIERDO_B);

    estadoAnteriorDerecho =
        (digitalRead(PIN_ENCODER_DERECHO_A) << 1) |
         digitalRead(PIN_ENCODER_DERECHO_B);

    portEXIT_CRITICAL(&muxEncoders);
}
