#include <SPI.h>
#include "DW1000Ranging.h"
#include "DW1000.h"
#include <U8g2lib.h>

char anchor_addr[] = "84:00:5B:D5:A9:9A:E2:9C";  //#4

uint16_t Adelay = 16296;
float dist_m = 1; //meters

#define SPI_SCK 18
#define SPI_MISO 19
#define SPI_MOSI 23
#define DW_CS 4

const uint8_t PIN_RST = 26;
const uint8_t PIN_IRQ = 15;
const uint8_t PIN_SS = 5;

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

// Biến toàn cục để lưu khoảng cách hợp lệ gần nhất
int lastValidDistance = 0;

void updateLCD(uint16_t distance, float rxPower, float quality) {
    char buffer[32];
    char signalLevel[10];

    if (rxPower > -60) {
        strcpy(signalLevel, "Qua gan");
    } else if (rxPower > -75 && quality > 0.90) {
        strcpy(signalLevel, "Tot");
    } else if (rxPower > -80 && quality > 0.75) {
        strcpy(signalLevel, "Tuong doi");
    } else if (rxPower > -85 && quality > 0.60) {
        strcpy(signalLevel, "Tru bi");
    } else if (rxPower > -88 && quality > 0.40) {
        strcpy(signalLevel, "Kem");
    } else {
        strcpy(signalLevel, "Yeu");
    }

    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_ncenB08_tr);

    u8g2.drawStr(0, 12, "Range:");
    sprintf(buffer, "%d mm", distance);
    u8g2.drawStr(45, 12, buffer);

    u8g2.drawStr(0, 28, "Power:");
    sprintf(buffer, "%+.1f dBm", rxPower);
    u8g2.drawStr(45, 28, buffer);

    u8g2.drawStr(0, 44, "Quality:");
    sprintf(buffer, "%.2f", quality);
    u8g2.drawStr(46, 44, buffer);

    u8g2.drawStr(0, 60, "Muc tin hieu:");
    u8g2.drawStr(85, 60, signalLevel);

    u8g2.sendBuffer();
}

void sendDistancePacket(uint16_t distance) {
    Serial.println(distance); 
}


void setup() {
    Serial.begin(115200);
    delay(100);

    u8g2.begin();
    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_ncenB08_tr);
    u8g2.drawStr(0, 10, "Welc TFT, BibiTran13");
    u8g2.drawStr(0, 20, "Starting receive...");
    u8g2.sendBuffer();
    delay(1000);

    SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
    DW1000Ranging.initCommunication(PIN_RST, PIN_SS, PIN_IRQ);
    DW1000.setAntennaDelay(Adelay);

    DW1000Ranging.attachNewRange(newRange);
    DW1000Ranging.attachNewDevice(newDevice);
    DW1000Ranging.attachInactiveDevice(inactiveDevice);
    DW1000Ranging.setReplyTime(10000);
    DW1000Ranging.setRangeFilterValue(20);

    DW1000Ranging.useRangeFilter(true);
    DW1000.setChannel(7);

    DW1000Ranging.startAsAnchor(anchor_addr, DW1000.MODE_LONGDATA_FAST_LOWPOWER, false);
}

void loop() {
    DW1000Ranging.loop();
}

void newRange() {
    float dist = DW1000Ranging.getDistantDevice()->getRange();
    float rxPower = DW1000Ranging.getDistantDevice()->getRXPower();
    float quality = DW1000Ranging.getDistantDevice()->getQuality();

    int dist_mm = round(dist * 1000);

    if (dist_mm <= 5000) {
        lastValidDistance = dist_mm;
    }

    sendDistancePacket(lastValidDistance);  

    updateLCD(lastValidDistance, rxPower, quality);
}

void newDevice(DW1000Device *device) {
    // Không gửi chuỗi nữa
}

void inactiveDevice(DW1000Device *device) {
    // Không gửi chuỗi nữa
}
