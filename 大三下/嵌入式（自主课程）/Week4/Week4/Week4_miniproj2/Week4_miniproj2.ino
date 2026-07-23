#include <Wire.h>

// TTP229 I2C 设备地址: 1010111  -> 0x57 
const int TTP229_I2C_ADDRESS = 0x57;

// 建立引脚与物理按键的映射表
const int keyMap[16] = {
  7, 6, 5, 4, 3, 2, 1, 0,       // 检测位0~7，对应的物理按键
  15, 14, 13, 12, 11, 10, 9, 8 
};

void setup() {
  Serial.begin(115200);
  Wire.begin(); 
  Serial.println("初始化完成");
}

void loop() {
  Wire.requestFrom(TTP229_I2C_ADDRESS, 2);

  if (Wire.available() == 2) {
    uint8_t data0 = Wire.read();
    uint8_t data1 = Wire.read();

    uint16_t keyStatus = (data1 << 8) | data0;

    if (keyStatus != 0) {
      for (int i = 0; i < 16; i++) {
        // 判断 i 位是否有信号
        if (keyStatus & (1 << i)) {
          
          // 通过映射表，转换
          int realKey = keyMap[i];
          
          Serial.print("检测位: ");
          Serial.print(i);
          Serial.print(" \t-> 实际触发按键: ");
          
          // 格式化输出，A~F为hex
          if (realKey >= 10) {
            Serial.println((char)('A' + (realKey - 10)));
          } else {
            Serial.println(realKey);
          }
        }
      }
    }
  }

  // 延时防抖
  delay(100); 
}