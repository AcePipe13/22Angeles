#include <Arduino.h>
#include "CytronMotorDriver.h"
#include "driver/gpio.h"

// U31 y U32: jumper entre los pines 1 y 2.
// Izquierdo: PWM = GPIO18, DIR = GPIO23.
// Derecho: PWM = GPIO21, DIR = GPIO22.

CytronMD motorIzquierdo(PWM_DIR, 18, 23);
CytronMD motorDerecho(PWM_DIR, 21, 22);

// Fase1 = A; Fase2 = B.
#define ENC_IZQ_A 33
#define ENC_IZQ_B 32
#define ENC_DER_A 26
#define ENC_DER_B 25

const int PPR_IZQ = 360;
const int PPR_DER = 360;

const int CUENTAS_REV_IZQ = PPR_IZQ * 4;
const int CUENTAS_REV_DER = PPR_DER * 4;

const int SIGNO_IZQ = -1;
const int SIGNO_DER = 1;

volatile long contadorIzq = 0;
volatile long contadorDer = 0;

volatile uint8_t estadoAnteriorIzq = 0;
volatile uint8_t estadoAnteriorDer = 0;

volatile uint32_t pulsosIzqA = 0;
volatile uint32_t pulsosIzqB = 0;
volatile uint32_t pulsosDerA = 0;
volatile uint32_t pulsosDerB = 0;

portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

const int8_t tablaCuadratura[16] = {
   0,  1, -1,  0,
  -1,  0,  0,  1,
   1,  0,  0, -1,
   0, -1,  1,  0
};

int pwmIzquierdo = 0;
int pwmDerecho = 0;

float rpmIzq = 0;
float rpmDer = 0;

long conteoAnteriorIzq = 0;
long conteoAnteriorDer = 0;

unsigned long tiempoAnterior = 0;
const unsigned long Ts = 50000;

String comando;

void IRAM_ATTR encoderIzq();
void IRAM_ATTR encoderDer();
void iniciarEncoders();
void calcularRPM();
void mostrarMotor(String nombre, int pwm);
void resetMotores();

void IRAM_ATTR encoderIzq() {
  uint8_t estado =
      (gpio_get_level((gpio_num_t)ENC_IZQ_A) << 1) |
       gpio_get_level((gpio_num_t)ENC_IZQ_B);

  portENTER_CRITICAL_ISR(&mux);

  uint8_t cambios = estadoAnteriorIzq ^ estado;

  if ((cambios & 0x02) && (estado & 0x02)) {
    pulsosIzqA++;
  }

  if ((cambios & 0x01) && (estado & 0x01)) {
    pulsosIzqB++;
  }

  uint8_t indice = (estadoAnteriorIzq << 2) | estado;

  contadorIzq += tablaCuadratura[indice];
  estadoAnteriorIzq = estado;

  portEXIT_CRITICAL_ISR(&mux);
}

void IRAM_ATTR encoderDer() {
  uint8_t estado =
      (gpio_get_level((gpio_num_t)ENC_DER_A) << 1) |
       gpio_get_level((gpio_num_t)ENC_DER_B);

  portENTER_CRITICAL_ISR(&mux);

  uint8_t cambios = estadoAnteriorDer ^ estado;

  if ((cambios & 0x02) && (estado & 0x02)) {
    pulsosDerA++;
  }

  if ((cambios & 0x01) && (estado & 0x01)) {
    pulsosDerB++;
  }

  uint8_t indice = (estadoAnteriorDer << 2) | estado;

  contadorDer += tablaCuadratura[indice];
  estadoAnteriorDer = estado;

  portEXIT_CRITICAL_ISR(&mux);
}

void iniciarEncoders() {
  pinMode(ENC_IZQ_A, INPUT_PULLUP);
  pinMode(ENC_IZQ_B, INPUT_PULLUP);

  pinMode(ENC_DER_A, INPUT_PULLUP);
  pinMode(ENC_DER_B, INPUT_PULLUP);

  estadoAnteriorIzq =
      (digitalRead(ENC_IZQ_A) << 1) |
       digitalRead(ENC_IZQ_B);

  estadoAnteriorDer =
      (digitalRead(ENC_DER_A) << 1) |
       digitalRead(ENC_DER_B);

  attachInterrupt(ENC_IZQ_A, encoderIzq, CHANGE);
  attachInterrupt(ENC_IZQ_B, encoderIzq, CHANGE);

  attachInterrupt(ENC_DER_A, encoderDer, CHANGE);
  attachInterrupt(ENC_DER_B, encoderDer, CHANGE);
}

void calcularRPM() {
  unsigned long ahora = micros();

  if (ahora - tiempoAnterior < Ts) {
    return;
  }

  tiempoAnterior = ahora;

  long cuentaI;
  long cuentaD;

  uint32_t cuentaIzqA;
  uint32_t cuentaIzqB;
  uint32_t cuentaDerA;
  uint32_t cuentaDerB;

  portENTER_CRITICAL(&mux);

  cuentaI = contadorIzq;
  cuentaD = contadorDer;

  cuentaIzqA = pulsosIzqA;
  cuentaIzqB = pulsosIzqB;

  cuentaDerA = pulsosDerA;
  cuentaDerB = pulsosDerB;

  portEXIT_CRITICAL(&mux);

  cuentaI *= SIGNO_IZQ;
  cuentaD *= SIGNO_DER;

  long deltaI = cuentaI - conteoAnteriorIzq;
  long deltaD = cuentaD - conteoAnteriorDer;

  float tiempo = Ts / 1000000.0;

  rpmIzq =
      (deltaI * 60.0) /
      (CUENTAS_REV_IZQ * tiempo);

  rpmDer =
      (deltaD * 60.0) /
      (CUENTAS_REV_DER * tiempo);

  conteoAnteriorIzq = cuentaI;
  conteoAnteriorDer = cuentaD;

  Serial.print("RPM IZQ: ");
  Serial.print(rpmIzq);

  Serial.print(" | PULSOS IZQ A: ");
  Serial.print(cuentaIzqA);

  Serial.print(" B: ");
  Serial.print(cuentaIzqB);

  Serial.print(" || RPM DER: ");
  Serial.print(rpmDer);

  Serial.print(" | PULSOS DER A: ");
  Serial.print(cuentaDerA);

  Serial.print(" B: ");
  Serial.println(cuentaDerB);
}

void mostrarMotor(String nombre, int pwm) {
  Serial.print(nombre);
  Serial.print(" -> ");

  if (pwm > 0) {
    Serial.print("ADELANTE | PWM = ");
    Serial.println(pwm);
  }
  else if (pwm < 0) {
    Serial.print("ATRAS | PWM = ");
    Serial.println(abs(pwm));
  }
  else {
    Serial.println("DETENIDO | PWM = 0");
  }
}

void resetMotores() {
  pwmIzquierdo = 0;
  pwmDerecho = 0;

  motorIzquierdo.setSpeed(0);
  motorDerecho.setSpeed(0);

  Serial.println("------------------------------");
  Serial.println("RESET EJECUTADO");
  Serial.println("Motor izquierdo: PWM = 0");
  Serial.println("Motor derecho: PWM = 0");
  Serial.println("------------------------------");
}

void setup() {
  Serial.begin(57600);

  pwmIzquierdo = 0;
  pwmDerecho = 0;

  motorIzquierdo.setSpeed(0);
  motorDerecho.setSpeed(0);

  iniciarEncoders();

  Serial.println();
  Serial.println("==============================");
  Serial.println("CYTRON MDDS30 + ENCODERS");
  Serial.println("==============================");
  Serial.println("Comandos:");
  Serial.println("M1 100  -> izquierdo adelante");
  Serial.println("M1 -100 -> izquierdo atras");
  Serial.println("M2 100  -> derecho adelante");
  Serial.println("M2 -100 -> derecho atras");
  Serial.println("RESET   -> detener ambos");
  Serial.println("==============================");
}

void loop() {
  if (Serial.available()) {
    comando = Serial.readStringUntil('\n');
    comando.trim();

    if (comando.equalsIgnoreCase("RESET")) {
      resetMotores();
    }
    else if (comando.startsWith("M1")) {
      pwmIzquierdo = comando.substring(2).toInt();
      pwmIzquierdo = constrain(pwmIzquierdo, -255, 255);

      motorIzquierdo.setSpeed(pwmIzquierdo);
      mostrarMotor("Motor izquierdo", pwmIzquierdo);
    }
    else if (comando.startsWith("M2")) {
      pwmDerecho = comando.substring(2).toInt();
      pwmDerecho = constrain(pwmDerecho, -255, 255);

      motorDerecho.setSpeed(pwmDerecho);
      mostrarMotor("Motor derecho", pwmDerecho);
    }
  }

  calcularRPM();
}