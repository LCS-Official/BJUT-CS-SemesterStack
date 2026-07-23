#define DELAY_MS 1000

#define MODE_1 1
#define MODE_2 2

const uint8_t keyPin = 0;
const uint8_t grdPin = 5;
const uint8_t redPin = 7;
uint8_t sysMode = MODE_1;

void keyISR() {
  delayMicroseconds(20000);
  if (LOW == digitalRead(keyPin)) {
    switch (sysMode) {
      case MODE_1:
        sysMode = MODE_2;
        break;
      case MODE_2:
        sysMode = MODE_1;
        break;
      default:
        break;
    }
  }
}

void setup() {
  // put your setup code here, to run once:
  pinMode(grdPin, OUTPUT);
  pinMode(redPin, OUTPUT);
  pinMode(keyPin, INPUT);
  attachInterrupt(keyPin, keyISR, FALLING);
  sysMode = MODE_1;
}

void loop() {
  // put your main code here, to run repeatedly:
  switch (sysMode) {
    case MODE_1:
      digitalWrite(redPin, HIGH);
      delay(DELAY_MS);
      digitalWrite(redPin, LOW);
      delay(DELAY_MS);
      break;
    case MODE_2:
      digitalWrite(grdPin, HIGH);
      delay(DELAY_MS);
      digitalWrite(grdPin, LOW);
      delay(DELAY_MS);
      break;
    default:
      break;
  }
}
