"""Hardware drawings remain usable on narrow screens."""
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8001'
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 390, 'height': 844})
    page.goto(base + '/arduino/')
    page.wait_for_function("document.querySelector('#code').value.includes('void setup')")
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert page.locator('svg[role="img"]').count() == 3
    page.locator('#pot').fill('1023')
    page.locator('#pot').dispatch_event('input')
    assert page.locator('#potKnob').get_attribute('transform') == 'rotate(135 70 49)'
    page.screenshot(path=str(Path(__file__).resolve().parents[1] / 'docs/screenshots/arduino-mobile.png'), full_page=True)
    browser.close()
    print('Arduino drawings: mobile layout and potentiometer interaction OK')
