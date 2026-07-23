const uint8_t keyPin = 0;
const uint8_t redPin = 5;
uint8_t ledState = LOW;

void setup() {
  // put your setup code here, to run once:
  pinMode(redPin, OUTPUT);
  pinMode(keyPin, INPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (LOW == digitalRead(keyPin)) {
    if (HIGH == ledState) {
      digitalWrite(redPin, LOW);
      ledState = LOW;
      
    } else {
      digitalWrite(redPin, HIGH);
      ledState = HIGH;
    }
  }
}

