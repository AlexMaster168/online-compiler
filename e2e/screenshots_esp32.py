"""Скриншоты схемы ESP32 для README: палитра, настройки детали, «приборная панель» в QEMU, телефон.

    python e2e/screenshots_esp32.py [http://127.0.0.1:8000]

Нужен образ oc-lang-esp32:1 (manage.py build_sandbox lang-esp32); прошивка собирается ~2 минуты.
"""
import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BASE, set_code, term_text, wait_until  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs/screenshots"

# Много деталей сразу: RGB и NeoPixel-матрица по ШИМ/oc_neopixel_show, 7-сегментный счётчик на GPIO,
# серво от джойстика (АЦП), DHT22 и ИК-пульт пишут на LCD по I2C, пищалка отвечает на кнопку пульта
FIRMWARE = r'''#include <stdio.h>
#include <math.h>
#include "oc_hw.h"

static const int SEG[7] = {13, 12, 14, 27, 26, 25, 33};  // a b c d e f g
static const uint8_t DIGITS[10] = {0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F};

void app_main(void) {
    for (int s = 0; s < 7; s++) oc_output(SEG[s]);
    oc_lcd_clear();
    oc_lcd_print(0, 1, "IR: press a key");
    uint32_t px[64];
    for (int i = 0; ; i++) {
        float t = i * 0.15f;
        oc_pwm(16, 5000, (1 + sinf(t)) / 2);  // RGB-светодиод переливается
        oc_pwm(17, 5000, (1 + sinf(t + 2.1f)) / 2);
        oc_pwm(5, 5000, (1 + sinf(t + 4.2f)) / 2);
        for (int p = 0; p < 64; p++) {  // волна на матрице 8×8
            int x = p % 8, y = p / 8;
            int v = (int)(127 + 127 * sinf(x * 0.8f + y * 0.5f + t));
            px[p] = (v << 16) | ((255 - v) << 8) | (x * 32);
        }
        oc_neopixel_show(23, px, 64);
        int digit = (i / 5) % 10;
        for (int s = 0; s < 7; s++) oc_write(SEG[s], (DIGITS[digit] >> s) & 1);
        int angle = oc_analog_mv(34) * 180 / 3300;  // джойстик по X → угол серво
        oc_servo(18, angle);
        float temperature, humidity;
        char line[17];
        if (oc_dht_read(32, &temperature, &humidity)) {
            snprintf(line, sizeof line, "%.1fC  %.0f%%     ", temperature, humidity);
            oc_lcd_print(0, 0, line);
        }
        uint8_t cmd;
        if (oc_ir_read(&cmd)) {
            snprintf(line, sizeof line, "IR key 0x%02X     ", cmd);
            oc_lcd_print(0, 1, line);
            oc_tone(4, 1200);
            oc_delay(120);
            oc_tone(4, 0);
        }
        if (i % 10 == 0) printf("tick %d: digit %d, servo %d deg\n", i, digit, angle);
        oc_delay(100);
    }
}
'''

DIAGRAM = {"version": 1, "board": "esp32", "parts": [
    {"id": "rgb", "type": "rgb", "x": 20, "y": 130, "pins": {"R": "GPIO16", "G": "GPIO17", "B": "GPIO5"}, "props": {}},
    {"id": "servo", "type": "servo", "x": 100, "y": 110, "pins": {"SIG": "GPIO18"}, "props": {}},
    {"id": "bz", "type": "buzzer", "x": 270, "y": 130, "pins": {"SIG": "GPIO4"}, "props": {"kind": "passive"}},
    {"id": "neo", "type": "neopixel", "x": 520, "y": 30, "pins": {"DIN": "GPIO23"}, "props": {"layout": "matrix"}},
    {"id": "lcd", "type": "lcd_i2c", "x": 20, "y": 530, "pins": {"SDA": "GPIO21", "SCL": "GPIO22"}, "props": {}},
    {"id": "seg", "type": "seg7", "x": 310, "y": 520, "props": {},
     "pins": {s: f"GPIO{n}" for s, n in zip("abcdefg", [13, 12, 14, 27, 26, 25, 33])}},
    {"id": "joy", "type": "joystick", "x": 420, "y": 520, "pins": {"VRX": "GPIO34", "VRY": "GPIO35", "SW": "GPIO19"}, "props": {}},
    {"id": "dht", "type": "dht22", "x": 560, "y": 500, "pins": {"DATA": "GPIO32"}, "props": {}, "state": {"t": 23, "h": 41}},
    {"id": "ir", "type": "ir", "x": 680, "y": 280, "pins": {"OUT": "GPIO39"}, "props": {}},
]}


def shot(page, name):
    page.screenshot(path=str(OUT / name))
    print("Captured", name, flush=True)


def open_esp32(page):
    page.goto(BASE)
    page.evaluate("localStorage.setItem('oc:theme', JSON.stringify('dark'))")
    page.reload()
    page.wait_for_selector("#tabs .tab")
    page.click("#langButton")
    page.fill("#langSearch", "esp32")
    page.keyboard.press("Enter")
    page.wait_for_selector("#esp32Hardware .cc-part", timeout=20000)
    page.wait_for_timeout(600)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.on("dialog", lambda d: d.accept())
    open_esp32(page)

    # ---------- палитра: что работает напрямую, что через oc_hw.h ----------
    page.click("#esp32Hardware .cc-add")
    page.wait_for_timeout(300)
    shot(page, "esp32-palette.png")
    page.click("#esp32Hardware .cc-add")

    # ---------- настройки детали и «Вставить пример кода» ----------
    page.click("#esp32Hardware .cc-add")
    page.click('#esp32Hardware .cc-tile[data-type="ultrasonic"]')
    page.click('#esp32Hardware .cc-inspector [data-act="example"]')
    page.wait_for_timeout(500)
    shot(page, "esp32-part-settings.png")

    # ---------- приборная панель в QEMU ----------
    page.evaluate("d => { OCProject.setFile('diagram.json', d); OCEsp32Hardware.projectLoaded(); }", json.dumps(DIAGRAM))
    page.wait_for_selector("#esp32Hardware .cc-part[data-id=ir]")
    if page.locator("#esp32Hardware .cc-inspector:not([hidden])").count():
        page.click("#esp32Hardware .cc-inspector [data-act=close]")
    set_code(page, FIRMWARE)
    page.click("#runBtn")
    assert wait_until(page, lambda: "tick " in term_text(page) or not page.locator('#runBtn.stop').count(), 600), term_text(page)[-2000:]
    assert "tick " in term_text(page), term_text(page)[-4000:]
    page.locator("#esp32Hardware .cc-part[data-id=ir] [data-ctl=ir][data-cmd='21']").click()  # «+»
    assert wait_until(page, lambda: "0x15" in (page.text_content(
        "#esp32Hardware .cc-part[data-id=lcd] [data-r=l1]") or ""), 15)
    page.evaluate("document.querySelector('#esp32Hardware .cc-view').scrollTo(0, 0)")
    page.wait_for_timeout(1500)
    shot(page, "esp32-dashboard.png")
    page.click("#espToggle")  # схема свёрнута — вся консоль видна
    page.wait_for_timeout(300)
    shot(page, "esp32-collapsed.png")
    page.click("#espToggle")
    page.click("#runBtn")
    page.wait_for_function("!document.getElementById('runBtn').classList.contains('stop')", timeout=30000)

    # ---------- телефон ----------
    mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    open_esp32(mobile)
    mobile.locator("#esp32Hardware").scroll_into_view_if_needed()
    mobile.screenshot(path=str(OUT / "esp32-mobile.png"), full_page=True)
    print("Captured esp32-mobile.png")
    browser.close()
