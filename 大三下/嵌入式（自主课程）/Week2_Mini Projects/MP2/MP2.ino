#define DELAY_MS 200

// 定义所有蓝灯连接的引脚
int bluePins[] = {4, 5, 7}; 
// 计算数组中引脚的数量
int pinCount = sizeof(bluePins) / sizeof(bluePins[0]);

void setup() {
  // 使用循环初始化所有引脚为输出模式
  for (int i = 0; i < pinCount; i++) {
    pinMode(bluePins[i], OUTPUT);
  }
}

void loop() {
  // 遍历数组，依次点亮和熄灭每一个灯
  for (int i = 0; i < pinCount; i++) {
    digitalWrite(bluePins[i], HIGH);
    delay(DELAY_MS);
    digitalWrite(bluePins[i], LOW);
    delay(DELAY_MS);
  }
}