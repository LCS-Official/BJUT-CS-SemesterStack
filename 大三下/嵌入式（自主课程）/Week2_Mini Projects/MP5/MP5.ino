const uint8_t keyPin = 0;
const uint8_t grdPin = 5;

void keyISR() {
  delayMicroseconds(20000);
  if (LOW == digitalRead(keyPin)) {
    digitalWrite(grdPin, !digitalRead(grdPin));
  }
}

void setup() {
  // put your setup code here, to run once:
  pinMode(grdPin, OUTPUT);
  pinMode(keyPin, INPUT);
  attachInterrupt(keyPin, keyISR, FALLING);
}

void loop() {
  // put your main code here, to run repeatedly:
}




