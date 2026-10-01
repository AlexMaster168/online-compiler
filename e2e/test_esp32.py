"""ESP32 firmware serves a real HTML page through the QEMU session bridge."""
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8001'
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 950})
    page.goto(base)
    page.wait_for_selector('#tabs .tab', timeout=60000)
    page.click('#langButton')
    page.click('li[data-slug="esp32"]')
    page.click('#modeConsole')
    page.click('#runBtn')
    page.wait_for_selector('#esp32Preview', timeout=30000)
    page.wait_for_function("document.querySelector('#terminal').textContent.includes('ESP32 HTTP ready') || "
                           "!document.querySelector('#runBtn').classList.contains('stop')", timeout=700000)
    assert 'ESP32 HTTP ready' in page.locator('#terminal').inner_text(), page.locator('#terminal').inner_text()[-4000:]
    url = page.locator('#esp32Preview').get_attribute('href')
    site = browser.new_page(viewport={'width': 1000, 'height': 700})
    site.goto(base + url)
    site.wait_for_selector('h1')
    assert site.locator('h1').inner_text() == 'Привет с ESP32!'
    site.click('button')
    assert site.locator('button').inner_text() == 'Работает!'
    out = Path(__file__).resolve().parents[1] / 'docs/screenshots'
    page.screenshot(path=str(out / 'esp32.png'))
    site.screenshot(path=str(out / 'esp32-website.png'))
    page.click('#runBtn')
    page.wait_for_function("document.querySelector('#runLabel').textContent === 'Запустить'")
    site.reload()
    assert 'Сессия ESP32 завершена' in site.locator('body').inner_text()
    browser.close()
    print('ESP32: compile, boot, IP, HTTP site, JavaScript, stop OK')
