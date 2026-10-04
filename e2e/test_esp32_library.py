"""Every ESP32 library entry loads its source and editable circuit together."""
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000'
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1000})
    page.on('dialog', lambda d: d.accept())
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(base)
    page.wait_for_selector('#tabs .tab')
    page.click('#langButton')
    page.fill('#langSearch', 'esp32')
    page.keyboard.press('Enter')
    page.wait_for_selector('#esp32Hardware .cc-part')
    items = page.request.get(base + '/api/library/?language=esp32').json()['items']
    assert len(items) == 15
    for item in items:
        expected = page.request.get(base + f"/api/library/esp32/{item['id']}/").json()
        page.click('#libraryBtn')
        page.locator(f'.library-item[data-id="{item["id"]}"]').click()
        page.wait_for_function('!document.querySelector("#libraryDialog").open')
        page.wait_for_function('code => monaco.editor.getEditors()[0].getValue() === code', arg=expected['code'])
        diagram = json.loads(expected['files'][0]['content'])
        page.wait_for_function('n => document.querySelectorAll("#esp32Hardware .cc-part").length === n',
                               arg=len(diagram['parts']))
        actual = page.evaluate("JSON.parse(OCProject.getFile('diagram.json'))")
        assert actual == diagram
        print('PASS', item['id'], flush=True)
    page.click('#libraryBtn')
    page.fill('#librarySearch', 'как на скриншоте')
    page.locator('.library-item[data-id=demo_stand]').click()
    page.wait_for_function('!document.querySelector("#libraryDialog").open')
    page.wait_for_selector('.cc-part[data-type=neopixel]')
    page.screenshot(path=str(Path(__file__).resolve().parents[1] / 'docs/screenshots/esp32-demo-stand.png'))
    assert not errors, errors
    browser.close()
print('ESP32 library: 15 source/circuit pairs, search, demo screenshot OK')
