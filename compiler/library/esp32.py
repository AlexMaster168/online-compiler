"""ESP32 teaching projects: source and a matching editable circuit."""
import json
from pathlib import Path

from ..engine.languages import get_language

CATEGORIES = ('Основы GPIO', 'ШИМ и моторы', 'Датчики', 'Дисплеи и подсветка', 'Готовые проекты', 'Сеть')


def part(kind, pins, x, y, props=None, state=None):
    return {'id': kind, 'type': kind, 'pins': pins, 'x': x, 'y': y,
            'props': props or {}, 'state': state or {}}


def led(pin=2, x=100, y=60):
    return part('led', {'A': f'GPIO{pin}'}, x, y, {'color': 'green'})


BUTTON = part('button', {'OUT': 'GPIO4'}, 210, 70)
SERVO = part('servo', {'SIG': 'GPIO18'}, 300, 50)
POT = part('pot', {'SIG': 'GPIO34'}, 350, 530, state={'value': 512})
LCD = part('lcd_i2c', {'SDA': 'GPIO21', 'SCL': 'GPIO22'}, 40, 530)
IR = part('ir', {'OUT': 'GPIO15'}, 490, 500)
BUZZER = part('buzzer', {'SIG': 'GPIO19'}, 420, 70, {'kind': 'passive'})
NEO = part('neopixel', {'DIN': 'GPIO5'}, 520, 100, {'layout': 'strip'})
DISTANCE = part('ultrasonic', {'TRIG': 'GPIO5', 'ECHO': 'GPIO18'}, 200, 50, state={'cm': 50})
DHT = part('dht22', {'DATA': 'GPIO4'}, 350, 60, state={'t': 24, 'h': 45})


def diagram(parts):
    parts = json.loads(json.dumps(parts))
    for device in list(parts):
        roles = ['A'] if device['type'] == 'led' else ['R', 'G', 'B'] if device['type'] == 'rgb' else []
        for i, role in enumerate(roles):
            parts.append({'id': f"r-{device['id']}-{role}", 'type': 'resistor', 'pins': {},
                          'x': max(0, device['x'] - 25), 'y': device['y'] + 105 + i * 65,
                          'props': {'ohms': '220'}, 'series': {'part': device['id'], 'pin': role}})
    return {'version': 1, 'board': 'esp32', 'parts': parts}


def source(setup, loop, delay=100):
    return ('#include <stdio.h>\n#include <math.h>\n#include "oc_hw.h"\n\n'
            'void app_main(void) {\n' + setup + '\n    while (1) {\n' + loop
            + f'\n        oc_delay({delay});\n    }}\n}}\n')


PROJECTS = []


def project(key, title, category, description, parts, setup, loop, delay=100):
    PROJECTS.append({'id': key, 'title': title, 'category': category, 'description': description,
                     'code': source(setup, loop, delay), 'diagram': diagram(parts)})


project('blink', 'Мигающий светодиод', 'Основы GPIO', 'GPIO2, переключение уровня и вывод в Serial.',
        [led()], '    oc_output(2);\n    int on = 0;',
        '        on = !on;\n        oc_write(2, on);\n        printf("LED %s\\n", on ? "ON" : "OFF");', 500)
project('button_led', 'Кнопка и светодиод', 'Основы GPIO', 'Вход с подтяжкой: нажатию соответствует уровень 0.',
        [led(), BUTTON], '    oc_output(2);\n    oc_input(4, true);',
        '        int pressed = oc_read(4) == 0;\n        oc_write(2, pressed);\n'
        '        printf("Button: %d\\n", pressed);', 200)
project('pot_pwm', 'Потенциометр и яркость', 'ШИМ и моторы', 'АЦП GPIO34 управляет скважностью LEDC на GPIO2.',
        [led(), POT], '',
        '        int mv = oc_analog_mv(34);\n        oc_pwm(2, 5000, mv / 3300.0f);\n'
        '        printf("ADC: %d mV\\n", mv);', 200)
project('servo_pot', 'Потенциометр крутит серво', 'ШИМ и моторы', 'Положение ручки преобразуется в угол 0–180°.',
        [SERVO, POT], '',
        '        int angle = oc_analog_mv(34) * 180 / 3300;\n        oc_servo(18, angle);\n'
        '        printf("Servo: %d deg\\n", angle);', 100)
project('rgb_wave', 'RGB: плавная смена цветов', 'Дисплеи и подсветка',
        'Три канала LEDC, синусоидальные волны и резистор на каждом канале.',
        [part('rgb', {'R': 'GPIO16', 'G': 'GPIO17', 'B': 'GPIO5'}, 100, 10)],
        '    float t = 0;',
        '        oc_pwm(16, 5000, (1 + sinf(t)) / 2);\n'
        '        oc_pwm(17, 5000, (1 + sinf(t + 2.1f)) / 2);\n'
        '        oc_pwm(5, 5000, (1 + sinf(t + 4.2f)) / 2);\n        t += 0.04f;', 50)
project('distance', 'HC-SR04: измерение расстояния', 'Датчики',
        'Ползунок расстояния на схеме, Serial и вывод сантиметров на LCD.',
        [DISTANCE, LCD], '    oc_lcd_clear();',
        '        float cm = oc_distance_cm(5, 18);\n        char line[17];\n'
        '        snprintf(line, sizeof line, "%6.1f cm       ", cm);\n'
        '        oc_lcd_print(0, 0, line);\n        printf("Distance: %.1f cm\\n", cm);', 300)
project('weather', 'DHT22: метеостанция', 'Датчики', 'Температура и влажность с ползунков датчика на LCD.',
        [DHT, LCD], '    oc_lcd_clear();',
        '        float t, h;\n        if (oc_dht_read(4, &t, &h)) {\n'
        '            char line[17];\n            snprintf(line, sizeof line, "Temp: %5.1f C   ", t);\n'
        '            oc_lcd_print(0, 0, line);\n'
        '            snprintf(line, sizeof line, "Hum: %5.1f %%    ", h);\n'
        '            oc_lcd_print(0, 1, line);\n            printf("%.1f C, %.1f %%\\n", t, h);\n        }', 500)
project('night_light', 'Автоматический ночник', 'Датчики',
        'Фоторезистор на GPIO34: при низком уровне АЦП включается светодиод.',
        [led(), part('ldr', {'SIG': 'GPIO34'}, 380, 80)], '    oc_output(2);',
        '        int mv = oc_analog_mv(34);\n        oc_write(2, mv < 1650);\n'
        '        printf("Light ADC: %d mV\\n", mv);', 200)
project('lcd_counter', 'LCD: счётчик секунд', 'Дисплеи и подсветка', 'Две строки LCD, обновление без очистки в цикле.',
        [LCD], '    oc_lcd_clear();\n    oc_lcd_print(0, 0, "ESP32 counter");\n    unsigned seconds = 0;',
        '        char line[17];\n        snprintf(line, sizeof line, "%u sec          ", seconds++);\n'
        '        oc_lcd_print(0, 1, line);', 1000)
project('neopixel_chase', 'NeoPixel: бегущий огонь', 'Дисплеи и подсветка',
        'Восемь пикселей WS2812 на GPIO5, цвет 0xRRGGBB.', [NEO], '    unsigned pos = 0;',
        '        uint32_t px[8] = {0};\n        px[pos++ % 8] = 0x00ff40;\n'
        '        oc_neopixel_show(5, px, 8);', 150)
project('ir_led', 'ИК-пульт: светодиод и звук', 'Готовые проекты',
        'Любая кнопка пульта переключает LED; код команды виден в Serial.',
        [led(), IR, BUZZER], '    oc_output(2);\n    int on = 0;',
        '        uint8_t cmd;\n        if (oc_ir_read(&cmd)) {\n'
        '            on = !on;\n            oc_write(2, on);\n'
        '            printf("IR 0x%02X\\n", cmd);\n            oc_tone(19, 880);\n'
        '            oc_delay(80);\n            oc_tone(19, 0);\n        }', 30)
project('parking', 'Парктроник: LCD и сигнал тревоги', 'Готовые проекты',
        'HC-SR04, светодиод и пищалка: сигнал при расстоянии менее 30 см.',
        [led(), DISTANCE, LCD, BUZZER], '    oc_output(2);\n    oc_lcd_clear();',
        '        float cm = oc_distance_cm(5, 18);\n        int alarm = cm >= 0 && cm < 30;\n'
        '        oc_write(2, alarm);\n        oc_tone(19, alarm ? 1200 : 0);\n'
        '        char line[17];\n        snprintf(line, sizeof line, "%6.1f cm       ", cm);\n'
        '        oc_lcd_print(0, 0, line);\n'
        '        oc_lcd_print(0, 1, alarm ? "STOP!           " : "Safe            ");', 200)
project('demo_stand', 'Демо-стенд: всё вместе (как на скриншоте)', 'Готовые проекты',
        'Кнопка, LED, серво, LCD, NeoPixel, потенциометр, пищалка и ИК-пульт.',
        [led(), BUTTON, SERVO, BUZZER, NEO, LCD, POT, IR],
        '    oc_output(2);\n    oc_input(4, true);\n'
        '    uint32_t px[8] = {0xff0000, 0x00ff00, 0x0000ff, 0, 0, 0, 0, 0xffffff};\n'
        '    oc_neopixel_show(5, px, 8);\n    oc_lcd_clear();\n'
        '    oc_lcd_print(0, 0, "ESP32 LCD ok");\n    oc_tone(19, 880);\n    unsigned tick = 0;',
        '        int pressed = oc_read(4) == 0;\n        oc_write(2, pressed);\n'
        '        oc_servo(18, (tick % 2) * 180);\n        uint8_t ir;\n'
        '        if (oc_ir_read(&ir)) printf("IR 0x%02X\\n", ir);\n'
        '        printf("TICK %u BTN=%d POT=%d\\n", tick++, pressed, oc_analog_mv(34));', 300)


def all_projects():
    network = [
        {'id': 'web_server', 'title': 'Сайт ESP32 в эмуляторе', 'category': 'Сеть',
         'description': 'HTTP-сервер через виртуальный Ethernet OpenETH.',
         'code': get_language('esp32').template, 'diagram': diagram([led(), SERVO])},
        {'id': 'wifi_hardware', 'title': 'Wi-Fi и сайт на настоящей ESP32', 'category': 'Сеть',
         'description': 'Только физическая плата: замените YOUR_SSID и YOUR_PASSWORD. QEMU не эмулирует Wi-Fi.',
         'code': (Path(__file__).parents[1] / 'engine/sandbox/esp32/main/wifi_hardware.c.example').read_text('utf-8'),
         'diagram': diagram([])},
    ]
    return PROJECTS + network


def catalog():
    return [{k: p[k] for k in ('id', 'title', 'category', 'description')} for p in all_projects()]


def get_project(key):
    item = next((p for p in all_projects() if p['id'] == key), None)
    if item is None:
        return None
    return {**{k: item[k] for k in ('id', 'title', 'category', 'description', 'code')}, 'language': 'esp32',
            'files': [{'name': 'diagram.json', 'content': json.dumps(item['diagram'], ensure_ascii=False, indent=2)}]}
