#include <Wire.h>
#include <SPI.h>
#include <Adafruit_LEDBackpack.h>

#define K1 0
#define LEFT 0x70
#define RIGHT 0x71
#define HZK_CS 7
#define BASE_ADDR 0x2C9D0 // P15

// 站名的 GB2312 十六进制编码
#define BEI    0xB1B1  // 北
#define TAI    0xCCAB  // 太
#define PING   0xC6BD  // 平
#define ZHUANG 0xD7AF  // 庄

#define YONG   0xD3C0  // 永
#define DING   0xB6A8  // 定
#define MEN    0xC3C5  // 门
#define WAI    0xCDE2  // 外

#define XI     0xCEF7  // 西
#define ZHI    0xD6B1  // 直

hw_timer_t * timer = NULL;

// 跨中断共享变量必须加volatile
volatile bool bo;
volatile int lop;
volatile bool last_btn_state = HIGH; // 按键边缘检测

Adafruit_8x16matrix matrixl = Adafruit_8x16matrix();
Adafruit_8x16matrix matrixr = Adafruit_8x16matrix();
uint8_t BUF[128];
byte led_arr[32];
byte ledl[16], ledr[16], zeros[16] = {0}; // 显式初始化全0
int word_addr;

// 拆分高低字节
int msb(int addr){
  return (addr & 0xFF00) >> 8;
}

int lsb(int addr){
  return addr & 0x00FF;
}

int findByteAddr(int addr){ // GB2312区位码转物理地址
// 乘32是一个汉字刚好256个点，偏移量
  int MSB = msb(addr);
  int LSB = lsb(addr);
  // 高低字节推算在矩阵中的位置，乘空间得到内存addr
  if(MSB >= 0xA1 && MSB <= 0Xa9 && LSB >= 0xA1)
    return ((MSB - 0xA1) * 94 + (LSB - 0xA1)) * 32 + BASE_ADDR;
  else if (MSB >= 0xB0 && MSB <= 0xF7 && LSB >= 0xA1)
    return ((MSB - 0xB0) * 94 + (LSB - 0xA1) + 846) * 32 + BASE_ADDR;
  
  // 防止查表失败时返回不可控的内存垃圾值
  return BASE_ADDR; 
}


// 格式 帧头 数据长度*2 命令字 文本编码格式
// 4个汉字(8字节) -> 长度为 0x0A (10)，数组总大小 13
uint8_t BTPZ[13] = {0xFD, 0x00, 0x0A, 0x01, 0x00, msb(BEI), lsb(BEI), msb(TAI), lsb(TAI), msb(PING), lsb(PING), msb(ZHUANG), lsb(ZHUANG)};
// 4个汉字(8字节) -> 长度为 0x0A (10)，数组总大小 13
uint8_t YDMW[13] = {0xFD, 0x00, 0x0A, 0x01, 0x00, msb(YONG), lsb(YONG), msb(DING), lsb(DING), msb(MEN), lsb(MEN), msb(WAI), lsb(WAI)};
// 3个汉字(6字节) -> 长度为 0x08 (8)，数组总大小 11
uint8_t XZM[11]  = {0xFD, 0x00, 0x08, 0x01, 0x00, msb(XI), lsb(XI), msb(ZHI), lsb(ZHI), msb(MEN), lsb(MEN)};


// ESP32中断服务函数必须放在IRAM中
void IRAM_ATTR onTimer(){
  bool current_state = digitalRead(K1);
  // 边缘检测：只有在按键从 HIGH 变到 LOW 的那一瞬间才触发
  if(current_state == LOW && last_btn_state == HIGH){
    bo = true;
    lop = (lop + 1) % 3;
  } 
  last_btn_state = current_state;
}

void setup() {
  Serial.begin(115200);
  
  Serial1.begin(115200); 
  
  SPI.begin();
  
  // 汉字库
  pinMode(HZK_CS, OUTPUT);
  digitalWrite(HZK_CS, HIGH);
  
  // LED点阵初始化
  matrixl.begin(LEFT);
  matrixr.begin(RIGHT);
  
  // 初始设为2，第一下按键触发时 (2+1)%3 刚好等于0，从而正常播报第0个站
  lop = 2; 
  bo = false; // 初始不上电就触发，等待按键
  
  pinMode(K1, INPUT_PULLUP); 

  timer = timerBegin(1000000); 
  
  // 绑定中断服务函数：只传2个参数
  timerAttachInterrupt(timer, &onTimer);
  
  // 设置报警并启动：参数为 (定时器指针, 报警阈值, 是否自动重载, 重载次数)
  // 50000 微秒 = 50 毫秒 (如果是 200000 则是 200 毫秒)。最后的 0 代表无限次重载触发。
  timerAlarm(timer, 50000, true, 0);
}

void led(int addr){
  int l = 0, r = 0;
  digitalWrite(HZK_CS, LOW);
  SPI.transfer(0x03); // 普通读，不用额外的空字节发送
  // 分3次 每次8位发送地址
  SPI.transfer(addr >> 16);
  SPI.transfer(addr >> 8);
  SPI.transfer(addr & 0xFF);
  for(int i = 0; i < 32; i++) 
    led_arr[i] = SPI.transfer(0x00); // read
  digitalWrite(HZK_CS, HIGH);
  
  // 按行存取
  for(int i = 0; i < 32; i++){
    if(i % 2) ledr[r++] = led_arr[i]; // 奇数存右屏
    else ledl[l++] = led_arr[i]; // 偶数存左屏
  }
}

void disp(bool clean){
  matrixl.clear();
  matrixr.clear();
  if(clean){ // 写入空
    matrixl.drawBitmap(0, 0, zeros, 8, 16, LED_ON);
    matrixr.drawBitmap(0, 0, zeros, 8, 16, LED_ON);
  }
  else{
    matrixl.drawBitmap(0, 0, ledl, 8, 16, LED_ON);
    matrixr.drawBitmap(0, 0, ledr, 8, 16, LED_ON);
  }
  matrixl.writeDisplay();
  matrixr.writeDisplay();
  delay(300);
}

void loop() {
  if(bo){
    bo = false; // 进来后立即重置标志位，防止中断再次触发导致状态混乱
    int current_lop = lop; // 缓存当前模式，防止在长时间 delay 中途被中断修改
    
    if(current_lop == 0){ // 1. 北太平庄
      Serial1.write(BTPZ, 13);
      led(findByteAddr(BEI)); disp(false);
      led(findByteAddr(TAI)); disp(false);
      led(findByteAddr(PING)); disp(false);
      led(findByteAddr(ZHUANG)); disp(false);
      disp(true);
    }
    else if(current_lop == 1){ // 2. 永定门外
      Serial1.write(YDMW, 13);
      led(findByteAddr(YONG)); disp(false);
      led(findByteAddr(DING)); disp(false);
      led(findByteAddr(MEN)); disp(false);
      led(findByteAddr(WAI)); disp(false);
      disp(true);
    }
    else if(current_lop == 2){ // 3. 西直门
      Serial1.write(XZM, 11);
      led(findByteAddr(XI)); disp(false);
      led(findByteAddr(ZHI)); disp(false);
      led(findByteAddr(MEN)); disp(false);
      disp(true);
    }
  }
}