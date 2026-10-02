/* Детали на схеме для ESP32 в эмуляторе.
 *
 * QEMU не выводит ножки наружу, поэтому сборка перехватывает (ld --wrap) gpio_set_level, gpio_get_level,
 * ledc_* и adc_oneshot_*: обычный код ESP-IDF сам двигает светодиоды, серво и моторы на схеме,
 * а кнопки и датчики со схемы приходят в прошивку через UART.
 *
 * Короткие функции ниже — обёртки над тем же ESP-IDF, на настоящей плате они тоже работают.
 * ИК, радио, NeoPixel, LCD, HC-SR04 и DHT22 в эмуляторе доступны только через функции oc_*_ —
 * их протоколы требуют точного тайминга железа (RMT, I2C), которого в QEMU нет.
 */
#pragma once
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Ножки */
void oc_output(int pin);
void oc_input(int pin, bool pullup);
void oc_write(int pin, int level);
int oc_read(int pin);
void oc_delay(int ms);

/* ШИМ (LEDC): duty от 0.0 до 1.0; сервопривод 0…180°; звук пищалки, 0 — тишина */
void oc_pwm(int pin, int freq_hz, float duty);
void oc_servo(int pin, int angle);
void oc_tone(int pin, int freq_hz);

/* АЦП1 (GPIO 32–39): милливольты 0…3300 */
int oc_analog_mv(int pin);

/* Только в эмуляторе — детали со сложным протоколом */
void oc_lcd_clear(void);
void oc_lcd_print(int col, int row, const char *text);
void oc_neopixel_show(int pin, const uint32_t *rgb, int count);  /* цвета 0xRRGGBB */
bool oc_ir_read(uint8_t *command);       /* нажата кнопка ИК-пульта: код NEC */
bool oc_rf_read(uint32_t *code);         /* нажата кнопка радиопульта 433 МГц */
float oc_distance_cm(int trig_pin, int echo_pin);  /* HC-SR04, -1 — нет датчика на схеме */
bool oc_dht_read(int pin, float *temperature, float *humidity);

#ifdef __cplusplus
}
#endif
