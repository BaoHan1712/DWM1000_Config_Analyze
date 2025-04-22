#include <SPI.h>
#include "DW1000Ranging.h"
#include "DW1000.h"
#include <U8g2lib.h>

// ESP32_UWB pin definitions
#define SPI_SCK 18
#define SPI_MISO 19
#define SPI_MOSI 23
#define DW_CS 4

const uint8_t PIN_RST = 26;
const uint8_t PIN_IRQ = 15;
const uint8_t PIN_SS = 5;

char this_anchor_addr[] = "84:00:22:EA:82:60:3B:9C";
float this_anchor_target_distance = 1.0; // mục tiêu (m)

uint16_t this_anchor_Adelay = 16511;
uint16_t Adelay_delta = 100;

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

void setup()
{
  Serial.begin(115200);
  while (!Serial);

  u8g2.begin();
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB08_tr);
  u8g2.drawStr(0, 15, "Calibrating Adelay...");
  u8g2.sendBuffer();

  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
  DW1000Ranging.initCommunication(PIN_RST, PIN_SS, PIN_IRQ);

  Serial.print("Starting Adelay: "); Serial.println(this_anchor_Adelay);
  Serial.print("Target distance: "); Serial.println(this_anchor_target_distance);

  DW1000.setAntennaDelay(this_anchor_Adelay);

  DW1000Ranging.attachNewRange(newRange);
  DW1000Ranging.attachNewDevice(newDevice);
  DW1000Ranging.attachInactiveDevice(inactiveDevice);
  DW1000.setChannel(7);

  DW1000Ranging.startAsAnchor(this_anchor_addr, DW1000.MODE_LONGDATA_FAST_LOWPOWER, false);
}

void loop()
{
  DW1000Ranging.loop();
}

void newRange()
{
  static float last_delta = 0.0;

  float dist = 0.0;
  for (int i = 0; i < 100; i++) {
    dist += DW1000Ranging.getDistantDevice()->getRange();
  }
  dist /= 100.0;

  float this_delta = dist - this_anchor_target_distance;

  // Hiển thị thông tin lên Serial
  Serial.print("Dist: ");
  Serial.print(dist);
  Serial.print(" m, Adelay: ");
  Serial.println(this_anchor_Adelay);

  // Hiển thị OLED
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB08_tr);

  char line1[32], line2[32], line3[32], line4[32];
  sprintf(line1, "Target: %.2f m", this_anchor_target_distance);
  sprintf(line2, "Measured: %.3f m", dist);
  sprintf(line3, "Delta: %.3f m", this_delta);
  sprintf(line4, "Adelay: %u", this_anchor_Adelay);

  u8g2.drawStr(0, 12, line1);
  u8g2.drawStr(0, 26, line2);
  u8g2.drawStr(0, 40, line3);
  u8g2.drawStr(0, 54, line4);
  u8g2.sendBuffer();

  // Điều chỉnh Adelay
  if (this_delta * last_delta < 0.0) {
    Adelay_delta = Adelay_delta / 2;
  }
  last_delta = this_delta;

  if (this_delta > 0.0) this_anchor_Adelay += Adelay_delta;
  else this_anchor_Adelay -= Adelay_delta;

  DW1000.setAntennaDelay(this_anchor_Adelay);

  // Nếu sai số nhỏ, dừng lại và hiển thị kết quả
  if (Adelay_delta < 3) {
    Serial.print("Final Adelay: ");
    Serial.println(this_anchor_Adelay);

    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_ncenB08_tr);
    sprintf(line1, "Calib Done");
    sprintf(line2, "Final Adelay:");
    sprintf(line3, "%u", this_anchor_Adelay);
    u8g2.drawStr(0, 20, line1);
    u8g2.drawStr(0, 40, line2);
    u8g2.drawStr(0, 56, line3);
    u8g2.sendBuffer();

    while (1); // kết thúc hiệu chỉnh
  }
}

void newDevice(DW1000Device *device)
{
  Serial.print("Device added: ");
  Serial.println(device->getShortAddress(), HEX);
}

void inactiveDevice(DW1000Device *device)
{
  Serial.print("delete inactive device: ");
  Serial.println(device->getShortAddress(), HEX);
}
