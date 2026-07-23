#include <Wire.h>
#include <RTClib.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
RTC_DS1307 rtc;

const int BTN_MODE = 0;  // K1: 切换模式
const int BTN_ADD = 1;   // K2: 增加数值/切换开关
const int BUZZER = 2;    // IO2 (蜂鸣器)

// 模式扩展: 0:正常, 1:设时间时, 2:设时间分, 3:设闹钟时, 4:设闹钟分, 5:闹钟开关
int mode = 0; 
int alarmHr = 0, alarmMin = 0;
bool alarmOn = false;
bool isRinging = false;
bool alarmDismissed = false; 

#define EEPROM_ADDR 0x50 // 默认7位地址

// 有效16bit，2byte
void writeEEPROM(unsigned int addr, byte data) {
  Wire.beginTransmission(EEPROM_ADDR);
  Wire.write((int)(addr >> 8)); // 发高位地址
  Wire.write((int)(addr & 0xFF)); // 发低位地址
  Wire.write(data);
  Wire.endTransmission();
  delay(5);
}

byte readEEPROM(unsigned int addr) {
  byte data = 0;
  Wire.beginTransmission(EEPROM_ADDR);
  Wire.write((int)(addr >> 8));
  Wire.write((int)(addr & 0xFF));
  Wire.endTransmission();
  Wire.requestFrom((uint16_t)EEPROM_ADDR, (uint8_t)1); // 每次读1byte
  if (Wire.available()) data = Wire.read();
  return data;
}

// 刷新屏幕显示
void updateDisplay() {
  DateTime now = rtc.now();
  display.clearDisplay();
  display.setTextColor(WHITE);
  display.setCursor(0, 0);

  if (mode == 0) {
    display.setTextSize(2);
    display.printf("%02d:%02d:%02d\n", now.hour(), now.minute(), now.second());
    display.setTextSize(1);
    display.setCursor(0, 30);
    display.printf("Alarm: %02d:%02d [%s]", alarmHr, alarmMin, alarmOn ? "ON" : "OFF");
  } else {
    display.setTextSize(1);
    if (mode == 1) display.println("SETTING: TIME HOUR");
    if (mode == 2) display.println("SETTING: TIME MIN");
    if (mode == 3) display.println("SETTING: ALARM HOUR");
    if (mode == 4) display.println("SETTING: ALARM MIN");
    if (mode == 5) display.println("SETTING: ALARM ON/OFF");
    
    display.setTextSize(2);
    display.setCursor(0, 20);
    
    if (mode == 1 || mode == 2) {
      // 正在设置本地时间
      display.printf("Time: \n%02d:%02d", now.hour(), now.minute());
    } else {
      // 正在设置闹钟
      display.printf("Alrm: \n%02d:%02d [%s]", alarmHr, alarmMin, alarmOn ? "ON" : "OFF");
    }
  }
  display.display();
}

void setup() {
  pinMode(BTN_MODE, INPUT_PULLUP);
  pinMode(BTN_ADD, INPUT_PULLUP);
  pinMode(BUZZER, OUTPUT);

  Wire.begin();
  rtc.begin();
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);

  if (!rtc.isrunning()) {
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }

  alarmHr = readEEPROM(0);
  alarmMin = readEEPROM(1);
  alarmOn = (readEEPROM(2) == 1);
  
  if (alarmHr > 23) alarmHr = 0;
  if (alarmMin > 59) alarmMin = 0;
}

void loop() {
  DateTime now = rtc.now();

  // 如果时间已经过了闹钟设定的分钟，重置静音标志位
  if (now.hour() != alarmHr || now.minute() != alarmMin) {
    alarmDismissed = false;
  }

  // K1按键逻辑：切换模式 (0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 0)
  if (digitalRead(BTN_MODE) == LOW) {
    delay(50); // 基础去抖
    if (digitalRead(BTN_MODE) == LOW) {
      if (isRinging) {
        alarmDismissed = true; 
      } else {
        mode = (mode + 1) % 6; // 模式拓展为6个
        if (mode == 0) {
          // 退出设置模式时，保存闹钟状态
          writeEEPROM(0, alarmHr);
          writeEEPROM(1, alarmMin);
          writeEEPROM(2, alarmOn ? 1 : 0);
        }
      }
      while(digitalRead(BTN_MODE) == LOW); // 等待释放
    }
  }

  // K2按键逻辑：数值增加/开关切换（含长按连续修改）
  if (digitalRead(BTN_ADD) == LOW) {
    delay(50); // 基础去抖
    if (digitalRead(BTN_ADD) == LOW) {
      
      if (isRinging) {
        alarmDismissed = true; 
        while(digitalRead(BTN_ADD) == LOW); 
      } 
      else if (mode == 5) { // 原 mode 3 变成了 mode 5
        alarmOn = !alarmOn;
        while(digitalRead(BTN_ADD) == LOW); 
      } 
      else if (mode >= 1 && mode <= 4) { 
        // 处于修改数值的模式：1(时间时), 2(时间分), 3(闹钟时), 4(闹钟分)
        
        // 1. 立即触发单次修改
        if (mode == 1) {
          rtc.adjust(DateTime(now.year(), now.month(), now.day(), (now.hour() + 1) % 24, now.minute(), now.second()));
        } else if (mode == 2) {
          // 修改分钟时，将秒数归零，方便精确对时
          rtc.adjust(DateTime(now.year(), now.month(), now.day(), now.hour(), (now.minute() + 1) % 60, 0));
        } else if (mode == 3) {
          alarmHr = (alarmHr + 1) % 24;
        } else if (mode == 4) {
          alarmMin = (alarmMin + 1) % 60;
        }
        
        updateDisplay(); // 立即刷新反馈
        
        // 2. 记录时间，准备检测长按
        unsigned long pressTime = millis();
        bool isLongPress = false;
        
        // 3. 长按连续增加逻辑
        while(digitalRead(BTN_ADD) == LOW) {
          if (!isLongPress) {
            if (millis() - pressTime > 1000) {
              isLongPress = true; // 超过1秒激活连发
            }
          } else {
            // 长按连发状态，需要重新获取当前时间(因为RTC刚才可能被修改了)
            now = rtc.now();
            
            if (mode == 1) {
              rtc.adjust(DateTime(now.year(), now.month(), now.day(), (now.hour() + 1) % 24, now.minute(), now.second()));
            } else if (mode == 2) {
              rtc.adjust(DateTime(now.year(), now.month(), now.day(), now.hour(), (now.minute() + 1) % 60, 0));
            } else if (mode == 3) {
              alarmHr = (alarmHr + 1) % 24;
            } else if (mode == 4) {
              alarmMin = (alarmMin + 1) % 60;
            }
            
            updateDisplay(); 
            delay(150); // 连发速度
          }
        }
      }
    }
  }

  // 判断是否响铃
  if (mode == 0 && alarmOn && now.hour() == alarmHr && now.minute() == alarmMin && now.second() < 30 && !alarmDismissed) {
    isRinging = true;
  } else {
    isRinging = false;
  }

  // 驱动蜂鸣器
  if (isRinging) tone(BUZZER, 1000); 
  else noTone(BUZZER);

  // 正常循环中的显示更新
  updateDisplay();
  delay(50);
}