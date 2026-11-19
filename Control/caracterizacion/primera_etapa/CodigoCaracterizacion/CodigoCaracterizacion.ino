#include <Arduino.h>
#include <esp_arduino_version.h>
#include <driver/gpio.h>
#include <cstring>
#include <cstdio>
#include <cmath>

// =====================================================
// CONFIGURACION GENERAL
// =====================================================

const uint32_t BAUDIOS = 115200;

// La ESP32 calcula y transmite velocidad cada 50 ms.
const uint32_t PERIODO_MUESTREO_US = 50000;

// Si Python deja de enviar KEEP, los motores se apagan.
const uint32_t TIMEOUT_COMUNICACION_MS = 1500;

// =====================================================
// PINES DEL L298N
// Esta es la unica seccion de actuacion que se reemplazara
// cuando se cambie al Cytron.
// =====================================================

// Motor izquierdo: 150 RPM
const uint8_t PIN_ENA = 13;
const uint8_t PIN_IN1 = 12;
const uint8_t PIN_IN2 = 14;

// Motor derecho: 300 RPM
const uint8_t PIN_ENB = 25;
const uint8_t PIN_IN3 = 27;
const uint8_t PIN_IN4 = 26;

// =====================================================
// PINES Y RESOLUCION DE LOS ENCODERS
// =====================================================

const uint8_t PIN_ENCODER_IZQUIERDO_A = 33;
const uint8_t PIN_ENCODER_IZQUIERDO_B = 32;

const uint8_t PIN_ENCODER_DERECHO_A = 35;
const uint8_t PIN_ENCODER_DERECHO_B = 34;

const int32_t PPR_ENCODER_IZQUIERDO = 408;
const int32_t PPR_ENCODER_DERECHO   = 240;

// Decodificacion completa A/B en cuadratura x4.
const int32_t CUENTAS_REV_IZQUIERDO =
  PPR_ENCODER_IZQUIERDO * 4;  // 1632

const int32_t CUENTAS_REV_DERECHO =
  PPR_ENCODER_DERECHO * 4;    // 960

// En las pruebas ambos encoders contaron negativo
// cuando los motores avanzaron.
const int8_t SIGNO_ENCODER_IZQUIERDO = -1;
const int8_t SIGNO_ENCODER_DERECHO   = -1;

// =====================================================
// CONFIGURACION PWM
// =====================================================

const uint8_t CANAL_PWM_IZQUIERDO = 0;
const uint8_t CANAL_PWM_DERECHO   = 1;

const uint32_t FRECUENCIA_PWM = 20000;
const uint8_t RESOLUCION_PWM  = 10;

const uint32_t PWM_MAXIMO =
  (1UL << RESOLUCION_PWM) - 1UL;

// =====================================================
// VARIABLES DE MOTORES Y VELOCIDAD
// =====================================================

float comandoMotorIzquierdo = 0.0f;
float comandoMotorDerecho   = 0.0f;

float rpmMotorIzquierdo = 0.0f;
float rpmMotorDerecho   = 0.0f;

// =====================================================
// VARIABLES DE ENCODERS
// =====================================================

volatile int32_t conteoIzquierdo = 0;
volatile int32_t conteoDerecho   = 0;

volatile uint8_t estadoAnteriorIzquierdo = 0;
volatile uint8_t estadoAnteriorDerecho   = 0;

portMUX_TYPE muxEncoders = portMUX_INITIALIZER_UNLOCKED;

DRAM_ATTR const int8_t TABLA_CUADRATURA[16] =
{
   0,  1, -1,  0,
  -1,  0,  0,  1,
   1,  0,  0, -1,
   0, -1,  1,  0
};

// =====================================================
// ESTADO DE ADQUISICION
// =====================================================

bool adquisicionActiva = false;

uint32_t tiempoInicioUs        = 0;
uint32_t tiempoMuestreoAnteriorUs = 0;
uint32_t ultimoContactoMs      = 0;

int32_t conteoAnteriorIzquierdo = 0;
int32_t conteoAnteriorDerecho   = 0;

// Buffer fijo para evitar fragmentacion de memoria.
char bufferComando[64];
size_t indiceBufferComando = 0;

// =====================================================
// DECLARACION DE FUNCIONES
// =====================================================

bool inicializarMotores();
void escribirMotorIzquierdo(float comando);
void escribirMotorDerecho(float comando);
void detenerMotores();

void inicializarEncoders();
void reiniciarConteos();

void leerConteosCorregidos(
  int32_t &cuentasIzquierdo,
  int32_t &cuentasDerecho
);

void IRAM_ATTR actualizarEncoderIzquierdo();
void IRAM_ATTR actualizarEncoderDerecho();

void leerPuertoSerial();
void procesarComando(const char *comando);
void iniciarAdquisicion();
void finalizarAdquisicion(const char *respuesta);
void aplicarComandosPWM(float izquierdo, float derecho);
void verificarTimeoutComunicacion();
void actualizarTelemetria();

void escribirCanalL298N(
  uint8_t pinPWM,
  uint8_t pinDireccion1,
  uint8_t pinDireccion2,
  uint8_t canalPWM,
  float comando
);

bool configurarSalidaPWM(
  uint8_t pinPWM,
  uint8_t canalPWM
);

void escribirPWM(
  uint8_t pinPWM,
  uint8_t canalPWM,
  uint32_t duty
);

uint32_t porcentajeADuty(float porcentaje);

// =====================================================
// SETUP
// =====================================================

void setup()
{
  Serial.begin(BAUDIOS);

  if (!inicializarMotores())
  {
    Serial.println("ERR,PWM_INIT");

    while (true)
    {
      detenerMotores();
      delay(1000);
    }
  }

  inicializarEncoders();
  detenerMotores();
  reiniciarConteos();

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
// PROTOCOLO SERIAL
//
// PING             -> comprobar comunicacion
// START            -> iniciar captura con motores en cero
// PWM,izq,der      -> aplicar comandos entre -100 y 100
// KEEP             -> mantener vivo el enlace
// STOP             -> apagar y terminar la captura
// =====================================================

void leerPuertoSerial()
{
  while (Serial.available() > 0)
  {
    char caracter = static_cast<char>(Serial.read());

    if (caracter == '\r')
    {
      continue;
    }

    if (caracter == '\n')
    {
      if (indiceBufferComando > 0)
      {
        bufferComando[indiceBufferComando] = '\0';
        procesarComando(bufferComando);
        indiceBufferComando = 0;
      }

      continue;
    }

    if (
      indiceBufferComando <
      sizeof(bufferComando) - 1
    )
    {
      bufferComando[indiceBufferComando++] =
        caracter;
    }
    else
    {
      indiceBufferComando = 0;
      Serial.println("ERR,LINE_TOO_LONG");
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
    float nuevoComandoIzquierdo;
    float nuevoComandoDerecho;

    int elementosLeidos = sscanf(
      comando + 4,
      "%f,%f",
      &nuevoComandoIzquierdo,
      &nuevoComandoDerecho
    );

    if (elementosLeidos != 2)
    {
      Serial.println("ERR,BAD_PWM_FORMAT");
      return;
    }

    if (!adquisicionActiva)
    {
      Serial.println("ERR,NOT_STARTED");
      return;
    }

    aplicarComandosPWM(
      nuevoComandoIzquierdo,
      nuevoComandoDerecho
    );

    ultimoContactoMs = millis();

    Serial.print("ACK,PWM,");
    Serial.print(comandoMotorIzquierdo, 3);
    Serial.print(",");
    Serial.println(comandoMotorDerecho, 3);

    return;
  }

  Serial.println("ERR,UNKNOWN_COMMAND");
}

void iniciarAdquisicion()
{
  detenerMotores();

  comandoMotorIzquierdo = 0.0f;
  comandoMotorDerecho   = 0.0f;

  rpmMotorIzquierdo = 0.0f;
  rpmMotorDerecho   = 0.0f;

  reiniciarConteos();

  conteoAnteriorIzquierdo = 0;
  conteoAnteriorDerecho   = 0;

  tiempoInicioUs = micros();
  tiempoMuestreoAnteriorUs = tiempoInicioUs;

  ultimoContactoMs = millis();
  adquisicionActiva = true;

  Serial.println("ACK,START");
}

void finalizarAdquisicion(const char *respuesta)
{
  detenerMotores();

  comandoMotorIzquierdo = 0.0f;
  comandoMotorDerecho   = 0.0f;

  rpmMotorIzquierdo = 0.0f;
  rpmMotorDerecho   = 0.0f;

  adquisicionActiva = false;

  if (respuesta != nullptr)
  {
    Serial.println(respuesta);
  }
}

void aplicarComandosPWM(
  float izquierdo,
  float derecho
)
{
  comandoMotorIzquierdo =
    constrain(izquierdo, -100.0f, 100.0f);

  comandoMotorDerecho =
    constrain(derecho, -100.0f, 100.0f);

  escribirMotorIzquierdo(
    comandoMotorIzquierdo
  );

  escribirMotorDerecho(
    comandoMotorDerecho
  );
}

void verificarTimeoutComunicacion()
{
  if (!adquisicionActiva)
  {
    return;
  }

  if (
    millis() - ultimoContactoMs >
    TIMEOUT_COMUNICACION_MS
  )
  {
    finalizarAdquisicion("ERR,COMM_TIMEOUT");
  }
}

// =====================================================
// TELEMETRIA Y CALCULO DE RPM
// =====================================================

void actualizarTelemetria()
{
  uint32_t tiempoActualUs = micros();

  uint32_t tiempoTranscurridoUs =
    tiempoActualUs -
    tiempoMuestreoAnteriorUs;

  if (
    tiempoTranscurridoUs <
    PERIODO_MUESTREO_US
  )
  {
    return;
  }

  int32_t conteoActualIzquierdo;
  int32_t conteoActualDerecho;

  leerConteosCorregidos(
    conteoActualIzquierdo,
    conteoActualDerecho
  );

  int32_t diferenciaIzquierdo =
    conteoActualIzquierdo -
    conteoAnteriorIzquierdo;

  int32_t diferenciaDerecho =
    conteoActualDerecho -
    conteoAnteriorDerecho;

  rpmMotorIzquierdo =
    (
      static_cast<float>(diferenciaIzquierdo) *
      60000000.0f
    )
    /
    (
      static_cast<float>(CUENTAS_REV_IZQUIERDO) *
      static_cast<float>(tiempoTranscurridoUs)
    );

  rpmMotorDerecho =
    (
      static_cast<float>(diferenciaDerecho) *
      60000000.0f
    )
    /
    (
      static_cast<float>(CUENTAS_REV_DERECHO) *
      static_cast<float>(tiempoTranscurridoUs)
    );

  conteoAnteriorIzquierdo =
    conteoActualIzquierdo;

  conteoAnteriorDerecho =
    conteoActualDerecho;

  tiempoMuestreoAnteriorUs =
    tiempoActualUs;

  uint32_t tiempoRelativoUs =
    tiempoActualUs -
    tiempoInicioUs;

  // DATA,time_us,duty_izq,cuentas_izq,rpm_izq,
  //      duty_der,cuentas_der,rpm_der
  Serial.print("DATA,");
  Serial.print(tiempoRelativoUs);
  Serial.print(",");

  Serial.print(comandoMotorIzquierdo, 3);
  Serial.print(",");
  Serial.print(conteoActualIzquierdo);
  Serial.print(",");
  Serial.print(rpmMotorIzquierdo, 3);
  Serial.print(",");

  Serial.print(comandoMotorDerecho, 3);
  Serial.print(",");
  Serial.print(conteoActualDerecho);
  Serial.print(",");
  Serial.println(rpmMotorDerecho, 3);
}

// =====================================================
// ENCODERS EN CUADRATURA x4
// =====================================================

void inicializarEncoders()
{
  pinMode(PIN_ENCODER_IZQUIERDO_A, INPUT);
  pinMode(PIN_ENCODER_IZQUIERDO_B, INPUT);

  pinMode(PIN_ENCODER_DERECHO_A, INPUT);
  pinMode(PIN_ENCODER_DERECHO_B, INPUT);

  reiniciarConteos();

  attachInterrupt(
    digitalPinToInterrupt(
      PIN_ENCODER_IZQUIERDO_A
    ),
    actualizarEncoderIzquierdo,
    CHANGE
  );

  attachInterrupt(
    digitalPinToInterrupt(
      PIN_ENCODER_IZQUIERDO_B
    ),
    actualizarEncoderIzquierdo,
    CHANGE
  );

  attachInterrupt(
    digitalPinToInterrupt(
      PIN_ENCODER_DERECHO_A
    ),
    actualizarEncoderDerecho,
    CHANGE
  );

  attachInterrupt(
    digitalPinToInterrupt(
      PIN_ENCODER_DERECHO_B
    ),
    actualizarEncoderDerecho,
    CHANGE
  );
}

void IRAM_ATTR actualizarEncoderIzquierdo()
{
  uint8_t estadoActual =
    (
      gpio_get_level(
        static_cast<gpio_num_t>(
          PIN_ENCODER_IZQUIERDO_A
        )
      ) << 1
    )
    |
    gpio_get_level(
      static_cast<gpio_num_t>(
        PIN_ENCODER_IZQUIERDO_B
      )
    );

  portENTER_CRITICAL_ISR(&muxEncoders);

  uint8_t indice =
    (estadoAnteriorIzquierdo << 2) |
    estadoActual;

  conteoIzquierdo +=
    TABLA_CUADRATURA[indice];

  estadoAnteriorIzquierdo =
    estadoActual;

  portEXIT_CRITICAL_ISR(&muxEncoders);
}

void IRAM_ATTR actualizarEncoderDerecho()
{
  uint8_t estadoActual =
    (
      gpio_get_level(
        static_cast<gpio_num_t>(
          PIN_ENCODER_DERECHO_A
        )
      ) << 1
    )
    |
    gpio_get_level(
      static_cast<gpio_num_t>(
        PIN_ENCODER_DERECHO_B
      )
    );

  portENTER_CRITICAL_ISR(&muxEncoders);

  uint8_t indice =
    (estadoAnteriorDerecho << 2) |
    estadoActual;

  conteoDerecho +=
    TABLA_CUADRATURA[indice];

  estadoAnteriorDerecho =
    estadoActual;

  portEXIT_CRITICAL_ISR(&muxEncoders);
}

void leerConteosCorregidos(
  int32_t &cuentasIzquierdo,
  int32_t &cuentasDerecho
)
{
  int32_t izquierdoTemporal;
  int32_t derechoTemporal;

  portENTER_CRITICAL(&muxEncoders);

  izquierdoTemporal = conteoIzquierdo;
  derechoTemporal   = conteoDerecho;

  portEXIT_CRITICAL(&muxEncoders);

  cuentasIzquierdo =
    izquierdoTemporal *
    SIGNO_ENCODER_IZQUIERDO;

  cuentasDerecho =
    derechoTemporal *
    SIGNO_ENCODER_DERECHO;
}

void reiniciarConteos()
{
  uint8_t estadoIzquierdo =
    (
      gpio_get_level(
        static_cast<gpio_num_t>(
          PIN_ENCODER_IZQUIERDO_A
        )
      ) << 1
    )
    |
    gpio_get_level(
      static_cast<gpio_num_t>(
        PIN_ENCODER_IZQUIERDO_B
      )
    );

  uint8_t estadoDerecho =
    (
      gpio_get_level(
        static_cast<gpio_num_t>(
          PIN_ENCODER_DERECHO_A
        )
      ) << 1
    )
    |
    gpio_get_level(
      static_cast<gpio_num_t>(
        PIN_ENCODER_DERECHO_B
      )
    );

  portENTER_CRITICAL(&muxEncoders);

  conteoIzquierdo = 0;
  conteoDerecho   = 0;

  estadoAnteriorIzquierdo =
    estadoIzquierdo;

  estadoAnteriorDerecho =
    estadoDerecho;

  portEXIT_CRITICAL(&muxEncoders);
}

// =====================================================
// INTERFAZ GENERAL DE MOTORES
// =====================================================

bool inicializarMotores()
{
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);

  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);

  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);

  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);

  bool pwmIzquierdoConfigurado =
    configurarSalidaPWM(
      PIN_ENA,
      CANAL_PWM_IZQUIERDO
    );

  bool pwmDerechoConfigurado =
    configurarSalidaPWM(
      PIN_ENB,
      CANAL_PWM_DERECHO
    );

  detenerMotores();

  return
    pwmIzquierdoConfigurado &&
    pwmDerechoConfigurado;
}

void escribirMotorIzquierdo(float comando)
{
  escribirCanalL298N(
    PIN_ENA,
    PIN_IN1,
    PIN_IN2,
    CANAL_PWM_IZQUIERDO,
    comando
  );
}

void escribirMotorDerecho(float comando)
{
  escribirCanalL298N(
    PIN_ENB,
    PIN_IN3,
    PIN_IN4,
    CANAL_PWM_DERECHO,
    comando
  );
}

void detenerMotores()
{
  escribirMotorIzquierdo(0.0f);
  escribirMotorDerecho(0.0f);
}

// =====================================================
// IMPLEMENTACION DEL DRIVER L298N
// =====================================================

void escribirCanalL298N(
  uint8_t pinPWM,
  uint8_t pinDireccion1,
  uint8_t pinDireccion2,
  uint8_t canalPWM,
  float comando
)
{
  comando = constrain(
    comando,
    -100.0f,
    100.0f
  );

  if (fabsf(comando) < 0.001f)
  {
    escribirPWM(pinPWM, canalPWM, 0);

    digitalWrite(pinDireccion1, LOW);
    digitalWrite(pinDireccion2, LOW);

    return;
  }

  // Se retira el PWM antes de cambiar la direccion.
  escribirPWM(pinPWM, canalPWM, 0);

  if (comando > 0.0f)
  {
    digitalWrite(pinDireccion1, HIGH);
    digitalWrite(pinDireccion2, LOW);
  }
  else
  {
    digitalWrite(pinDireccion1, LOW);
    digitalWrite(pinDireccion2, HIGH);
  }

  uint32_t duty =
    porcentajeADuty(fabsf(comando));

  escribirPWM(pinPWM, canalPWM, duty);
}

uint32_t porcentajeADuty(float porcentaje)
{
  porcentaje = constrain(
    porcentaje,
    0.0f,
    100.0f
  );

  return static_cast<uint32_t>(
    porcentaje *
    static_cast<float>(PWM_MAXIMO) /
    100.0f
  );
}

// =====================================================
// COMPATIBILIDAD ARDUINO-ESP32 2.x Y 3.x
// =====================================================

bool configurarSalidaPWM(
  uint8_t pinPWM,
  uint8_t canalPWM
)
{
#if ESP_ARDUINO_VERSION_MAJOR >= 3

  return ledcAttach(
    pinPWM,
    FRECUENCIA_PWM,
    RESOLUCION_PWM
  );

#else

  double frecuenciaConfigurada =
    ledcSetup(
      canalPWM,
      FRECUENCIA_PWM,
      RESOLUCION_PWM
    );

  ledcAttachPin(pinPWM, canalPWM);

  return frecuenciaConfigurada > 0.0;

#endif
}

void escribirPWM(
  uint8_t pinPWM,
  uint8_t canalPWM,
  uint32_t duty
)
{
  duty = constrain(
    duty,
    static_cast<uint32_t>(0),
    PWM_MAXIMO
  );

#if ESP_ARDUINO_VERSION_MAJOR >= 3

  ledcWrite(pinPWM, duty);

#else

  ledcWrite(canalPWM, duty);

#endif
}
