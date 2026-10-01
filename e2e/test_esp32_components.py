"""Browser checks for explicit Serial telemetry and language switching."""
import sys
from playwright.sync_api import sync_playwright

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8001'
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(base)
    page.wait_for_selector('#tabs .tab')
    page.click('#langButton')
    page.click('li[data-slug="esp32"]')
    assert page.locator('#esp32Hardware').is_visible()
    page.evaluate(r"""() => {
        OCEsp32Hardware.feed('@OC SER');
        OCEsp32Hardware.feed('VO 90\n@OC LED 1\n@OC LCD <b>safe</b>\n');
    }""")
    assert page.locator('#espAngle').inner_text().startswith('90')
    assert page.locator('#espLed').get_attribute('class') == 'active'
    assert page.locator('#espDisplay').inner_text() == '<b>safe</b>'
    assert page.locator('#espDisplay b').count() == 0
    page.evaluate('OCEsp32Hardware.reset()')
    assert page.locator('#espLed').get_attribute('class') == ''
    page.click('#langButton')
    page.click('li[data-slug="python"]')
    assert not page.locator('#esp32Hardware').is_visible()
    browser.close()
    print('ESP32 components: split Serial, LED, servo, safe display, reset, visibility OK')
