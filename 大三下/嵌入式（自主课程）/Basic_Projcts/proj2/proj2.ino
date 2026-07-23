#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// 触摸键盘I2C地址
const int TTP229_I2C_ADDRESS = 0x57;

// 键盘映射表
const char keyMap[16] = {'7', '6', '5', '4', '3', '2', '1', '0', 
                         'F', 'E', 'D', 'C', 'B', 'A', '9', '8'};
uint16_t lastKeyStatus = 0; // 按键防抖 边缘检测

// 状态机枚举
enum SafeState {
  UNLOCKED, 
  LOCKED    
};
SafeState currentState = UNLOCKED; // 一开始归零

String currentInput = "";   // 当前输入的字符串
String savedPassword = "";  // 存入系统的一次性密码
String adminPassword = "admin123"; // 管理员密码

void setup() {
  Serial.begin(115200);
  Wire.begin(); // 初始化I2C总线

  // 初始化 OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("OLED 初始化失败"));
    for(;;);
  }
  display.setTextColor(SSD1306_WHITE);
  
  updateDisplay(); // 刷新初始屏幕
  Serial.println("电子密码箱系统启动。管理员密码为: admin123");
}

void loop() {
  // 读取触摸按键
  char key = readTTP229();
  if (key != '\0') {
    handleKeypress(key);
  }

  // 监听串口管理员指令
  handleAdminSerial();

  delay(20); // 略微延时
}

// TTP229读取
char readTTP229() {
  Wire.requestFrom(TTP229_I2C_ADDRESS, 2);
  if (Wire.available() == 2) {
    uint8_t data0 = Wire.read();
    uint8_t data1 = Wire.read();
    uint16_t keyStatus = (data1 << 8) | data0;

    // 只有在按键刚按下时才触发，按住不放不重复触发
    if (keyStatus != 0 && lastKeyStatus == 0) {
      lastKeyStatus = keyStatus;
      for (int i = 0; i < 16; i++) {
        if (keyStatus & (1 << i)) {
          return keyMap[i];
        }
      }
    } else if (keyStatus == 0) {
      lastKeyStatus = 0; // 按键松开重置
    }
  }
  return '\0'; // 无有效按键
}

// 按键逻辑处理
void handleKeypress(char key) {
  if (key == 'C') { 
    currentInput = "";
    updateDisplay();
  } 
  else if (key == 'A') {
    if (currentState == UNLOCKED) {
      // 在开锁状态下 输入的是“设定新密码”
      if (currentInput.length() >= 4) {
        savedPassword = currentInput;
        currentState = LOCKED;      // 关门上锁
        currentInput = "";          // 清空输入框
      } else {
        showTemporaryMessage("Error!", "Password too short!", "Must be >= 4 chars");
      }
    } 
    else if (currentState == LOCKED) {
      // 在上锁状态下 输入的是“解锁密码”
      if (currentInput == savedPassword) {
        currentState = UNLOCKED;    // 开锁
        savedPassword = "";         // 密码单次有效，立即销毁
        currentInput = "";
        showTemporaryMessage("Success!", "Safe Unlocked.", "");
      } else {
        showTemporaryMessage("Denied!", "Wrong Password!", "");
        currentInput = ""; // 清空错误输入
      }
    }
    updateDisplay();
  } 
  else {
    // 常规字符输入逻辑
    if (currentInput.length() < 10) { // 限制密码最大长度为10
      currentInput += key;
      updateDisplay();
    }
  }
}

// 串口管理员控制
void handleAdminSerial() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim(); // 去除换行符和空格

    if (input == adminPassword) {
      // 管理员密码正确，强制重置密码箱
      currentState = UNLOCKED;
      savedPassword = "";
      currentInput = "";
      
      Serial.println("【管理员操作】密码箱已强制解锁，用户密码已清除。");
      showTemporaryMessage("Admin Access", "System Overridden", "Safe Unlocked");
      updateDisplay();
    } else {
      Serial.println("【管理员操作】密码错误！拒绝访问。");
    }
  }
}

// OLED 显示更新
void updateDisplay() {
  display.clearDisplay();
  
  // 绘制顶部标题栏
  display.setTextSize(1);
  display.setCursor(0, 0);
  if (currentState == UNLOCKED) {
    display.print("Status: OPEN (Set PWD)");
  } else {
    display.print("Status: LOCKED");
  }
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);

  // 绘制当前输入框
  display.setTextSize(2);
  display.setCursor(0, 25);
  
  if (currentInput.length() == 0) {
    display.print("_");
  } else {
    if (currentState == UNLOCKED) {
      display.print(currentInput); // 明文
    } else {
      for (int i = 0; i < currentInput.length(); i++) {
        display.print("Z");        // 掩码
      }
    }
  }

  // 绘制底部按键提示
  display.setTextSize(1);
  display.setCursor(0, 55);
  display.print("[A] Confirm  [C] Clear");
  
  display.display();
}

// OLED 临时弹窗提示
void showTemporaryMessage(String line1, String line2, String line3) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(10, 15);
  display.print(line1);
  display.setCursor(10, 30);
  display.print(line2);
  display.setCursor(10, 45);
  display.print(line3);
  display.display();
  delay(1500); // 提示停留 1.5 秒
}