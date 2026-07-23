const uint8_t bluPin = 4;

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

void ARDUINO_ISR_ATTR TIMER_ISR() {
  digitalWrite(bluPin, !digitalRead(bluPin));
}

void setup() {
  // put your setup code here, to run once:
  pinMode(bluPin, OUTPUT);

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

