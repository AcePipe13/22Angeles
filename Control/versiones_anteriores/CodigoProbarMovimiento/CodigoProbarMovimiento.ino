#include <Arduino.h>
#include <esp_arduino_version.h>
#include <driver/gpio.h>

// =====================================================
// COMANDOS DE LOS MOTORES
// =====================================================

// Rango: -100.0 a 100.0 %
// Positivo: adelante
// Negativo: reversa
// Cero: detenido

float comandoMotorIzquierdo = 100.0;
float comandoMotorDerecho   = 20.0;

// =====================================================
// PINES DEL L298N
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
// PINES DE LOS ENCODERS
// =====================================================

// Encoder izquierdo
const uint8_t PIN_ENCODER_IZQUIERDO_A = 33;
const uint8_t PIN_ENCODER_IZQUIERDO_B = 32;

// Encoder derecho
const uint8_t PIN_ENCODER_DERECHO_A = 35;
const uint8_t PIN_ENCODER_DERECHO_B = 34;

// =====================================================
// RESOLUCIÓN DE ENCODERS
// =====================================================

const int32_t PPR_ENCODER_IZQUIERDO = 408;
const int32_t PPR_ENCODER_DERECHO   = 240;

// Decodificación completa en cuadratura x4
const int32_t CUENTAS_REV_IZQUIERDO =
  PPR_ENCODER_IZQUIERDO * 4;  // 1632

const int32_t CUENTAS_REV_DERECHO =
  PPR_ENCODER_DERECHO * 4;    // 960

// Ambos encoders contaron negativo hacia adelante.
// Esto corrige el signo sin cambiar los cables.
const int8_t SIGNO_ENCODER_IZQUIERDO = -1;
const int8_t SIGNO_ENCODER_DERECHO   = -1;

// =====================================================
// CONFIGURACIÓN DE LA MEDICIÓN
// =====================================================

// 50 ms = 20 mediciones por segundo
const uint32_t PERIODO_MUESTREO_US = 50000;

// Variables donde quedará almacenada la velocidad
float rpmMotorIzquierdo = 0.0;
float rpmMotorDerecho   = 0.0;

// =====================================================
// CONFIGURACIÓN PWM
// =====================================================

const uint8_t CANAL_PWM_IZQUIERDO = 0;
const uint8_t CANAL_PWM_DERECHO   = 1;

const uint32_t FRECUENCIA_PWM = 20000;
const uint8_t RESOLUCION_PWM  = 10;

const uint32_t PWM_MAXIMO =
  (1UL << RESOLUCION_PWM) - 1UL;

// =====================================================
// VARIABLES DE LOS ENCODERS
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
// VARIABLES DE TIEMPO
// =====================================================

bool motoresActivos = false;

uint32_t tiempoInicioMs   = 0;
uint32_t tiempoAnteriorUs = 0;

int32_t conteoAnteriorIzquierdo = 0;
int32_t conteoAnteriorDerecho   = 0;

// =====================================================
// DECLARACIÓN DE FUNCIONES GENERALES
// =====================================================

void inicializarMotores();

void escribirMotorIzquierdo(float comando);
void escribirMotorDerecho(float comando);

void detenerMotores();

// =====================================================
// FUNCIONES DE ENCODERS Y VELOCIDAD
// =====================================================

void inicializarEncoders();
void reiniciarConteos();

void leerConteosCorregidos(
  int32_t &cuentasIzquierdo,
  int32_t &cuentasDerecho
);

bool actualizarVelocidades();

void IRAM_ATTR actualizarEncoderIzquierdo();
void IRAM_ATTR actualizarEncoderDerecho();

// =====================================================
// FUNCIONES DE PRUEBA
// =====================================================

void procesarMonitorSerial();
void iniciarPruebaVelocidad();
void detenerPruebaVelocidad();
void imprimirDatos();

// =====================================================
// FUNCIONES INTERNAS DEL L298N
// =====================================================

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
  Serial.begin(115200);

  inicializarMotores();
  inicializarEncoders();

  detenerMotores();
  reiniciarConteos();

  Serial.println();
  Serial.println("PRUEBA DE VELOCIDAD");
  Serial.println("R = iniciar motores y medir RPM");
  Serial.println("S = detener motores");
  Serial.println();
}

// =====================================================
// LOOP
// =====================================================

void loop()
{
  procesarMonitorSerial();

  if (motoresActivos)
  {
    if (actualizarVelocidades())
    {
      imprimirDatos();
    }
  }
}

// =====================================================
// CONTROL DE LA PRUEBA
// =====================================================

void procesarMonitorSerial()
{
  while (Serial.available() > 0)
  {
    char comando = Serial.read();

    if (comando == 'R' || comando == 'r')
    {
      iniciarPruebaVelocidad();
    }
    else if (comando == 'S' || comando == 's')
    {
      detenerPruebaVelocidad();
    }
  }
}

void iniciarPruebaVelocidad()
{
  detenerMotores();
  motoresActivos = false;

  delay(200);

  reiniciarConteos();

  conteoAnteriorIzquierdo = 0;
  conteoAnteriorDerecho   = 0;

  rpmMotorIzquierdo = 0.0;
  rpmMotorDerecho   = 0.0;

  tiempoInicioMs   = millis();
  tiempoAnteriorUs = micros();

  escribirMotorIzquierdo(
    comandoMotorIzquierdo
  );

  escribirMotorDerecho(
    comandoMotorDerecho
  );

  motoresActivos = true;

  Serial.println();
  Serial.println("Motores y medicion iniciados.");

  Serial.println(
    "tiempo_ms,duty_izq,cuentas_izq,rpm_izq,"
    "duty_der,cuentas_der,rpm_der"
  );
}

void detenerPruebaVelocidad()
{
  detenerMotores();
  motoresActivos = false;

  rpmMotorIzquierdo = 0.0;
  rpmMotorDerecho   = 0.0;

  int32_t cuentasIzquierdo;
  int32_t cuentasDerecho;

  leerConteosCorregidos(
    cuentasIzquierdo,
    cuentasDerecho
  );

  Serial.println();
  Serial.println("Motores detenidos.");

  Serial.print("Conteo final izquierdo: ");
  Serial.println(cuentasIzquierdo);

  Serial.print("Conteo final derecho: ");
  Serial.println(cuentasDerecho);

  Serial.println();
  Serial.println("Envia R para iniciar nuevamente.");
}

// =====================================================
// CÁLCULO DE VELOCIDAD
// =====================================================

bool actualizarVelocidades()
{
  uint32_t tiempoActualUs = micros();

  uint32_t tiempoTranscurridoUs =
    tiempoActualUs - tiempoAnteriorUs;

  if (
    tiempoTranscurridoUs <
    PERIODO_MUESTREO_US
  )
  {
    return false;
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

  tiempoAnteriorUs = tiempoActualUs;

  return true;
}

// =====================================================
// SALIDA SERIAL EN FORMATO CSV
// =====================================================

void imprimirDatos()
{
  int32_t cuentasIzquierdo;
  int32_t cuentasDerecho;

  leerConteosCorregidos(
    cuentasIzquierdo,
    cuentasDerecho
  );

  uint32_t tiempoPruebaMs =
    millis() - tiempoInicioMs;

  Serial.print(tiempoPruebaMs);
  Serial.print(",");

  Serial.print(comandoMotorIzquierdo, 1);
  Serial.print(",");

  Serial.print(cuentasIzquierdo);
  Serial.print(",");

  Serial.print(rpmMotorIzquierdo, 2);
  Serial.print(",");

  Serial.print(comandoMotorDerecho, 1);
  Serial.print(",");

  Serial.print(cuentasDerecho);
  Serial.print(",");

  Serial.println(rpmMotorDerecho, 2);
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
  int32_t conteoIzquierdoTemporal;
  int32_t conteoDerechoTemporal;

  portENTER_CRITICAL(&muxEncoders);

  conteoIzquierdoTemporal =
    conteoIzquierdo;

  conteoDerechoTemporal =
    conteoDerecho;

  portEXIT_CRITICAL(&muxEncoders);

  cuentasIzquierdo =
    conteoIzquierdoTemporal *
    SIGNO_ENCODER_IZQUIERDO;

  cuentasDerecho =
    conteoDerechoTemporal *
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

void inicializarMotores()
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

  if (
    !pwmIzquierdoConfigurado ||
    !pwmDerechoConfigurado
  )
  {
    Serial.println("ERROR configurando PWM.");

    while (true)
    {
      delay(1000);
    }
  }

  detenerMotores();
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
  escribirMotorIzquierdo(0.0);
  escribirMotorDerecho(0.0);
}

// =====================================================
// IMPLEMENTACIÓN DEL L298N
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

  if (comando == 0.0f)
  {
    escribirPWM(pinPWM, canalPWM, 0);

    digitalWrite(pinDireccion1, LOW);
    digitalWrite(pinDireccion2, LOW);

    return;
  }

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
    porcentaje * PWM_MAXIMO / 100.0f
  );
}

// =====================================================
// COMPATIBILIDAD ESP32 2.x Y 3.x
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

  return frecuenciaConfigurada > 0;

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
    0UL,
    PWM_MAXIMO
  );

#if ESP_ARDUINO_VERSION_MAJOR >= 3

  ledcWrite(pinPWM, duty);

#else

  ledcWrite(canalPWM, duty);

#endif
}