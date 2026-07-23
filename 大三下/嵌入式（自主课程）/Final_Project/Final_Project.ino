#define ENABLE_BLINKER 1

#if ENABLE_BLINKER
#define BLINKER_PRINT Serial
#define BLINKER_WIFI
#include <Blinker.h>


char BLINKER_AUTH[] = "df18a8eb0f58";

char WIFI_SSID[] = "CMCC-edu";
char WIFI_PSWD[] = "LC_State";
#endif

#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <XPT2046_Touchscreen.h>
#include <RTClib.h>
#include "WT2003S_Player.h"


#define TFT_CS     7
#define TFT_DC     10
#define TOUCH_CS   0
#define TOUCH_IRQ  1
#define EEPROM_ADDR 0x50

#define MP3_RX_PIN 3
#define MP3_TX_PIN 2
#define TFT_BL_PIN 19

#define TIME_DISPLAY_WITH_SECONDS 1

// 60 秒无操作自动锁屏
#define SCREEN_AUTO_LOCK_TIMEOUT_MS 60000

#define MP3_LIBRARY_FIRST_TRACK_ARG 1

#define MAX_SONGS 99
#define SONGS_PER_PAGE 5
#define SONG_NAME_READ_DELAY_MS 240

#define DEFAULT_TRACK_DURATION_SEC 180
#define PROGRESS_X 36
#define PROGRESS_Y 111
#define PROGRESS_W 248
#define PROGRESS_H 9

// UI
#define UI_BG              (tft.color565(6, 10, 22))
#define UI_HEADER          (tft.color565(12, 22, 48))
#define UI_CARD            (tft.color565(18, 25, 44))
#define UI_CARD_2          (tft.color565(23, 32, 55))
#define UI_LINE            (tft.color565(55, 70, 100))
#define UI_ACCENT          (tft.color565(72, 188, 210))
#define UI_ACCENT_2        (tft.color565(255, 178, 72))
#define UI_GREEN           (tft.color565(75, 190, 115))
#define UI_RED             (tft.color565(225, 82, 82))
#define UI_PURPLE          (tft.color565(118, 100, 210))
#define UI_TEXT_DIM        (tft.color565(155, 165, 185))

#define USE_MANUAL_SONG_NAMES 1

const char* MANUAL_SONG_NAMES[] = {
  "",
  "zimin ulimate battle",
  "zimin Watery Graves",
  "zimin Graze the Roof",
  "Sanctuary Guardian - SMJesus",
  "MHW - Proof of a Hero"
};

const int MANUAL_SONG_COUNT = sizeof(MANUAL_SONG_NAMES) / sizeof(MANUAL_SONG_NAMES[0]) - 1;

const uint16_t SONG_DURATIONS_SEC[] = {
  0,
  116,
  138,
  157,
  142,
  299
};


HardwareSerial mp3Serial(1);
Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC);
XPT2046_Touchscreen ts(TOUCH_CS, TOUCH_IRQ);
RTC_DS1307 rtc;
WT2003S<HardwareSerial> Mp3Player;

#if ENABLE_BLINKER
BlinkerButton AppBtnPlay("btn-play");
BlinkerButton AppBtnPrev("btn-prev");
BlinkerButton AppBtnNext("btn-next");
BlinkerButton AppBtnMode("btn-mode");
BlinkerButton AppBtnLock("btn-lock");
BlinkerButton AppBtnList("btn-list");
BlinkerButton AppBtnVolUp("btn-vup");
BlinkerButton AppBtnVolDown("btn-vdown");

BlinkerSlider AppSliderVol("ran-vol");

BlinkerText AppTextTitle("tex-title");
BlinkerText AppTextState("tex-state");
BlinkerText AppTextMode("tex-mode");
BlinkerText AppTextTime("tex-time");

BlinkerNumber AppNumTrack("num-track");
BlinkerNumber AppNumVol("num-vol");
#endif

// 状态机
enum PageState {
  PAGE_PLAYER,
  PAGE_LIST,
  PAGE_TIME_SET
};

PageState currentPage = PAGE_PLAYER;

int TOTAL_SONGS = 1;
int currentTrack = 1;
int listPage = 0;

bool isPlaying = false;
bool hasStarted = false;

int volume = 15;
int playMode = 0;

String modeNames[3] = {
  "Loop",
  "Single",
  "Random"
};

String songNames[MAX_SONGS + 1];

unsigned long lastTimeUpdate = 0;
unsigned long lastTouchTime = 0;
unsigned long lastUserAction = 0;
unsigned long lastLockClockUpdate = 0;

bool isScreenLocked = false;
bool rtcAvailable = false;

int editHour = 0;
int editMinute = 0;
int editSecond = 0;

unsigned long trackStartMillis = 0;
unsigned long pausedAtMillis = 0;
unsigned long pausedAccumMillis = 0;
unsigned long lastProgressUpdate = 0;
int lastProgressPercent = -1;

bool blinkerReady = false;
unsigned long lastBlinkerInfoPush = 0;

// ==================== 函数声明 ====================
void playTrack(int trackNum, bool save = true);
void playNext();
void playPrev();
void togglePlay();
void switchMode();
void setVolumeSafe(int v);
void saveMemory();

void updateBlinkerInfo(bool force = false);
void updateBlinkerTask();
void setupBlinkerApp();
void redrawAfterAppAction();

uint16_t getTrackDurationSec(int trackNum);
unsigned long getTrackElapsedMillis();
void resetTrackProgress();
void drawProgressBar(bool force = false);
void updateProgressTask();

void drawHeader(const char* title);
void drawPlayScreen();
void updateDynamicUI();
void drawListScreen();
void drawListFrame();
void drawListContent();
void refreshCurrentPage();
void drawTopStatus(bool force = false);

void drawLockScreen();
void drawLockPattern();
void updateLockScreenClock(bool force = false);
void enterLockScreen();
void exitLockScreen();

void initRTC();
DateTime getDisplayNow();

void handleTouch();
void setBacklight(bool on);
void enterListPage();
void enterPlayerPage();

bool isTimeAreaTouched(int x, int y);
void enterTimeSetPage();
void drawTimeSetScreen();
void updateTimeSetValue();
void saveEditedTime();
void changeEditTime(int field, int delta);

void loadSongNames();
void setDefaultSongNames();
String cleanSongName(const char* raw);
String getSongTitle(int trackNum);
String shortenText(String text, int maxChars);
String formatDuration(uint16_t sec);
String twoDigits(int v);
void printFit(String text, int x, int y, int maxChars, uint16_t color, uint8_t textSize);
void drawButton(int x, int y, int w, int h, const char* label, uint16_t color, uint16_t textColor = ILI9341_WHITE);
void prepareTftBus();
uint16_t mp3ArgFromTrack(int trackNum);
int maxListPage();

#if ENABLE_BLINKER
void blinkerPlayCallback(const String & state);
void blinkerPrevCallback(const String & state);
void blinkerNextCallback(const String & state);
void blinkerModeCallback(const String & state);
void blinkerLockCallback(const String & state);
void blinkerListCallback(const String & state);
void blinkerVolUpCallback(const String & state);
void blinkerVolDownCallback(const String & state);
void blinkerVolSliderCallback(int32_t value);
void blinkerHeartbeat();
#endif

// ==================== 底层辅助 ====================
void prepareTftBus() {
  digitalWrite(TOUCH_CS, HIGH);
}

void setBacklight(bool on) {
#if TFT_BL_PIN >= 0
  digitalWrite(TFT_BL_PIN, on ? HIGH : LOW);
#endif
}

uint16_t mp3ArgFromTrack(int trackNum) {
  trackNum = constrain(trackNum, 1, TOTAL_SONGS);
  return (uint16_t)(trackNum - 1 + MP3_LIBRARY_FIRST_TRACK_ARG);
}

int maxListPage() {
  if (TOTAL_SONGS <= 0) return 0;
  return (TOTAL_SONGS - 1) / SONGS_PER_PAGE;
}

// ==================== RTC 时间 ====================
void initRTC() {
  rtcAvailable = rtc.begin();

  if (!rtcAvailable) return;

  if (!rtc.isrunning()) {
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }
}

DateTime getDisplayNow() {
  if (rtcAvailable) return rtc.now();
  return DateTime(F(__DATE__), F(__TIME__));
}

String twoDigits(int v) {
  if (v < 10) return "0" + String(v);
  return String(v);
}

// ==================== 文本和按钮绘制 ====================
String shortenText(String text, int maxChars) {
  text.trim();

  if ((int)text.length() <= maxChars) return text;
  if (maxChars <= 3) return text.substring(0, maxChars);

  return text.substring(0, maxChars - 2) + "..";
}

String formatDuration(uint16_t sec) {
  int m = sec / 60;
  int s = sec % 60;

  String out = "";
  out += String(m);
  out += ":";

  if (s < 10) out += "0";
  out += String(s);

  return out;
}

void printFit(String text, int x, int y, int maxChars, uint16_t color, uint8_t textSize) {
  tft.setTextColor(color);
  tft.setTextSize(textSize);
  tft.setCursor(x, y);
  tft.print(shortenText(text, maxChars));
}

void drawButton(int x, int y, int w, int h, const char* label, uint16_t color, uint16_t textColor) {
  prepareTftBus();

  tft.fillRoundRect(x, y, w, h, 12, color);
  tft.drawRoundRect(x, y, w, h, 12, tft.color565(80, 90, 115));

  tft.setTextColor(textColor);
  tft.setTextSize(2);

  int16_t bx, by;
  uint16_t bw, bh;

  tft.getTextBounds((char*)label, 0, 0, &bx, &by, &bw, &bh);
  tft.setCursor(x + (w - bw) / 2, y + (h - 16) / 2);
  tft.print(label);
}

// ==================== 曲名读取与整理 ====================
void setDefaultSongNames() {
  for (int i = 1; i <= MAX_SONGS; i++) {
    songNames[i] = "Track " + twoDigits(i);
  }
}

String cleanSongName(const char* raw) {
  String s = "";

  for (int i = 0; i < 31 && raw[i] != '\0'; i++) {
    char c = raw[i];

    if (c >= 32 && c <= 126) {
      s += c;
    }
  }

  s.trim();

  if (s.length() == 0) return "";

  int slash = s.lastIndexOf('/');

  if (slash >= 0 && slash < (int)s.length() - 1) {
    s = s.substring(slash + 1);
  }

  String upper = s;
  upper.toUpperCase();

  if (upper.endsWith(".MP3") || upper.endsWith(".WAV")) {
    int dot = s.lastIndexOf('.');

    if (dot > 0) {
      s = s.substring(0, dot);
    }
  }

  s.replace('_', ' ');
  s.trim();

  return s;
}

String getSongTitle(int trackNum) {
  trackNum = constrain(trackNum, 1, TOTAL_SONGS);

  if (songNames[trackNum].length() == 0) {
    return "Track " + twoDigits(trackNum);
  }

  return songNames[trackNum];
}

void loadSongNames() {
  setDefaultSongNames();

#if USE_MANUAL_SONG_NAMES
  int manualCount = min(MANUAL_SONG_COUNT, MAX_SONGS);

  if (manualCount > 0) {
    TOTAL_SONGS = manualCount;

    for (int i = 1; i <= manualCount; i++) {
      songNames[i] = String(MANUAL_SONG_NAMES[i]);
    }

    return;
  }
#endif

  int scanCount = min(TOTAL_SONGS, MAX_SONGS);

  if (scanCount <= 0) return;

  int savedVolume = volume;

  Mp3Player.volume(0);
  delay(120);

  Mp3Player.playSDRootSong(mp3ArgFromTrack(1));
  delay(SONG_NAME_READ_DELAY_MS);

  for (int i = 1; i <= scanCount; i++) {
    char rawName[64];
    memset(rawName, 0, sizeof(rawName));

    Mp3Player.getSongName(rawName);

    String name = cleanSongName(rawName);

    if (name.length() > 0) {
      songNames[i] = name;
    }

    if (i < scanCount) {
      Mp3Player.next();
      delay(SONG_NAME_READ_DELAY_MS);
    }
  }

  Mp3Player.pause_or_play();
  delay(80);

  Mp3Player.volume(savedVolume);
  delay(80);
}

// ==================== MP3 播放控制 ====================
void setVolumeSafe(int v) {
  volume = constrain(v, 0, 31);

  Mp3Player.volume(volume);
  delay(30);

  updateBlinkerInfo();
}

void playTrack(int trackNum, bool save) {
  currentTrack = constrain(trackNum, 1, TOTAL_SONGS);

  Mp3Player.volume(volume);
  delay(40);

  Mp3Player.playSDRootSong(mp3ArgFromTrack(currentTrack));
  delay(80);

  resetTrackProgress();

  isPlaying = true;
  hasStarted = true;

  if (save) {
    saveMemory();
  }

  updateBlinkerInfo();
}

void playNext() {
  if (TOTAL_SONGS <= 1) {
    currentTrack = 1;
  } else if (playMode == 2) {
    int oldTrack = currentTrack;

    do {
      currentTrack = random(1, TOTAL_SONGS + 1);
    } while (currentTrack == oldTrack && TOTAL_SONGS > 1);
  } else {
    currentTrack = (currentTrack >= TOTAL_SONGS) ? 1 : currentTrack + 1;
  }

  playTrack(currentTrack);
}

void playPrev() {
  currentTrack = (currentTrack <= 1) ? TOTAL_SONGS : currentTrack - 1;
  playTrack(currentTrack);
}

void togglePlay() {
  if (!hasStarted) {
    playTrack(currentTrack);
    return;
  }

  Mp3Player.pause_or_play();
  delay(50);

  if (isPlaying) {
    pausedAtMillis = millis();
    isPlaying = false;
  } else {
    if (pausedAtMillis > 0) {
      pausedAccumMillis += millis() - pausedAtMillis;
    }

    pausedAtMillis = 0;
    isPlaying = true;
  }

  updateBlinkerInfo();
  drawProgressBar(true);
}

void switchMode() {
  playMode = (playMode + 1) % 3;

  if (playMode == 0) Mp3Player.playMode(WT2003S_CYCLE);
  if (playMode == 1) Mp3Player.playMode(WT2003S_SINGLE_CYCLE);
  if (playMode == 2) Mp3Player.playMode(WT2003S_RANDOM);

  delay(50);

  updateBlinkerInfo();
}

void saveMemory() {
  Wire.beginTransmission(EEPROM_ADDR);
  Wire.write(0x00);
  Wire.write(0x00);
  Wire.write((uint8_t)currentTrack);
  Wire.endTransmission();

  delay(6);
}

// ==================== Blinker APP 功能 ====================
void setupBlinkerApp() {
#if ENABLE_BLINKER
  AppBtnPlay.attach(blinkerPlayCallback);
  AppBtnPrev.attach(blinkerPrevCallback);
  AppBtnNext.attach(blinkerNextCallback);
  AppBtnMode.attach(blinkerModeCallback);
  AppBtnLock.attach(blinkerLockCallback);
  AppBtnList.attach(blinkerListCallback);
  AppBtnVolUp.attach(blinkerVolUpCallback);
  AppBtnVolDown.attach(blinkerVolDownCallback);
  AppSliderVol.attach(blinkerVolSliderCallback);

  Blinker.attachHeartbeat(blinkerHeartbeat);

  Blinker.begin(BLINKER_AUTH, WIFI_SSID, WIFI_PSWD);

  blinkerReady = true;
  updateBlinkerInfo(true);
#endif
}

void updateBlinkerInfo(bool force) {
#if ENABLE_BLINKER
  if (!blinkerReady) return;

  if (!force && millis() - lastBlinkerInfoPush < 800) return;

  DateTime now = getDisplayNow();

  String nowStr = "";
  nowStr += twoDigits(now.hour());
  nowStr += ":";
  nowStr += twoDigits(now.minute());

#if TIME_DISPLAY_WITH_SECONDS
  nowStr += ":";
  nowStr += twoDigits(now.second());
#endif

  AppTextTitle.print(shortenText(getSongTitle(currentTrack), 40));
  AppTextState.print(isPlaying ? "Playing" : "Paused");
  AppTextMode.print(modeNames[playMode]);
  AppTextTime.print(nowStr);

  AppNumTrack.print(currentTrack);
  AppNumVol.print(volume);
  AppSliderVol.print(volume);

  lastBlinkerInfoPush = millis();
#endif
}

void updateBlinkerTask() {
#if ENABLE_BLINKER
  if (!blinkerReady) return;

  if (millis() - lastBlinkerInfoPush > 5000) {
    updateBlinkerInfo(true);
  }
#endif
}

void redrawAfterAppAction() {
  lastUserAction = millis();
  updateBlinkerInfo(true);

  if (isScreenLocked) {
    drawLockScreen();
    return;
  }

  if (currentPage == PAGE_PLAYER) {
    updateDynamicUI();
  } else if (currentPage == PAGE_LIST) {
    drawListContent();
  } else if (currentPage == PAGE_TIME_SET) {
    updateTimeSetValue();
  }
}

#if ENABLE_BLINKER
void blinkerPlayCallback(const String & state) {
  lastUserAction = millis();
  togglePlay();
  redrawAfterAppAction();
}

void blinkerPrevCallback(const String & state) {
  lastUserAction = millis();
  playPrev();
  redrawAfterAppAction();
}

void blinkerNextCallback(const String & state) {
  lastUserAction = millis();
  playNext();
  redrawAfterAppAction();
}

void blinkerModeCallback(const String & state) {
  lastUserAction = millis();
  switchMode();
  redrawAfterAppAction();
}

void blinkerLockCallback(const String & state) {
  lastUserAction = millis();

  if (isScreenLocked) {
    exitLockScreen();
  } else {
    enterLockScreen();
  }

  updateBlinkerInfo(true);
}

void blinkerListCallback(const String & state) {
  lastUserAction = millis();

  if (isScreenLocked) {
    exitLockScreen();
  }

  if (currentPage == PAGE_LIST) {
    enterPlayerPage();
  } else {
    enterListPage();
  }

  updateBlinkerInfo(true);
}

void blinkerVolUpCallback(const String & state) {
  lastUserAction = millis();
  setVolumeSafe(volume + 1);
  redrawAfterAppAction();
}

void blinkerVolDownCallback(const String & state) {
  lastUserAction = millis();
  setVolumeSafe(volume - 1);
  redrawAfterAppAction();
}

void blinkerVolSliderCallback(int32_t value) {
  lastUserAction = millis();

  int v = constrain((int)value, 0, 31);
  setVolumeSafe(v);

  redrawAfterAppAction();
}

void blinkerHeartbeat() {
  updateBlinkerInfo(true);
}
#endif

// ==================== 播放进度条 ====================
uint16_t getTrackDurationSec(int trackNum) {
  int count = sizeof(SONG_DURATIONS_SEC) / sizeof(SONG_DURATIONS_SEC[0]);

  if (trackNum > 0 && trackNum < count && SONG_DURATIONS_SEC[trackNum] > 0) {
    return SONG_DURATIONS_SEC[trackNum];
  }

  return DEFAULT_TRACK_DURATION_SEC;
}

unsigned long getTrackElapsedMillis() {
  if (!hasStarted) return 0;

  unsigned long nowMs = millis();

  if (!isPlaying && pausedAtMillis > 0) {
    nowMs = pausedAtMillis;
  }

  unsigned long baseMs = trackStartMillis + pausedAccumMillis;

  if (nowMs <= baseMs) return 0;

  return nowMs - baseMs;
}

void resetTrackProgress() {
  trackStartMillis = millis();
  pausedAtMillis = 0;
  pausedAccumMillis = 0;
  lastProgressUpdate = 0;
  lastProgressPercent = -1;
}

void drawProgressBar(bool force) {
  if (currentPage != PAGE_PLAYER) return;
  if (isScreenLocked) return;

  unsigned long durationMs = (unsigned long)getTrackDurationSec(currentTrack) * 1000UL;
  unsigned long elapsedMs = getTrackElapsedMillis();

  if (elapsedMs > durationMs) elapsedMs = durationMs;

  int percent = 0;

  if (durationMs > 0) {
    percent = (int)((elapsedMs * 100UL) / durationMs);
  }

  if (!force && percent == lastProgressPercent) return;

  lastProgressPercent = percent;

  tft.fillRoundRect(PROGRESS_X, PROGRESS_Y, PROGRESS_W, PROGRESS_H, 4, tft.color565(35, 42, 62));
  tft.drawRoundRect(PROGRESS_X, PROGRESS_Y, PROGRESS_W, PROGRESS_H, 4, tft.color565(75, 90, 120));

  int fillW = ((PROGRESS_W - 2) * percent) / 100;

  if (fillW > 0) {
    tft.fillRoundRect(PROGRESS_X + 1, PROGRESS_Y + 1, fillW, PROGRESS_H - 2, 3, UI_ACCENT);
  }

  uint16_t durSec = getTrackDurationSec(currentTrack);
  uint16_t elapsedSec = elapsedMs / 1000UL;

  tft.fillRect(32, 123, 260, 10, UI_BG);

  tft.setTextColor(UI_TEXT_DIM);
  tft.setTextSize(1);

  tft.setCursor(34, 124);
  tft.print(formatDuration(elapsedSec));

  String totalText = formatDuration(durSec);
  tft.setCursor(260, 124);
  tft.print(totalText);
}

void updateProgressTask() {
  if (currentPage != PAGE_PLAYER || !hasStarted) return;
  if (isScreenLocked) return;

  if (millis() - lastProgressUpdate < 500) return;

  lastProgressUpdate = millis();

  drawProgressBar(false);
}

// ==================== 锁屏功能 ====================
void drawLockPattern() {
  tft.drawCircle(160, 118, 91, tft.color565(18, 32, 62));
  tft.drawCircle(160, 118, 72, tft.color565(22, 45, 82));
  tft.drawCircle(160, 118, 54, tft.color565(30, 70, 105));

  tft.fillCircle(42, 53, 3, UI_ACCENT);
  tft.fillCircle(278, 53, 3, UI_ACCENT_2);
  tft.fillCircle(42, 192, 3, UI_PURPLE);
  tft.fillCircle(278, 192, 3, UI_GREEN);

  tft.drawLine(42, 53, 77, 72, tft.color565(30, 60, 90));
  tft.drawLine(278, 53, 243, 72, tft.color565(30, 60, 90));
  tft.drawLine(42, 192, 77, 172, tft.color565(30, 60, 90));
  tft.drawLine(278, 192, 243, 172, tft.color565(30, 60, 90));

  tft.fillRoundRect(101, 93, 118, 85, 18, UI_CARD);
  tft.drawRoundRect(101, 93, 118, 85, 18, UI_ACCENT);

  tft.drawRoundRect(126, 65, 68, 62, 28, UI_ACCENT);
  tft.drawRoundRect(132, 72, 56, 50, 23, tft.color565(20, 38, 68));

  tft.fillRoundRect(114, 112, 92, 55, 13, tft.color565(24, 34, 58));
  tft.drawRoundRect(114, 112, 92, 55, 13, UI_ACCENT_2);

  tft.fillCircle(160, 135, 7, UI_ACCENT_2);
  tft.fillRoundRect(157, 139, 7, 17, 3, UI_ACCENT_2);

  tft.drawFastHLine(130, 158, 60, tft.color565(72, 88, 120));
}

void updateLockScreenClock(bool force) {
  if (!force && millis() - lastLockClockUpdate < 1000) return;

  prepareTftBus();

  tft.fillRoundRect(72, 23, 176, 34, 17, tft.color565(9, 16, 34));
  tft.drawRoundRect(72, 23, 176, 34, 17, tft.color565(42, 60, 95));

  DateTime now = getDisplayNow();

  tft.setTextColor(UI_ACCENT);
  tft.setTextSize(2);
  tft.setCursor(103, 33);

  if (now.hour() < 10) tft.print("0");
  tft.print(now.hour());
  tft.print(":");

  if (now.minute() < 10) tft.print("0");
  tft.print(now.minute());

#if TIME_DISPLAY_WITH_SECONDS
  tft.print(":");
  if (now.second() < 10) tft.print("0");
  tft.print(now.second());
#endif

  lastLockClockUpdate = millis();
}

void drawLockScreen() {
  prepareTftBus();

  tft.fillScreen(UI_BG);

  tft.fillRoundRect(-20, -18, 360, 78, 26, tft.color565(10, 20, 48));
  tft.drawFastHLine(0, 60, 320, UI_ACCENT);

  updateLockScreenClock(true);

  drawLockPattern();

  tft.setTextColor(ILI9341_WHITE);
  tft.setTextSize(2);
  tft.setCursor(78, 186);
  tft.print("SCREEN LOCKED");

  tft.setTextColor(UI_TEXT_DIM);
  tft.setTextSize(1);
  tft.setCursor(82, 211);
  tft.print("Tap anywhere to unlock");

  tft.setTextColor(UI_ACCENT_2);
  tft.setTextSize(1);
  tft.setCursor(26, 226);

  if (hasStarted) {
    tft.print(isPlaying ? "Playing: " : "Paused: ");
    tft.print(shortenText(getSongTitle(currentTrack), 34));
  } else {
    tft.print("MP3 Player Standby");
  }
}

void enterLockScreen() {
  if (isScreenLocked) return;

  isScreenLocked = true;
  lastLockClockUpdate = 0;

#if TFT_BL_PIN >= 0
  setBacklight(true);
#endif

  drawLockScreen();
}

void exitLockScreen() {
  if (!isScreenLocked) return;

  isScreenLocked = false;

  lastUserAction = millis();
  lastTimeUpdate = 0;
  lastProgressPercent = -1;

#if TFT_BL_PIN >= 0
  setBacklight(true);
#endif

  if (currentPage == PAGE_PLAYER) {
    drawPlayScreen();
  } else if (currentPage == PAGE_LIST) {
    drawListScreen();
  } else if (currentPage == PAGE_TIME_SET) {
    drawTimeSetScreen();
  }
}

// ==================== 时间设置页面 ====================
bool isTimeAreaTouched(int x, int y) {
  return (x >= 175 && x <= 319 && y >= 0 && y <= 40);
}

void enterTimeSetPage() {
  DateTime now = getDisplayNow();

  editHour = now.hour();
  editMinute = now.minute();
  editSecond = now.second();

  currentPage = PAGE_TIME_SET;

  drawTimeSetScreen();
}

void changeEditTime(int field, int delta) {
  if (field == 0) {
    editHour = (editHour + delta + 24) % 24;
  } else if (field == 1) {
    editMinute = (editMinute + delta + 60) % 60;
  } else if (field == 2) {
    editSecond = (editSecond + delta + 60) % 60;
  }

  updateTimeSetValue();
}

void saveEditedTime() {
  if (rtcAvailable) {
    DateTime now = getDisplayNow();

    rtc.adjust(DateTime(
      now.year(),
      now.month(),
      now.day(),
      editHour,
      editMinute,
      editSecond
    ));
  }

  lastTimeUpdate = 0;

  enterPlayerPage();
}

void updateTimeSetValue() {
  prepareTftBus();

  tft.fillRoundRect(24, 52, 272, 54, 14, UI_CARD);
  tft.drawRoundRect(24, 52, 272, 54, 14, UI_LINE);

  tft.setTextColor(UI_ACCENT);
  tft.setTextSize(4);
  tft.setCursor(49, 64);

  if (editHour < 10) tft.print("0");
  tft.print(editHour);
  tft.print(":");

  if (editMinute < 10) tft.print("0");
  tft.print(editMinute);
  tft.print(":");

  if (editSecond < 10) tft.print("0");
  tft.print(editSecond);
}

void drawTimeSetScreen() {
  prepareTftBus();

  tft.fillScreen(UI_BG);
  drawHeader("SET CLOCK");

  tft.setTextColor(UI_TEXT_DIM);
  tft.setTextSize(1);
  tft.setCursor(36, 38);
  tft.print("Tap + or - to adjust RTC time");

  updateTimeSetValue();

  drawButton(10, 118, 95, 32, "H+", UI_PURPLE);
  drawButton(112, 118, 95, 32, "M+", UI_PURPLE);
  drawButton(215, 118, 95, 32, "S+", UI_PURPLE);

  drawButton(10, 158, 95, 32, "H-", tft.color565(75, 80, 105));
  drawButton(112, 158, 95, 32, "M-", tft.color565(75, 80, 105));
  drawButton(215, 158, 95, 32, "S-", tft.color565(75, 80, 105));

  drawButton(10, 205, 145, 28, "SAVE", UI_GREEN);
  drawButton(165, 205, 145, 28, "BACK", tft.color565(70, 76, 92));
}

// ==================== 页面切换 ====================
void enterListPage() {
  currentPage = PAGE_LIST;
  listPage = (currentTrack - 1) / SONGS_PER_PAGE;

  drawListScreen();
}

void enterPlayerPage() {
  currentPage = PAGE_PLAYER;

  drawPlayScreen();
}

void refreshCurrentPage() {
  if (currentPage == PAGE_PLAYER) {
    updateDynamicUI();
  } else if (currentPage == PAGE_LIST) {
    drawListContent();
  } else if (currentPage == PAGE_TIME_SET) {
    updateTimeSetValue();
  }
}

// ==================== UI 绘制 ====================
void drawHeader(const char* title) {
  prepareTftBus();

  tft.fillRect(0, 0, 320, 33, UI_HEADER);
  tft.fillRect(0, 32, 320, 2, UI_ACCENT);

  tft.setTextColor(ILI9341_WHITE);
  tft.setTextSize(2);
  tft.setCursor(10, 9);
  tft.print(title);

  drawTopStatus(true);
}

void drawPlayScreen() {
  prepareTftBus();

  tft.fillScreen(UI_BG);
  drawHeader("Pocket MP3");

  tft.fillRoundRect(12, 43, 296, 92, 16, UI_CARD);
  tft.drawRoundRect(12, 43, 296, 92, 16, UI_LINE);

  tft.fillCircle(45, 79, 24, tft.color565(28, 36, 62));
  tft.drawCircle(45, 79, 24, UI_ACCENT);
  tft.fillCircle(45, 79, 9, UI_ACCENT_2);
  tft.fillCircle(45, 79, 3, UI_BG);

  tft.fillRoundRect(12, 142, 296, 93, 18, tft.color565(13, 18, 32));
  tft.drawRoundRect(12, 142, 296, 93, 18, tft.color565(45, 58, 85));

  drawButton(28, 154, 66, 38, "<<", tft.color565(50, 58, 82));
  drawButton(226, 154, 66, 38, ">>", tft.color565(50, 58, 82));

  drawButton(16, 203, 58, 29, "LIST", UI_ACCENT);
  drawButton(82, 203, 64, 29, "MODE", UI_PURPLE);
  drawButton(154, 203, 64, 29, "LOCK", tft.color565(245, 145, 58));
  drawButton(226, 203, 36, 29, "V-", tft.color565(100, 80, 72));
  drawButton(272, 203, 36, 29, "V+", UI_GREEN);

  updateDynamicUI();
}

void updateDynamicUI() {
  if (isScreenLocked) return;

  prepareTftBus();

  tft.fillRect(74, 52, 222, 47, UI_CARD);

  String title = getSongTitle(currentTrack);
  String line1 = title;
  String line2 = "";

  if (title.length() > 30) {
    line1 = title.substring(0, 30);
    line2 = title.substring(30);
  }

  tft.setTextColor(UI_TEXT_DIM);
  tft.setTextSize(1);
  tft.setCursor(76, 54);
  tft.print(isPlaying ? "NOW PLAYING" : "PAUSED");

  printFit(line1, 76, 70, 30, ILI9341_WHITE, 1);

  if (line2.length() > 0) {
    printFit(line2, 76, 86, 30, ILI9341_WHITE, 1);
  }

  drawProgressBar(true);

  tft.fillRoundRect(28, 137, 264, 16, 8, tft.color565(22, 30, 50));
  tft.setTextColor(UI_TEXT_DIM);
  tft.setTextSize(1);
  tft.setCursor(39, 141);

  tft.print("No.");
  tft.print(currentTrack);
  tft.print("/");
  tft.print(TOTAL_SONGS);
  tft.print("   Vol ");
  tft.print(volume);
  tft.print("   ");
  tft.print(modeNames[playMode]);

  uint16_t btnColor = isPlaying ? UI_RED : UI_GREEN;

  tft.fillRoundRect(120, 148, 80, 50, 16, btnColor);
  tft.drawRoundRect(120, 148, 80, 50, 16, tft.color565(95, 105, 130));

  if (isPlaying) {
    tft.fillRect(148, 162, 8, 23, ILI9341_WHITE);
    tft.fillRect(164, 162, 8, 23, ILI9341_WHITE);
  } else {
    tft.fillTriangle(148, 159, 148, 187, 174, 173, ILI9341_WHITE);
  }
}

void drawListFrame() {
  prepareTftBus();

  tft.fillScreen(UI_BG);
  drawHeader("Music Library");

  tft.fillRoundRect(10, 41, 300, 24, 12, UI_CARD);
  tft.drawRoundRect(10, 41, 300, 24, 12, UI_LINE);

  tft.setTextSize(1);
  tft.setTextColor(UI_TEXT_DIM);
  tft.setCursor(22, 49);
  tft.print("Tap a song card to play");

  drawButton(8, 204, 92, 30, "PLAYER", UI_ACCENT);
  drawButton(112, 204, 88, 30, "UP", tft.color565(64, 72, 98));
  drawButton(212, 204, 100, 30, "DOWN", tft.color565(64, 72, 98));
}

void drawListContent() {
  if (isScreenLocked) return;

  prepareTftBus();

  listPage = constrain(listPage, 0, maxListPage());

  tft.fillRect(230, 45, 72, 14, UI_CARD);
  tft.setTextSize(1);
  tft.setTextColor(UI_ACCENT);
  tft.setCursor(238, 49);
  tft.print("Page ");
  tft.print(listPage + 1);
  tft.print("/");
  tft.print(maxListPage() + 1);

  tft.fillRect(5, 70, 310, 128, UI_BG);

  for (int row = 0; row < SONGS_PER_PAGE; row++) {
    int track = listPage * SONGS_PER_PAGE + row + 1;
    int y = 72 + row * 25;

    if (track > TOTAL_SONGS) {
      tft.fillRoundRect(10, y, 300, 21, 8, tft.color565(12, 16, 28));
      tft.drawRoundRect(10, y, 300, 21, 8, tft.color565(30, 38, 58));
      continue;
    }

    bool active = (track == currentTrack);

    uint16_t bg = active ? tft.color565(36, 56, 86) : UI_CARD_2;
    uint16_t edge = active ? UI_ACCENT_2 : tft.color565(45, 56, 82);
    uint16_t fg = active ? ILI9341_WHITE : tft.color565(220, 225, 235);

    tft.fillRoundRect(10, y, 300, 21, 8, bg);
    tft.drawRoundRect(10, y, 300, 21, 8, edge);

    tft.fillRoundRect(16, y + 3, 34, 15, 6, active ? UI_ACCENT_2 : tft.color565(42, 50, 74));
    tft.setTextSize(1);
    tft.setTextColor(active ? UI_BG : ILI9341_WHITE);
    tft.setCursor(24, y + 7);

    if (track < 10) tft.print("0");
    tft.print(track);

    if (active && isPlaying) {
      tft.setTextColor(UI_ACCENT_2);
      tft.setCursor(57, y + 7);
      tft.print(">");
      printFit(getSongTitle(track), 66, y + 7, 28, fg, 1);
    } else {
      printFit(getSongTitle(track), 58, y + 7, 31, fg, 1);
    }

    String dur = formatDuration(getTrackDurationSec(track));
    tft.setTextSize(1);
    tft.setTextColor(UI_TEXT_DIM);
    tft.setCursor(270, y + 7);
    tft.print(dur);
  }
}

void drawListScreen() {
  drawListFrame();
  drawListContent();
}

void drawTopStatus(bool force) {
  if (isScreenLocked) return;
  if (!force && millis() - lastTimeUpdate <= 1000) return;

  prepareTftBus();

  tft.fillRoundRect(176, 5, 136, 23, 11, tft.color565(25, 35, 65));
  tft.drawRoundRect(176, 5, 136, 23, 11, tft.color565(55, 72, 110));

  tft.setTextColor(UI_ACCENT);
  tft.setTextSize(2);
  tft.setCursor(184, 9);

  DateTime now = getDisplayNow();

  if (now.hour() < 10) tft.print("0");
  tft.print(now.hour());
  tft.print(":");

  if (now.minute() < 10) tft.print("0");
  tft.print(now.minute());

#if TIME_DISPLAY_WITH_SECONDS
  tft.print(":");

  if (now.second() < 10) tft.print("0");
  tft.print(now.second());
#endif

  lastTimeUpdate = millis();
}

// ==================== 触摸处理 ====================
void handleTouch() {
  if (!ts.touched()) return;
  if (millis() - lastTouchTime < 120) return;

  lastTouchTime = millis();

  digitalWrite(TFT_CS, HIGH);
  TS_Point p = ts.getPoint();
  digitalWrite(TOUCH_CS, HIGH);

  if (isScreenLocked) {
    exitLockScreen();
    return;
  }

  lastUserAction = millis();

  int x = map(p.x, 300, 3800, 0, 320);
  int y = map(p.y, 3800, 200, 0, 240);

  if (currentPage == PAGE_TIME_SET) {
    if (y >= 118 && y <= 150) {
      if (x >= 10 && x <= 105) {
        changeEditTime(0, +1);
      } else if (x >= 112 && x <= 207) {
        changeEditTime(1, +1);
      } else if (x >= 215 && x <= 310) {
        changeEditTime(2, +1);
      }
    } else if (y >= 158 && y <= 190) {
      if (x >= 10 && x <= 105) {
        changeEditTime(0, -1);
      } else if (x >= 112 && x <= 207) {
        changeEditTime(1, -1);
      } else if (x >= 215 && x <= 310) {
        changeEditTime(2, -1);
      }
    } else if (y >= 205 && y <= 235) {
      if (x >= 10 && x <= 155) {
        saveEditedTime();
      } else if (x >= 165 && x <= 310) {
        enterPlayerPage();
      }
    }

    return;
  }

  if (currentPage == PAGE_PLAYER && isTimeAreaTouched(x, y)) {
    enterTimeSetPage();
    return;
  }

  if (currentPage == PAGE_PLAYER) {
    if (x >= 28 && x <= 94 && y >= 154 && y <= 192) {
      playPrev();
      updateDynamicUI();
      return;
    }

    if (x >= 120 && x <= 200 && y >= 148 && y <= 198) {
      togglePlay();
      updateDynamicUI();
      return;
    }

    if (x >= 226 && x <= 292 && y >= 154 && y <= 192) {
      playNext();
      updateDynamicUI();
      return;
    }

    if (y >= 203 && y <= 235) {
      if (x >= 16 && x <= 74) {
        enterListPage();
      } else if (x >= 82 && x <= 146) {
        switchMode();
        updateDynamicUI();
      } else if (x >= 154 && x <= 218) {
        enterLockScreen();
      } else if (x >= 226 && x <= 262) {
        setVolumeSafe(volume - 1);
        updateDynamicUI();
      } else if (x >= 272 && x <= 308) {
        setVolumeSafe(volume + 1);
        updateDynamicUI();
      }

      return;
    }

    return;
  }

  if (currentPage == PAGE_LIST) {
    if (y >= 72 && y < 72 + SONGS_PER_PAGE * 25) {
      int row = (y - 72) / 25;
      int track = listPage * SONGS_PER_PAGE + row + 1;

      if (track >= 1 && track <= TOTAL_SONGS) {
        playTrack(track);
        enterPlayerPage();
      }

      return;
    }

    if (y >= 204 && y <= 236) {
      if (x >= 8 && x <= 100) {
        enterPlayerPage();
      } else if (x >= 112 && x <= 200) {
        if (listPage > 0) listPage--;
        drawListContent();
      } else if (x >= 212 && x <= 312) {
        if (listPage < maxListPage()) listPage++;
        drawListContent();
      }

      return;
    }
  }
}

// ==================== 初始化 ====================
void setup() {
  Serial.begin(115200);

#if TFT_BL_PIN >= 0
  pinMode(TFT_BL_PIN, OUTPUT);
#endif

  setBacklight(true);

  pinMode(TOUCH_CS, OUTPUT);
  digitalWrite(TOUCH_CS, HIGH);

  pinMode(TFT_CS, OUTPUT);
  digitalWrite(TFT_CS, HIGH);

  Wire.begin();

  randomSeed((uint32_t)micros());

  tft.begin();
  tft.setRotation(1);
  tft.setTextWrap(false);

  ts.begin();
  ts.setRotation(1);

  initRTC();

  tft.fillScreen(UI_BG);
  tft.fillRoundRect(28, 62, 264, 98, 20, UI_CARD);
  tft.drawRoundRect(28, 62, 264, 98, 20, UI_ACCENT);

  tft.setTextColor(ILI9341_WHITE);
  tft.setTextSize(2);
  tft.setCursor(63, 82);
  tft.print("Pocket MP3");

  tft.setTextColor(UI_TEXT_DIM);
  tft.setTextSize(1);
  tft.setCursor(77, 112);
  tft.print("Loading player module...");

  mp3Serial.begin(9600, SERIAL_8N1, MP3_RX_PIN, MP3_TX_PIN);
  delay(200);

  Mp3Player.init(mp3Serial);
  delay(500);

  int sdCount = Mp3Player.getSDMp3FileNumber();

  if (sdCount > 0 && sdCount < 1000) {
    TOTAL_SONGS = min(sdCount, MAX_SONGS);
  }

  tft.fillRect(60, 132, 210, 14, UI_CARD);
  tft.setTextColor(UI_ACCENT);
  tft.setTextSize(1);
  tft.setCursor(84, 134);
  tft.print("Reading songs from SD card");

  loadSongNames();

  Wire.beginTransmission(EEPROM_ADDR);
  Wire.write(0x00);
  Wire.write(0x00);
  Wire.endTransmission();

  Wire.requestFrom(EEPROM_ADDR, 1);

  if (Wire.available()) {
    currentTrack = Wire.read();
  }

  if (currentTrack < 1 || currentTrack > TOTAL_SONGS) {
    currentTrack = 1;
  }

  setVolumeSafe(volume);

  playTrack(currentTrack, false);

  drawPlayScreen();

  lastUserAction = millis();

#if ENABLE_BLINKER
  tft.fillRoundRect(38, 92, 244, 48, 15, UI_CARD);
  tft.drawRoundRect(38, 92, 244, 48, 15, UI_ACCENT);
  tft.setTextColor(UI_ACCENT);
  tft.setTextSize(1);
  tft.setCursor(71, 111);
  tft.print("Connecting Blinker WiFi...");
#endif

  setupBlinkerApp();

  drawPlayScreen();
}

// ==================== 主循环 ====================
void loop() {
#if ENABLE_BLINKER
  if (blinkerReady) {
    Blinker.run();
  }
#endif

  handleTouch();

  if (isScreenLocked) {
    updateLockScreenClock(false);
    updateBlinkerTask();
    return;
  }

#if SCREEN_AUTO_LOCK_TIMEOUT_MS > 0
  if (!isScreenLocked && millis() - lastUserAction > SCREEN_AUTO_LOCK_TIMEOUT_MS) {
    enterLockScreen();
    return;
  }
#endif

  if (!isScreenLocked && currentPage != PAGE_TIME_SET) {
    drawTopStatus(false);
  }

  if (!isScreenLocked && currentPage == PAGE_PLAYER) {
    updateProgressTask();
  }

  updateBlinkerTask();
}