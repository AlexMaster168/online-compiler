/* Страница Arduino Uno: скетч собирается на сервере (arduino-cli), прошивка исполняется в браузере на avr8js,
   а детали на схеме подключены к ножкам эмулятора через AvrBus. */
import {CPU, avrInstruction, AVRTimer, timer0Config, timer1Config, timer2Config,
  AVRIOPort, portBConfig, portCConfig, portDConfig, AVRUSART, usart0Config,
  AVRADC, adcConfig, AVRTWI, twiConfig} from 'https://cdn.jsdelivr.net/npm/avr8js@0.21.0/+esm';
import {Circuit} from './circuit/editor.js';
import {AvrBus} from './circuit/avr-bus.js';

const $ = id => document.getElementById(id);
const store = {
  get: key => { try { return localStorage.getItem(key); } catch { return null; } },
  set: (key, value) => { try { localStorage.setItem(key, value); } catch { /* приватный режим */ } },
};

/* Примеры: скетч + схема к нему */
const led = (id, pin, x, y, color = 'red') => ({id, type: 'led', x, y, pins: {A: pin}, props: {color}});
const EXAMPLES = {
  blink: {
    title: 'Мигающий светодиод',
    code: 'void setup() {\n  pinMode(13, OUTPUT);\n  Serial.begin(9600);\n}\n\nvoid loop() {\n  digitalWrite(13, HIGH);\n  Serial.println("LED ON");\n  delay(500);\n  digitalWrite(13, LOW);\n  Serial.println("LED OFF");\n  delay(500);\n}\n',
    parts: [led('led1', 'D13', 200, 120)],
  },
  button: {
    title: 'Кнопка и светодиод',
    code: 'void setup() {\n  pinMode(13, OUTPUT);\n  pinMode(2, INPUT_PULLUP);  // кнопка замыкает D2 на GND\n}\n\nvoid loop() {\n  digitalWrite(13, digitalRead(2) == LOW);\n}\n',
    parts: [led('led1', 'D13', 180, 120, 'green'), {id: 'btn1', type: 'button', x: 360, y: 110, pins: {OUT: 'D2'}, props: {}}],
  },
  analog: {
    title: 'Потенциометр и яркость',
    code: 'void setup() {\n  Serial.begin(9600);\n  pinMode(9, OUTPUT);\n}\n\nvoid loop() {\n  int value = analogRead(A0);       // 0…1023\n  analogWrite(9, value / 4);        // ШИМ 0…255\n  Serial.println(value);\n  delay(100);\n}\n',
    parts: [{id: 'pot1', type: 'pot', x: 360, y: 560, pins: {SIG: 'A0'}, props: {}}, led('led1', 'D9', 260, 120, 'yellow')],
  },
  servo: {
    title: 'Сервопривод',
    code: '#include <Servo.h>\nServo motor;\n\nvoid setup() {\n  motor.attach(9);\n}\n\nvoid loop() {\n  motor.write(0);\n  delay(1000);\n  motor.write(90);\n  delay(1000);\n  motor.write(180);\n  delay(1000);\n}\n',
    parts: [{id: 'servo1', type: 'servo', x: 240, y: 70, pins: {SIG: 'D9'}, props: {}}],
  },
  lcd: {
    title: 'LCD 16×2',
    code: '#include <LiquidCrystal.h>\nLiquidCrystal lcd(12, 11, 5, 4, 3, 2);\n\nvoid setup() {\n  lcd.begin(16, 2);\n  lcd.print("Hello Arduino!");\n}\n\nvoid loop() {\n  lcd.setCursor(0, 1);\n  lcd.print(millis() / 1000);\n  delay(200);\n}\n',
    parts: [{id: 'lcd1', type: 'lcd', x: 170, y: 90, pins: {RS: 'D12', E: 'D11', D4: 'D5', D5: 'D4', D6: 'D3', D7: 'D2'}, props: {}}],
  },
  traffic: {
    title: 'Светофор с пищалкой',
    code: 'const int RED = 4, YELLOW = 3, GREEN = 2, BUZZER = 8;\n\nvoid setup() {\n  for (int pin = 2; pin <= 4; pin++) pinMode(pin, OUTPUT);\n}\n\nvoid light(int pin, int ms) {\n  digitalWrite(pin, HIGH);\n  delay(ms);\n  digitalWrite(pin, LOW);\n}\n\nvoid loop() {\n  light(RED, 2000);\n  light(YELLOW, 700);\n  for (int i = 0; i < 4; i++) {  // зелёный — пищим для пешеходов\n    digitalWrite(GREEN, HIGH);\n    tone(BUZZER, 1200, 150);\n    delay(500);\n  }\n  digitalWrite(GREEN, LOW);\n}\n',
    parts: [led('red', 'D4', 360, 130), led('yellow', 'D3', 420, 130, 'yellow'), led('green', 'D2', 480, 130, 'green'),
      {id: 'bz', type: 'buzzer', x: 240, y: 120, pins: {SIG: 'D8'}, props: {kind: 'passive'}}],
  },
  neopixel: {
    title: 'NeoPixel: радуга на кольце',
    code: '#include <Adafruit_NeoPixel.h>\nAdafruit_NeoPixel ring(16, 6, NEO_GRB + NEO_KHZ800);\n\nvoid setup() {\n  ring.begin();\n  ring.setBrightness(60);\n}\n\nvoid loop() {\n  static uint16_t hue = 0;\n  for (int i = 0; i < 16; i++) ring.setPixelColor(i, ring.ColorHSV(hue + i * 4096));\n  ring.show();\n  hue += 1024;\n  delay(30);\n}\n',
    parts: [{id: 'ring', type: 'neopixel', x: 260, y: 40, pins: {DIN: 'D6'}, props: {layout: 'ring'}}],
  },
  remote: {
    title: 'ИК-пульт управляет светодиодами',
    code: '#include <IRremote.hpp>\n\nvoid setup() {\n  Serial.begin(9600);\n  IrReceiver.begin(11);\n  for (int pin = 2; pin <= 4; pin++) pinMode(pin, OUTPUT);\n}\n\nvoid loop() {\n  if (!IrReceiver.decode()) return;\n  int cmd = IrReceiver.decodedIRData.command;\n  Serial.print("Кнопка 0x");\n  Serial.println(cmd, HEX);\n  if (cmd == 0x0C) digitalWrite(2, !digitalRead(2));  // «1»\n  if (cmd == 0x18) digitalWrite(3, !digitalRead(3));  // «2»\n  if (cmd == 0x5E) digitalWrite(4, !digitalRead(4));  // «3»\n  IrReceiver.resume();\n}\n',
    parts: [{id: 'ir1', type: 'ir', x: 470, y: 10, pins: {OUT: 'D11'}, props: {}},
      led('l1', 'D2', 240, 130), led('l2', 'D3', 300, 130, 'green'), led('l3', 'D4', 360, 130, 'blue')],
  },
  parking: {
    title: 'Парктроник: дальномер + пищалка',
    code: 'const int TRIG = 9, ECHO = 10, BUZZER = 8;\n\nvoid setup() {\n  pinMode(TRIG, OUTPUT);\n  pinMode(ECHO, INPUT);\n  Serial.begin(9600);\n}\n\nvoid loop() {\n  digitalWrite(TRIG, HIGH);\n  delayMicroseconds(10);\n  digitalWrite(TRIG, LOW);\n  int cm = pulseIn(ECHO, HIGH, 30000) / 58;\n  Serial.print(cm);\n  Serial.println(" см");\n  if (cm > 0 && cm < 100) {  // чем ближе, тем чаще пищит\n    tone(BUZZER, 1500, 60);\n    delay(cm * 6);\n  } else {\n    delay(200);\n  }\n}\n',
    parts: [{id: 'us', type: 'ultrasonic', x: 300, y: 70, pins: {TRIG: 'D9', ECHO: 'D10'}, props: {}, state: {cm: 40}},
      {id: 'bz', type: 'buzzer', x: 200, y: 110, pins: {SIG: 'D8'}, props: {kind: 'passive'}}],
  },
  weather: {
    title: 'Метеостанция: DHT22 + OLED',
    code: '#include <DHT.h>\n#include <Wire.h>\n#include <Adafruit_GFX.h>\n#include <Adafruit_SSD1306.h>\n\nDHT dht(4, DHT22);\nAdafruit_SSD1306 display(128, 64, &Wire, -1);\n\nvoid setup() {\n  dht.begin();\n  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);\n  display.setTextColor(SSD1306_WHITE);\n}\n\nvoid loop() {\n  float t = dht.readTemperature(), h = dht.readHumidity();\n  display.clearDisplay();\n  display.setTextSize(2);\n  display.setCursor(0, 8);\n  display.print(t, 1);\n  display.print(" C");\n  display.setCursor(0, 36);\n  display.print(h, 0);\n  display.print(" %");\n  display.display();\n  delay(2000);\n}\n',
    parts: [{id: 'dht', type: 'dht22', x: 240, y: 70, pins: {DATA: 'D4'}, props: {}},
      {id: 'oled', type: 'oled', x: 330, y: 560, pins: {SDA: 'A4', SCL: 'A5'}, props: {}}],
  },
};

let cpu, usart, running = false, timer, bus = null;
let project = JSON.parse($('project-data').textContent);

$('example').add(new Option('— выбери пример —', ''));
for (const [value, ex] of Object.entries(EXAMPLES)) $('example').add(new Option(ex.title, value));

const circuit = new Circuit($('circuit'), {
  board: 'uno',
  onChange: diagram => store.set('oc:arduino:diagram', JSON.stringify(diagram)),
  onExample: code => {
    if ($('code').value.trim() && $('code').value !== code && !confirm('Заменить текущий скетч примером для этой детали?')) return;
    $('code').value = code;
    saveDraft();
  },
});

/* ---------- черновик и проект ---------- */
const diagramOf = p => {
  const file = p?.files?.find(f => f.name === 'diagram.json');
  try { return file ? JSON.parse(file.content) : null; } catch { return null; }
};
const savedDiagram = () => { try { return JSON.parse(store.get('oc:arduino:diagram')); } catch { return null; } };
function saveDraft() { store.set('oc:arduino:code', $('code').value); }

$('title').value = project?.title || '';
$('code').value = project?.code || store.get('oc:arduino:code') || EXAMPLES.blink.code;
circuit.load(diagramOf(project) || savedDiagram() || {parts: EXAMPLES.blink.parts});
$('code').addEventListener('input', saveDraft);

$('example').value = '';
$('example').addEventListener('change', () => {
  const ex = EXAMPLES[$('example').value];
  if (!ex) return;
  if ($('code').value.trim() && !confirm('Заменить скетч и схему примером?')) { $('example').value = ''; return; }
  stop();
  $('code').value = ex.code;
  circuit.load({parts: ex.parts});
  saveDraft();
  store.set('oc:arduino:diagram', JSON.stringify(circuit.toJSON()));
  $('status').textContent = `Пример «${ex.title}» — нажми «Собрать и запустить»`;
  $('example').value = '';
});

const csrf = () => document.cookie.split('; ').find(x => x.startsWith('csrftoken='))?.split('=')[1] || '';
$('save').addEventListener('click', async () => {
  $('save').disabled = true;
  try {
    const response = await fetch('/api/arduino/save/', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf()},
      body: JSON.stringify({code: $('code').value, title: $('title').value, diagram: JSON.stringify(circuit.toJSON()),
        id: project?.is_owner ? project.id : ''}),
    });
    const data = await response.json();
    if (!response.ok) throw Error(data.error);
    project = data;
    history.replaceState(null, '', data.url);
    $('status').textContent = `Проект сохранён: ${location.href}`;
  } catch (error) {
    $('status').textContent = error.message;
  } finally {
    $('save').disabled = false;
  }
});

/* ---------- эмуляция ---------- */
function stop() {
  running = false;
  clearTimeout(timer);
  bus?.stop();
  bus = null;
  circuit.stop();
  $('stop').disabled = true;
  $('run').disabled = false;
}
$('stop').addEventListener('click', () => { stop(); $('status').textContent = 'Остановлен'; });

function loadHex(hex) {
  const memory = new Uint8Array(32768);
  let base = 0;
  for (const line of hex.trim().split(/\r?\n/)) {
    const bytes = line.slice(1).match(/../g).map(x => parseInt(x, 16));
    if (line[0] !== ':' || bytes.reduce((a, b) => a + b, 0) % 256) throw Error('Повреждён HEX');
    const [length, hi, lo, type] = bytes;
    if (type === 4) base = (bytes[4] * 256 + bytes[5]) * 65536;
    if (type === 0) memory.set(bytes.slice(4, 4 + length), base + hi * 256 + lo);
  }
  return new Uint16Array(memory.buffer);
}

/* Порциями по ~10 мс эмулируемого времени; если браузер не успевает, эмуляция просто идёт медленнее */
function execute() {
  if (!running) return;
  const until = cpu.cycles + 160000;
  while (cpu.cycles < until) { avrInstruction(cpu); cpu.tick(); }
  $('clock').textContent = `${(cpu.cycles / 16e6).toFixed(2)} с`;
  timer = setTimeout(execute, 0);
}

function start(hex) {
  cpu = new CPU(loadHex(hex));
  for (const config of [timer0Config, timer1Config, timer2Config]) new AVRTimer(cpu, config);
  const ports = {B: new AVRIOPort(cpu, portBConfig), C: new AVRIOPort(cpu, portCConfig), D: new AVRIOPort(cpu, portDConfig)};
  const adc = new AVRADC(cpu, adcConfig);
  const twi = new AVRTWI(cpu, twiConfig, 16e6);
  usart = new AVRUSART(cpu, usart0Config, 16e6);
  const utf8 = new TextDecoder();  // Serial.print("см") — это UTF-8 по байту за раз
  usart.onByteTransmit = byte => {
    const text = utf8.decode(new Uint8Array([byte]), {stream: true});
    if (!text) return;
    $('serial').textContent = ($('serial').textContent + text).slice(-24000);
    $('serial').scrollTop = $('serial').scrollHeight;
  };
  bus = new AvrBus({cpu, ports, adc, twi, configs: {B: portBConfig, C: portCConfig, D: portDConfig}});
  window.ocArduino = {bus, cpu};  // для e2e-тестов
  circuit.run(bus);
  running = true;
  $('stop').disabled = false;
  execute();
}

$('run').addEventListener('click', async () => {
  stop();
  circuit.audio();  // звук разрешается только из клика
  $('run').disabled = true;
  $('status').textContent = 'Собираю прошивку…';
  $('serial').textContent = '';
  $('log').textContent = '';
  try {
    const response = await fetch('/api/arduino/compile/', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf()},
      body: JSON.stringify({code: $('code').value}),
    });
    const data = await response.json();
    $('log').textContent = data.log || '';
    if (!response.ok) throw Error(data.error || 'Ошибка сборки');
    start(data.hex);
    $('status').textContent = 'Прошивка работает';
  } catch (error) {
    stop();
    $('status').textContent = error.message;
  }
});

$('send').addEventListener('submit', event => {
  event.preventDefault();
  if (!running) return;
  const bytes = new TextEncoder().encode(`${$('input').value}\n`);
  let i = 0;
  const send = () => {
    if (!running || i === bytes.length) return;
    if (usart.writeByte(bytes[i])) i++;
    setTimeout(send, 2);
  };
  send();
  $('input').value = '';
});

$('download').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([$('code').value], {type: 'text/plain'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'sketch.ino';
  link.click();
  URL.revokeObjectURL(url);
});
window.addEventListener('pagehide', stop);
window.ocCircuit = circuit;
