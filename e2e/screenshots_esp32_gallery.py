"""Capture actual ESP32 circuit configurations and their generated source examples."""
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright
from screenshot_resistors import esp32_resistors

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000'
out = Path(__file__).resolve().parents[1] / 'docs/screenshots'


def part(kind, pins, x=200, y=100, props=None):
    return {'id': kind, 'type': kind, 'x': x, 'y': y, 'pins': pins, 'props': props or {}}


scenes = [
    ('ultrasonic', [part('ultrasonic', {'TRIG': 'GPIO5', 'ECHO': 'GPIO18'}),
                    part('led', {'A': 'GPIO2'}, 420, 100, {'color': 'green'})]),
    ('rgb', [part('rgb', {'R': 'GPIO16', 'G': 'GPIO17', 'B': 'GPIO5'}, 160, 10)]),
    ('lcd_i2c', [part('lcd_i2c', {'SDA': 'GPIO21', 'SCL': 'GPIO22'}, 140, 60)]),
    ('servo', [part('servo', {'SIG': 'GPIO18'}, 150, 90),
               part('pot', {'SIG': 'GPIO34'}, 420, 70)]),
    ('dht22', [part('dht22', {'DATA': 'GPIO4'}, 180, 80),
               part('lcd_i2c', {'SDA': 'GPIO21', 'SCL': 'GPIO22'}, 400, 60)]),
    ('neopixel', [part('neopixel', {'DIN': 'GPIO23'}, 200, 40, {'layout': 'matrix'})]),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1000})
    page.on('dialog', lambda d: d.accept())
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(base)
    page.wait_for_selector('#tabs .tab')
    page.evaluate("localStorage.setItem('oc:theme', JSON.stringify('dark'))")
    page.reload()
    page.wait_for_selector('#tabs .tab')
    page.click('#langButton')
    page.fill('#langSearch', 'esp32')
    page.keyboard.press('Enter')
    page.wait_for_selector('#esp32Hardware .cc-part')
    for name, parts in scenes:
        if not any(p['type'] in ('led', 'rgb') for p in parts):
            parts.append(part('led', {'A': 'GPIO2'}, 40, 60, {'color': 'blue'}))
        diagram = {'version': 1, 'board': 'esp32', 'parts': parts}
        page.evaluate("d => { OCProject.setFile('diagram.json', d); OCEsp32Hardware.projectLoaded(); }", json.dumps(diagram))
        esp32_resistors(page)
        page.click(f'#esp32Hardware .cc-part[data-id="{name}"]')
        page.click('#esp32Hardware .cc-inspector [data-act=example]')
        page.click('#esp32Hardware .cc-inspector [data-act=close]')
        page.evaluate("document.querySelector('#esp32Hardware .cc-view').scrollTo(0, 0)")
        page.wait_for_timeout(400)
        assert page.locator('#esp32Hardware .cc-part[data-type=resistor]').count()
        page.screenshot(path=str(out / f'esp32-example-{name}.png'))
        print('Captured', name, flush=True)
    assert not errors, errors
    browser.close()
