#define STATE_M1S1 1
#define STATE_M1S2 2
#define STATE_M2S1 3
#define STATE_M2S2 4

uint8_t sysState = STATE_M1S1;

const uint8_t keyPin = 0;
const uint8_t bluPin = 4;
const uint8_t ledPin = 10;

// timer frequency
#define TM_FREQ_1MHZ 1000000
// value for timer
#define VAL_1S 1000000
// auto reload
#define AUTO_RELOAD true
// timer number of autoreloads (0 = unlimited)
#define RELOADS_NUM 0
// timer handle
hw_timer_t *timer_hw = NULL;

void stateM1S1() {
  digitalWrite(ledPin, HIGH);
  digitalWrite(bluPin, LOW);
}

void stateM1S2() {
  digitalWrite(ledPin, LOW);
  digitalWrite(bluPin, LOW);
}

void stateM2S1() {
  digitalWrite(ledPin, LOW);
  digitalWrite(bluPin, HIGH);
}

void stateM2S2() {
  digitalWrite(ledPin, LOW);
  digitalWrite(bluPin, LOW);
}

void keyISR() {
  delayMicroseconds(20000);
  if (LOW == digitalRead(keyPin)) {
    if ((STATE_M1S1 == sysState) || (STATE_M1S2 == sysState)) {
      sysState = STATE_M2S1;
      stateM2S1();
    } else if ((STATE_M2S1 == sysState) || (STATE_M2S2 == sysState)) {
      sysState = STATE_M1S1;
      stateM1S1();
    } else {
      /* Error */
    }
  }
}

void ARDUINO_ISR_ATTR TIMER_ISR() {
  switch (sysState) {
    case STATE_M1S1:
      sysState = STATE_M1S2;
      stateM1S2();
      break;
    case STATE_M1S2:
      sysState = STATE_M1S1;
      stateM1S1();
      break;
    case STATE_M2S1:
      sysState = STATE_M2S2;
      stateM2S2();
      break;
    case STATE_M2S2:
      sysState = STATE_M2S1;
      stateM2S1();
      break;
    default:
      /* Error */
      break;
  }
}

void setup() {
  // put your setup code here, to run once:
  pinMode(bluPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  attachInterrupt(keyPin, keyISR, FALLING);

  // timer init
  while (NULL == timer_hw) {
    timer_hw = timerBegin(TM_FREQ_1MHZ);
  }
  timerAttachInterrupt(timer_hw, &TIMER_ISR);
  timerAlarm(timer_hw, VAL_1S, AUTO_RELOAD, RELOADS_NUM);
}

void loop() {
  // put your main code here, to run repeatedly:
}

