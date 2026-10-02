/* Каталог деталей схемы: картинка, ножки, поведение и пример кода для Arduino и ESP32.
 *
 * Ножка детали: {id, label, need, prefer?, x, y} — need: что должна уметь ножка платы
 * (out — выход МК, in — вход МК, analog — АЦП, int — прерывание, sda/scl — шина I2C, ставятся сами).
 *
 * Хуки детали получают ctx (см. editor.js): art(part) → SVG, controls(part) → HTML под картинкой,
 * bind(ctx) — один раз, start(ctx) — при запуске прошивки, frame(ctx, dt) — каждый кадр, idle(ctx) — после остановки.
 */
import {Hd44780, Ssd1306, NEC_KEYS, RF_KEYS, attachDht, attachLcdParallel, attachNeoPixel, attachUltrasonic,
  necWave, pcf8574Lcd, rcSwitchWave, servoAngle, stepperTracker} from './devices.js';

export const CATEGORIES = ['Пассивные элементы', 'Датчики', 'Выходы', 'Моторы', 'Дисплеи', 'Кнопки и ручки', 'Пульты'];

/* ---------- маленькие помощники для картинок ---------- */
const leg = (x, y1, y2, color = '#b9c3ca') =>
  `<path d="M${x} ${y1}V${y2}" stroke="${color}" stroke-width="3" stroke-linecap="round"/>`;
const legs = (pins, from, to) => pins.map(p => leg(p.x, from, to)).join('');
const text = (x, y, t, size = 9, color = '#cbd5e1', anchor = 'middle') =>
  `<text x="${x}" y="${y}" font-size="${size}" fill="${color}" text-anchor="${anchor}" font-family="system-ui,sans-serif">${t}</text>`;
const spread = (ids, width, need, extra = {}) => ids.map((id, i) => ({
  id, label: id, need, x: Math.round(width * (i + 1) / (ids.length + 1)), ...extra,
}));
const pinsAt = (pins, y) => pins.map(p => ({...p, y}));

/* Уровень выхода как яркость: ШИМ — скважность, иначе 0/1 */
const brightness = r => r.level === null ? 0 : r.freq ? r.duty : r.level;
const COLORS = {red: '#ff3b30', green: '#30d158', blue: '#3a8bff', yellow: '#ffd60a', white: '#f5f7ff', orange: '#ff9f0a'};
const COLOR_OPTIONS = [['red', 'красный'], ['green', 'зелёный'], ['blue', 'синий'], ['yellow', 'жёлтый'],
  ['white', 'белый'], ['orange', 'оранжевый']];

/* ---------- примеры кода ---------- */
const ino = (setup, loop, head = '') => `${head}${head ? '\n' : ''}void setup() {\n${setup}\n}\n\nvoid loop() {\n${loop}\n}\n`;
const idf = (setup, loop, head = '') => `#include <stdio.h>\n#include "oc_hw.h"  // мост к схеме: oc_write, oc_read, oc_pwm …\n${head}
void app_main(void) {\n${setup}\n    while (1) {\n${loop}\n    }\n}\n`;

/* ======================================================================== */
export const PARTS = {};
const part = (type, def) => { PARTS[type] = {type, esp32: 'native', props: {}, ...def}; };

part('resistor', {
  title: 'Резистор', category: 'Пассивные элементы', w: 120, h: 60,
  note: 'Резистор сохраняется как обозначение схемы. Эмулятор моделирует цифровые сигналы и не рассчитывает ток и падение напряжения.',
  pins: [],
  props: {ohms: {label: 'Сопротивление', default: '220', options: [
    ['100', '100 Ом'], ['220', '220 Ом'], ['330', '330 Ом'], ['1000', '1 кОм'],
    ['4700', '4,7 кОм'], ['10000', '10 кОм'],
  ]}},
  art: p => {
    const bands = {'100': ['#7c3f17', '#111', '#7c3f17'], '220': ['#b91c1c', '#b91c1c', '#7c3f17'],
      '330': ['#ea580c', '#ea580c', '#7c3f17'], '1000': ['#7c3f17', '#111', '#b91c1c'],
      '4700': ['#eab308', '#7e22ce', '#b91c1c'], '10000': ['#7c3f17', '#111', '#ea580c']}[p.props.ohms];
    return `<path d="M3 28H117" stroke="#b9c3ca" stroke-width="3"/>
    <rect x="25" y="17" width="70" height="22" rx="8" fill="#d9bd83" stroke="#a58a54"/>
    ${bands.map((color, i) => `<path d="M${40 + i * 13} 18V38" stroke="${color}" stroke-width="5"/>`).join('')}
    <path d="M83 18V38" stroke="#d4af37" stroke-width="4"/>
    ${text(60, 55, `${p.props.ohms} Ом`, 11)}`;
  },
  example: (_p, board) => board === 'esp32'
    ? idf('    oc_output(2);', '        oc_write(2, 1);\n        oc_delay(500);\n        oc_write(2, 0);\n        oc_delay(500);')
    : ino('  pinMode(13, OUTPUT);', '  digitalWrite(13, HIGH);\n  delay(500);\n  digitalWrite(13, LOW);\n  delay(500);'),
});

/* ---------- Светодиод ---------- */
part('led', {
  title: 'Светодиод', category: 'Выходы', w: 44, h: 96,
  pins: pinsAt([{id: 'A', label: '+', need: 'out', prefer: 'pwm', x: 26}], 94),
  props: {color: {label: 'Цвет', options: COLOR_OPTIONS, default: 'red'}},
  art: p => {
    const c = COLORS[p.props.color] || COLORS.red;
    return `<circle data-r="glow" cx="22" cy="28" r="24" fill="${c}" opacity="0" filter="url(#ocGlow)"/>
      ${leg(17, 52, 94)}${leg(26, 52, 92)}
      <path d="M8 54V24a14 14 0 0 1 28 0v30z" fill="${c}" opacity=".35" stroke="${c}" stroke-width="1.5"/>
      <rect x="5" y="52" width="34" height="5" rx="1.5" fill="${c}" opacity=".5"/>
      <path data-r="lit" d="M8 54V24a14 14 0 0 1 28 0v30z" fill="${c}" opacity="0"/>
      <path d="M13 24a9 9 0 0 1 8-8" stroke="#fff" stroke-width="2" fill="none" opacity=".5"/>`;
  },
  frame(ctx) {
    const b = brightness(ctx.read('A'));
    ctx.q('lit').setAttribute('opacity', b);
    ctx.q('glow').setAttribute('opacity', b * 0.75);
  },
  idle(ctx) { ctx.q('lit').setAttribute('opacity', 0); ctx.q('glow').setAttribute('opacity', 0); },
  example: (p, board) => board === 'esp32'
    ? idf(`    oc_output(${p('A')});`, `        oc_write(${p('A')}, 1);\n        oc_delay(500);\n        oc_write(${p('A')}, 0);\n        oc_delay(500);`)
    : ino(`  pinMode(${p('A')}, OUTPUT);`, `  digitalWrite(${p('A')}, HIGH);\n  delay(500);\n  digitalWrite(${p('A')}, LOW);\n  delay(500);`),
});

/* ---------- RGB-светодиод ---------- */
part('rgb', {
  title: 'RGB-светодиод', category: 'Выходы', w: 60, h: 100,
  pins: pinsAt([{id: 'R', label: 'R', need: 'out', prefer: 'pwm', x: 12}, {id: 'G', label: 'G', need: 'out', prefer: 'pwm', x: 36},
    {id: 'B', label: 'B', need: 'out', prefer: 'pwm', x: 48}], 98),
  props: {common: {label: 'Общий вывод', options: [['cathode', 'катод (−)'], ['anode', 'анод (+)']], default: 'cathode'}},
  art: () => `<circle data-r="glow" cx="30" cy="30" r="26" fill="#000" opacity="0" filter="url(#ocGlow)"/>
    ${leg(12, 56, 98)}${leg(24, 56, 92, '#7c8791')}${leg(36, 56, 98)}${leg(48, 56, 98)}
    <path d="M14 58V28a16 16 0 0 1 32 0v30z" fill="#e8eef5" opacity=".45" stroke="#c7d0da"/>
    <path data-r="lit" d="M14 58V28a16 16 0 0 1 32 0v30z" fill="#000" opacity="0"/>
    <rect x="11" y="56" width="38" height="5" rx="1.5" fill="#d5dde5" opacity=".7"/>`,
  frame(ctx) {
    const anode = ctx.part.props.common === 'anode';
    const v = role => {
      const r = ctx.read(role);
      if (r.level === null) return 0;
      const b = brightness(r);
      return anode ? 1 - b : b;
    };
    const [r, g, b] = [v('R'), v('G'), v('B')];
    const color = `rgb(${Math.round(r * 255)},${Math.round(g * 255)},${Math.round(b * 255)})`;
    const on = Math.max(r, g, b);
    ctx.q('lit').setAttribute('fill', color);
    ctx.q('lit').setAttribute('opacity', on ? 0.35 + on * 0.65 : 0);
    ctx.q('glow').setAttribute('fill', color);
    ctx.q('glow').setAttribute('opacity', on * 0.7);
  },
  idle(ctx) { ctx.q('lit').setAttribute('opacity', 0); ctx.q('glow').setAttribute('opacity', 0); },
  example: (p, board) => board === 'esp32'
    ? idf('    float t = 0;', `        oc_pwm(${p('R')}, 5000, (1 + sinf(t)) / 2);\n        oc_pwm(${p('G')}, 5000, (1 + sinf(t + 2.1f)) / 2);\n        oc_pwm(${p('B')}, 5000, (1 + sinf(t + 4.2f)) / 2);\n        t += 0.2f;\n        oc_delay(50);`, '#include <math.h>\n')
    : ino(`  pinMode(${p('R')}, OUTPUT);\n  pinMode(${p('G')}, OUTPUT);\n  pinMode(${p('B')}, OUTPUT);`,
      `  static float t = 0;\n  analogWrite(${p('R')}, 127 + 127 * sin(t));\n  analogWrite(${p('G')}, 127 + 127 * sin(t + 2.1));\n  analogWrite(${p('B')}, 127 + 127 * sin(t + 4.2));\n  t += 0.1;\n  delay(30);`),
});

/* ---------- NeoPixel (WS2812): лента, кольцо, матрица ---------- */
const NEO_LAYOUTS = {
  strip: {count: 8, w: 228, h: 70}, ring: {count: 16, w: 150, h: 175}, matrix: {count: 64, w: 168, h: 200},
};
const neoPositions = layout => {
  if (layout === 'ring') return Array.from({length: 16}, (_, i) => {
    const a = -Math.PI / 2 + i * Math.PI * 2 / 16;
    return [75 + Math.cos(a) * 58, 75 + Math.sin(a) * 58];
  });
  if (layout === 'matrix') return Array.from({length: 64}, (_, i) => [20 + (i % 8) * 18.5, 20 + Math.floor(i / 8) * 18.5]);
  return Array.from({length: 8}, (_, i) => [22 + i * 26, 26]);
};
part('neopixel', {
  title: 'NeoPixel (WS2812)', category: 'Выходы', esp32: 'helper',
  w: 228, h: 70,
  size: p => NEO_LAYOUTS[p.props.layout] || NEO_LAYOUTS.strip,
  pins: [{id: 'DIN', label: 'DIN', need: 'out'}],
  pinPos: p => {
    const {w, h} = NEO_LAYOUTS[p.props.layout] || NEO_LAYOUTS.strip;
    return {DIN: [w / 2, h - 2]};
  },
  props: {layout: {label: 'Вид', options: [['strip', 'лента 8'], ['ring', 'кольцо 16'], ['matrix', 'матрица 8×8']], default: 'strip'}},
  art: p => {
    const layout = p.props.layout || 'strip';
    const {w, h} = NEO_LAYOUTS[layout] || NEO_LAYOUTS.strip;
    const pos = neoPositions(layout);
    const base = layout === 'ring'
      ? `<circle cx="75" cy="75" r="70" fill="#1c1f26"/><circle cx="75" cy="75" r="46" fill="#11141a"/>`
      : layout === 'matrix'
        ? `<rect x="4" y="4" width="160" height="160" rx="6" fill="#1c1f26"/>`
        : `<rect x="2" y="8" width="224" height="36" rx="5" fill="#f2f2ee"/>`;
    const size = layout === 'matrix' ? 7.5 : 9;
    return `${base}${pos.map(([x, y], i) => `<rect x="${x - size}" y="${y - size}" width="${size * 2}" height="${size * 2}" rx="2" fill="#e4e0d8" stroke="#9ca3af" stroke-width=".8"/>
      <circle data-r="px${i}" cx="${x}" cy="${y}" r="${size - 2}" fill="#2a2a2a"/>`).join('')}
      ${leg(w / 2, h - 22, h - 2)}`;
  },
  start(ctx) {
    const layout = ctx.part.props.layout || 'strip';
    const count = (NEO_LAYOUTS[layout] || NEO_LAYOUTS.strip).count;
    const paint = frame => {
      for (let i = 0; i < count; i++) {
        const c = frame[i] || {r: 0, g: 0, b: 0};
        const lift = v => Math.round(255 * Math.pow(v / 255, 0.45));  // гамма: тусклые цвета тоже видно
        const el = ctx.q(`px${i}`);
        if (!el) continue;
        const dark = !c.r && !c.g && !c.b;
        el.setAttribute('fill', dark ? '#2a2a2a' : `rgb(${lift(c.r)},${lift(c.g)},${lift(c.b)})`);
        el.style.filter = dark ? '' : 'url(#ocGlow)';
      }
    };
    if (ctx.io.kind === 'avr') {
      const neo = attachNeoPixel(ctx.io, ctx.pin('DIN'), count, paint);
      ctx.cleanup(neo.off);
      ctx.poll = () => neo.poll(ctx.io.now());
    } else {
      const gpio = ctx.pinCode('DIN');
      ctx.cleanup(ctx.io.onMessage('NEO', msg => {
        const m = msg.match(/^(\d+) ([0-9a-fA-F]*)$/);
        if (!m || m[1] !== gpio) return;
        const colors = (m[2].match(/.{6}/g) || []).map(h => ({r: parseInt(h.slice(0, 2), 16), g: parseInt(h.slice(2, 4), 16), b: parseInt(h.slice(4), 16)}));
        paint(colors);
      }));
    }
  },
  frame(ctx) { ctx.poll?.(); },
  idle(ctx) {
    for (let i = 0; i < 64; i++) {
      const el = ctx.q(`px${i}`);
      if (!el) break;
      el.setAttribute('fill', '#2a2a2a');
      el.style.filter = '';
    }
  },
  example: (p, board, part) => {
    const count = (NEO_LAYOUTS[part.props.layout] || NEO_LAYOUTS.strip).count;
    return board === 'esp32'
      ? idf(`    uint32_t px[${count}];\n    int shift = 0;`, `        for (int i = 0; i < ${count}; i++) {\n            int h = (i * 256 / ${count} + shift) & 255;  // радуга\n            px[i] = h < 85 ? ((255 - h * 3) << 16) | ((h * 3) << 8)\n                  : h < 170 ? ((255 - (h - 85) * 3) << 8) | ((h - 85) * 3)\n                  : (((h - 170) * 3) << 16) | (255 - (h - 170) * 3);\n        }\n        oc_neopixel_show(${p('DIN')}, px, ${count});\n        shift += 8;\n        oc_delay(60);`)
      : ino(`  pixels.begin();\n  pixels.setBrightness(80);`,
        `  static uint16_t hue = 0;\n  for (int i = 0; i < ${count}; i++) {\n    pixels.setPixelColor(i, pixels.ColorHSV(hue + i * 65536L / ${count}));\n  }\n  pixels.show();\n  hue += 1024;\n  delay(30);`,
        `#include <Adafruit_NeoPixel.h>\nAdafruit_NeoPixel pixels(${count}, ${p('DIN')}, NEO_GRB + NEO_KHZ800);`);
  },
});

/* ---------- Пищалка ---------- */
part('buzzer', {
  title: 'Пищалка', category: 'Выходы', w: 70, h: 96,
  pins: pinsAt([{id: 'SIG', label: '+', need: 'out', x: 28}], 94),
  props: {kind: {label: 'Тип', options: [['passive', 'пассивная (tone)'], ['active', 'активная (HIGH = писк)']], default: 'passive'}},
  art: () => `<g data-r="waves" opacity="0" stroke="#fbbf24" stroke-width="2.5" fill="none" stroke-linecap="round">
      <path d="M58 16a16 16 0 0 1 0 26"/><path d="M63 9a26 26 0 0 1 0 40"/></g>
    ${leg(28, 58, 94)}${leg(42, 58, 92)}
    <circle cx="35" cy="30" r="27" fill="#1d2127" stroke="#3b4350" stroke-width="2"/>
    <circle cx="35" cy="30" r="7" fill="#0b0d10"/>${text(16, 18, '+', 11, '#e5e7eb')}
    <text data-r="hz" x="35" y="72" font-size="9" fill="#fbbf24" text-anchor="middle" font-family="monospace"></text>`,
  frame(ctx) {
    const r = ctx.read('SIG');
    const freq = ctx.part.props.kind === 'active' ? (r.level === 1 ? 2300 : 0) : (r.freq > 20 && r.freq < 20000 ? r.freq : 0);
    ctx.sound(freq);
    ctx.q('waves').setAttribute('opacity', freq ? 1 : 0);
    ctx.q('hz').textContent = freq ? `${Math.round(freq)} Гц` : '';
  },
  idle(ctx) { ctx.sound(0); ctx.q('waves').setAttribute('opacity', 0); ctx.q('hz').textContent = ''; },
  example: (p, board, part) => part.props.kind === 'active'
    ? (board === 'esp32'
      ? idf(`    oc_output(${p('SIG')});`, `        oc_write(${p('SIG')}, 1);\n        oc_delay(200);\n        oc_write(${p('SIG')}, 0);\n        oc_delay(800);`)
      : ino(`  pinMode(${p('SIG')}, OUTPUT);`, `  digitalWrite(${p('SIG')}, HIGH);\n  delay(200);\n  digitalWrite(${p('SIG')}, LOW);\n  delay(800);`))
    : (board === 'esp32'
      ? idf('    const int notes[] = {262, 294, 330, 349, 392, 440, 494, 523};', `        for (int i = 0; i < 8; i++) {\n            oc_tone(${p('SIG')}, notes[i]);\n            oc_delay(250);\n        }\n        oc_tone(${p('SIG')}, 0);\n        oc_delay(1000);`)
      : ino('', `  int notes[] = {262, 294, 330, 349, 392, 440, 494, 523};  // до-ре-ми…\n  for (int i = 0; i < 8; i++) {\n    tone(${p('SIG')}, notes[i], 200);\n    delay(250);\n  }\n  delay(1000);`)),
});

/* ---------- Реле ---------- */
part('relay', {
  title: 'Реле с лампой', category: 'Выходы', w: 120, h: 112,
  pins: pinsAt([{id: 'IN', label: 'IN', need: 'out', x: 30}], 110),
  props: {trigger: {label: 'Срабатывает от', options: [['high', 'HIGH'], ['low', 'LOW']], default: 'high'}},
  art: () => `<rect x="4" y="30" width="58" height="62" rx="4" fill="#1e5fb4" stroke="#5b9be0"/>
    <rect x="10" y="38" width="46" height="34" rx="2" fill="#2b7de0" stroke="#9cc8f5"/>${text(33, 58, 'RELAY', 9, '#e0efff')}
    <circle data-r="led" cx="16" cy="82" r="4" fill="#3b1d1d"/>${leg(30, 92, 110)}
    <path d="M62 50H80M62 70H74" stroke="#9aa5ae" stroke-width="3"/>
    <circle data-r="glow" cx="96" cy="34" r="22" fill="#ffd166" opacity="0" filter="url(#ocGlow)"/>
    <circle cx="96" cy="34" r="17" fill="#f8f3e6" opacity=".5" stroke="#cbd5e1"/>
    <path data-r="bulb" d="M90 40q6-14 12 0" stroke="#78716c" stroke-width="2" fill="none"/>
    <rect x="89" y="50" width="14" height="10" rx="2" fill="#94a3b8"/><path d="M96 60V70H74" stroke="#9aa5ae" stroke-width="3" fill="none"/>`,
  frame(ctx) {
    const level = ctx.read('IN').level;
    const on = level !== null && level === (ctx.part.props.trigger === 'low' ? 0 : 1);
    ctx.q('glow').setAttribute('opacity', on ? 0.9 : 0);
    ctx.q('led').setAttribute('fill', on ? '#ff4d4d' : '#3b1d1d');
    ctx.q('bulb').setAttribute('stroke', on ? '#f59e0b' : '#78716c');
  },
  idle(ctx) { ctx.q('glow').setAttribute('opacity', 0); ctx.q('led').setAttribute('fill', '#3b1d1d'); },
  example: (p, board) => board === 'esp32'
    ? idf(`    oc_output(${p('IN')});`, `        oc_write(${p('IN')}, 1);  // лампа горит\n        oc_delay(2000);\n        oc_write(${p('IN')}, 0);\n        oc_delay(2000);`)
    : ino(`  pinMode(${p('IN')}, OUTPUT);`, `  digitalWrite(${p('IN')}, HIGH);  // лампа горит\n  delay(2000);\n  digitalWrite(${p('IN')}, LOW);\n  delay(2000);`),
});

/* ---------- Семисегментный индикатор ---------- */
const SEGS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'dp'];
const SEG_PATH = {
  a: 'M22 14h28l-4 6H26z', b: 'M52 16l-4 30-5-4 4-24z', c: 'M47 52l-4 30-5-6 3-20z', d: 'M14 86h26l4 6H12z',
  e: 'M17 54l-4 30-4-4 3-22z', f: 'M22 18l5 4-3 22-5 4z', g: 'M20 48h26l-3 4H22l-3-4z',
};
part('seg7', {
  title: '7-сегментный индикатор', category: 'Дисплеи', w: 88, h: 132,
  pins: pinsAt(SEGS.map((id, i) => ({id, label: id, need: 'out', x: 8 + i * 10.3})), 130),
  props: {common: {label: 'Общий вывод', options: [['cathode', 'катод (−)'], ['anode', 'анод (+)']], default: 'cathode'}},
  art: () => `<rect x="2" y="4" width="70" height="98" rx="4" fill="#111418" stroke="#2f3640"/>
    ${Object.entries(SEG_PATH).map(([s, d]) => `<path data-r="s${s}" d="${d}" fill="#3a1414" transform="translate(4 0)"/>`).join('')}
    <circle data-r="sdp" cx="64" cy="92" r="4" fill="#3a1414"/>
    ${SEGS.map((s, i) => leg(8 + i * 10.3, 102, 130)).join('')}`,
  frame(ctx) {
    const anode = ctx.part.props.common === 'anode';
    for (const s of SEGS) {
      const level = ctx.read(s).level;
      const on = level !== null && (anode ? level === 0 : level === 1);
      ctx.q(`s${s}`).setAttribute('fill', on ? '#ff3b30' : '#3a1414');
      ctx.q(`s${s}`).style.filter = on ? 'url(#ocGlow)' : '';
    }
  },
  idle(ctx) { for (const s of SEGS) { ctx.q(`s${s}`).setAttribute('fill', '#3a1414'); ctx.q(`s${s}`).style.filter = ''; } },
  example: (p, board) => {
    const pins = SEGS.slice(0, 7).map(s => p(s)).join(', ');
    const table = '{0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F}';  // биты: a…g
    return board === 'esp32'
      ? idf(`    for (int s = 0; s < 7; s++) oc_output(pins[s]);`, `        for (int n = 0; n < 10; n++) {\n            for (int s = 0; s < 7; s++) oc_write(pins[s], (digits[n] >> s) & 1);\n            oc_delay(700);\n        }`,
        `const int pins[7] = {${pins}};  // a b c d e f g\nconst uint8_t digits[10] = ${table};\n`)
      : ino(`  for (int s = 0; s < 7; s++) pinMode(pins[s], OUTPUT);`, `  for (int n = 0; n < 10; n++) {\n    for (int s = 0; s < 7; s++) digitalWrite(pins[s], (digits[n] >> s) & 1);\n    delay(700);\n  }`,
        `const int pins[7] = {${pins}};  // a b c d e f g\nconst byte digits[10] = ${table};`);
  },
});

/* ---------- LCD 16×2 (параллельный и по I2C) ---------- */
const lcdArt = (backpack) => `<rect x="2" y="4" width="256" height="84" rx="5" fill="#1b5e37" stroke="#2f855a"/>
  <rect x="14" y="16" width="232" height="60" rx="3" fill="#24422b"/>
  <rect data-r="screen" x="20" y="22" width="220" height="48" rx="2" fill="#9ccc65"/>
  <text data-r="l0" x="26" y="42" font-size="17" fill="#1f3a12" font-family="monospace" xml:space="preserve" textLength="208"> </text>
  <text data-r="l1" x="26" y="64" font-size="17" fill="#1f3a12" font-family="monospace" xml:space="preserve" textLength="208"> </text>
  ${backpack ? `<rect x="100" y="88" width="60" height="12" rx="2" fill="#1e3a8a"/>${text(130, 97, 'I2C 0x27', 7, '#c7d2fe')}` : ''}`;

const lcdRender = (ctx, lcd) => {
  if (ctx.state.lcdVersion === lcd.version && ctx.state.lcdLight === lcd.backlight) return;
  ctx.state.lcdVersion = lcd.version;
  ctx.state.lcdLight = lcd.backlight;
  const [l0, l1] = lcd.lines();
  ctx.q('l0').textContent = l0.replace(/ /g, ' ');
  ctx.q('l1').textContent = l1.replace(/ /g, ' ');
  ctx.q('screen').setAttribute('fill', lcd.backlight ? '#9ccc65' : '#5f7a3d');
};
const lcdIdle = ctx => {
  ctx.q('l0').textContent = ' '; ctx.q('l1').textContent = ' ';
  ctx.q('screen').setAttribute('fill', '#9ccc65');
  ctx.state.lcdVersion = -1;
};
/* ESP32: «@OC LCD <кол> <стр> <текст>» / «@OC LCD CLR» / старое «@OC LCD текст» */
const lcdFromSerial = (ctx, lcd) => ctx.cleanup(ctx.io.onMessage('LCD', msg => {
  lcd.version++;
  if (msg === 'CLR') { lcd.ddram.fill(32); return; }
  const m = msg.match(/^(\d+) (\d+) (.*)$/);
  const [col, row, value] = m ? [Number(m[1]), Number(m[2]), m[3]] : [0, 0, msg.padEnd(16)];
  for (let i = 0; i < value.length && col + i < 40; i++) lcd.ddram[(row ? 0x40 : 0) + col + i] = value.charCodeAt(i) < 127 ? value.charCodeAt(i) : 63;
}));
const lcdEspExample = () => idf('    oc_lcd_clear();\n    oc_lcd_print(0, 0, "Hello, ESP32!");\n    int seconds = 0;',
  '        char line[17];\n        snprintf(line, sizeof line, "Uptime: %4d s", seconds++);\n        oc_lcd_print(0, 1, line);\n        oc_delay(1000);');

part('lcd', {
  title: 'LCD 16×2', category: 'Дисплеи', w: 260, h: 112, esp32: 'helper',
  pins: pinsAt(['RS', 'E', 'D4', 'D5', 'D6', 'D7'].map((id, i) => ({id, label: id, need: 'out', x: 70 + i * 24})), 110),
  art: () => lcdArt(false) + ['RS', 'E', 'D4', 'D5', 'D6', 'D7'].map((_, i) => leg(70 + i * 24, 88, 110)).join(''),
  start(ctx) {
    const lcd = ctx.state.lcd = new Hd44780();
    if (ctx.io.kind === 'avr') {
      const pins = Object.fromEntries(['RS', 'E', 'D4', 'D5', 'D6', 'D7'].map(r => [r, ctx.pin(r)]));
      if (Object.values(pins).every(Boolean)) ctx.cleanup(attachLcdParallel(ctx.io, pins, lcd));
    } else lcdFromSerial(ctx, lcd);
  },
  frame(ctx) { if (ctx.state.lcd) lcdRender(ctx, ctx.state.lcd); },
  idle: lcdIdle,
  example: (p, board) => board === 'esp32' ? lcdEspExample()
    : ino('  lcd.begin(16, 2);\n  lcd.print("Hello, Arduino!");', '  lcd.setCursor(0, 1);\n  lcd.print("Uptime: ");\n  lcd.print(millis() / 1000);\n  delay(200);',
      `#include <LiquidCrystal.h>\nLiquidCrystal lcd(${['RS', 'E', 'D4', 'D5', 'D6', 'D7'].map(p).join(', ')});`),
});

part('lcd_i2c', {
  title: 'LCD 16×2 I2C', category: 'Дисплеи', w: 260, h: 122, esp32: 'helper',
  pins: pinsAt([{id: 'SDA', label: 'SDA', need: 'sda', x: 116}, {id: 'SCL', label: 'SCL', need: 'scl', x: 144}], 120),
  props: {address: {label: 'Адрес', options: [['39', '0x27'], ['63', '0x3F']], default: '39'}},
  art: () => lcdArt(true) + leg(116, 100, 120) + leg(144, 100, 120),
  start(ctx) {
    const lcd = ctx.state.lcd = new Hd44780();
    if (ctx.io.kind === 'avr') ctx.io.i2c(Number(ctx.part.props.address || 39), pcf8574Lcd(lcd));
    else lcdFromSerial(ctx, lcd);
  },
  frame(ctx) { if (ctx.state.lcd) lcdRender(ctx, ctx.state.lcd); },
  idle: lcdIdle,
  example: (p, board, part) => board === 'esp32' ? lcdEspExample()
    : ino('  lcd.init();\n  lcd.backlight();\n  lcd.print("Hello, I2C!");', '  lcd.setCursor(0, 1);\n  lcd.print("Uptime: ");\n  lcd.print(millis() / 1000);\n  delay(200);',
      `#include <Wire.h>\n#include <LiquidCrystal_I2C.h>\nLiquidCrystal_I2C lcd(0x${Number(part.props.address || 39).toString(16).toUpperCase()}, 16, 2);`),
});

/* ---------- OLED SSD1306 ---------- */
part('oled', {
  title: 'OLED 128×64', category: 'Дисплеи', w: 164, h: 122, esp32: false,
  pins: pinsAt([{id: 'SDA', label: 'SDA', need: 'sda', x: 68}, {id: 'SCL', label: 'SCL', need: 'scl', x: 96}], 120),
  art: () => `<rect x="2" y="2" width="160" height="98" rx="6" fill="#123b70" stroke="#2c5aa0"/>
    <rect x="12" y="12" width="140" height="74" rx="2" fill="#05070a"/>
    <image data-r="img" x="16" y="17" width="132" height="66" style="image-rendering:pixelated"/>
    ${leg(68, 100, 120)}${leg(96, 100, 120)}`,
  start(ctx) {
    if (ctx.io.kind !== 'avr') return;
    const oled = ctx.state.oled = new Ssd1306();
    ctx.io.i2c(0x3c, oled);
    ctx.state.canvas ||= Object.assign(document.createElement('canvas'), {width: 128, height: 64});
  },
  frame(ctx) {
    const oled = ctx.state.oled;
    if (!oled || ctx.state.oledVersion === oled.version) return;
    ctx.state.oledVersion = oled.version;
    const g = ctx.state.canvas.getContext('2d');
    const img = g.createImageData(128, 64);
    for (let y = 0; y < 64; y++) for (let x = 0; x < 128; x++) {
      const on = oled.on && oled.pixel(x, y);
      const i = (y * 128 + x) * 4;
      img.data[i] = on ? 140 : 0; img.data[i + 1] = on ? 220 : 0; img.data[i + 2] = on ? 255 : 0; img.data[i + 3] = 255;
    }
    g.putImageData(img, 0, 0);
    ctx.q('img').setAttribute('href', ctx.state.canvas.toDataURL());
  },
  idle(ctx) { ctx.q('img').removeAttribute('href'); ctx.state.oledVersion = -1; },
  example: () => ino('  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);\n  display.setTextColor(SSD1306_WHITE);',
    '  display.clearDisplay();\n  display.setTextSize(2);\n  display.setCursor(0, 0);\n  display.print("Hello!");\n  display.setTextSize(1);\n  display.setCursor(0, 30);\n  display.print("Uptime: ");\n  display.print(millis() / 1000);\n  display.drawCircle(110, 45, 10 + (millis() / 100) % 8, SSD1306_WHITE);\n  display.display();\n  delay(100);',
    '#include <Wire.h>\n#include <Adafruit_GFX.h>\n#include <Adafruit_SSD1306.h>\nAdafruit_SSD1306 display(128, 64, &Wire, -1);'),
});

/* ---------- Сервопривод ---------- */
part('servo', {
  title: 'Сервопривод SG90', category: 'Моторы', w: 150, h: 112,
  pins: pinsAt([{id: 'SIG', label: 'SIG', need: 'out', x: 40}], 110),
  art: () => `<path d="M40 110V96" stroke="#eda334" stroke-width="4"/>
    <rect x="8" y="44" width="134" height="18" rx="4" fill="#285ea2"/><circle cx="17" cy="53" r="4" fill="#101727"/><circle cx="133" cy="53" r="4" fill="#101727"/>
    <rect x="22" y="20" width="106" height="78" rx="7" fill="#397fd3" stroke="#75b4f0" stroke-width="2"/>
    <rect x="30" y="62" width="90" height="20" rx="2" fill="#e5e8df"/>${text(75, 76, 'SG90 · SERVO', 10, '#263442')}
    <circle cx="75" cy="22" r="17" fill="#dfe4e7" stroke="#86939e"/>
    <g data-r="horn"><rect x="28" y="13" width="94" height="18" rx="9" fill="#f8f9f2" stroke="#88939a"/>
    ${[36, 48, 60, 90, 102, 114].map(x => `<circle cx="${x}" cy="22" r="2.5" fill="#738493"/>`).join('')}</g>
    <circle cx="75" cy="22" r="5" fill="#adb8bf"/>
    <text data-r="deg" x="75" y="50" font-size="10" fill="#e0efff" text-anchor="middle" font-family="monospace">0°</text>`,
  frame(ctx) {
    const angle = servoAngle(ctx.read('SIG').pulse);
    if (angle === null || angle === ctx.state.angle) return;
    ctx.state.angle = angle;
    ctx.q('horn').setAttribute('transform', `rotate(${angle - 90} 75 22)`);
    ctx.q('deg').textContent = `${angle}°`;
  },
  idle(ctx) { ctx.state.angle = null; ctx.q('horn').setAttribute('transform', 'rotate(-90 75 22)'); ctx.q('deg').textContent = '0°'; },
  example: (p, board) => board === 'esp32'
    ? idf('', `        for (int a = 0; a <= 180; a += 10) { oc_servo(${p('SIG')}, a); oc_delay(60); }\n        for (int a = 180; a >= 0; a -= 10) { oc_servo(${p('SIG')}, a); oc_delay(60); }`)
    : ino(`  motor.attach(${p('SIG')});`, '  for (int a = 0; a <= 180; a += 5) { motor.write(a); delay(20); }\n  for (int a = 180; a >= 0; a -= 5) { motor.write(a); delay(20); }',
      '#include <Servo.h>\nServo motor;'),
});

/* ---------- DC-мотор (через транзистор) ---------- */
const fan = (cx, cy, r) => `<g data-r="rotor">${[0, 120, 240].map(a =>
  `<path d="M${cx} ${cy}c${r * 0.3} -${r * 0.25} ${r * 0.7} -${r * 0.75} ${r * 0.15} -${r}c-${r * 0.35} ${r * 0.2} -${r * 0.4} ${r * 0.6} -${r * 0.15} ${r}" fill="#94a3b8" transform="rotate(${a} ${cx} ${cy})"/>`).join('')}
  <circle cx="${cx}" cy="${cy}" r="${r * 0.18}" fill="#475569"/></g>`;
const spin = (ctx, speed, dt, cx, cy) => {
  ctx.state.angle = ((ctx.state.angle || 0) + speed * dt * 1440) % 360;
  ctx.q('rotor').setAttribute('transform', `rotate(${ctx.state.angle} ${cx} ${cy})`);
  ctx.q('rpm').textContent = speed ? `${Math.round(Math.abs(speed) * 240)} об/мин${speed < 0 ? ' ⟲' : ''}` : 'стоп';
};
part('motor', {
  title: 'DC-мотор', category: 'Моторы', w: 110, h: 122,
  pins: pinsAt([{id: 'SIG', label: 'ШИМ', need: 'out', prefer: 'pwm', x: 55}], 120),
  art: () => `<rect x="30" y="66" width="50" height="34" rx="5" fill="#cbd5e1" stroke="#64748b"/>
    <rect x="44" y="60" width="22" height="8" fill="#94a3b8"/>${fan(55, 36, 34)}
    <text data-r="rpm" x="55" y="88" font-size="8" fill="#1e293b" text-anchor="middle" font-family="monospace">стоп</text>
    ${leg(55, 100, 120)}`,
  frame(ctx, dt) { spin(ctx, brightness(ctx.read('SIG')), dt, 55, 36); },
  idle(ctx) { ctx.q('rpm').textContent = 'стоп'; },
  example: (p, board) => board === 'esp32'
    ? idf('', `        for (int i = 0; i <= 10; i++) { oc_pwm(${p('SIG')}, 1000, i / 10.0f); oc_delay(300); }\n        oc_pwm(${p('SIG')}, 1000, 0);\n        oc_delay(1500);`)
    : ino(`  pinMode(${p('SIG')}, OUTPUT);`, `  for (int speed = 0; speed <= 255; speed += 25) {\n    analogWrite(${p('SIG')}, speed);  // разгон\n    delay(300);\n  }\n  analogWrite(${p('SIG')}, 0);\n  delay(1500);`),
});

/* ---------- Драйвер L298N с мотором ---------- */
part('l298n', {
  title: 'Мотор + драйвер L298N', category: 'Моторы', w: 200, h: 132,
  pins: pinsAt([{id: 'ENA', label: 'ENA', need: 'out', prefer: 'pwm', x: 30}, {id: 'IN1', label: 'IN1', need: 'out', x: 56},
    {id: 'IN2', label: 'IN2', need: 'out', x: 82}], 130),
  art: () => `<rect x="4" y="30" width="100" height="80" rx="4" fill="#b91c1c" stroke="#f87171"/>
    <rect x="22" y="36" width="64" height="32" rx="2" fill="#111827"/>${[0, 1, 2, 3, 4, 5].map(i => `<rect x="${26 + i * 10}" y="38" width="5" height="28" fill="#374151"/>`).join('')}
    ${text(54, 84, 'L298N', 11, '#fee2e2')}${leg(30, 110, 130)}${leg(56, 110, 130)}${leg(82, 110, 130)}
    <path d="M104 60H130" stroke="#ef4444" stroke-width="3"/><path d="M104 70H130" stroke="#111" stroke-width="3"/>
    <rect x="128" y="54" width="34" height="26" rx="4" fill="#cbd5e1" stroke="#64748b"/>${fan(166, 40, 30)}
    <text data-r="rpm" x="150" y="112" font-size="9" fill="#cbd5e1" text-anchor="middle" font-family="monospace">стоп</text>`,
  frame(ctx, dt) {
    const ena = ctx.pin('ENA') ? brightness(ctx.read('ENA')) : 1;
    const in1 = ctx.read('IN1').level === 1, in2 = ctx.read('IN2').level === 1;
    const dir = in1 && !in2 ? 1 : in2 && !in1 ? -1 : 0;
    spin(ctx, ena * dir, dt, 166, 40);
  },
  idle(ctx) { ctx.q('rpm').textContent = 'стоп'; },
  example: (p, board) => board === 'esp32'
    ? idf(`    oc_output(${p('IN1')});\n    oc_output(${p('IN2')});`, `        oc_write(${p('IN1')}, 1); oc_write(${p('IN2')}, 0);  // вперёд\n        oc_pwm(${p('ENA')}, 1000, 0.8f);\n        oc_delay(2000);\n        oc_write(${p('IN1')}, 0); oc_write(${p('IN2')}, 1);  // назад\n        oc_pwm(${p('ENA')}, 1000, 0.4f);\n        oc_delay(2000);`)
    : ino(`  pinMode(${p('IN1')}, OUTPUT);\n  pinMode(${p('IN2')}, OUTPUT);\n  pinMode(${p('ENA')}, OUTPUT);`,
      `  digitalWrite(${p('IN1')}, HIGH);  // вперёд\n  digitalWrite(${p('IN2')}, LOW);\n  analogWrite(${p('ENA')}, 200);\n  delay(2000);\n  digitalWrite(${p('IN1')}, LOW);  // назад, медленнее\n  digitalWrite(${p('IN2')}, HIGH);\n  analogWrite(${p('ENA')}, 100);\n  delay(2000);`),
});

/* ---------- Шаговый 28BYJ-48 + ULN2003 ---------- */
const COILS = ['IN1', 'IN2', 'IN3', 'IN4'];
part('stepper', {
  title: 'Шаговый 28BYJ-48', category: 'Моторы', w: 170, h: 130,
  pins: pinsAt(COILS.map((id, i) => ({id, label: id, need: 'out', x: 24 + i * 22})), 128),
  art: () => `<rect x="4" y="44" width="100" height="62" rx="4" fill="#15803d" stroke="#4ade80"/>
    <rect x="16" y="60" width="44" height="22" rx="2" fill="#111827"/>${text(38, 75, 'ULN2003', 8, '#d1fae5')}
    ${COILS.map((_, i) => `<circle data-r="c${i}" cx="${72 + (i % 2) * 14}" cy="${60 + Math.floor(i / 2) * 14}" r="4" fill="#3f1d1d"/>`).join('')}
    ${COILS.map((_, i) => leg(24 + i * 22, 106, 128)).join('')}
    <path d="M104 74H118" stroke="#f59e0b" stroke-width="4"/>
    <circle cx="140" cy="60" r="28" fill="#cbd5e1" stroke="#64748b" stroke-width="2"/><circle cx="140" cy="60" r="8" fill="#e2e8f0" stroke="#94a3b8"/>
    <g data-r="shaft"><rect x="137" y="30" width="6" height="30" rx="2" fill="#f59e0b"/></g>
    <text data-r="deg" x="140" y="104" font-size="9" fill="#cbd5e1" text-anchor="middle" font-family="monospace">0°</text>`,
  start(ctx) {
    const tracker = ctx.state.tracker = stepperTracker();
    const pins = COILS.map(r => ctx.pin(r));
    const update = () => tracker.update(pins.reduce((mask, pin, i) => mask | ((pin && ctx.io.read(pin).level === 1 ? 1 : 0) << i), 0));
    for (const pin of pins) if (pin) ctx.cleanup(ctx.io.onEdge(pin, update));
  },
  frame(ctx) {
    const tracker = ctx.state.tracker;
    if (!tracker) return;
    ctx.q('shaft').setAttribute('transform', `rotate(${tracker.angle} 140 60)`);
    ctx.q('deg').textContent = `${Math.round(tracker.angle)}°`;
    COILS.forEach((r, i) => ctx.q(`c${i}`).setAttribute('fill', ctx.read(r).level === 1 ? '#ef4444' : '#3f1d1d'));
  },
  idle(ctx) { ctx.q('shaft').setAttribute('transform', ''); ctx.q('deg').textContent = '0°'; },
  example: (p, board) => board === 'esp32'
    ? idf('    for (int i = 0; i < 4; i++) oc_output(coils[i]);', '        for (int s = 0; s < 512; s++) {  // четверть оборота: 2048 шагов на оборот\n            for (int i = 0; i < 4; i++) oc_write(coils[i], i == s % 4 || i == (s + 1) % 4);\n            oc_delay(3);\n        }\n        oc_delay(1000);',
      `const int coils[4] = {${COILS.map(p).join(', ')}};  // IN1…IN4\n`)
    : ino('  motor.setSpeed(10);  // об/мин', '  motor.step(512);   // четверть оборота\n  delay(500);\n  motor.step(-512);  // и обратно\n  delay(500);',
      `#include <Stepper.h>\n// 2048 шагов на оборот; порядок IN1, IN3, IN2, IN4 — так требует библиотека\nStepper motor(2048, ${p('IN1')}, ${p('IN3')}, ${p('IN2')}, ${p('IN4')});`),
});

/* ---------- Кнопка ---------- */
part('button', {
  title: 'Кнопка', category: 'Кнопки и ручки', w: 76, h: 96,
  pins: pinsAt([{id: 'OUT', label: 'OUT', need: 'in', x: 38}], 94),
  props: {
    wiring: {label: 'Подключение', options: [['pullup', 'к GND (INPUT_PULLUP, нажата = LOW)'], ['pulldown', 'к +5V (нажата = HIGH)']], default: 'pullup'},
    cap: {label: 'Цвет', options: [['#e11d48', 'красная'], ['#2563eb', 'синяя'], ['#16a34a', 'зелёная'], ['#eab308', 'жёлтая'], ['#334155', 'чёрная']], default: '#e11d48'},
  },
  art: p => `<g data-ctl="press" style="cursor:pointer">
    <path d="M18 16H6v18m64-18h-12v18M18 72H6V56m64 16h-12V56" stroke="#b0bec8" stroke-width="5" fill="none"/>
    <rect x="12" y="10" width="52" height="64" rx="5" fill="#c1ccd1" stroke="#627a87" stroke-width="2"/>
    <circle cx="38" cy="42" r="21" fill="#17212b"/><circle data-r="cap" cx="38" cy="39" r="16" fill="${p.props.cap || '#e11d48'}" stroke="#0005" stroke-width="2"/></g>
    ${leg(38, 74, 94)}`,
  bind(ctx) {
    const set = pressed => {
      ctx.state.pressed = pressed;
      ctx.q('cap').setAttribute('transform', pressed ? 'translate(0 3)' : '');
      ctx.q('cap').style.filter = pressed ? 'brightness(.7)' : '';
      ctx.apply();
    };
    ctx.press(ctx.q('press'), set);
  },
  start(ctx) { ctx.apply(); },
  apply(ctx) {
    const pullup = ctx.part.props.wiring !== 'pulldown';
    ctx.digital('OUT', ctx.state.pressed ? !pullup : pullup);
  },
  example: (p, board, part) => {
    const pullup = part.props.wiring !== 'pulldown';
    return board === 'esp32'
      ? idf(`    oc_input(${p('OUT')}, ${pullup ? 'true' : 'false'});\n    oc_output(2);`, `        int pressed = oc_read(${p('OUT')}) == ${pullup ? 0 : 1};\n        oc_write(2, pressed);  // светодиод на плате\n        printf("Кнопка: %s\\n", pressed ? "нажата" : "отпущена");\n        oc_delay(200);`)
      : ino(`  pinMode(${p('OUT')}, ${pullup ? 'INPUT_PULLUP' : 'INPUT'});\n  pinMode(13, OUTPUT);\n  Serial.begin(9600);`,
        `  bool pressed = digitalRead(${p('OUT')}) == ${pullup ? 'LOW' : 'HIGH'};\n  digitalWrite(13, pressed);  // светодиод L на плате\n  Serial.println(pressed ? "нажата" : "отпущена");\n  delay(200);`);
  },
});

/* ---------- Переключатель ---------- */
part('switch', {
  title: 'Переключатель', category: 'Кнопки и ручки', w: 86, h: 80,
  pins: pinsAt([{id: 'OUT', label: 'OUT', need: 'in', x: 43}], 78),
  art: () => `<g data-ctl="toggle" style="cursor:pointer"><rect x="6" y="20" width="74" height="34" rx="6" fill="#1f2937" stroke="#4b5563"/>
    <rect x="14" y="28" width="58" height="18" rx="9" fill="#111827"/>
    <rect data-r="knob" x="16" y="26" width="26" height="22" rx="5" fill="#e5e7eb" stroke="#9ca3af"/>
    ${text(22, 16, 'OFF', 8, '#9ca3af')}${text(64, 16, 'ON', 8, '#9ca3af')}</g>${leg(43, 54, 78)}`,
  bind(ctx) {
    ctx.q('toggle').addEventListener('click', () => { ctx.state.on = !ctx.state.on; ctx.render(); ctx.apply(); ctx.changed(); });
    ctx.render();
  },
  render(ctx) { ctx.q('knob').setAttribute('x', ctx.state.on ? 44 : 16); },
  start(ctx) { ctx.apply(); },
  apply(ctx) { ctx.digital('OUT', Boolean(ctx.state.on)); },
  example: (p, board) => board === 'esp32'
    ? idf(`    oc_input(${p('OUT')}, false);`, `        printf("Переключатель: %s\\n", oc_read(${p('OUT')}) ? "ON" : "OFF");\n        oc_delay(500);`)
    : ino(`  pinMode(${p('OUT')}, INPUT);\n  Serial.begin(9600);`, `  Serial.println(digitalRead(${p('OUT')}) ? "ON" : "OFF");\n  delay(500);`),
});

/* ---------- Аналоговые ручки и датчики: общий слайдер ---------- */
const slider = (ctl, min, max, step = 1) => `<input type="range" data-ctl="${ctl}" min="${min}" max="${max}" step="${step}">`;
const bindSlider = (ctx, ctl, key, initial, show) => {
  const input = ctx.q(ctl);
  if (ctx.state[key] == null) ctx.state[key] = initial;
  input.value = ctx.state[key];
  const update = () => { ctx.state[key] = Number(input.value); show?.(ctx.state[key]); ctx.apply(); };
  input.addEventListener('input', update);
  input.addEventListener('change', () => ctx.changed());
  show?.(ctx.state[key]);
};
const readout = (ctx, value) => { const el = ctx.q('value'); if (el) el.textContent = value; };

part('pot', {
  title: 'Потенциометр', category: 'Кнопки и ручки', w: 90, h: 104, analog: true,
  pins: pinsAt([{id: 'SIG', label: 'SIG', need: 'analog', x: 45}], 102),
  art: () => `${leg(25, 76, 96, '#64748b')}${leg(45, 76, 102)}${leg(65, 76, 96, '#64748b')}
    <circle cx="45" cy="42" r="34" fill="#bcc7c9" stroke="#6c7e88" stroke-width="3"/><circle cx="45" cy="42" r="27" fill="#192632" stroke="#506272" stroke-width="4"/>
    <g data-r="knob"><path d="M45 42V20" stroke="#dce4e8" stroke-width="4" stroke-linecap="round"/></g>
    <text data-r="value" x="45" y="92" font-size="8" fill="#cbd5e1" text-anchor="middle" font-family="monospace"></text>`,
  controls: () => slider('range', 0, 1023),
  bind(ctx) {
    bindSlider(ctx, 'range', 'value', 512, v => {
      ctx.q('knob').setAttribute('transform', `rotate(${v * 270 / 1023 - 135} 45 42)`);
      readout(ctx, Math.round(v));
    });
  },
  start(ctx) { ctx.apply(); },
  apply(ctx) { ctx.analog('SIG', ctx.state.value / 1023); },
  example: (p, board) => board === 'esp32'
    ? idf('', `        printf("Потенциометр: %d мВ\\n", oc_analog_mv(${p('SIG')}));\n        oc_delay(300);`)
    : ino('  Serial.begin(9600);', `  Serial.println(analogRead(${p('SIG')}));  // 0…1023\n  delay(250);`),
});

part('ldr', {
  title: 'Фоторезистор', category: 'Датчики', w: 80, h: 104, analog: true,
  pins: pinsAt([{id: 'SIG', label: 'AO', need: 'analog', x: 40}], 102),
  art: () => `<rect x="8" y="46" width="64" height="38" rx="4" fill="#1e3a8a" stroke="#60a5fa"/>${text(40, 76, 'LDR', 8, '#bfdbfe')}
    <circle data-r="sun" cx="40" cy="22" r="18" fill="#fbbf24" opacity=".5"/>
    <circle cx="40" cy="22" r="11" fill="#f59e0b" stroke="#b45309"/><path d="M33 18h14M33 22h14M33 26h14" stroke="#7c2d12" stroke-width="1.5"/>
    <path d="M34 33V46M46 33V46" stroke="#b9c3ca" stroke-width="2"/>${leg(40, 84, 102)}
    <text data-r="value" x="40" y="62" font-size="8" fill="#e0e7ff" text-anchor="middle" font-family="monospace"></text>`,
  controls: () => slider('range', 0, 100),
  bind(ctx) {
    bindSlider(ctx, 'range', 'light', 60, v => {
      ctx.q('sun').setAttribute('opacity', 0.1 + v / 110);
      readout(ctx, `${v}% света`);
    });
  },
  start(ctx) { ctx.apply(); },
  apply(ctx) { ctx.analog('SIG', 0.05 + ctx.state.light / 100 * 0.9); },
  example: (p, board) => board === 'esp32'
    ? idf('', `        int mv = oc_analog_mv(${p('SIG')});\n        printf("Свет: %d мВ — %s\\n", mv, mv > 1600 ? "светло" : "темно");\n        oc_delay(500);`)
    : ino('  Serial.begin(9600);', `  int light = analogRead(${p('SIG')});\n  Serial.print("Свет: ");\n  Serial.println(light > 512 ? "светло" : "темно");\n  delay(500);`),
});

part('tmp36', {
  title: 'Термодатчик TMP36', category: 'Датчики', w: 70, h: 104, analog: true,
  pins: pinsAt([{id: 'SIG', label: 'OUT', need: 'analog', x: 35}], 102),
  art: () => `<path d="M14 54V24a21 21 0 0 1 42 0v30z" fill="#1f2937" stroke="#4b5563"/>${text(35, 40, 'TMP36', 8, '#9ca3af')}
    ${leg(22, 54, 92, '#64748b')}${leg(35, 54, 102)}${leg(48, 54, 92, '#64748b')}
    <text data-r="value" x="35" y="72" font-size="9" fill="#fca5a5" text-anchor="middle" font-family="monospace"></text>`,
  controls: () => slider('range', -40, 125),
  bind(ctx) { bindSlider(ctx, 'range', 'celsius', 22, v => readout(ctx, `${v}°C`)); },
  start(ctx) { ctx.apply(); },
  apply(ctx) { ctx.volts('SIG', 0.5 + ctx.state.celsius / 100); },
  example: (p, board) => board === 'esp32'
    ? idf('', `        float celsius = (oc_analog_mv(${p('SIG')}) - 500) / 10.0f;\n        printf("Температура: %.1f °C\\n", celsius);\n        oc_delay(1000);`)
    : ino('  Serial.begin(9600);', `  float volts = analogRead(${p('SIG')}) * 5.0 / 1023;\n  float celsius = (volts - 0.5) * 100;  // 10 мВ на градус\n  Serial.print(celsius);\n  Serial.println(" °C");\n  delay(1000);`),
});

/* ---------- Джойстик ---------- */
part('joystick', {
  title: 'Джойстик', category: 'Кнопки и ручки', w: 112, h: 126, analog: true,
  pins: pinsAt([{id: 'VRX', label: 'VRx', need: 'analog', x: 30}, {id: 'VRY', label: 'VRy', need: 'analog', x: 56},
    {id: 'SW', label: 'SW', need: 'in', x: 82}], 124),
  art: () => `<rect x="6" y="4" width="100" height="96" rx="6" fill="#111827" stroke="#374151"/>
    <circle cx="56" cy="50" r="38" fill="#1f2937" stroke="#4b5563"/>
    <g data-ctl="stick" style="cursor:grab;touch-action:none"><circle data-r="knob" cx="56" cy="50" r="22" fill="#374151" stroke="#9ca3af" stroke-width="2"/></g>
    ${leg(30, 100, 124)}${leg(56, 100, 124)}${leg(82, 100, 124)}`,
  bind(ctx) {
    const s = ctx.state;
    s.x ??= 0.5; s.y ??= 0.5;
    const knob = ctx.q('knob');
    const draw = () => { knob.setAttribute('cx', 56 + (s.x - 0.5) * 50); knob.setAttribute('cy', 50 + (s.y - 0.5) * 50); knob.setAttribute('fill', s.pressed ? '#64748b' : '#374151'); };
    let start = null, moved = false;
    const stick = ctx.q('stick');
    stick.addEventListener('pointerdown', e => {
      e.stopPropagation(); stick.setPointerCapture(e.pointerId);
      start = {x: e.clientX, y: e.clientY}; moved = false;
    });
    stick.addEventListener('pointermove', e => {
      if (!start) return;
      const scale = ctx.scale() * 25;
      const dx = (e.clientX - start.x) / scale, dy = (e.clientY - start.y) / scale;
      if (Math.abs(dx) + Math.abs(dy) > 0.1) moved = true;
      const len = Math.max(1, Math.hypot(dx, dy));
      s.x = 0.5 + dx / len / 2; s.y = 0.5 + dy / len / 2;
      draw(); ctx.apply();
    });
    const release = () => {
      if (!start) return;
      start = null;
      if (!moved) { s.pressed = true; draw(); ctx.apply(); setTimeout(() => { s.pressed = false; draw(); ctx.apply(); }, 250); }
      s.x = 0.5; s.y = 0.5;  // ручка пружинит в центр
      draw(); ctx.apply();
    };
    stick.addEventListener('pointerup', release);
    stick.addEventListener('pointercancel', release);
    draw();
  },
  start(ctx) { ctx.apply(); },
  apply(ctx) {
    ctx.analog('VRX', ctx.state.x ?? 0.5);
    ctx.analog('VRY', ctx.state.y ?? 0.5);
    ctx.digital('SW', !ctx.state.pressed);
  },
  example: (p, board) => board === 'esp32'
    ? idf(`    oc_input(${p('SW')}, true);`, `        printf("X=%d Y=%d кнопка=%d\\n", oc_analog_mv(${p('VRX')}), oc_analog_mv(${p('VRY')}), !oc_read(${p('SW')}));\n        oc_delay(200);`)
    : ino(`  pinMode(${p('SW')}, INPUT_PULLUP);\n  Serial.begin(9600);`, `  Serial.print("X=");\n  Serial.print(analogRead(${p('VRX')}));\n  Serial.print(" Y=");\n  Serial.print(analogRead(${p('VRY')}));\n  Serial.print(" кнопка=");\n  Serial.println(digitalRead(${p('SW')}) == LOW);\n  delay(200);`),
});

/* ---------- Датчик движения PIR ---------- */
part('pir', {
  title: 'Датчик движения PIR', category: 'Датчики', w: 96, h: 112,
  pins: pinsAt([{id: 'OUT', label: 'OUT', need: 'in', x: 48}], 110),
  art: () => `<rect x="6" y="54" width="84" height="34" rx="4" fill="#15803d" stroke="#4ade80"/>
    <path d="M14 56a34 34 0 0 1 68 0z" fill="#f8fafc" stroke="#cbd5e1"/>
    ${[22, 36, 48, 60, 74].map(x => `<path d="M${x} 54q0-${x === 48 ? 30 : 22} ${x < 48 ? 8 : -8}-28" stroke="#e2e8f0" fill="none"/>`).join('')}
    <circle data-r="led" cx="16" cy="78" r="4" fill="#3b1d1d"/>${leg(48, 88, 110)}
    <g data-ctl="motion" style="cursor:pointer"><rect x="28" y="64" width="56" height="18" rx="9" fill="#0f172a" stroke="#64748b"/>${text(56, 77, '👋 махнуть', 8, '#e2e8f0')}</g>`,
  bind(ctx) {
    ctx.q('motion').addEventListener('click', () => {
      ctx.state.motion = true; ctx.render(); ctx.apply();
      clearTimeout(ctx.state.timer);
      ctx.state.timer = setTimeout(() => { ctx.state.motion = false; ctx.render(); ctx.apply(); }, 3000);
    });
  },
  render(ctx) { ctx.q('led').setAttribute('fill', ctx.state.motion ? '#ef4444' : '#3b1d1d'); },
  start(ctx) { ctx.apply(); },
  apply(ctx) { ctx.digital('OUT', Boolean(ctx.state.motion)); },
  example: (p, board) => board === 'esp32'
    ? idf(`    oc_input(${p('OUT')}, false);`, `        if (oc_read(${p('OUT')})) printf("Движение!\\n");\n        oc_delay(300);`)
    : ino(`  pinMode(${p('OUT')}, INPUT);\n  Serial.begin(9600);`, `  if (digitalRead(${p('OUT')}) == HIGH) Serial.println("Движение!");\n  delay(300);`),
});

/* ---------- ИК-датчик препятствия ---------- */
part('obstacle', {
  title: 'ИК-датчик препятствия', category: 'Датчики', w: 110, h: 90,
  pins: pinsAt([{id: 'OUT', label: 'OUT', need: 'in', x: 50}], 88),
  art: () => `<rect x="20" y="20" width="84" height="44" rx="4" fill="#1e3a8a" stroke="#60a5fa"/>
    <circle cx="10" cy="30" r="8" fill="#111827" stroke="#6b7280"/><circle cx="10" cy="52" r="8" fill="#e5e7eb" stroke="#6b7280"/>
    <path d="M18 30h4M18 52h4" stroke="#9ca3af" stroke-width="3"/><circle data-r="led" cx="92" cy="30" r="4" fill="#1f2937"/>
    ${text(62, 46, 'FC-51', 8, '#bfdbfe')}${leg(50, 64, 88)}
    <g data-ctl="toggle" style="cursor:pointer"><rect x="56" y="4" width="50" height="14" rx="7" fill="#0f172a" stroke="#64748b"/>
    <text data-r="label" x="81" y="14" font-size="7.5" fill="#e2e8f0" text-anchor="middle" font-family="system-ui">✋ поставить</text></g>
    <rect data-r="hand" x="-30" y="22" width="18" height="40" rx="6" fill="#f2c8a0" opacity="0"/>`,
  bind(ctx) {
    ctx.q('toggle').addEventListener('click', () => { ctx.state.blocked = !ctx.state.blocked; ctx.render(); ctx.apply(); });
    ctx.render();
  },
  render(ctx) {
    const b = Boolean(ctx.state.blocked);
    ctx.q('led').setAttribute('fill', b ? '#22c55e' : '#1f2937');
    ctx.q('hand').setAttribute('opacity', b ? 0.9 : 0);
    ctx.q('label').textContent = b ? '✋ убрать' : '✋ поставить';
  },
  start(ctx) { ctx.apply(); },
  apply(ctx) { ctx.digital('OUT', !ctx.state.blocked); },  // препятствие — низкий уровень
  example: (p, board) => board === 'esp32'
    ? idf(`    oc_input(${p('OUT')}, false);`, `        printf(oc_read(${p('OUT')}) == 0 ? "Препятствие!\\n" : "Путь свободен\\n");\n        oc_delay(300);`)
    : ino(`  pinMode(${p('OUT')}, INPUT);\n  Serial.begin(9600);`, `  Serial.println(digitalRead(${p('OUT')}) == LOW ? "Препятствие!" : "Путь свободен");\n  delay(300);`),
});

/* ---------- Ультразвуковой дальномер HC-SR04 ---------- */
part('ultrasonic', {
  title: 'Дальномер HC-SR04', category: 'Датчики', w: 150, h: 100, esp32: 'helper',
  pins: pinsAt([{id: 'TRIG', label: 'TRIG', need: 'out', x: 62}, {id: 'ECHO', label: 'ECHO', need: 'in', x: 88}], 98),
  art: () => `<rect x="4" y="18" width="142" height="54" rx="4" fill="#1e40af" stroke="#60a5fa"/>
    ${[38, 112].map(x => `<circle cx="${x}" cy="45" r="24" fill="#cbd5e1" stroke="#64748b" stroke-width="2"/><circle cx="${x}" cy="45" r="16" fill="#334155"/>`).join('')}
    ${text(75, 30, 'HC-SR04', 7, '#dbeafe')}${leg(62, 72, 98)}${leg(88, 72, 98)}
    <text data-r="value" x="75" y="12" font-size="9" fill="#93c5fd" text-anchor="middle" font-family="monospace"></text>`,
  controls: () => slider('range', 2, 400),
  bind(ctx) { bindSlider(ctx, 'range', 'cm', 50, v => readout(ctx, `${v} см`)); },
  start(ctx) {
    if (ctx.io.kind === 'avr') {
      if (ctx.pin('TRIG') && ctx.pin('ECHO')) ctx.cleanup(attachUltrasonic(ctx.io, ctx.pin('TRIG'), ctx.pin('ECHO'), () => ctx.state.cm));
    } else ctx.apply();
  },
  apply(ctx) {
    if (ctx.io?.kind === 'esp32' && ctx.pin('TRIG')) ctx.io.value(`DIST${ctx.pin('TRIG')}`, `@IN DIST ${ctx.pinCode('TRIG')} ${ctx.state.cm * 10}`);
  },
  example: (p, board) => board === 'esp32'
    ? idf('', `        printf("Расстояние: %.1f см\\n", oc_distance_cm(${p('TRIG')}, ${p('ECHO')}));\n        oc_delay(300);`)
    : ino(`  pinMode(${p('TRIG')}, OUTPUT);\n  pinMode(${p('ECHO')}, INPUT);\n  Serial.begin(9600);`,
      `  digitalWrite(${p('TRIG')}, LOW);\n  delayMicroseconds(2);\n  digitalWrite(${p('TRIG')}, HIGH);  // импульс 10 мкс\n  delayMicroseconds(10);\n  digitalWrite(${p('TRIG')}, LOW);\n  long us = pulseIn(${p('ECHO')}, HIGH, 30000);\n  Serial.print(us / 58);  // 58 мкс на сантиметр\n  Serial.println(" см");\n  delay(200);`),
});

/* ---------- DHT22: температура и влажность ---------- */
part('dht22', {
  title: 'DHT22 (температура, влажность)', category: 'Датчики', w: 80, h: 112, esp32: 'helper',
  pins: pinsAt([{id: 'DATA', label: 'DATA', need: 'in', x: 40}], 110),
  art: () => `<rect x="14" y="4" width="52" height="74" rx="4" fill="#f8fafc" stroke="#94a3b8"/>
    ${[0, 1, 2, 3, 4, 5].map(i => `<rect x="22" y="${12 + i * 9}" width="36" height="5" rx="2" fill="#cbd5e1"/>`).join('')}
    ${leg(26, 78, 100, '#64748b')}${leg(40, 78, 110)}${leg(54, 78, 100, '#64748b')}
    <text data-r="value" x="40" y="92" font-size="7.5" fill="#cbd5e1" text-anchor="middle" font-family="monospace"></text>`,
  controls: () => `<label>🌡 ${slider('temp', -40, 80)}</label><label>💧 ${slider('hum', 0, 100)}</label>`,
  bind(ctx) {
    const show = () => readout(ctx, `${ctx.state.t ?? 24}° ${ctx.state.h ?? 45}%`);
    bindSlider(ctx, 'temp', 't', 24, show);
    bindSlider(ctx, 'hum', 'h', 45, show);
  },
  start(ctx) {
    if (ctx.io.kind === 'avr') {
      if (ctx.pin('DATA')) ctx.cleanup(attachDht(ctx.io, ctx.pin('DATA'), () => ({temperature: ctx.state.t, humidity: ctx.state.h})));
    } else ctx.apply();
  },
  apply(ctx) {
    if (ctx.io?.kind === 'esp32' && ctx.pin('DATA')) {
      ctx.io.value(`DHT${ctx.pin('DATA')}`, `@IN DHT ${ctx.pinCode('DATA')} ${Math.round(ctx.state.t * 10)} ${Math.round(ctx.state.h * 10)}`);
    }
  },
  example: (p, board) => board === 'esp32'
    ? idf('    float t, h;', `        if (oc_dht_read(${p('DATA')}, &t, &h)) printf("%.1f °C, %.1f %%\\n", t, h);\n        oc_delay(2000);`)
    : ino('  Serial.begin(9600);\n  dht.begin();', '  delay(2000);  // DHT22 меряет раз в 2 секунды\n  Serial.print(dht.readTemperature());\n  Serial.print(" °C, ");\n  Serial.print(dht.readHumidity());\n  Serial.println(" %");',
      `#include <DHT.h>\nDHT dht(${p('DATA')}, DHT22);`),
});

/* ---------- Клавиатура 4×4 ---------- */
const KEYPAD = [['1', '2', '3', 'A'], ['4', '5', '6', 'B'], ['7', '8', '9', 'C'], ['*', '0', '#', 'D']];
const KP_ROWS = ['R1', 'R2', 'R3', 'R4'], KP_COLS = ['C1', 'C2', 'C3', 'C4'];
part('keypad', {
  title: 'Клавиатура 4×4', category: 'Кнопки и ручки', w: 150, h: 196,
  pins: pinsAt([...KP_ROWS, ...KP_COLS].map((id, i) => ({id, label: id, need: i < 4 ? 'out' : 'in', x: 19 + i * 16})), 194),
  art: () => `<rect x="4" y="4" width="142" height="156" rx="6" fill="#1f2937" stroke="#4b5563"/>
    ${KEYPAD.map((row, r) => row.map((k, c) => `<g data-ctl="key" data-k="${r},${c}" style="cursor:pointer">
      <rect data-r="k${r}${c}" x="${12 + c * 33}" y="${12 + r * 36}" width="28" height="30" rx="5" fill="${'ABCD'.includes(k) ? '#dc2626' : k === '*' || k === '#' ? '#2563eb' : '#e5e7eb'}" stroke="#111"/>
      ${text(26 + c * 33, 32 + r * 36, k, 13, 'ABCD*#'.includes(k) ? '#fff' : '#111827')}</g>`).join('')).join('')}
    ${[...KP_ROWS, ...KP_COLS].map((_, i) => leg(19 + i * 16, 160, 194)).join('')}`,
  bind(ctx) {
    for (const key of ctx.el.querySelectorAll('[data-ctl="key"]')) {
      const [r, c] = key.dataset.k.split(',').map(Number);
      ctx.press(key, pressed => {
        ctx.q(`k${r}${c}`).style.filter = pressed ? 'brightness(.6)' : '';
        const row = ctx.pin(KP_ROWS[r]), col = ctx.pin(KP_COLS[c]);
        if (ctx.io && row && col) ctx.io.connect(row, col, pressed);
      });
    }
  },
  example: (p, board) => board === 'esp32'
    ? idf('    for (int i = 0; i < 4; i++) { oc_output(rows[i]); oc_write(rows[i], 1); oc_input(cols[i], true); }',
      '        for (int r = 0; r < 4; r++) {  // опрос: строку в LOW, читаем столбцы\n            oc_write(rows[r], 0);\n            for (int c = 0; c < 4; c++) if (oc_read(cols[c]) == 0) {\n                printf("Клавиша %c\\n", keys[r][c]);\n                while (oc_read(cols[c]) == 0) oc_delay(10);\n            }\n            oc_write(rows[r], 1);\n        }\n        oc_delay(20);',
      `const int rows[4] = {${KP_ROWS.map(p).join(', ')}};\nconst int cols[4] = {${KP_COLS.map(p).join(', ')}};\nconst char keys[4][4] = {{'1','2','3','A'}, {'4','5','6','B'}, {'7','8','9','C'}, {'*','0','#','D'}};\n`)
    : ino('  Serial.begin(9600);', '  char key = keypad.getKey();\n  if (key) Serial.println(key);',
      `#include <Keypad.h>\nchar keys[4][4] = {{'1','2','3','A'}, {'4','5','6','B'}, {'7','8','9','C'}, {'*','0','#','D'}};\nbyte rowPins[4] = {${KP_ROWS.map(p).join(', ')}};\nbyte colPins[4] = {${KP_COLS.map(p).join(', ')}};\nKeypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, 4, 4);`),
});

/* ---------- ИК-приёмник и пульт ---------- */
part('ir', {
  title: 'ИК-приёмник и пульт', category: 'Пульты', w: 230, h: 214, esp32: 'helper',
  pins: pinsAt([{id: 'OUT', label: 'OUT', need: 'in', x: 30}], 212),
  art: () => `<rect x="12" y="150" width="36" height="28" rx="3" fill="#111827"/><circle cx="30" cy="150" r="13" fill="#1f2937" stroke="#4b5563"/>
    <circle data-r="rx" cx="30" cy="150" r="5" fill="#374151"/>${leg(30, 178, 212)}${leg(20, 178, 200, '#64748b')}${leg(40, 178, 200, '#64748b')}
    ${text(30, 136, 'VS1838B', 7, '#94a3b8')}
    <path data-r="beam" d="M100 112L42 146" stroke="#f472b6" stroke-width="3" stroke-dasharray="4 4" opacity="0"/>
    <rect x="96" y="4" width="128" height="206" rx="14" fill="#18181b" stroke="#3f3f46"/>
    <circle data-r="tx" cx="160" cy="14" r="4" fill="#3f3f46"/>
    ${NEC_KEYS.map(([label, cmd], i) => {
      const x = 106 + (i % 3) * 38, y = 24 + Math.floor(i / 3) * 26;
      return `<g data-ctl="ir" data-cmd="${cmd}" style="cursor:pointer"><rect x="${x}" y="${y}" width="32" height="20" rx="8" fill="${i < 3 ? '#b91c1c' : '#27272a'}" stroke="#52525b"/>${text(x + 16, y + 14, label, 9, '#fafafa')}</g>`;
    }).join('')}`,
  bind(ctx) {
    for (const key of ctx.el.querySelectorAll('[data-ctl="ir"]')) {
      key.addEventListener('click', () => {
        const cmd = Number(key.dataset.cmd);
        ctx.flash(['tx', 'rx'], '#f472b6', 'beam');
        if (!ctx.io || !ctx.pin('OUT')) return;
        if (ctx.io.kind === 'avr') ctx.io.wave(ctx.pin('OUT'), necWave(0x00, cmd), 1);
        else ctx.io.event('IR', cmd);
      });
    }
  },
  start(ctx) { if (ctx.io.kind === 'avr') ctx.digital('OUT', 1); },
  example: (p, board) => board === 'esp32'
    ? idf('    uint8_t cmd;', '        if (oc_ir_read(&cmd)) printf("Кнопка пульта: 0x%02X\\n", cmd);\n        oc_delay(50);')
    : ino(`  Serial.begin(9600);\n  IrReceiver.begin(${p('OUT')}, ENABLE_LED_FEEDBACK);`,
      '  if (IrReceiver.decode()) {\n    Serial.print("Кнопка пульта: 0x");\n    Serial.println(IrReceiver.decodedIRData.command, HEX);\n    IrReceiver.resume();\n  }',
      '#include <IRremote.hpp>  // коды: CH- 0x45, CH 0x46, CH+ 0x47, 1 0xC, 2 0x18, 3 0x5E …'),
});

/* ---------- Радиопульт 433 МГц ---------- */
part('rf', {
  title: 'Радиопульт 433 МГц', category: 'Пульты', w: 200, h: 130, esp32: 'helper',
  pins: pinsAt([{id: 'DATA', label: 'DATA', need: 'int', x: 40}], 128),
  art: () => `<rect x="6" y="60" width="72" height="40" rx="3" fill="#166534" stroke="#4ade80"/>
    <path d="M70 60V18" stroke="#d4d4d8" stroke-width="2"/><path d="M66 22l4-4 4 4" stroke="#d4d4d8" fill="none"/>
    ${text(36, 84, 'RX 433', 9, '#dcfce7')}<circle data-r="rx" cx="16" cy="70" r="3.5" fill="#14532d"/>${leg(40, 100, 128)}
    <path data-r="beam" d="M118 54Q96 30 74 26" stroke="#38bdf8" stroke-width="3" stroke-dasharray="4 4" fill="none" opacity="0"/>
    <path d="M120 20h60q14 0 14 14v66q0 22-22 22h-44q-22 0-22-22V34q0-14 14-14z" fill="#27272a" stroke="#52525b"/>
    <circle data-r="tx" cx="150" cy="30" r="3.5" fill="#3f3f46"/>
    ${RF_KEYS.map(([label, code], i) => {
      const x = 126 + (i % 2) * 34, y = 42 + Math.floor(i / 2) * 36;
      return `<g data-ctl="rf" data-code="${code}" style="cursor:pointer"><circle cx="${x + 12}" cy="${y + 12}" r="13" fill="#3f3f46" stroke="#71717a"/>${text(x + 12, y + 16, label, 11, '#fafafa')}</g>`;
    }).join('')}`,
  bind(ctx) {
    for (const key of ctx.el.querySelectorAll('[data-ctl="rf"]')) {
      key.addEventListener('click', () => {
        const code = Number(key.dataset.code);
        ctx.flash(['tx', 'rx'], '#38bdf8', 'beam');
        if (!ctx.io || !ctx.pin('DATA')) return;
        if (ctx.io.kind === 'avr') ctx.io.wave(ctx.pin('DATA'), rcSwitchWave(code), 0);
        else ctx.io.event('RF', code);
      });
    }
  },
  start(ctx) { if (ctx.io.kind === 'avr') ctx.digital('DATA', 0); },
  example: (p, board) => board === 'esp32'
    ? idf('    uint32_t code;', '        if (oc_rf_read(&code)) printf("Радиопульт: %lu\\n", (unsigned long)code);\n        oc_delay(50);')
    : ino(`  Serial.begin(9600);\n  radio.enableReceive(digitalPinToInterrupt(${p('DATA')}));`,
      '  if (radio.available()) {\n    Serial.print("Радиопульт: ");\n    Serial.println(radio.getReceivedValue());  // A 5592332, B 5592512, C 5592323, D 5592368\n    radio.resetAvailable();\n  }',
      '#include <RCSwitch.h>\nRCSwitch radio;'),
});

export const PART_LIST = Object.values(PARTS);
