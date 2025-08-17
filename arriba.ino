#include <DHT.h>
#define DHTPIN 10
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastRead = 0;

void setup() {
  Serial.begin(9600);
  dht.begin();
  Serial.println("UP:READY");
}

void loop() {
  if (millis() - lastRead >= 2000) {
    lastRead = millis();
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (isnan(t) || isnan(h)) {
      Serial.println("UP:ERR:DHT");
    } else {
      Serial.print("UP:T:"); Serial.println(t, 1);  // ej: UP:T:25.6
      Serial.print("UP:H:"); Serial.println(h, 1);  // ej: UP:H:62.3
    }
  }
}
