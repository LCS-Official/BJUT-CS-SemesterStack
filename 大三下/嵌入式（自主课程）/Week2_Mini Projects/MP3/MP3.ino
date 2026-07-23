const uint8_t keyPin = 0;
const uint8_t redPin = 4;

void setup() {
  // put your setup code here, to run once:
  pinMode(redPin, OUTPUT);
  pinMode(keyPin, INPUT);  
}

void loop() {
  // put your main code here, to run repeatedly:
  if (LOW == digitalRead(keyPin)) {
    digitalWrite(redPin, HIGH);
  } else {
    digitalWrite(redPin, LOW);
  }
}


