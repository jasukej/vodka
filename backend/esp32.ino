/*
 * ESP32 Drumstick with MPU6050
 * Detects impacts and sends via WebSocket
 *
 * Libraries needed (install via PlatformIO or Arduino IDE):
 * - ArduinoWebsockets by Gil Maimon
 * - (Optional) Adafruit MPU6050 - only if MOCK_MODE = false
 * - (Optional) Adafruit Unified Sensor - only if MOCK_MODE = false
 */


#include <WiFi.h>
#include <ArduinoWebsockets.h>

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

using namespace websockets;

// WiFi credentials
const char* ssid = "*Hidden Network*";
const char* password = "AliceInBorderland!";

// WebSocket server (your computer's IP)
const char* ws_server = "192.168.0.106";
const int ws_port = 8080;

WebsocketsClient client;

Adafruit_MPU6050 mpu;
// Impact detection parameters
const float IMPACT_THRESHOLD = 15.0;  // m/s^2 (tune this!)
const int COOLDOWN_MS = 50;          // Min time between hits
unsigned long lastHitTime = 0;
float accel_offset = 0;

float gravity_x = 0;
float gravity_y = 0;
float gravity_z = 0;
const float GRAVITY_ALPHA = 0.98;

// Add these at the top with your other variables
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
  // Normalize both vectors
  vec3_normalize(&impact_vector);
  vec3_normalize(&gravity_vector);

  // Calculate dot product to find angle with gravity
  float dot = vec3_dot(impact_vector, gravity_vector);

  // Project impact onto horizontal plane (perpendicular to gravity)
  Vec3 horizontal;
  horizontal.x = impact_vector.x - dot * gravity_vector.x;
  horizontal.y = impact_vector.y - dot * gravity_vector.y;
  horizontal.z = impact_vector.z - dot * gravity_vector.z;
  float horizontal_mag = vec3_magnitude(horizontal);

  // Determine primary direction
  if (dot > 0.7) {
    return "DOWN";
  } else if (dot < -0.7) {
    return "UP";
  } else if (horizontal_mag > 0.3) {
    vec3_normalize(&horizontal);

    float abs_x = abs(horizontal.x);
    float abs_y = abs(horizontal.y);
    float abs_z = abs(horizontal.z);

    if (abs_x > abs_y && abs_x > abs_z) {
      return horizontal.x > 0 ? "HORIZONTAL_POS_X" : "HORIZONTAL_NEG_X";
    } else if (abs_y > abs_z) {
      return horizontal.y > 0 ? "HORIZONTAL_POS_Y" : "HORIZONTAL_NEG_Y";
    } else {
      return horizontal.z > 0 ? "HORIZONTAL_POS_Z" : "HORIZONTAL_NEG_Z";
    }
  }
  return "DIAGONAL";
}

// Function to reset and reinitialize the MPU6050
bool resetMPU6050() {
  Serial.println("Attempting to reset MPU6050...");

  // Reset I2C bus
  Wire.end();
  delay(100);
  Wire.begin();
  delay(100);

  // Wake up MPU6050
  Wire.beginTransmission(0x68);
  Wire.write(0x6B);  // PWR_MGMT_1 register
  Wire.write(0);     // Wake up
  Wire.endTransmission(true);
  delay(100);

  // Reinitialize
  if (!mpu.begin()) {
    Serial.println("Reset failed!");
    return false;
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);

  Serial.println("MPU6050 reset successful!");
  return true;
}

void setup() {
  Serial.begin(115200);
  Serial.println("Starting drumstick with MPU6050...");

  Wire.begin(18, 19);
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

void loop() {
  // Keep WebSocket alive
  if (client.available()) {
    client.poll();
  } else {
    Serial.println("Reconnecting...");
    connectWebSocket();
    delay(1000);
  }

  // Real MPU6050 mode
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // Check if readings are all zeros (indicates stuck sensor)
  if (a.acceleration.x == 0 && a.acceleration.y == 0 && a.acceleration.z == 0 &&
      g.gyro.x == 0 && g.gyro.y == 0 && g.gyro.z == 0) {
    Serial.println("⚠️ Zero readings detected - resetting MPU6050...");
    resetMPU6050();
    delay(500);
    return;
  }

  // Update gravity vector with low-pass filter
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

    Vec3 impact = {motion_x, motion_y, motion_z};
    Vec3 gravity = {gravity_x, gravity_y, gravity_z};
    String direction = getStrikeDirection(impact, gravity);

    // Calculate velocity (simplified: v = a * dt, assuming 10ms sampling)
    float velocity = magnitude * 0.01;

    if (direction == "DOWN") {
      sendImpact(velocity, magnitude);
    }
  } else {
    // Serial.print("Magnitude: ");
    // Serial.println(magnitude);
  }

  delay(10);  // 100Hz sampling rate
}

void sendImpact(float velocity, float magnitude) {
  unsigned long now = millis();

  String json = "{\"type\":\"impact\",\"velocity\":" + String(velocity, 2) +
                ",\"magnitude\":" + String(magnitude, 2) +
                ",\"timestamp\":" + String(now) +
                ",\"id\":" + 2 + "}";

  client.send(json);

  Serial.print("IMPACT! Magnitude: ");
  Serial.print(magnitude);
  Serial.print(" m/s^2, Velocity: ");
  Serial.println(velocity);
}