#include "WifiCam.hpp"
#include <WiFi.h>

static const char* WIFI_SSID = "iPhone de Benjamín";
static const char* WIFI_PASS = "9376pecos";

esp32cam::Resolution initialResolution;
WebServer server(80);

#define LED_PIN 4       // GPIO4 controla el flash LED
#define PWM_CHANNEL 0   // Canal PWM para el LED
#define PWM_FREQUENCY 5000 // Frecuencia de PWM en Hz
#define PWM_RESOLUTION 8   // Resolución de 8 bits (0 - 255)
#define LED_BRIGHTNESS 7  // Ajusta la intensidad (0-255)

void setup() {
  Serial.begin(115200);
  Serial.println();
  delay(2000);

  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  if (WiFi.waitForConnectResult() != WL_CONNECTED) {
    Serial.println("WiFi failure");
    delay(5000);
    ESP.restart();
  }
  Serial.println("WiFi connected");

  // Configurar el canal PWM para el LED
  ledcSetup(PWM_CHANNEL, PWM_FREQUENCY, PWM_RESOLUTION);
  ledcAttachPin(LED_PIN, PWM_CHANNEL);
  ledcWrite(PWM_CHANNEL, 0);  // Apagar LED al inicio

  {
    using namespace esp32cam;

    initialResolution = Resolution::find(1024, 768);

    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(initialResolution);
    cfg.setJpeg(80);

    bool ok = Camera.begin(cfg);
    if (!ok) {
      Serial.println("camera initialize failure");
      delay(5000);
      ESP.restart();
    }
    Serial.println("camera initialize success");

    // Encender el LED con brillo reducido
    ledcWrite(PWM_CHANNEL, LED_BRIGHTNESS);
  }

  Serial.println("camera starting");
  Serial.print("http://");
  Serial.println(WiFi.localIP());

  addRequestHandlers();
  server.begin();
}

void loop() {
  server.handleClient();
}
