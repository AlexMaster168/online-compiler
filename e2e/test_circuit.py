"""Схема Arduino: каждый пример со страницы собирается, прошивка двигает детали, детали подают сигналы в прошивку.

    python e2e/test_circuit.py [http://127.0.0.1:8000]

Нужен образ oc-lang-arduino:1 (manage.py build_sandbox lang-arduino).
"""
import os
import re
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BASE, OUT, check, errors, results, wait_until  # noqa: E402


def part(page, part_id):
    return page.locator(f'.cc-part[data-id="{part_id}"]')


def attr(page, part_id, role, name):
    return part(page, part_id).locator(f'[data-r="{role}"]').get_attribute(name)


def serial(page):
    return page.inner_text("#serial")


def run_example(page, name):
    page.select_option("#example", name)
    page.click("#run")
    page.wait_for_function("() => /работает|Ошибка|недоступен|заняты/.test(document.getElementById('status').textContent)",
                           timeout=120000)
    status = page.inner_text("#status")
    check(f"{name}: firmware runs", "работает" in status, status + page.inner_text("#log")[-600:])


def lit(page, part_id):
    return float(attr(page, part_id, "lit", "opacity") or 0)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 950})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("dialog", lambda d: d.accept())
    page.goto(BASE + "/arduino/")
    page.wait_for_selector(".cc-part")
    page.evaluate("localStorage.clear()")
    page.reload()
    page.wait_for_selector(".cc-part")

    # ---------- мигалка: светодиод на D13 и встроенный L ----------
    run_example(page, "blink")
    check("blink: LED turns on", wait_until(page, lambda: lit(page, "led1") > 0.9, 10))
    check("blink: LED turns off", wait_until(page, lambda: lit(page, "led1") < 0.1, 10))
    check("blink: serial", "LED ON" in serial(page), serial(page))

    # ---------- кнопка: удержание мышью подаёт LOW на D2 ----------
    run_example(page, "button")
    page.wait_for_timeout(500)
    check("button: LED off while released", lit(page, "led1") < 0.1)
    cap = part(page, "btn1").locator('[data-ctl="press"]')
    box = cap.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    check("button: LED on while pressed", wait_until(page, lambda: lit(page, "led1") > 0.9, 5))
    page.mouse.up()
    check("button: LED off after release", wait_until(page, lambda: lit(page, "led1") < 0.1, 5))

    # ---------- потенциометр → АЦП → ШИМ ----------
    run_example(page, "analog")
    part(page, "pot1").locator('input[type="range"]').fill("1023")
    check("pot: max value in serial", wait_until(page, lambda: "1023" in serial(page), 10), serial(page)[-200:])
    check("pot: LED full brightness", wait_until(page, lambda: lit(page, "led1") > 0.95, 5))
    part(page, "pot1").locator('input[type="range"]').fill("256")
    check("pot: PWM ~25%", wait_until(page, lambda: 0.15 < lit(page, "led1") < 0.35, 5), lit(page, "led1"))

    # ---------- серво ----------
    run_example(page, "servo")
    angles = set()

    def servo_sweeps():
        angles.add(part(page, "servo1").locator('[data-r="deg"]').text_content())
        return {"0°", "90°", "180°"} <= angles
    check("servo: horn visits 0/90/180", wait_until(page, servo_sweeps, 12), angles)

    # ---------- LCD 16×2 ----------
    run_example(page, "lcd")
    check("lcd: text on display", wait_until(
        page, lambda: "Hello Arduino!" in part(page, "lcd1").locator('[data-r="l0"]').text_content().replace(" ", " "), 10))

    # ---------- светофор с пищалкой: tone() → частота ----------
    run_example(page, "traffic")
    check("traffic: red light", wait_until(page, lambda: lit(page, "red") > 0.9, 10))
    # tone(1200) на Timer2 даёт 1201.9 Гц — как и на настоящей плате
    check("traffic: buzzer plays ~1200 Hz", wait_until(
        page, lambda: re.match(r"1(19|20)\d Гц", part(page, "bz").locator('[data-r="hz"]').text_content() or ""), 15),
        part(page, "bz").locator('[data-r="hz"]').text_content())

    # ---------- NeoPixel ----------
    run_example(page, "neopixel")
    check("neopixel: ring lights up", wait_until(
        page, lambda: attr(page, "ring", "px0", "fill") not in (None, "#2a2a2a"), 10), attr(page, "ring", "px0", "fill"))
    first = attr(page, "ring", "px0", "fill")
    check("neopixel: colors change", wait_until(page, lambda: attr(page, "ring", "px0", "fill") != first, 5))
    page.screenshot(path=f"{OUT}/circuit_neopixel.png")

    # ---------- ИК-пульт: NEC-сигнал → IRremote ----------
    run_example(page, "remote")
    page.wait_for_timeout(800)
    part(page, "ir1").locator('[data-ctl="ir"][data-cmd="12"]').click()  # «1» = 0x0C
    check("ir: sketch decodes button 1", wait_until(page, lambda: "0xC" in serial(page), 10), serial(page))
    check("ir: LED toggled", wait_until(page, lambda: lit(page, "l1") > 0.9, 5))

    # ---------- дальномер + пищалка ----------
    run_example(page, "parking")
    check("ultrasonic: 40 cm measured", wait_until(page, lambda: re.search(r"\b(39|40|41) см", serial(page)), 10), serial(page)[-200:])
    part(page, "us").locator('input[type="range"]').fill("150")
    check("ultrasonic: slider changes distance", wait_until(page, lambda: re.search(r"\b(149|150|151) см", serial(page)), 10))

    # ---------- DHT22 + OLED по I2C ----------
    run_example(page, "weather")
    check("oled: picture drawn", wait_until(page, lambda: (attr(page, "oled", "img", "href") or "").startswith("data:image"), 15))
    page.screenshot(path=f"{OUT}/circuit_weather.png")
    page.click("#stop")

    # ---------- деталь из палитры + пример кода с её ножками ----------
    page.select_option("#example", "blink")
    page.click(".cc-add")
    page.click('.cc-tile[data-type="seg7"]')
    check("palette: part added and selected", page.locator(".cc-inspector:not([hidden])").count() == 1)
    seg = page.locator('.cc-part[data-type="seg7"]')
    seg_id = seg.get_attribute("data-id")
    pins = page.evaluate(f"Object.values(ocCircuit.toJSON().parts.find(p => p.id === '{seg_id}').pins)")
    taken = page.evaluate(f"ocCircuit.toJSON().parts.filter(p => p.id !== '{seg_id}').flatMap(p => Object.values(p.pins))")
    check("new part gets distinct free pins", len(set(pins)) == len(pins) and not set(pins) & set(taken), (pins, taken))
    page.select_option('.cc-inspector select[data-pin="a"]', "D7")
    page.click('.cc-inspector [data-act="example"]')
    code = page.input_value("#code")
    check("example uses chosen pin", "const int pins[7] = {7," in code, code[:200])
    page.click("#run")
    page.wait_for_function("() => /работает|Ошибка/.test(document.getElementById('status').textContent)", timeout=120000)
    check("seg7: digit drawn", wait_until(page, lambda: attr(page, seg_id, "sa", "fill") == "#ff3b30"
                                          or attr(page, seg_id, "sb", "fill") == "#ff3b30", 10))
    page.click("#stop")

    # ---------- сохранение схемы в проект ----------
    page.fill("#title", "Схема из e2e")
    page.click("#save")
    page.wait_for_function("() => /сохранён/.test(document.getElementById('status').textContent)", timeout=15000)
    url = page.url
    count = page.locator(".cc-part").count()
    page.evaluate("localStorage.clear()")
    page.goto(url)
    page.wait_for_selector(".cc-part")
    check("saved project restores circuit", page.locator(".cc-part").count() == count
          and page.locator('.cc-part[data-type="seg7"]').count() == 1, (count, page.locator(".cc-part").count()))

    # ---------- телефон: схема влезает, палитра открывается ----------
    mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    mobile.goto(url)
    mobile.wait_for_selector(".cc-part")
    mobile.click(".cc-add")
    scroll = mobile.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    check("mobile: no horizontal scroll", not scroll)
    mobile.screenshot(path=f"{OUT}/circuit_mobile.png", full_page=True)

    check("no page errors", not errors, errors[:5])
    browser.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
