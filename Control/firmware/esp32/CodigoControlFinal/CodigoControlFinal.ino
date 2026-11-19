#include <Arduino.h>
#include "CytronMotorDriver.h"
#include <driver/gpio.h>
#include <cmath>
#include <cstdio>
#include <cstring>

// =====================================================
// CONFIGURACION GENERAL
// =====================================================

const uint32_t BAUDIOS = 57600;
const uint32_t PERIODO_CONTROL_US = 50000;  // Ts = 0.05 s

// =====================================================
// CYTRON MDDS30 - PWM / DIR
// =====================================================
// Cableado para este programa (canales independientes, Sign-Magnitude):
// Motor izquierdo: GPIO18 -> AN1; GPIO23 -> IN1. U31: jumper 1-2.
// Motor derecho:   GPIO21 -> AN2; GPIO22 -> IN2. U32: jumper 1-2.
// Asignacion comprobada con el codigo de probar movimiento.
// Unir GND de la ESP32 y GND de senales del Cytron.
// AN1/IN1 deben pertenecer al mismo motor; igual para AN2/IN2.

const uint8_t PIN_PWM_IZQUIERDO = 18;
const uint8_t PIN_DIR_IZQUIERDO = 23;

const uint8_t PIN_PWM_DERECHO = 21;
const uint8_t PIN_DIR_DERECHO = 22;

// Mismo sentido del mando que probar movimiento: sin inversion adicional.
const int8_t SIGNO_MOTOR_IZQUIERDO = 1;
const int8_t SIGNO_MOTOR_DERECHO = 1;

CytronMD motorIzquierdo(
  PWM_DIR,
  PIN_PWM_IZQUIERDO,
  PIN_DIR_IZQUIERDO
);

CytronMD motorDerecho(
  PWM_DIR,
  PIN_PWM_DERECHO,
  PIN_DIR_DERECHO
);

// =====================================================
// ENCODERS
// =====================================================

const uint8_t PIN_ENCODER_IZQUIERDO_A = 33;
const uint8_t PIN_ENCODER_IZQUIERDO_B = 32;
const uint8_t PIN_ENCODER_DERECHO_A = 26;
const uint8_t PIN_ENCODER_DERECHO_B = 25;

// Mismos encoders de 360 PPR de probarmovimiento.
// Se cuentan los cambios de ambos canales: cuadratura x4.

const int32_t PPR_ENCODER_IZQUIERDO = 360;
const int32_t PPR_ENCODER_DERECHO = 360;

const int32_t CUENTAS_REV_IZQUIERDO =
  PPR_ENCODER_IZQUIERDO * 4;

const int32_t CUENTAS_REV_DERECHO =
  PPR_ENCODER_DERECHO * 4;

// Misma lectura A/B y correccion que en probar movimiento.
const int8_t SIGNO_ENCODER_IZQUIERDO = -1;
const int8_t SIGNO_ENCODER_DERECHO = 1;

volatile int32_t conteoIzquierdo = 0;
volatile int32_t conteoDerecho = 0;
volatile uint8_t estadoAnteriorIzquierdo = 0;
volatile uint8_t estadoAnteriorDerecho = 0;

portMUX_TYPE muxEncoders = portMUX_INITIALIZER_UNLOCKED;

DRAM_ATTR const int8_t TABLA_CUADRATURA[16] = {
   0,  1, -1,  0,
  -1,  0,  0,  1,
   1,  0,  0, -1,
   0, -1,  1,  0
};

// =====================================================
// CONTROLADORES DE VELOCIDAD
//
// u[k] = AU*u[k-1] + B0*e[k] + B1*e[k-1]
//
// Cada motor conserva su propio estado. Los coeficientes
// del motor derecho quedan separados para poder sustituirlos
// cuando se identifique su planta.
// =====================================================

struct CoeficientesPI {
  float au;
  float b0;
  float b1;
};

struct EstadoPI {
  float referenciaRPM;
  float errorAnterior;
  float salidaAnterior;
  int8_t ultimoSentido;
  bool esperandoInversion;
};

const CoeficientesPI PI_IZQUIERDO = {
  1.00000000f,
  1.40769293f,
  -1.13312504f
};

// Ganancias provisionales: validar y resintonizar con mediciones.
const CoeficientesPI PI_DERECHO = {
  1.00000000f,
  0.54608491f,
  -0.36916756f
};

const float REFERENCIA_MAX_IZQUIERDA_RPM = 120.0f;
const float REFERENCIA_MAX_DERECHA_RPM = 120.0f;

const float PWM_MINIMO = -100.0f;
const float PWM_MAXIMO_PORCENTAJE = 100.0f;
const float REFERENCIA_CERO_RPM = 0.01f;
const float UMBRAL_INVERSION_RPM = 5.0f; // Esperar a casi detenerse antes de invertir
const float PASO_MAX_PWM = 6.0f;         // Cambio maximo de PWM por ciclo (40 ms)

EstadoPI estadoIzquierdo = {0.0f, 0.0f, 0.0f, 0, false};
EstadoPI estadoDerecho = {0.0f, 0.0f, 0.0f, 0, false};

float rpmMotorIzquierdo = 0.0f;
float rpmMotorDerecho = 0.0f;
float comandoMotorIzquierdo = 0.0f;
float comandoMotorDerecho = 0.0f;

// =====================================================
// ESTADO DEL PROGRAMA
// =====================================================

bool controlActivo = false;

uint32_t tiempoInicioUs = 0;
uint32_t tiempoControlAnteriorUs = 0;

int32_t conteoAnteriorIzquierdo = 0;
int32_t conteoAnteriorDerecho = 0;

char bufferComando[64];
size_t indiceBufferComando = 0;

// =====================================================
// DECLARACIONES
// =====================================================

bool inicializarMotores();
void escribirMotorIzquierdo(float comando);
void escribirMotorDerecho(float comando);
void detenerMotores();

void inicializarEncoders();
void reiniciarConteos();

void leerConteosCorregidos(
  int32_t &izquierdo,
  int32_t &derecho
);

void IRAM_ATTR actualizarEncoderIzquierdo();
void IRAM_ATTR actualizarEncoderDerecho();

void leerPuertoSerial();
void procesarComando(const char *comando);
void iniciarControl();
void finalizarControl(const char *respuesta);
void cambiarReferencias(float izquierda, float derecha);
void actualizarControlVelocidad();

void transmitirTelemetria(
  uint32_t tiempoRelativoUs,
  int32_t cuentasIzquierda,
  int32_t cuentasDerecha
);

void reiniciarPI(EstadoPI &estado, bool borrarReferencia);

void actualizarReferenciaPI(
  EstadoPI &estado,
  float nuevaReferencia
);

float calcularPI(
  const CoeficientesPI &coeficientes,
  EstadoPI &estado,
  float rpmMedida
);

// =====================================================
// SETUP Y LOOP
// =====================================================

void setup() {
  Serial.begin(BAUDIOS);

  if (!inicializarMotores()) {
    Serial.println("ERR,PWM_INIT");

    while (true) {
      detenerMotores();
      delay(1000);
    }
  }

  inicializarEncoders();
  detenerMotores();

  Serial.println("READY");
}

void loop() {
  leerPuertoSerial();

  if (controlActivo) {
    actualizarControlVelocidad();
  }
}

// =====================================================
// PROTOCOLO SERIAL
//
// PING              -> prueba de comunicacion
// START             -> habilita el control en 0 RPM
// RPM,izq,der       -> referencias firmadas de velocidad
// KEEP              -> aceptado por compatibilidad
// STOP              -> detiene los motores
// DIR               -> consulta los GPIO de direccion y sus niveles actuales
//
// Ejemplo: RPM,60,60 controla ambos motores a 60 RPM.
// =====================================================

void leerPuertoSerial() {
  while (Serial.available() > 0) {
    char caracter = static_cast<char>(Serial.read());

    if (caracter == '\r') {
      continue;
    }

    if (caracter == '\n') {
      if (indiceBufferComando > 0) {
        bufferComando[indiceBufferComando] = '\0';
        procesarComando(bufferComando);
        indiceBufferComando = 0;
      }

      continue;
    }

    if (indiceBufferComando < sizeof(bufferComando) - 1) {
      bufferComando[indiceBufferComando++] = caracter;
    } else {
      indiceBufferComando = 0;
      Serial.println("ERR,LINE_TOO_LONG");
    }
  }
}

void procesarComando(const char *comando) {
  if (strcmp(comando, "PING") == 0) {
    Serial.println("ACK,PONG");
    return;
  }

  if (strcmp(comando, "START") == 0) {
    iniciarControl();
    return;
  }

  if (strcmp(comando, "KEEP") == 0) {
    return;
  }

  if (strcmp(comando, "DIR") == 0) {
    // Solo consulta: no cambia el PWM, las referencias ni el control.
    // Son los niveles en la ESP32; revisar tambien el cable hasta IN1/IN2.
    Serial.print("ACK,DIR,IZQ_GPIO");
    Serial.print(PIN_DIR_IZQUIERDO);
    Serial.print(",");
    Serial.print(digitalRead(PIN_DIR_IZQUIERDO));
    Serial.print(",DER_GPIO");
    Serial.print(PIN_DIR_DERECHO);
    Serial.print(",");
    Serial.println(digitalRead(PIN_DIR_DERECHO));
    return;
  }

  if (strcmp(comando, "STOP") == 0) {
    finalizarControl("ACK,STOP");
    return;
  }

  if (strncmp(comando, "RPM,", 4) == 0) {
    float referenciaIzquierda;
    float referenciaDerecha;

    int elementos = sscanf(
      comando + 4,
      "%f,%f",
      &referenciaIzquierda,
      &referenciaDerecha
    );

    if (elementos != 2 ||
        !std::isfinite(referenciaIzquierda) ||
        !std::isfinite(referenciaDerecha)) {
      Serial.println("ERR,BAD_RPM_FORMAT");
      return;
    }

    if (!controlActivo) {
      Serial.println("ERR,NOT_STARTED");
      return;
    }

    cambiarReferencias(
      referenciaIzquierda,
      referenciaDerecha
    );

    Serial.print("ACK,RPM,");
    Serial.print(estadoIzquierdo.referenciaRPM, 3);
    Serial.print(",");
    Serial.println(estadoDerecho.referenciaRPM, 3);

    return;
  }

  Serial.println("ERR,UNKNOWN_COMMAND");
}

void iniciarControl() {
  detenerMotores();

  reiniciarPI(estadoIzquierdo, true);
  reiniciarPI(estadoDerecho, true);

  rpmMotorIzquierdo = 0.0f;
  rpmMotorDerecho = 0.0f;

  comandoMotorIzquierdo = 0.0f;
  comandoMotorDerecho = 0.0f;

  reiniciarConteos();

  conteoAnteriorIzquierdo = 0;
  conteoAnteriorDerecho = 0;

  tiempoInicioUs = micros();
  tiempoControlAnteriorUs = tiempoInicioUs;

  controlActivo = true;

  Serial.println("ACK,START");
}

void finalizarControl(const char *respuesta) {
  controlActivo = false;

  detenerMotores();

  reiniciarPI(estadoIzquierdo, true);
  reiniciarPI(estadoDerecho, true);

  comandoMotorIzquierdo = 0.0f;
  comandoMotorDerecho = 0.0f;

  if (respuesta != nullptr) {
    Serial.println(respuesta);
  }
}

void cambiarReferencias(float izquierda, float derecha) {
  izquierda = constrain(
    izquierda,
    -REFERENCIA_MAX_IZQUIERDA_RPM,
    REFERENCIA_MAX_IZQUIERDA_RPM
  );

  derecha = constrain(
    derecha,
    -REFERENCIA_MAX_DERECHA_RPM,
    REFERENCIA_MAX_DERECHA_RPM
  );

  bool cambioSentidoIzquierdo =
    estadoIzquierdo.referenciaRPM * izquierda < 0.0f;

  bool cambioSentidoDerecho =
    estadoDerecho.referenciaRPM * derecha < 0.0f;

  actualizarReferenciaPI(estadoIzquierdo, izquierda);
  actualizarReferenciaPI(estadoDerecho, derecha);

  if (cambioSentidoIzquierdo ||
      fabsf(estadoIzquierdo.referenciaRPM) < REFERENCIA_CERO_RPM) {
    comandoMotorIzquierdo = 0.0f;
    escribirMotorIzquierdo(0.0f);
  }

  if (cambioSentidoDerecho ||
      fabsf(estadoDerecho.referenciaRPM) < REFERENCIA_CERO_RPM) {
    comandoMotorDerecho = 0.0f;
    escribirMotorDerecho(0.0f);
  }
}

// =====================================================
// CONTROL DE VELOCIDAD Y TELEMETRIA
// =====================================================

void actualizarControlVelocidad() {
  uint32_t tiempoActualUs = micros();

  uint32_t tiempoTranscurridoUs =
    tiempoActualUs - tiempoControlAnteriorUs;

  if (tiempoTranscurridoUs < PERIODO_CONTROL_US) {
    return;
  }

  int32_t conteoActualIzquierdo;
  int32_t conteoActualDerecho;

  leerConteosCorregidos(
    conteoActualIzquierdo,
    conteoActualDerecho
  );

  int32_t diferenciaIzquierda =
    conteoActualIzquierdo - conteoAnteriorIzquierdo;

  int32_t diferenciaDerecha =
    conteoActualDerecho - conteoAnteriorDerecho;

  // RPM = cuentas del intervalo * 60 /
  //       (cuentas por vuelta * dt en segundos).
  //
  // Como dt esta en microsegundos, se utiliza 60000000.

  rpmMotorIzquierdo =
    (static_cast<float>(diferenciaIzquierda) * 60000000.0f) /
    (static_cast<float>(CUENTAS_REV_IZQUIERDO) *
     static_cast<float>(tiempoTranscurridoUs));

  rpmMotorDerecho =
    (static_cast<float>(diferenciaDerecha) * 60000000.0f) /
    (static_cast<float>(CUENTAS_REV_DERECHO) *
     static_cast<float>(tiempoTranscurridoUs));

  comandoMotorIzquierdo = calcularPI(
    PI_IZQUIERDO,
    estadoIzquierdo,
    rpmMotorIzquierdo
  );

  comandoMotorDerecho = calcularPI(
    PI_DERECHO,
    estadoDerecho,
    rpmMotorDerecho
  );

  escribirMotorIzquierdo(comandoMotorIzquierdo);
  escribirMotorDerecho(comandoMotorDerecho);

  conteoAnteriorIzquierdo = conteoActualIzquierdo;
  conteoAnteriorDerecho = conteoActualDerecho;

  tiempoControlAnteriorUs = tiempoActualUs;

  transmitirTelemetria(
    tiempoActualUs - tiempoInicioUs,
    conteoActualIzquierdo,
    conteoActualDerecho
  );
}

float calcularPI(
  const CoeficientesPI &coeficientes,
  EstadoPI &estado,
  float rpmMedida
) {
  if (fabsf(estado.referenciaRPM) < REFERENCIA_CERO_RPM) {
    reiniciarPI(estado, false);
    return 0.0f;
  }

  // Al invertir, dejar el PWM en cero hasta que el motor casi se detenga.
  // Se usa la MAGNITUD porque el signo del encoder aun requiere validacion.
  if (estado.esperandoInversion) {
    if (fabsf(rpmMedida) > UMBRAL_INVERSION_RPM) {
      reiniciarPI(estado, false);
      return 0.0f;
    }
    estado.esperandoInversion = false;
    reiniciarPI(estado, false);
  }

  // El PI controla solo la magnitud de la velocidad y del PWM.
  // La direccion depende EXCLUSIVAMENTE del comando RPM recibido.
  float errorActual = fabsf(estado.referenciaRPM) - fabsf(rpmMedida);
  float salida = coeficientes.au * estado.salidaAnterior +
                 coeficientes.b0 * errorActual +
                 coeficientes.b1 * estado.errorAnterior;

  if (!std::isfinite(salida)) {
    reiniciarPI(estado, false);
    return 0.0f;
  }

  // Nunca permitir PWM de sentido opuesto por correccion de velocidad.
  salida = constrain(salida, 0.0f, PWM_MAXIMO_PORCENTAJE);
  salida = constrain(salida,
                    fmaxf(0.0f, estado.salidaAnterior - PASO_MAX_PWM),
                    fminf(PWM_MAXIMO_PORCENTAJE,
                          estado.salidaAnterior + PASO_MAX_PWM));

  estado.errorAnterior = errorActual;
  estado.salidaAnterior = salida;
  return (estado.referenciaRPM > 0.0f) ? salida : -salida;
}

void actualizarReferenciaPI(
  EstadoPI &estado,
  float nuevaReferencia
) {
  bool esCero = fabsf(nuevaReferencia) < REFERENCIA_CERO_RPM;
  int8_t sentidoNuevo = esCero ? 0 : (nuevaReferencia > 0.0f ? 1 : -1);

  // Conservar el ultimo sentido incluso si se envia RPM,0,0.
  if (sentidoNuevo != 0) {
    if (estado.ultimoSentido != 0 &&
        sentidoNuevo != estado.ultimoSentido) {
      estado.esperandoInversion = true;
      reiniciarPI(estado, false);
    }
    estado.ultimoSentido = sentidoNuevo;
  }

  if (esCero) {
    reiniciarPI(estado, false);
  }
  estado.referenciaRPM = esCero ? 0.0f : nuevaReferencia;
}

void reiniciarPI(EstadoPI &estado, bool borrarReferencia) {
  if (borrarReferencia) {
    estado.referenciaRPM = 0.0f;
    estado.ultimoSentido = 0;
    estado.esperandoInversion = false;
  }
  estado.errorAnterior = 0.0f;
  estado.salidaAnterior = 0.0f;
}

void transmitirTelemetria(
  uint32_t tiempoRelativoUs,
  int32_t cuentasIzquierda,
  int32_t cuentasDerecha
) {
  // DATA,t_us,ref_izq,rpm_izq,pwm_izq,cuentas_izq,
  //      ref_der,rpm_der,pwm_der,cuentas_der

  Serial.print("DATA,");
  Serial.print(tiempoRelativoUs);
  Serial.print(",");

  Serial.print(estadoIzquierdo.referenciaRPM, 3);
  Serial.print(",");

  Serial.print(rpmMotorIzquierdo, 3);
  Serial.print(",");

  Serial.print(comandoMotorIzquierdo, 3);
  Serial.print(",");

  Serial.print(cuentasIzquierda);
  Serial.print(",");

  Serial.print(estadoDerecho.referenciaRPM, 3);
  Serial.print(",");

  Serial.print(rpmMotorDerecho, 3);
  Serial.print(",");

  Serial.print(comandoMotorDerecho, 3);
  Serial.print(",");

  Serial.println(cuentasDerecha);
}

// =====================================================
// ENCODERS EN CUADRATURA x4
// =====================================================

void inicializarEncoders() {
  pinMode(PIN_ENCODER_IZQUIERDO_A, INPUT_PULLUP);
  pinMode(PIN_ENCODER_IZQUIERDO_B, INPUT_PULLUP);

  pinMode(PIN_ENCODER_DERECHO_A, INPUT_PULLUP);
  pinMode(PIN_ENCODER_DERECHO_B, INPUT_PULLUP);

  reiniciarConteos();

  attachInterrupt(
    digitalPinToInterrupt(PIN_ENCODER_IZQUIERDO_A),
    actualizarEncoderIzquierdo,
    CHANGE
  );

  attachInterrupt(
    digitalPinToInterrupt(PIN_ENCODER_IZQUIERDO_B),
    actualizarEncoderIzquierdo,
    CHANGE
  );

  attachInterrupt(
    digitalPinToInterrupt(PIN_ENCODER_DERECHO_A),
    actualizarEncoderDerecho,
    CHANGE
  );

  attachInterrupt(
    digitalPinToInterrupt(PIN_ENCODER_DERECHO_B),
    actualizarEncoderDerecho,
    CHANGE
  );
}

void IRAM_ATTR actualizarEncoderIzquierdo() {
  uint8_t estadoActual =
    (
      gpio_get_level(
        static_cast<gpio_num_t>(PIN_ENCODER_IZQUIERDO_A)
      ) << 1
    ) |
    gpio_get_level(
      static_cast<gpio_num_t>(PIN_ENCODER_IZQUIERDO_B)
    );

  portENTER_CRITICAL_ISR(&muxEncoders);

  uint8_t indice =
    (estadoAnteriorIzquierdo << 2) | estadoActual;

  conteoIzquierdo += TABLA_CUADRATURA[indice];
  estadoAnteriorIzquierdo = estadoActual;

  portEXIT_CRITICAL_ISR(&muxEncoders);
}

void IRAM_ATTR actualizarEncoderDerecho() {
  uint8_t estadoActual =
    (
      gpio_get_level(
        static_cast<gpio_num_t>(PIN_ENCODER_DERECHO_A)
      ) << 1
    ) |
    gpio_get_level(
      static_cast<gpio_num_t>(PIN_ENCODER_DERECHO_B)
    );

  portENTER_CRITICAL_ISR(&muxEncoders);

  uint8_t indice =
    (estadoAnteriorDerecho << 2) | estadoActual;

  conteoDerecho += TABLA_CUADRATURA[indice];
  estadoAnteriorDerecho = estadoActual;

  portEXIT_CRITICAL_ISR(&muxEncoders);
}

void leerConteosCorregidos(
  int32_t &izquierdo,
  int32_t &derecho
) {
  int32_t izquierdoTemporal;
  int32_t derechoTemporal;

  portENTER_CRITICAL(&muxEncoders);

  izquierdoTemporal = conteoIzquierdo;
  derechoTemporal = conteoDerecho;

  portEXIT_CRITICAL(&muxEncoders);

  izquierdo = izquierdoTemporal * SIGNO_ENCODER_IZQUIERDO;
  derecho = derechoTemporal * SIGNO_ENCODER_DERECHO;
}

void reiniciarConteos() {
  uint8_t estadoIzquierdoActual =
    (
      gpio_get_level(
        static_cast<gpio_num_t>(PIN_ENCODER_IZQUIERDO_A)
      ) << 1
    ) |
    gpio_get_level(
      static_cast<gpio_num_t>(PIN_ENCODER_IZQUIERDO_B)
    );

  uint8_t estadoDerechoActual =
    (
      gpio_get_level(
        static_cast<gpio_num_t>(PIN_ENCODER_DERECHO_A)
      ) << 1
    ) |
    gpio_get_level(
      static_cast<gpio_num_t>(PIN_ENCODER_DERECHO_B)
    );

  portENTER_CRITICAL(&muxEncoders);

  conteoIzquierdo = 0;
  conteoDerecho = 0;

  estadoAnteriorIzquierdo = estadoIzquierdoActual;
  estadoAnteriorDerecho = estadoDerechoActual;

  portEXIT_CRITICAL(&muxEncoders);
}

// =====================================================
// INTERFAZ GENERAL DE MOTORES
// =====================================================

bool inicializarMotores() {
  detenerMotores();
  return true;
}

void escribirMotorIzquierdo(float comando) {
  comando = constrain(
    comando,
    PWM_MINIMO,
    PWM_MAXIMO_PORCENTAJE
  );

  motorIzquierdo.setSpeed(
    static_cast<int16_t>(
      lroundf(
        SIGNO_MOTOR_IZQUIERDO *
        comando * 255.0f / 100.0f
      )
    )
  );
}

void escribirMotorDerecho(float comando) {
  comando = constrain(
    comando,
    PWM_MINIMO,
    PWM_MAXIMO_PORCENTAJE
  );

  motorDerecho.setSpeed(
    static_cast<int16_t>(
      lroundf(
        SIGNO_MOTOR_DERECHO *
        comando * 255.0f / 100.0f
      )
    )
  );
}

void detenerMotores() {
  escribirMotorIzquierdo(0.0f);
  escribirMotorDerecho(0.0f);

  digitalWrite(PIN_DIR_IZQUIERDO, LOW);
  digitalWrite(PIN_DIR_DERECHO, LOW);
}
