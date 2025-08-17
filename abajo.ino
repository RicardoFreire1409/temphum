#include <DHT.h>
#define DHTPIN 10
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastRead = 0;

void setup() {
  Serial.begin(9600);
  dht.begin();
  Serial.println("DOWN:READY");
}

void loop() {
  if (millis() - lastRead >= 2000) {
    lastRead = millis();
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (isnan(t) || isnan(h)) {
      Serial.println("DOWN:ERR:DHT");
    } else {
      Serial.print("DOWN:T:"); Serial.println(t, 1);
      Serial.print("DOWN:H:"); Serial.println(h, 1);
    }
  }
}
