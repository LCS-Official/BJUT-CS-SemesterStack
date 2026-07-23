// --- 宏定义与定时器参数 ---
#define TM_FREQ_1MHZ 1000000
#define VAL_200MS    200000
#define AUTO_RELOAD  true
#define RELOADS_NUM  0

// --- 引脚定义 ---
const uint8_t key1Pin = 0;  // 按键K1：切换颜色 
const uint8_t key2Pin = 1;  // 按键K2：切换频率 (请确保你的板子Pin2能正常用作输入)
const int ledPins[] = {4, 5, 7}; 
const int pinCount = sizeof(ledPins) / sizeof(ledPins[0]);

// --- 状态机宏定义 ---
#define COLOR_1 0
#define COLOR_2 1
#define COLOR_3 2

#define FREQ_200MS 0
#define FREQ_1S    1
#define FREQ_2S    2

// --- 系统与状态机全局变量 ---
volatile uint8_t colorState = COLOR_1; 
volatile uint8_t freqState = FREQ_200MS; 
volatile bool sysEnable = false;       
volatile bool ledOutputState = false;  

// --- 定时器资源与标志位 ---
hw_timer_t *timer_hw = NULL;
volatile uint8_t tick_count = 0;
volatile bool toggle_flag = false;

// --- 按键消抖时间记录 ---
volatile unsigned long lastKey1Time = 0;
volatile unsigned long lastKey2Time = 0;
const unsigned long debounceDelay = 200; // 200毫秒消抖时间

// ---------------------------------------------------------
// 按键 K1 外部中断服务函数：切换颜色 (安全消抖版)
// ---------------------------------------------------------
void ARDUINO_ISR_ATTR key1ISR() {
  unsigned long currentTime = millis();
  // 只有距离上次按键超过200ms才认为是一次有效触发
  if (currentTime - lastKey1Time > debounceDelay) {
    if (digitalRead(key1Pin) == LOW) {
      colorState = (colorState + 1) % 3;
      lastKey1Time = currentTime;
    }
  }
}

// ---------------------------------------------------------
// 按键 K2 外部中断服务函数：切换频率 (安全消抖版)
// ---------------------------------------------------------
void ARDUINO_ISR_ATTR key2ISR() {
  unsigned long currentTime = millis();
  if (currentTime - lastKey2Time > debounceDelay) {
    if (digitalRead(key2Pin) == LOW) {
      freqState = (freqState + 1) % 3;
      tick_count = 0; 
      lastKey2Time = currentTime;
    }
  }
}

// ---------------------------------------------------------
// 定时器中断服务函数
// ---------------------------------------------------------
void ARDUINO_ISR_ATTR TIMER_ISR() {
  tick_count++;
  uint8_t target_ticks = 1; 
  if (freqState == FREQ_1S) target_ticks = 5;       
  else if (freqState == FREQ_2S) target_ticks = 10;      

  if (tick_count >= target_ticks) {
    toggle_flag = true;
    tick_count = 0;
  }
}

void turnOffAllLeds() {
  for (int i = 0; i < pinCount; i++) {
    digitalWrite(ledPins[i], LOW);
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000); // 给串口留出初始化时间
  Serial.println("\n--- ESP32 彩灯控制器已启动 ---");
  Serial.println(">>> 状态：等待启动。请在下方输入框发送“开启”以点亮彩灯！");
  
  for (int i = 0; i < pinCount; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
  }

  pinMode(key1Pin, INPUT_PULLUP);
  pinMode(key2Pin, INPUT_PULLUP);

  attachInterrupt(key1Pin, key1ISR, FALLING);
  attachInterrupt(key2Pin, key2ISR, FALLING);

  timer_hw = timerBegin(TM_FREQ_1MHZ);
  timerAttachInterrupt(timer_hw, &TIMER_ISR);
  timerAlarm(timer_hw, VAL_200MS, AUTO_RELOAD, RELOADS_NUM);
}

// 记录上次打印的状态，防止在loop里刷屏
uint8_t lastColorPrint = 255;
uint8_t lastFreqPrint = 255;

void loop() {
  // 1. 监听串口命令
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim(); 
    
    if (cmd == "开启") {
      sysEnable = true;
      Serial.println(">>> [执行指令]：彩灯效果已开启！现在可以按键切换了。");
    } else if (cmd == "关闭") {
      sysEnable = false;
      turnOffAllLeds(); 
      ledOutputState = false;
      Serial.println(">>> [执行指令]：彩灯效果已关闭！");
    }
  }

  // 2. 打印按键状态变化 (用于帮你排查硬件按键是否接通)
  if (colorState != lastColorPrint) {
    Serial.printf(">>> [按键触发] 切换到颜色模式: %d\n", colorState + 1);
    lastColorPrint = colorState;
  }
  if (freqState != lastFreqPrint) {
    Serial.printf(">>> [按键触发] 切换到频率模式: %d\n", freqState + 1);
    lastFreqPrint = freqState;
  }

  // 3. LED 闪烁逻辑
  if (sysEnable && toggle_flag) {
    toggle_flag = false; 
    ledOutputState = !ledOutputState; 
    turnOffAllLeds(); 
    
    if (ledOutputState) {
      digitalWrite(ledPins[colorState], HIGH);
    }
  }
}