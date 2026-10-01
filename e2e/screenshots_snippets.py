"""Capture algorithm examples and real execution results in different languages."""
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8001'
OUT = Path(__file__).resolve().parents[1] / 'docs/screenshots'
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width':1600,'height':1000})
    page.on('dialog',lambda dialog:dialog.accept())
    page.goto(BASE)
    page.wait_for_selector('#tabs .tab',timeout=60000)
    for slug in ['python','cpp','java','go','rust','sql']:
        page.click('#langButton')
        page.click(f'li[data-slug="{slug}"]')
        page.wait_for_timeout(900)
        page.click('#libraryBtn')
        page.wait_for_selector('.library-item[data-id="binary_search"]')
        if slug == 'python':
            page.screenshot(path=str(OUT/'snippets-library.png'))
        page.click('.library-item[data-id="binary_search"]')
        page.click('#modeBatch')
        page.click('#runBtn')
        page.wait_for_function("!document.querySelector('#runBtn').disabled && "
                               "!document.querySelector('#statusBadge').hidden && "
                               "document.querySelector('#statusBadge').textContent !== 'Выполняется…'",timeout=120000)
        # The same reference example must produce a successful execution in each language.
        assert page.locator('#statusBadge').inner_text() == 'Успешно', page.locator('#statusBadge').inner_text()
        page.screenshot(path=str(OUT/f'snippet-{slug}.png'))
        print('Captured snippet',slug,flush=True)
    page.click('#langButton')
    page.click('li[data-slug="esp32"]')
    page.click('#libraryBtn')
    page.wait_for_selector('.library-item[data-id="wifi_hardware"]')
    page.screenshot(path=str(OUT/'esp32-network-examples.png'))
    page.click('.library-item[data-id="wifi_hardware"]')
    page.screenshot(path=str(OUT/'esp32-wifi-source.png'))
    browser.close()
