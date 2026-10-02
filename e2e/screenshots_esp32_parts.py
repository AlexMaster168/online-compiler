"""Capture ESP32 palette, resistor settings, HC-SR04, and mobile layout."""
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000'
out = Path(__file__).resolve().parents[1] / 'docs/screenshots'
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1000})
    page.goto(base)
    page.wait_for_selector('#tabs .tab')
    page.click('#langButton')
    page.fill('#langSearch', 'esp32')
    page.keyboard.press('Enter')
    page.wait_for_selector('#esp32Hardware .cc-part')
    page.click('#esp32Hardware .cc-add')
    page.wait_for_timeout(400)
    assert page.locator('.cc-tile[data-type=resistor]').is_visible()
    assert page.locator('.cc-tile[data-type=ultrasonic]').is_visible()
    page.screenshot(path=str(out / 'esp32-palette.png'))
    page.click('.cc-tile[data-type=resistor]')
    page.select_option('.cc-inspector [data-prop=ohms]', '330')
    assert '330' in page.locator('.cc-selected').inner_text()
    page.screenshot(path=str(out / 'esp32-resistor.png'))
    page.click('.cc-inspector [data-act=close]')
    page.click('#esp32Hardware .cc-add')
    page.click('.cc-tile[data-type=ultrasonic]')
    page.screenshot(path=str(out / 'esp32-part-settings.png'))
    page.set_viewport_size({'width': 390, 'height': 844})
    page.locator('#esp32Hardware').scroll_into_view_if_needed()
    page.screenshot(path=str(out / 'esp32-mobile.png'), full_page=True)
    browser.close()
print('ESP32: resistor nominal, ultrasonic palette, screenshots OK')
