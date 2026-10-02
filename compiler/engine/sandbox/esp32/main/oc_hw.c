/* Мост между прошивкой в QEMU и схемой в браузере (см. oc_hw.h).
 *
 * Прошивка → схема: строки «@OC …» в Serial (их прячет консоль и разбирает схема):
 *   @OC D <gpio> <0|1>                 уровень выхода
 *   @OC P <gpio> <скважность‱> <Гц>    ШИМ LEDC
 *   @OC LCD <кол> <стр> <текст> | @OC LCD CLR
 *   @OC NEO <gpio> <RRGGBB…>
 *   @OC HELLO                        прошивка начала слушать входы
 * Схема → прошивка: строки «@IN …» во входе UART0:
 *   @IN D <gpio> <0|1>   @IN A <gpio> <мВ>   @IN SW <gpio> <gpio> <0|1>
 *   @IN IR <код>   @IN RF <код>   @IN DIST <trig> <мм>   @IN DHT <gpio> <t×10> <h×10>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "driver/uart.h"
#include "esp_adc/adc_oneshot.h"
#include "oc_hw.h"

#define PINS 40
#define LINKS 32

static int8_t out_level[PINS] = {[0 ... PINS - 1] = -1};
static int8_t in_level[PINS] = {[0 ... PINS - 1] = -1};
static int16_t in_mv[PINS] = {[0 ... PINS - 1] = -1};
static int16_t distance_mm[PINS] = {[0 ... PINS - 1] = -1};
static int16_t dht_t[PINS], dht_h[PINS];
static bool dht_known[PINS];
static uint8_t links[LINKS][2];
static int link_count;
static volatile int ir_command = -1;
static volatile int64_t rf_code = -1;

/* ---------- телеметрия с ограничением: не больше ~300 строк в секунду, остальное — пачкой раз в 20 мс ---------- */
static int tokens = 300;
static TickType_t refill_at;
static uint64_t dirty;
static TaskHandle_t flusher;

static bool take_token(void) {
    TickType_t now = xTaskGetTickCount();
    if (now - refill_at >= pdMS_TO_TICKS(100)) { tokens = 30; refill_at = now; }
    if (tokens <= 0) return false;
    tokens--;
    return true;
}

static void flush_task(void *arg) {
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(20));
        uint64_t pending = dirty;
        dirty = 0;
        for (int pin = 0; pin < PINS; pin++)
            if (pending & (1ULL << pin)) printf("@OC D %d %d\n", pin, out_level[pin]);
    }
}

static void emit_level(int pin) {
    if (take_token()) { printf("@OC D %d %d\n", pin, out_level[pin]); return; }
    dirty |= 1ULL << pin;
    if (!flusher) xTaskCreate(flush_task, "oc_flush", 2048, NULL, 4, &flusher);
}

/* ---------- входы со схемы ---------- */
static void handle_line(char *line) {
    int a, b, c;
    if (sscanf(line, "@IN D %d %d", &a, &b) == 2 && a >= 0 && a < PINS) in_level[a] = b ? 1 : 0;
    else if (sscanf(line, "@IN A %d %d", &a, &b) == 2 && a >= 0 && a < PINS) in_mv[a] = b;
    else if (sscanf(line, "@IN SW %d %d %d", &a, &b, &c) == 3 && a >= 0 && a < PINS && b >= 0 && b < PINS) {
        int found = -1, free_slot = -1;
        for (int i = 0; i < link_count; i++) {
            if ((links[i][0] == a && links[i][1] == b) || (links[i][0] == b && links[i][1] == a)) found = i;
            if (links[i][0] == 0xff && free_slot < 0) free_slot = i;
        }
        if (c && found < 0) {
            if (free_slot < 0 && link_count < LINKS) free_slot = link_count++;
            if (free_slot >= 0) { links[free_slot][0] = a; links[free_slot][1] = b; }
        }
        if (!c && found >= 0) links[found][0] = links[found][1] = 0xff;
    }
    else if (sscanf(line, "@IN IR %d", &a) == 1) ir_command = a & 0xff;
    else if (strncmp(line, "@IN RF ", 7) == 0) rf_code = strtoll(line + 7, NULL, 10);
    else if (sscanf(line, "@IN DIST %d %d", &a, &b) == 2 && a >= 0 && a < PINS) distance_mm[a] = b;
    else if (sscanf(line, "@IN DHT %d %d %d", &a, &b, &c) == 3 && a >= 0 && a < PINS) {
        dht_t[a] = b; dht_h[a] = c; dht_known[a] = true;
    }
}

static void reader_task(void *arg) {
    char line[96];
    int length = 0;
    uint8_t byte;
    uart_driver_install(UART_NUM_0, 512, 0, 0, NULL, 0);
    printf("@OC HELLO\n");  // схема сразу пришлёт текущее состояние кнопок и датчиков
    for (;;) {
        if (uart_read_bytes(UART_NUM_0, &byte, 1, portMAX_DELAY) != 1) continue;
        if (byte == '\n' || byte == '\r') {
            line[length] = 0;
            if (length) handle_line(line);
            length = 0;
        } else if (length < (int)sizeof line - 1) {
            line[length++] = (char)byte;
        }
    }
}

/* UART0 слушаем только когда прошивка что-то читает со схемы — иначе ввод в консоль остаётся программе */
static void ensure_reader(void) {
    static bool started;
    if (started) return;
    started = true;
    xTaskCreate(reader_task, "oc_hw_in", 3072, NULL, 5, NULL);
}

/* ---------- перехват ESP-IDF ---------- */
esp_err_t __real_gpio_set_level(gpio_num_t pin, uint32_t level);
int __real_gpio_get_level(gpio_num_t pin);

esp_err_t __wrap_gpio_set_level(gpio_num_t pin, uint32_t level) {
    if (pin >= 0 && pin < PINS && out_level[pin] != (level ? 1 : 0)) {
        out_level[pin] = level ? 1 : 0;
        emit_level(pin);
    }
    return __real_gpio_set_level(pin, level);
}

int __wrap_gpio_get_level(gpio_num_t pin) {
    ensure_reader();
    if (pin < 0 || pin >= PINS) return __real_gpio_get_level(pin);
    // Нажатая кнопка клавиатуры соединяет ножку с выходом: читаем его уровень, иначе — подтяжку
    bool linked = false;
    for (int i = 0; i < link_count; i++) {
        int peer = links[i][0] == pin ? links[i][1] : links[i][1] == pin ? links[i][0] : -1;
        if (peer < 0 || peer >= PINS) continue;
        linked = true;
        if (out_level[peer] == 0) return 0;
    }
    if (linked) return 1;
    if (in_level[pin] >= 0) return in_level[pin];
    if (out_level[pin] >= 0) return out_level[pin];
    // QEMU читает свободные ножки как 0; на схеме у входов подтяжка, как у кнопки на INPUT_PULLUP
    return 1;
}

/* LEDC в QEMU не эмулируется: запоминаем настройки и шлём их на схему, в регистры не пишем */
typedef struct { bool on; int gpio; int timer; uint32_t duty; } channel_t;
static channel_t channels[LEDC_SPEED_MODE_MAX][LEDC_CHANNEL_MAX];
static uint32_t timer_freq[LEDC_SPEED_MODE_MAX][LEDC_TIMER_MAX];
static uint8_t timer_bits[LEDC_SPEED_MODE_MAX][LEDC_TIMER_MAX];

static void emit_pwm(int mode, int channel) {
    channel_t *ch = &channels[mode][channel];
    if (!ch->on || ch->gpio < 0 || ch->gpio >= PINS) return;
    int bits = timer_bits[mode][ch->timer] ? timer_bits[mode][ch->timer] : 13;
    uint64_t permyriad = (uint64_t)ch->duty * 10000 >> bits;
    printf("@OC P %d %u %lu\n", ch->gpio, (unsigned)(permyriad > 10000 ? 10000 : permyriad),
           (unsigned long)timer_freq[mode][ch->timer]);
}

esp_err_t __wrap_ledc_timer_config(const ledc_timer_config_t *cfg) {
    if (!cfg || cfg->speed_mode >= LEDC_SPEED_MODE_MAX || cfg->timer_num >= LEDC_TIMER_MAX) return ESP_ERR_INVALID_ARG;
    timer_freq[cfg->speed_mode][cfg->timer_num] = cfg->freq_hz;
    timer_bits[cfg->speed_mode][cfg->timer_num] = cfg->duty_resolution;
    return ESP_OK;
}

esp_err_t __wrap_ledc_channel_config(const ledc_channel_config_t *cfg) {
    if (!cfg || cfg->speed_mode >= LEDC_SPEED_MODE_MAX || cfg->channel >= LEDC_CHANNEL_MAX) return ESP_ERR_INVALID_ARG;
    channels[cfg->speed_mode][cfg->channel] = (channel_t){true, cfg->gpio_num, cfg->timer_sel, cfg->duty};
    emit_pwm(cfg->speed_mode, cfg->channel);
    return ESP_OK;
}

esp_err_t __wrap_ledc_set_duty(ledc_mode_t mode, ledc_channel_t channel, uint32_t duty) {
    if (mode >= LEDC_SPEED_MODE_MAX || channel >= LEDC_CHANNEL_MAX) return ESP_ERR_INVALID_ARG;
    channels[mode][channel].duty = duty;
    return ESP_OK;
}

esp_err_t __wrap_ledc_update_duty(ledc_mode_t mode, ledc_channel_t channel) {
    if (mode >= LEDC_SPEED_MODE_MAX || channel >= LEDC_CHANNEL_MAX) return ESP_ERR_INVALID_ARG;
    emit_pwm(mode, channel);
    return ESP_OK;
}

esp_err_t __wrap_ledc_set_duty_and_update(ledc_mode_t mode, ledc_channel_t channel, uint32_t duty, uint32_t hpoint) {
    if (__wrap_ledc_set_duty(mode, channel, duty) != ESP_OK) return ESP_ERR_INVALID_ARG;
    return __wrap_ledc_update_duty(mode, channel);
}

esp_err_t __wrap_ledc_set_freq(ledc_mode_t mode, ledc_timer_t timer, uint32_t freq) {
    if (mode >= LEDC_SPEED_MODE_MAX || timer >= LEDC_TIMER_MAX) return ESP_ERR_INVALID_ARG;
    timer_freq[mode][timer] = freq;
    for (int ch = 0; ch < LEDC_CHANNEL_MAX; ch++)
        if (channels[mode][ch].on && channels[mode][ch].timer == (int)timer) emit_pwm(mode, ch);
    return ESP_OK;
}

esp_err_t __wrap_ledc_stop(ledc_mode_t mode, ledc_channel_t channel, uint32_t idle_level) {
    if (mode >= LEDC_SPEED_MODE_MAX || channel >= LEDC_CHANNEL_MAX) return ESP_ERR_INVALID_ARG;
    channels[mode][channel].duty = 0;
    emit_pwm(mode, channel);
    return ESP_OK;
}

/* АЦП: значения берём со схемы (потенциометр, фоторезистор, датчик температуры) */
struct adc_oneshot_unit_ctx_t { adc_unit_t unit; };
static struct adc_oneshot_unit_ctx_t adc_units[2] = {{ADC_UNIT_1}, {ADC_UNIT_2}};
static const int8_t ADC1_GPIO[] = {36, 37, 38, 39, 32, 33, 34, 35};
static const int8_t ADC2_GPIO[] = {4, 0, 2, 15, 13, 12, 14, 27, 25, 26};

esp_err_t __wrap_adc_oneshot_new_unit(const adc_oneshot_unit_init_cfg_t *cfg, adc_oneshot_unit_handle_t *out) {
    if (!cfg || !out || cfg->unit_id > ADC_UNIT_2) return ESP_ERR_INVALID_ARG;
    *out = &adc_units[cfg->unit_id];
    return ESP_OK;
}

esp_err_t __wrap_adc_oneshot_config_channel(adc_oneshot_unit_handle_t unit, adc_channel_t channel,
                                            const adc_oneshot_chan_cfg_t *cfg) {
    return ESP_OK;
}

esp_err_t __wrap_adc_oneshot_del_unit(adc_oneshot_unit_handle_t unit) {
    return ESP_OK;
}

esp_err_t __wrap_adc_oneshot_read(adc_oneshot_unit_handle_t unit, adc_channel_t channel, int *out_raw) {
    ensure_reader();
    if (!unit || !out_raw) return ESP_ERR_INVALID_ARG;
    int gpio = unit->unit == ADC_UNIT_1 ? (channel < 8 ? ADC1_GPIO[channel] : -1) : (channel < 10 ? ADC2_GPIO[channel] : -1);
    int mv = gpio >= 0 && in_mv[gpio] >= 0 ? in_mv[gpio] : 0;
    *out_raw = mv >= 3300 ? 4095 : mv * 4095 / 3300;
    return ESP_OK;
}

/* ---------- короткие функции ---------- */
void oc_output(int pin) {
    gpio_reset_pin(pin);
    gpio_set_direction(pin, GPIO_MODE_OUTPUT);
}

void oc_input(int pin, bool pullup) {
    gpio_reset_pin(pin);
    gpio_set_direction(pin, GPIO_MODE_INPUT);
    gpio_set_pull_mode(pin, pullup ? GPIO_PULLUP_ONLY : GPIO_FLOATING);
}

void oc_write(int pin, int level) { gpio_set_level(pin, level ? 1 : 0); }
int oc_read(int pin) { return gpio_get_level(pin); }
void oc_delay(int ms) { vTaskDelay(pdMS_TO_TICKS(ms > 0 ? ms : 1)); }

/* Каждой ножке — свой канал LEDC; таймеры делятся по частоте */
static int pwm_channel(int pin, int freq) {
    static int8_t pin_channel[PINS] = {[0 ... PINS - 1] = -1};
    static int used;
    if (pin < 0 || pin >= PINS) return -1;
    if (pin_channel[pin] < 0) {
        if (used >= LEDC_CHANNEL_MAX) return -1;
        pin_channel[pin] = used++;
    }
    int ch = pin_channel[pin];
    int timer = ch / 2;  // два канала на таймер
    ledc_timer_config_t t = {.speed_mode = LEDC_LOW_SPEED_MODE, .duty_resolution = LEDC_TIMER_13_BIT,
                             .timer_num = timer, .freq_hz = freq > 0 ? freq : 1000, .clk_cfg = LEDC_AUTO_CLK};
    ledc_timer_config(&t);
    ledc_channel_config_t c = {.gpio_num = pin, .speed_mode = LEDC_LOW_SPEED_MODE, .channel = ch,
                               .timer_sel = timer, .duty = 0, .hpoint = 0};
    ledc_channel_config(&c);
    return ch;
}

void oc_pwm(int pin, int freq_hz, float duty) {
    int ch = pwm_channel(pin, freq_hz);
    if (ch < 0) return;
    if (duty < 0) duty = 0;
    if (duty > 1) duty = 1;
    ledc_set_duty(LEDC_LOW_SPEED_MODE, ch, (uint32_t)(duty * 8191));
    ledc_update_duty(LEDC_LOW_SPEED_MODE, ch);
}

void oc_servo(int pin, int angle) {
    if (angle < 0) angle = 0;
    if (angle > 180) angle = 180;
    float pulse_us = 544 + angle * (2400 - 544) / 180.0f;
    oc_pwm(pin, 50, pulse_us / 20000.0f);
}

void oc_tone(int pin, int freq_hz) {
    if (freq_hz > 0) oc_pwm(pin, freq_hz, 0.5f);
    else oc_pwm(pin, 1000, 0);
}

int oc_analog_mv(int pin) {
    static adc_oneshot_unit_handle_t unit;
    int channel = -1;
    for (int i = 0; i < 8; i++) if (ADC1_GPIO[i] == pin) channel = i;
    if (channel < 0) return -1;
    if (!unit) {
        adc_oneshot_unit_init_cfg_t cfg = {.unit_id = ADC_UNIT_1};
        adc_oneshot_new_unit(&cfg, &unit);
    }
    adc_oneshot_chan_cfg_t chan = {.atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_12};
    adc_oneshot_config_channel(unit, channel, &chan);
    int raw = 0;
    adc_oneshot_read(unit, channel, &raw);
    return raw * 3300 / 4095;
}

void oc_lcd_clear(void) { printf("@OC LCD CLR\n"); }

void oc_lcd_print(int col, int row, const char *text) {
    printf("@OC LCD %d %d %.40s\n", col, row, text ? text : "");
}

void oc_neopixel_show(int pin, const uint32_t *rgb, int count) {
    if (count > 64) count = 64;
    printf("@OC NEO %d ", pin);
    for (int i = 0; i < count; i++) printf("%06lx", (unsigned long)(rgb[i] & 0xffffff));
    printf("\n");
}

bool oc_ir_read(uint8_t *command) {
    ensure_reader();
    int value = ir_command;
    if (value < 0) return false;
    ir_command = -1;
    if (command) *command = (uint8_t)value;
    return true;
}

bool oc_rf_read(uint32_t *code) {
    ensure_reader();
    int64_t value = rf_code;
    if (value < 0) return false;
    rf_code = -1;
    if (code) *code = (uint32_t)value;
    return true;
}

float oc_distance_cm(int trig_pin, int echo_pin) {
    ensure_reader();
    if (trig_pin < 0 || trig_pin >= PINS || distance_mm[trig_pin] < 0) return -1;
    return distance_mm[trig_pin] / 10.0f;
}

bool oc_dht_read(int pin, float *temperature, float *humidity) {
    ensure_reader();
    if (pin < 0 || pin >= PINS || !dht_known[pin]) return false;
    if (temperature) *temperature = dht_t[pin] / 10.0f;
    if (humidity) *humidity = dht_h[pin] / 10.0f;
    return true;
}
