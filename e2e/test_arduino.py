"""Compile real firmware and verify its execution in the browser."""
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8001'
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 950})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('dialog', lambda dialog: dialog.accept())
    page.goto(base + '/arduino/')
    page.wait_for_function("document.querySelector('#code').value.includes('void setup')")
    page.click('#run')
    page.wait_for_function("document.querySelector('#serial').textContent.includes('LED ON')", timeout=120000)
    page.wait_for_function("document.querySelector('#serial').textContent.includes('LED OFF')", timeout=15000)
    page.click('#stop')
    page.select_option('#example', 'button')
    page.click('#run')
    page.wait_for_function("document.querySelector('#status').textContent === 'Прошивка работает'", timeout=120000)
    page.locator('#button').dispatch_event('pointerdown', {'pointerId': 1})
    page.wait_for_selector('#led.on')
    page.locator('#button').dispatch_event('pointerup', {'pointerId': 1})
    page.wait_for_function("!document.querySelector('#led').classList.contains('on')")
    page.click('#stop')
    page.select_option('#example', 'analog')
    page.click('#run')
    page.wait_for_function("document.querySelector('#serial').textContent.includes('512')", timeout=120000)
    page.locator('#pot').fill('1023')
    page.locator('#pot').dispatch_event('input')
    page.wait_for_function("document.querySelector('#serial').textContent.includes('1023')")
    assert page.locator('#potKnob').get_attribute('transform') == 'rotate(135 70 49)'
    page.click('#stop')
    page.select_option('#example', 'servo')
    page.click('#run')
    page.wait_for_function("document.querySelector('#servo').textContent === '90°'", timeout=120000)
    assert page.locator('#servoHorn').get_attribute('transform') == 'rotate(0 130 48)'
    page.click('#stop')
    page.select_option('#example', 'lcd')
    page.click('#run')
    page.wait_for_function("document.querySelector('#lcd').textContent.includes('Hello Arduino!')", timeout=120000)
    output = Path(__file__).resolve().parents[1] / 'docs/screenshots/arduino.png'
    output.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(output), full_page=True)
    page.click('#stop')
    assert not errors, errors
    browser.close()
    print('Arduino: firmware compilation, LED, button, ADC, servo, LCD, screenshot OK')
