"""Capture actual Scratch/Blockly editors and running Arduino firmware for README.

python e2e/screenshots_hardware.py [http://127.0.0.1:8001]
ESP32 screenshots: python e2e/test_esp32.py [http://127.0.0.1:8001]
"""
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright
from screenshot_resistors import arduino_resistors

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8001'
OUT = Path(__file__).resolve().parents[1] / 'docs/screenshots'
OUT.mkdir(parents=True, exist_ok=True)


def screenshot(page, name):
    page.screenshot(path=str(OUT / name), full_page=True)
    print('Captured', name, flush=True)


with sync_playwright() as p:
    browser = p.chromium.launch(args=['--use-gl=swiftshader'])
    page = browser.new_page(viewport={'width': 1600, 'height': 1000})
    page.on('dialog', lambda dialog: dialog.accept())
    page.goto(BASE + '/scratch/')
    page.wait_for_function('window.ocScratch && ocScratch.vm', timeout=90000)
    page.wait_for_function('!document.querySelector("#saveBtn").disabled', timeout=60000)
    page.evaluate("""() => {
      const vm = ocScratch.vm;
      const target = vm.runtime.targets.find(t => !t.isStage);
      const block = (id,opcode,next,parent,inputs={},fields={},topLevel=false) =>
        target.blocks.createBlock({id,opcode,next,parent,inputs,fields,shadow:['text','math_number'].includes(opcode),topLevel,x:65,y:60});
      block('demo_flag','event_whenflagclicked','demo_say',null,{}, {}, true);
      block('demo_say','looks_say','demo_move','demo_flag',
        {MESSAGE:{name:'MESSAGE',block:'demo_message',shadow:'demo_message'}});
      block('demo_message','text',null,'demo_say',{},
        {TEXT:{name:'TEXT',value:'Привет! Я программирую в Scratch.'}});
      block('demo_move','motion_movesteps','demo_turn','demo_say',
        {STEPS:{name:'STEPS',block:'demo_steps',shadow:'demo_steps'}});
      block('demo_steps','math_number',null,'demo_move',{}, {NUM:{name:'NUM',value:40}});
      block('demo_turn','motion_turnright',null,'demo_move',
        {DEGREES:{name:'DEGREES',block:'demo_angle',shadow:'demo_angle'}});
      block('demo_angle','math_number',null,'demo_turn',{}, {NUM:{name:'NUM',value:15}});
      vm.emitWorkspaceUpdate(); vm.greenFlag();
    }""")
    frame = page.frame_locator('#scratchFrame')
    frame.locator('.blocklyDraggable').first.wait_for(timeout=30000)
    page.wait_for_timeout(1200)  # Wait for the stage and Blockly to finish drawing.
    screenshot(page, 'scratch-program.png')
    frame.get_by_text('Костюмы', exact=True).first.click()
    page.wait_for_timeout(1000)
    screenshot(page, 'scratch-costumes.png')

    page.goto(BASE)
    page.wait_for_selector('#tabs .tab', timeout=60000)
    page.click('#langButton')
    page.click('li[data-slug="blocks"]')
    page.wait_for_function('window.OCBlocks && OCBlocks.workspace', timeout=60000)
    page.click('#runBtn')
    page.wait_for_function("document.querySelector('#terminal').textContent.includes('Как тебя зовут?')", timeout=60000)
    page.click('#terminal')
    page.keyboard.insert_text('Лёха')
    page.keyboard.press('Enter')
    page.wait_for_function("!document.querySelector('#runBtn').classList.contains('stop')", timeout=60000)
    assert 'Привет, Лёха!' in page.locator('#terminal').inner_text()
    screenshot(page, 'blocks-python.png')

    page.goto(BASE + '/arduino/')
    page.wait_for_selector('.cc-part')
    lit = "(id) => Number(document.querySelector(`.cc-part[data-id='${id}'] [data-r=lit]`)?.getAttribute('opacity')) > 0.9"
    shots = [
        ('blink', 'arduino-led.png', f"({lit})('led1')"),
        ('servo', 'arduino-servo.png', "document.querySelector('.cc-part[data-id=servo1] [data-r=deg]').textContent === '90°'"),
        ('analog', 'arduino-potentiometer.png', "document.querySelector('#serial').textContent.includes('768')"),
        ('lcd', 'arduino-lcd.png', "document.querySelector('.cc-part[data-id=lcd1] [data-r=l0]').textContent.includes('Hello')"),
        ('neopixel', 'arduino-neopixel.png', "document.querySelector('.cc-part[data-id=ring] [data-r=px0]').getAttribute('fill') !== '#2a2a2a'"),
        ('remote', 'arduino-remote.png', f"({lit})('l1')"),
        ('weather', 'arduino-weather.png', "(document.querySelector('.cc-part[data-id=oled] [data-r=img]').getAttribute('href') || '').startsWith('data:')"),
    ]
    for example, name, ready in shots:
        page.select_option('#example', example)
        arduino_resistors(page)
        page.click('#run')
        page.wait_for_function("document.querySelector('#status').textContent === 'Прошивка работает'", timeout=120000)
        if example == 'analog':
            page.locator('.cc-part[data-id=pot1] input[type=range]').fill('768')
        if example == 'remote':
            page.wait_for_timeout(800)
            page.click('.cc-part[data-id=ir1] [data-ctl=ir][data-cmd="12"]')
        page.wait_for_function(ready, timeout=20000)
        page.evaluate("document.querySelector('.cc-view').scrollTo(0, 0)")  # клик по пульту прокручивает схему
        page.wait_for_timeout(300)
        screenshot(page, name)
        page.click('#stop')
    page.click('.cc-add')
    screenshot(page, 'arduino-parts.png')
    page.click('.cc-add')
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    screenshot(page, 'arduino-mobile.png')
    browser.close()
