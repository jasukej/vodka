/*
 * ESP32 Drumstick with MPU6050 - BLE Version
 * Detects impacts and sends via Bluetooth Low Energy
 *
 * Libraries needed:
 * - Adafruit MPU6050
 * - Adafruit Unified Sensor
 * - ArduinoJson
 * - ESP32 BLE Arduino (built-in)
 *
 * IMPORTANT: Remove/Uninstall ArduinoBLE library if installed
 * Only use ESP32's built-in BLE library
 */

#include "BLEDevice.h"
#include "BLEServer.h"
#include "BLEUtils.h"
#include "BLE2902.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <ArduinoJson.h>

// BLE Service and Characteristic UUIDs
#define SERVICE_UUID        "12345678-1234-1234-1234-123456789abc"
#define IMPACT_CHAR_UUID    "87654321-4321-4321-4321-cba987654321"
#define STATUS_CHAR_UUID    "11111111-2222-3333-4444-555555555555"
#define CONFIG_CHAR_UUID    "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

// Device info
#define DEVICE_NAME "VODKA-Drumstick"
#define MANUFACTURER "VODKA-Team"

BLEServer* pServer = NULL;
BLECharacteristic* pImpactCharacteristic = NULL;
BLECharacteristic* pStatusCharacteristic = NULL;
BLECharacteristic* pConfigCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

Adafruit_MPU6050 mpu;

// Impact detection parameters
float IMPACT_THRESHOLD = 15.0;  // m/s^2 (configurable via BLE)
const int COOLDOWN_MS = 50;
unsigned long lastHitTime = 0;
float accel_offset = 0;

// Gravity tracking
float gravity_x = 0;
float gravity_y = 0;
float gravity_z = 0;
const float GRAVITY_ALPHA = 0.98;

// Battery monitoring (optional)
#define BATTERY_PIN A0
float batteryVoltage = 0;

// Statistics
unsigned long totalHits = 0;
unsigned long uptime = 0;

struct Vec3 {
  float x, y, z;
};

float vec3_magnitude(Vec3 v) {
  return sqrt(v.x*v.x + v.y*v.y + v.z*v.z);
}

void vec3_normalize(Vec3* v) {
  float mag = vec3_magnitude(*v);
  if (mag > 0.001) {
    v->x /= mag;
    v->y /= mag;
    v->z /= mag;
  }
}

float vec3_dot(Vec3 a, Vec3 b) {
  return a.x*b.x + a.y*b.y + a.z*b.z;
}

String getStrikeDirection(Vec3 impact_vector, Vec3 gravity_vector) {
  vec3_normalize(&impact_vector);
  vec3_normalize(&gravity_vector);

  float dot_product = vec3_dot(impact_vector, gravity_vector);

  if (dot_product > 0.3) {
    return "DOWN";
  } else if (dot_product < -0.3) {
    return "UP";
  } else {
    return "SIDE";
  }
}

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
      Serial.println("✅ BLE Client connected!");

      // Send welcome message
      sendStatusUpdate("connected", "BLE connection established");
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      Serial.println("❌ BLE Client disconnected!");
    }
};

class ConfigCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* pCharacteristic) {
      String value = pCharacteristic->getValue().c_str();
      Serial.println("📝 Config received: " + value);

      // Parse JSON config
      DynamicJsonDocument doc(1024);
      deserializeJson(doc, value);

      if (doc.containsKey("impact_threshold")) {
        IMPACT_THRESHOLD = doc["impact_threshold"];
        Serial.println("🎯 Impact threshold set to: " + String(IMPACT_THRESHOLD));
      }

      if (doc.containsKey("calibrate")) {
        if (doc["calibrate"]) {
          Serial.println("🔧 Calibrating...");
          calibrate();
          sendStatusUpdate("calibrated", "Calibration complete");
        }
      }

      if (doc.containsKey("reset_stats")) {
        if (doc["reset_stats"]) {
          totalHits = 0;
          Serial.println("📊 Statistics reset");
          sendStatusUpdate("stats_reset", "Hit counter reset");
        }
      }
    }
};

void setup() {
  Serial.begin(115200);
  Serial.println("🥁 Starting VODKA Drumstick (BLE Version)...");

  // Initialize I2C for MPU6050
  Wire.begin(18, 19);

  // Initialize MPU6050
  if (!mpu.begin()) {
    Serial.println("❌ Failed to find MPU6050!");
    while (1) delay(10);
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  Serial.println("✅ MPU6050 initialized");

  // Calibrate sensor
  calibrate();

  // Initialize BLE
  initBLE();

  Serial.println("🟢 VODKA Drumstick ready! Waiting for BLE connection...");
}

void initBLE() {
  // Initialize BLE
  BLEDevice::init(DEVICE_NAME);

  // Create BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create BLE Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create Impact Characteristic (for sending hit data)
  pImpactCharacteristic = pService->createCharacteristic(
                      IMPACT_CHAR_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_NOTIFY
                    );
  pImpactCharacteristic->addDescriptor(new BLE2902());

  // Create Status Characteristic (for device status/battery/stats)
  pStatusCharacteristic = pService->createCharacteristic(
                      STATUS_CHAR_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_NOTIFY
                    );
  pStatusCharacteristic->addDescriptor(new BLE2902());

  // Create Config Characteristic (for receiving configuration)
  pConfigCharacteristic = pService->createCharacteristic(
                      CONFIG_CHAR_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_WRITE
                    );
  pConfigCharacteristic->setCallbacks(new ConfigCallbacks());

  // Start the service
  pService->start();

  // Start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);  // Set value to 0x00 to not advertise this parameter
  BLEDevice::startAdvertising();

  Serial.println("📡 BLE advertising started - device discoverable as: " + String(DEVICE_NAME));
}

void calibrate() {
  Serial.println("🔧 Calibrating... Keep drumstick still!");

  float sum_x = 0, sum_y = 0, sum_z = 0;
  int samples = 100;

  for (int i = 0; i < samples; i++) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    sum_x += a.acceleration.x;
    sum_y += a.acceleration.y;
    sum_z += a.acceleration.z;

    delay(10);
  }

  gravity_x = sum_x / samples;
  gravity_y = sum_y / samples;
  gravity_z = sum_z / samples;

  Serial.println("✅ Calibration complete!");
  Serial.printf("Gravity: (%.2f, %.2f, %.2f)\n", gravity_x, gravity_y, gravity_z);
}

void loop() {
  // Handle BLE connection state changes
  if (!deviceConnected && oldDeviceConnected) {
    delay(500); // Give time for disconnect
    pServer->startAdvertising(); // Restart advertising
    Serial.println("📡 Restarting BLE advertising...");
    oldDeviceConnected = deviceConnected;
  }

  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
  }

  // Read sensor data
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // Check for stuck sensor
  if (a.acceleration.x == 0 && a.acceleration.y == 0 && a.acceleration.z == 0 &&
      g.gyro.x == 0 && g.gyro.y == 0 && g.gyro.z == 0) {
    Serial.println("⚠️ Zero readings detected - sensor may be stuck");
    delay(100);
    return;
  }

  // Update gravity with low-pass filter
  gravity_x = GRAVITY_ALPHA * gravity_x + (1 - GRAVITY_ALPHA) * a.acceleration.x;
  gravity_y = GRAVITY_ALPHA * gravity_y + (1 - GRAVITY_ALPHA) * a.acceleration.y;
  gravity_z = GRAVITY_ALPHA * gravity_z + (1 - GRAVITY_ALPHA) * a.acceleration.z;

  // Calculate motion (subtract gravity)
  float motion_x = a.acceleration.x - gravity_x;
  float motion_y = a.acceleration.y - gravity_y;
  float motion_z = a.acceleration.z - gravity_z;

  float magnitude = sqrt(motion_x * motion_x + motion_y * motion_y + motion_z * motion_z);
  magnitude = abs(magnitude - accel_offset);

  // Detect impact
  unsigned long now = millis();
  if (magnitude > IMPACT_THRESHOLD && (now - lastHitTime) > COOLDOWN_MS) {
    lastHitTime = now;
    totalHits++;

    Vec3 impact = {motion_x, motion_y, motion_z};
    Vec3 gravity = {gravity_x, gravity_y, gravity_z};
    String direction = getStrikeDirection(impact, gravity);

    // Calculate velocity
    float velocity = magnitude * 0.01;

    if (direction == "DOWN") {
      sendImpact(velocity, magnitude, now);
      Serial.printf("🥁 IMPACT! Mag: %.2f, Vel: %.2f (Hit #%lu)\n", magnitude, velocity, totalHits);
    }
  }

  // Send periodic status updates (every 30 seconds)
  static unsigned long lastStatusUpdate = 0;
  if (deviceConnected && (now - lastStatusUpdate) > 30000) {
    sendPeriodicStatus();
    lastStatusUpdate = now;
  }

  delay(10);  // 100Hz sampling rate
}

void sendImpact(float velocity, float magnitude, unsigned long timestamp) {
  if (!deviceConnected) return;

  // Create JSON impact data
  DynamicJsonDocument doc(512);
  doc["type"] = "impact";
  doc["velocity"] = velocity;
  doc["magnitude"] = magnitude;
  doc["timestamp"] = timestamp;
  doc["id"] = totalHits;
  doc["device"] = "drumstick";
  doc["battery"] = readBatteryVoltage();

  String json;
  serializeJson(doc, json);

  // Send via BLE
  pImpactCharacteristic->setValue(json.c_str());
  pImpactCharacteristic->notify();

  Serial.println("📤 Sent impact: " + json);
}

void sendStatusUpdate(String status, String message) {
  if (!deviceConnected) return;

  DynamicJsonDocument doc(512);
  doc["type"] = "status";
  doc["status"] = status;
  doc["message"] = message;
  doc["timestamp"] = millis();
  doc["uptime"] = millis() / 1000;
  doc["total_hits"] = totalHits;
  doc["battery"] = readBatteryVoltage();
  doc["threshold"] = IMPACT_THRESHOLD;

  String json;
  serializeJson(doc, json);

  pStatusCharacteristic->setValue(json.c_str());
  pStatusCharacteristic->notify();

  Serial.println("📊 Status: " + json);
}

void sendPeriodicStatus() {
  sendStatusUpdate("periodic", "Heartbeat");
}

float readBatteryVoltage() {
  // Optional: Read battery voltage if connected
  // For now, return a mock value
  return 3.7; // Volts
}