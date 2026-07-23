const uint8_t ledPin = 10;

// timer frequency
#define TM_FREQ_1MHZ 1000000
// value for timer
#define VAL_200MS 200000
// auto reload
#define AUTO_RELOAD true
// timer number of autoreloads (0 = unlimited)
#define RELOADS_NUM 0
// timer handle
hw_timer_t *timer_hw = NULL;

bool led_flag = false;
bool print_flag = false;
uint8_t tp_count = 0;

uint32_t printnum = 0;

void ARDUINO_ISR_ATTR TIMER_ISR() {
  // LED blink per 200ms
  led_flag = true;
  // print num per 1s
  tp_count = (tp_count + 1) % 5;
  if (0 == tp_count) {
    print_flag = true;
  }
}

void setup() {
  // put your setup code here, to run once:
  led_flag = false;
  print_flag = false;
  tp_count = 0;
  printnum = 0;

  pinMode(ledPin, OUTPUT);
  Serial.begin(115200);

  // timer init
  while (NULL == timer_hw) {
    timer_hw = timerBegin(TM_FREQ_1MHZ);
  }
  timerAttachInterrupt(timer_hw, &TIMER_ISR);
  timerAlarm(timer_hw, VAL_200MS, AUTO_RELOAD, RELOADS_NUM);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (led_flag) {
    digitalWrite(ledPin, !digitalRead(ledPin));
    led_flag = false;
  }
  if (print_flag) {
    Serial.print("Num: ");
    Serial.println(++printnum, DEC);
    print_flag = false;
  }
}

