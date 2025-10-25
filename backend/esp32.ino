/*
 * ESP32 Drumstick with MPU6050
 * Detects impacts and sends via WebSocket
 *
 * Libraries needed (install via PlatformIO or Arduino IDE):
 * - ArduinoWebsockets by Gil Maimon
 * - (Optional) Adafruit MPU6050 - only if MOCK_MODE = false
 * - (Optional) Adafruit Unified Sensor - only if MOCK_MODE = false
 */

// ============ MOCK MODE - SET TO false WHEN YOU HAVE MPU6050 ============
#define MOCK_MODE true  // Set to false when hardware is connected
// ========================================================================

#include <WiFi.h>
#include <ArduinoWebsockets.h>

#if !MOCK_MODE
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#endif

using namespace websockets;

// WiFi credentials
const char* ssid = "iPhone (280)";
const char* password = "432101234";

// WebSocket server (your computer's IP)
const char* ws_server = "172.20.10.4";
const int ws_port = 8080;

WebsocketsClient client;

#if MOCK_MODE
// Mock mode: use button or timer to simulate impacts
const int BUTTON_PIN = 0;  // Boot button on most ESP32 boards
bool lastButtonState = HIGH;
unsigned long mockTimer = 0;
const int MOCK_INTERVAL = 2000;  // Send mock impact every 2 seconds
#else
Adafruit_MPU6050 mpu;
// Impact detection parameters
const float IMPACT_THRESHOLD = 15.0;  // m/s^2 (tune this!)
const int COOLDOWN_MS = 100;          // Min time between hits
unsigned long lastHitTime = 0;
float accel_offset = 0;
#endif

void setup() {
  Serial.begin(115200);

#if MOCK_MODE
  Serial.println("Starting drumstick in MOCK MODE...");
  Serial.println("Press BOOT button to simulate impact");
  Serial.println("Or wait for automatic impacts every 2 seconds");
  pinMode(BUTTON_PIN, INPUT_PULLUP);
#else
  Serial.println("Starting drumstick with MPU6050...");

  // Initialize MPU6050
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050!");
    while (1) delay(10);
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  Serial.println("MPU6050 initialized");

  // Calibrate (assumes drumstick at rest)
  calibrate();
#endif

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // Connect to WebSocket server
  connectWebSocket();
}

void connectWebSocket() {
  Serial.println("Connecting to WebSocket server...");

  client.onMessage([](WebsocketsMessage message) {
    Serial.print("Received: ");
    Serial.println(message.data());
  });

  client.onEvent([](WebsocketsEvent event, String data) {
    if (event == WebsocketsEvent::ConnectionOpened) {
      Serial.println("WebSocket Connected!");
    } else if (event == WebsocketsEvent::ConnectionClosed) {
      Serial.println("WebSocket Disconnected!");
    }
  });

  bool connected = client.connect(ws_server, ws_port, "/drumstick");

  if (connected) {
    Serial.println("WebSocket connected!");
    client.send("{\"type\":\"connected\",\"device\":\"drumstick\"}");
  } else {
    Serial.println("WebSocket connection failed!");
  }
}

#if !MOCK_MODE
void calibrate() {
  Serial.println("Calibrating... keep drumstick still");
  float sum = 0;
  int samples = 100;

  for (int i = 0; i < samples; i++) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    float magnitude = sqrt(a.acceleration.x * a.acceleration.x +
                          a.acceleration.y * a.acceleration.y +
                          a.acceleration.z * a.acceleration.z);
    sum += magnitude;
    delay(10);
  }

  accel_offset = sum / samples;
  Serial.print("Calibration complete. Offset: ");
  Serial.println(accel_offset);
}
#endif

void loop() {
  // Keep WebSocket alive
  if (client.available()) {
    client.poll();
  } else {
    Serial.println("Reconnecting...");
    connectWebSocket();
    delay(1000);
  }

#if MOCK_MODE
  // Mock mode: button or timer triggers
  unsigned long now = millis();

  // Check button
  bool buttonState = digitalRead(BUTTON_PIN);
  if (buttonState == LOW && lastButtonState == HIGH) {
    sendMockImpact();
    delay(50);  // Debounce
  }
  lastButtonState = buttonState;

  // Or automatic timer
  if (now - mockTimer > MOCK_INTERVAL) {
    mockTimer = now;
    // sendMockImpact();
  }

  delay(50);

#else
  // Real MPU6050 mode
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // Calculate acceleration magnitude (subtract gravity)
  float magnitude = sqrt(a.acceleration.x * a.acceleration.x +
                        a.acceleration.y * a.acceleration.y +
                        a.acceleration.z * a.acceleration.z);

  magnitude = abs(magnitude - accel_offset);

  // Detect impact
  unsigned long now = millis();
  if (magnitude > IMPACT_THRESHOLD && (now - lastHitTime) > COOLDOWN_MS) {
    lastHitTime = now;

    // Calculate velocity (simplified: v = a * dt, assuming 10ms sampling)
    float velocity = magnitude * 0.01;

    sendImpact(velocity, magnitude);
  }

  delay(10);  // 100Hz sampling rate
#endif
}

void sendImpact(float velocity, float magnitude) {
  unsigned long now = millis();

  String json = "{\"type\":\"impact\",\"velocity\":" + String(velocity, 2) +
                ",\"magnitude\":" + String(magnitude, 2) +
                ",\"timestamp\":" + String(now) + "}";

  client.send(json);

  Serial.print("IMPACT! Magnitude: ");
  Serial.print(magnitude);
  Serial.print(" m/s^2, Velocity: ");
  Serial.println(velocity);
}

#if MOCK_MODE
void sendMockImpact() {
  // Generate random velocity between 0.5 and 2.0
  float velocity = random(50, 200) / 100.0;
  float magnitude = velocity / 0.01;  // Reverse calculation

  sendImpact(velocity, magnitude);

  Serial.println("(Mock impact sent)");
}
#endif