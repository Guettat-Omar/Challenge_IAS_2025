// =========================
// GLOBAL TIMERS
// =========================
#include "time.h"
unsigned long lastMinuteStart = 0;
const unsigned long ONE_MINUTE = 60000UL;

// =========================
// MQ7 VARIABLES
// =========================
const int MQ7_PIN = 34;           // MQ7 analog pin
int mq7_buffer[60];               // one reading per second
int mq7_index = 0;
int lastValidCO = 0;
bool mq7Valid = false;            // valid only during the stable phase
unsigned long mq7CycleStart = 0;  // to detect heating/valid windows

// =========================
// DSM501A VARIABLES
// =========================
const int DSM_PIN = 35;
const unsigned long DSM_WINDOW_MS = 30000UL;

volatile unsigned long dsmLowStartMicros = 0;
volatile unsigned long dsmLowAccumMicros = 0;

unsigned long dsmWindowStart = 0;
bool dsmFirstWindow = true;

float pm25_win1 = 0, pm10_win1 = 0;
float pm25_win2 = 0, pm10_win2 = 0;

// =========================
// BMP280 VARIABLES
// =========================
#include <Adafruit_BMP280.h>
Adafruit_BMP280 bmp;

float currentTemp = 0.0;
float currentPressure = 0.0;
//MQTT Setup
#include <WiFi.h>
#include <PubSubClient.h>

// MQTT CONFIG
const char* ssid        = "OPPO Reno5";
const char* password    = "1234567890";

const char* mqtt_server = "broker.hivemq.com";
const int   mqtt_port   = 1883;
const char* mqtt_topic  = "omar/factory/sensors";
const char* mqtt_control_topic = "omar/factory/ventilation";


WiFiClient espClient;
PubSubClient client(espClient);

// =========================
// FAN CONTROL (L298N)
// =========================
const int FAN_PWM = 15;   // ENA
const int FAN_IN1 = 18;
const int FAN_IN2 = 19;

const int FAN_PWM_CH = 5;
const int FAN_PWM_FREQ = 25000;
const int FAN_PWM_RES = 8;


void setupTime() {
  // Use NTP servers
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");

  Serial.print("Waiting for time sync...");
  time_t now = time(nullptr);
  while (now < 100000) {   // wait until time is not 1970
    delay(500);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println("\nTime synchronized!");
}

void setupWiFi() {
  Serial.print("Connecting to WiFi ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected.");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}


void readBMP280() {
  currentTemp = bmp.readTemperature();
  currentPressure = bmp.readPressure() / 100.0;  // convert Pa → hPa
}
//update heating cycle MQ7
void updateMQ7Validity() {
  unsigned long elapsed = (millis() - mq7CycleStart) / 1000; //Calculates how many milliseconds have passed since mq7CycleStart

  if (elapsed < 60) {
    mq7Valid = false;  // heating
  } 
  else if (elapsed < 150) {
    mq7Valid = true;   // stable
  } 
  else {
    mq7CycleStart = millis(); // restart cycle
    mq7Valid = false;
  }
}
//1-second sampling into buffer MQ7
void sampleMQ7() {
  int raw = analogRead(MQ7_PIN);

  if (!mq7Valid) {
    raw = lastValidCO;     // use previous stable value
  } else {
    lastValidCO = raw;     // update stable value
  }

  mq7_buffer[mq7_index] = raw;
  mq7_index = (mq7_index + 1) % 60;
}
//compute CO mean + max MQ7
void computeMQ7Stats(float &mean, int &maxv) {
  long sum = 0;
  maxv = mq7_buffer[0];

  for (int i = 0; i < 60; i++) {
    sum += mq7_buffer[i];
    if (mq7_buffer[i] > maxv) maxv = mq7_buffer[i];
  }
  mean = sum / 60.0;
}
//Interrupt to measure LOW durations DSM501A
void IRAM_ATTR dsm_isr() {
  int level = digitalRead(DSM_PIN);
  unsigned long now = micros();

  if (level == LOW)
    dsmLowStartMicros = now;
  else {
    if (dsmLowStartMicros != 0) {
      dsmLowAccumMicros += (now - dsmLowStartMicros);
      dsmLowStartMicros = 0;
    }
  }
}
//Conversion formula DSM501A
void computePM(float ratio, float &pm25, float &pm10) {
  float conc = 0.172 * ratio * ratio + 0.002204 * ratio + 0.000002;
  pm25 = 1.1 * conc + 3.3;
  pm10 = 1.3 * conc + 5.2;
}
//End of 30-second window
void processDSMWindow() {
  noInterrupts();
  unsigned long lowMicros = dsmLowAccumMicros;
  dsmLowAccumMicros = 0;
  interrupts();

  float lowSec = lowMicros / 1e6;
  float ratio = lowSec / (DSM_WINDOW_MS / 1000.0);

  float pm25, pm10;
  computePM(ratio, pm25, pm10);

  if (dsmFirstWindow) {
    pm25_win1 = pm25;
    pm10_win1 = pm10;
    dsmFirstWindow = false;
  } else {
    pm25_win2 = pm25;
    pm10_win2 = pm10;
    dsmFirstWindow = true;
  }
}
//Final PM of the minute
void computeMinutePM(float &pm25, float &pm10) {
  pm25 = (pm25_win1 + pm25_win2) / 2.0;
  pm10 = (pm10_win1 + pm10_win2) / 2.0;
}
//FINAL MINUTE DATA PROCESSOR
void processMinuteCycle() {
  // BMP280
  readBMP280();

  // MQ7
  float co_mean;
  int co_max;
  computeMQ7Stats(co_mean, co_max);

  // DSM501A
  float pm25, pm10;
  computeMinutePM(pm25, pm10);

  // === Timestamp ===
  time_t now = time(nullptr);
  char timestamp[30];
  strftime(timestamp, sizeof(timestamp), "%Y-%m-%dT%H:%M:%SZ", gmtime(&now));

  // Output (later → send MQTT)
  Serial.println("---- MINUTE SUMMARY ----");
  Serial.print("Temp: "); Serial.println(currentTemp);
  Serial.print("Pressure: "); Serial.println(currentPressure);
  Serial.print("CO mean: "); Serial.println(co_mean);
  Serial.print("CO max : "); Serial.println(co_max);
  Serial.print("PM2.5  : "); Serial.println(pm25);
  Serial.print("PM10   : "); Serial.println(pm10);

  // === Build JSON manually ===
  String payload = "{";
  payload += "\"timestamp\":\"" + String(timestamp) + "\",";
  payload += "\"temp\":" + String(currentTemp, 2) + ",";
  payload += "\"pressure\":" + String(currentPressure, 2) + ",";
  payload += "\"co_mean\":" + String(co_mean, 2) + ",";
  payload += "\"co_max\":" + String(co_max) + ",";
  payload += "\"co_valid\":" + String(mq7Valid ? "true" : "false") + ",";
  payload += "\"pm2_5\":" + String(pm25, 2) + ",";
  payload += "\"pm10\":" + String(pm10, 2);
  payload += "}";

  Serial.println("=== MQTT Payload ===");
  Serial.println(payload);

  // === Send via MQTT ===
  client.publish(mqtt_topic, payload.c_str());
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT ... ");

    if (client.connect("ESP32_AirMonitor")) {
      Serial.println("connected.");

      // SUBSCRIBE HERE — ONLY ON SUCCESSFUL CONNECT
      client.subscribe(mqtt_control_topic);
      Serial.println("Subscribed to: omar/factory/ventilation/control");

    } else {
      Serial.print("failed (");
      Serial.print(client.state());
      Serial.println("). Retry in 2 seconds...");
      delay(2000);
    }
  }
}


int percentToPWM(int percent) {
  if (percent < 0) percent = 0;
  if (percent > 100) percent = 100;
  return (percent * 255) / 100;
}

void setFanSpeed(int percent) {
  int pwmValue = percentToPWM(percent);
  ledcWrite(FAN_PWM_CH, pwmValue);

  Serial.print("⚙ FAN speed set to ");
  Serial.print(percent);
  Serial.print("% → PWM ");
  Serial.println(pwmValue);
}

void mqttCallback(char* topic, byte* message, unsigned int length) {

  Serial.print("\n📥 MQTT Message received on: ");
  Serial.println(topic);

  if (strcmp(topic, mqtt_control_topic) != 0) {
    Serial.println("Ignoring message from other topic.");
    return;
  }

  // Convert payload to string
  String payload;
  for (unsigned int i = 0; i < length; i++)
    payload += (char)message[i];

  Serial.println("Payload: " + payload);

  // Extract fan speed
  int keyIndex = payload.indexOf("\"fan_supply_speed\":");
  if (keyIndex != -1) {
    int start = payload.indexOf(":", keyIndex) + 1;
    int end = payload.indexOf(",", start);
    if (end == -1) end = payload.indexOf("}", start);

    int speed = payload.substring(start, end).toInt();
    setFanSpeed(speed);   // <-- FAN CONTROL HERE
  }
}




void setup() {
  Serial.begin(115200);
  delay(200);

  setupWiFi();
  setupTime();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);


  // MQ7 cycle start
  mq7CycleStart = millis();

  pinMode(FAN_IN1, OUTPUT);
  pinMode(FAN_IN2, OUTPUT);

  // Fixed direction (supply fan)
  digitalWrite(FAN_IN1, HIGH);
  digitalWrite(FAN_IN2, LOW);

  // PWM setup
  ledcSetup(FAN_PWM_CH, FAN_PWM_FREQ, FAN_PWM_RES);
  ledcAttachPin(FAN_PWM, FAN_PWM_CH);
  ledcWrite(FAN_PWM_CH, 0);  // Fan OFF initially


  // DSM501A setup
  pinMode(DSM_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(DSM_PIN), dsm_isr, CHANGE);
  dsmWindowStart = millis();

  // BMP280
  if (!bmp.begin(0x76)) {
    Serial.println("BMP ERROR!");
    while(1);
  }

  // Start 60-second cycle
  lastMinuteStart = millis();
}


void loop() {

  // --- MQTT connection ---
  if (!client.connected()) {
  reconnectMQTT();
  }
  client.loop();

  // --- Update MQ7 cycle (heating/valid) ---
  updateMQ7Validity();

  // ============ MQ7 sampling every 1 sec ============
  static unsigned long lastMQ7Sample = 0;
  if (millis() - lastMQ7Sample >= 1000) {
    lastMQ7Sample = millis();
    sampleMQ7();
  }

  // ============ DSM501A window every 30 sec ============
  if (millis() - dsmWindowStart >= DSM_WINDOW_MS) {
    dsmWindowStart = millis();
    processDSMWindow();
  }

  // ============ Full minute summary ============
  if (millis() - lastMinuteStart >= ONE_MINUTE) {
    lastMinuteStart = millis();
    processMinuteCycle();

  }
}

