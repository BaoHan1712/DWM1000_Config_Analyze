#include <SPI.h>
#include "DW1000Ranging.h"
#include "DW1000.h"
#include <U8g2lib.h>

#define SPI_SCK 18
#define SPI_MISO 19
#define SPI_MOSI 23
#define DW_CS 4

// UART2 pin
#define UART2_TX 17
#define UART2_RX 16

// connection pins
const uint8_t PIN_RST = 26; // reset pin
const uint8_t PIN_IRQ = 15; // irq pin
const uint8_t PIN_SS = 5;   // spi select pin

// TAG antenna delay defaults to 16384
char tag_addr[] = "7D:00:22:EA:82:60:3B:9C";

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);
bool hasRange = false;
int lastDistance = 0;

void showWelcomeScreen() {
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB08_tr);
  u8g2.drawStr(0, 20, "TAG - Hi HanBao!");
  u8g2.sendBuffer();
}

void updateOLED(int distance) {
  char buffer[32];
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB08_tr);
  u8g2.drawStr(0, 12, "Range:");
  sprintf(buffer, "%d mm", distance);
  u8g2.drawStr(45, 12, buffer);
  u8g2.sendBuffer();
}

void sendDistance() {
  uint8_t packet[3];
  packet[0] = 0x02; // Start byte
  packet[1] = (lastDistance >> 8) & 0xFF; // High byte
  packet[2] = lastDistance & 0xFF;        // Low byte

  Serial2.write(packet, 3); // Gửi 3 byte
}

void checkSerialCommand() {
  if (Serial2.available()) {
    uint8_t cmd = Serial2.read();
    if (cmd == 1 or cmd == 0 && hasRange) {
      sendDistance();
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial2.begin(115200, SERIAL_8N1, UART2_RX, UART2_TX); // Khởi tạo UART2

  u8g2.begin();
  showWelcomeScreen();

  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
  DW1000Ranging.initCommunication(PIN_RST, PIN_SS, PIN_IRQ);

  DW1000Ranging.attachNewRange(newRange);
  DW1000Ranging.attachNewDevice(newDevice);
  DW1000Ranging.attachInactiveDevice(inactiveDevice);
  DW1000.setChannel(7);

  DW1000Ranging.startAsTag(tag_addr, DW1000.MODE_LONGDATA_FAST_LOWPOWER, false);
}

void loop() {
  DW1000Ranging.loop();
  checkSerialCommand(); // luôn kiểm tra nếu STM32 gửi lệnh

  if (!hasRange) {
    static unsigned long lastUpdate = 0;
    if (millis() - lastUpdate > 5000) {
      showWelcomeScreen();
      lastUpdate = millis();
    }
  }
}

void newRange() {
  float range = DW1000Ranging.getDistantDevice()->getRange();
  int dist_mm = round(range * 1000);

  // Serial.println(dist_mm); // debug ra USB Serial

  hasRange = true;
  lastDistance = dist_mm;
  updateOLED(dist_mm);
}

void newDevice(DW1000Device *device) {
  // Thêm xử lý nếu cần
}

void inactiveDevice(DW1000Device *device) {
  hasRange = false;
}
