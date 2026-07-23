// set pins
const int TRIG_PIN = 2;
const int ECHO_PIN = 3;

const int NUM_READINGS = 5;     // 滤波采样num
float readings[NUM_READINGS];   // 存储历史数据 数组
int readIndex = 0;              // 当前数据的索引
float total = 0;                // 历史数据总和
float averageDistance = 0;      // 滤波后的平均距离

void setup() {
  // 初始化 波特率 115200
  Serial.begin(115200);
  
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // 初始化滤波数组
  for (int i = 0; i < NUM_READINGS; i++) {
    readings[i] = 0;
  }
  Serial.println("初始化完成");
}

void loop() {
  // 产生TRIG
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2); 
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10); 
  digitalWrite(TRIG_PIN, LOW);

  // 读取ECHO
  long duration = pulseIn(ECHO_PIN, HIGH, 70000);  // 超时时间

  // 计算距离
  float distance = 0;
  
  if (duration == 0 || duration > 60000) {
    distance = -1.0; // 错了
  } else {
    // 算出距离
    distance = (duration * 0.034) / 2.0;
  }

  if (distance > 555) {
    Serial.println("范围超限");
  } else if (distance != -1.0) { // 滤波
    total = total - readings[readIndex];
    readings[readIndex] = distance;
    total = total + readings[readIndex];
    readIndex = readIndex + 1;

    if (readIndex >= NUM_READINGS) {
      readIndex = 0;
    }

    averageDistance = total / NUM_READINGS;

    Serial.print("实时距离: ");
    Serial.print(distance);
    Serial.print(" cm \t");
    Serial.print("滤波后距离: ");
    Serial.print(averageDistance);
    Serial.println(" cm");
  } else {
    Serial.println("传感器未检测到有效目标！");
  }

  // 100ms测一次
  delay(100); 
}