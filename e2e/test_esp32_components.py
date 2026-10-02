"""Схема ESP32 в редакторе: телеметрия «@OC» прячется из консоли и двигает детали, детали отвечают прошивке «@IN».

    python e2e/test_esp32_components.py [http://127.0.0.1:8000] [--qemu]

Без --qemu проверяется только разбор телеметрии в браузере (секунды).
С --qemu прошивка с мостом oc_hw.c собирается и запускается в QEMU (нужен образ oc-lang-esp32:1, ~3 минуты).
"""
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BASE, OUT, check, errors, results, set_code, term_text, wait_until  # noqa: E402

QEMU = "--qemu" in sys.argv

FIRMWARE = r'''#include <stdio.h>
#include "oc_hw.h"

void app_main(void) {
    oc_output(2);
    oc_input(4, true);
    uint32_t px[8] = {0xff0000, 0x00ff00, 0x0000ff, 0, 0, 0, 0, 0xffffff};
    oc_neopixel_show(5, px, 8);
    oc_lcd_clear();
    oc_lcd_print(0, 0, "ESP32 LCD ok");
    oc_tone(19, 880);
    for (int i = 0; ; i++) {
        int pressed = oc_read(4) == 0;
        oc_write(2, pressed);
        oc_servo(18, (i % 2) * 180);
        uint8_t ir;
        if (oc_ir_read(&ir)) printf("IR 0x%02X\n", ir);
        printf("TICK %d BTN=%d POT=%d\n", i, pressed, oc_analog_mv(34));
        oc_delay(300);
    }
}
'''

DIAGRAM = {"version": 1, "board": "esp32", "parts": [
    {"id": "led", "type": "led", "x": 40, "y": 120, "pins": {"A": "GPIO2"}, "props": {"color": "green"}},
    {"id": "btn", "type": "button", "x": 100, "y": 110, "pins": {"OUT": "GPIO4"}, "props": {}},
    {"id": "servo", "type": "servo", "x": 190, "y": 90, "pins": {"SIG": "GPIO18"}, "props": {}},
    {"id": "bz", "type": "buzzer", "x": 350, "y": 110, "pins": {"SIG": "GPIO19"}, "props": {"kind": "passive"}},
    {"id": "neo", "type": "neopixel", "x": 430, "y": 140, "pins": {"DIN": "GPIO5"}, "props": {"layout": "strip"}},
    {"id": "pot", "type": "pot", "x": 330, "y": 530, "pins": {"SIG": "GPIO34"}, "props": {}},
    {"id": "lcd", "type": "lcd_i2c", "x": 40, "y": 530, "pins": {"SDA": "GPIO21", "SCL": "GPIO22"}, "props": {}},
    {"id": "ir", "type": "ir", "x": 460, "y": 470, "pins": {"OUT": "GPIO15"}, "props": {}},
]}


def q(page, part, role, prop="textContent"):
    return page.evaluate(f"document.querySelector('#esp32Hardware .cc-part[data-id={part}] [data-r={role}]')"
                         f"?.{'getAttribute(' + json.dumps(prop) + ')' if prop != 'textContent' else 'textContent'}")


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1500, "height": 1000})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("dialog", lambda d: d.accept())
    page.goto(BASE)
    page.wait_for_selector("#tabs .tab")
    page.click("#langButton")
    page.fill("#langSearch", "esp32")
    page.keyboard.press("Enter")
    page.wait_for_selector("#esp32Hardware .cc-part", timeout=20000)
    check("panel visible for ESP32", page.locator("#esp32Hardware").is_visible())

    # ---------- телеметрия: строки «@OC» не попадают в консоль, кусок строки ждёт продолжения ----------
    shown = page.evaluate(r"""() => {
      OCEsp32Hardware.start(line => (window.sent ||= []).push(line));
      return [OCEsp32Hardware.feed('boot\n@OC D 2 1\n@OC P 18 735 50\nESP32: 1\n@O'),
              OCEsp32Hardware.feed('C LCD 0 0 <b>safe</b>\nend')];
    }""")
    check("service lines hidden from console", shown == ["boot\nESP32: 1\n", "end"], shown)
    check("builtin LED parts follow GPIO2", wait_until(page, lambda: q(page, "led2", "lit", "opacity") == "1", 3))
    check("servo follows LEDC pulse", wait_until(page, lambda: q(page, "servo18", "deg") == "90°", 3), q(page, "servo18", "deg"))
    page.evaluate("OCEsp32Hardware.reset()")
    check("reset turns parts off", q(page, "led2", "lit", "opacity") == "0")

    # ---------- схема хранится в проекте файлом diagram.json ----------
    page.click("#esp32Hardware .cc-add")
    page.click('#esp32Hardware .cc-tile[data-type="relay"]')
    check("diagram.json added to project", wait_until(
        page, lambda: "diagram.json" in page.eval_on_selector_all("#tabs .tab .tab-name", "els => els.map(e => e.textContent)"), 3))
    diagram = json.loads(page.evaluate("OCProject.getFile('diagram.json')"))
    check("relay saved in diagram", any(part["type"] == "relay" for part in diagram["parts"]), diagram)
    check("OLED is Arduino-only", page.locator('#esp32Hardware .cc-tile[data-type="oled"]').is_disabled())

    if QEMU:
        page.evaluate("d => { OCProject.setFile('diagram.json', d); OCEsp32Hardware.projectLoaded(); }", json.dumps(DIAGRAM))
        page.wait_for_selector("#esp32Hardware .cc-part[data-id=ir]")
        set_code(page, FIRMWARE)
        page.click("#runBtn")
        check("firmware boots", wait_until(page, lambda: "TICK" in term_text(page), 400), term_text(page)[-1500:])
        check("no telemetry in console", "@OC" not in term_text(page), term_text(page)[-800:])
        # Вход со схемы до первой посылки читается как подтяжка, а не как «нажата»
        check("released button reads 1 from the start", "TICK 0 BTN=0" in term_text(page), term_text(page)[-400:])
        check("lcd via oc_lcd_print", wait_until(page, lambda: "ESP32 LCD ok" in (q(page, "lcd", "l0") or "").replace(" ", " "), 10))
        check("neopixel via oc_neopixel_show", wait_until(page, lambda: q(page, "neo", "px0", "fill") == "rgb(255,0,0)", 10),
              q(page, "neo", "px0", "fill"))
        check("buzzer via LEDC tone", wait_until(page, lambda: "880" in (q(page, "bz", "hz") or ""), 10), q(page, "bz", "hz"))
        angles = set()

        def servo_moves():
            angles.add(q(page, "servo", "deg"))
            return {"0°", "180°"} <= angles
        check("servo via oc_servo", wait_until(page, servo_moves, 10), angles)

        page.locator("#esp32Hardware .cc-part[data-id=pot] input[type=range]").fill("1023")
        check("pot → ADC", wait_until(page, lambda: re.search(r"POT=3[23]\d\d", term_text(page)), 15), term_text(page)[-400:])
        cap = page.locator("#esp32Hardware .cc-part[data-id=btn] [data-ctl=press]").bounding_box()
        page.mouse.move(cap["x"] + cap["width"] / 2, cap["y"] + cap["height"] / 2)
        page.mouse.down()
        check("button → gpio_get_level", wait_until(page, lambda: "BTN=1" in term_text(page), 10), term_text(page)[-400:])
        check("LED follows button", wait_until(page, lambda: q(page, "led", "lit", "opacity") == "1", 5))
        page.mouse.up()
        page.click("#esp32Hardware .cc-part[data-id=ir] [data-ctl=ir][data-cmd='12']")
        check("IR remote → oc_ir_read", wait_until(page, lambda: "IR 0x0C" in term_text(page), 10), term_text(page)[-400:])
        page.screenshot(path=f"{OUT}/esp32_circuit.png")
        page.click("#runBtn")  # стоп

    page.click("#langButton")
    page.fill("#langSearch", "python")
    page.keyboard.press("Enter")
    check("panel hidden for other languages", wait_until(page, lambda: not page.locator("#esp32Hardware").is_visible(), 5))
    check("no page errors", not errors, errors[:5])
    browser.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
