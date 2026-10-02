/* Протоколы деталей без DOM: их же гоняют тесты в node на настоящих прошивках. */

/* ---------- Символьный LCD на HD44780 (16×2) ---------- */
export class Hd44780 {
  constructor(cols = 16, rows = 2) {
    this.cols = cols; this.rows = rows;
    this.reset();
  }
  reset() {
    this.ddram = new Array(128).fill(32);
    this.address = 0;
    this.cgMode = false;
    this.increment = true;
    this.displayOn = true;
    this.fourBit = false;
    this.pending = null;  // старший полубайт в 4-битном режиме
    this.backlight = true;
    this.version = 0;
  }
  /* 4-битная шина: после инициализации (0x3, 0x3, 0x3, 0x2) байты идут двумя полубайтами */
  nibble(rs, half) {
    if (!this.fourBit) {
      if (half === 0x2) this.fourBit = true;
      return;
    }
    if (this.pending === null) { this.pending = half; return; }
    const value = (this.pending << 4) | half;
    this.pending = null;
    this.byte(rs, value);
  }
  byte(rs, value) {
    this.version++;
    if (rs) {
      if (this.cgMode) return;  // свои символы не рисуем, только не портим текст
      this.ddram[this.address & 0x7f] = value;
      this.address = (this.address + (this.increment ? 1 : 127)) & 0x7f;
      return;
    }
    if (value & 0x80) { this.address = value & 0x7f; this.cgMode = false; }
    else if (value & 0x40) this.cgMode = true;
    else if (value & 0x20) { if (!(value & 0x10)) this.fourBit = true; }
    else if (value & 0x08) this.displayOn = Boolean(value & 0x04);
    else if (value & 0x04) this.increment = Boolean(value & 0x02);
    else if (value & 0x02) { this.address = 0; this.cgMode = false; }
    else if (value & 0x01) { this.ddram.fill(32); this.address = 0; this.cgMode = false; }
  }
  lines() {
    const out = [];
    for (let row = 0; row < this.rows; row++) {
      const base = [0x00, 0x40, 0x14, 0x54][row];
      let line = '';
      for (let col = 0; col < this.cols; col++) {
        const code = this.ddram[(base + col) & 0x7f];
        line += code < 8 ? '█' : code >= 32 && code < 127 ? String.fromCharCode(code) : code === 0xdf ? '°' : ' ';
      }
      out.push(this.displayOn ? line : ' '.repeat(this.cols));
    }
    return out;
  }
}

/* LCD по параллельной шине: на спаде E читаем D4–D7 и RS */
export function attachLcdParallel(io, pins, lcd) {
  const level = id => io.read(id).level === 1 ? 1 : 0;
  return io.onEdge(pins.E, (value) => {
    if (value !== 0) return;
    const half = level(pins.D4) | (level(pins.D5) << 1) | (level(pins.D6) << 2) | (level(pins.D7) << 3);
    lcd.nibble(level(pins.RS), half);
  });
}

/* LCD с переходником PCF8574 (LiquidCrystal_I2C): P0=RS, P2=E, P3=подсветка, P4–P7=D4–D7 */
export function pcf8574Lcd(lcd) {
  let last = 0;
  return {
    write(byte) {
      lcd.backlight = Boolean(byte & 0x08);
      if ((last & 0x04) && !(byte & 0x04)) lcd.nibble(byte & 0x01, byte >> 4);
      last = byte;
    },
    read: () => last,
  };
}

/* ---------- OLED SSD1306 128×64 по I2C ---------- */
const SSD_ARGS = {0x20: 1, 0x21: 2, 0x22: 2, 0x81: 1, 0x8d: 1, 0xa8: 1, 0xd3: 1, 0xd5: 1, 0xd9: 1, 0xda: 1, 0xdb: 1,
  0xa3: 2, 0x26: 6, 0x27: 6, 0x29: 5, 0x2a: 5};

export class Ssd1306 {
  constructor() {
    this.ram = new Uint8Array(128 * 8);
    this.mode = 2; this.col = 0; this.page = 0;
    this.colStart = 0; this.colEnd = 127; this.pageStart = 0; this.pageEnd = 7;
    this.on = false; this.invert = false; this.flipX = false; this.flipY = false;
    this.state = 'control'; this.single = false; this.cmd = []; this.version = 0;
  }
  start() { this.state = 'control'; }
  stop() {}
  read() { return 0; }
  write(byte) {
    if (this.state === 'control') {
      this.single = Boolean(byte & 0x80);
      this.state = byte & 0x40 ? 'data' : 'cmd';
      return;
    }
    if (this.state === 'data') this.data(byte); else this.command(byte);
    if (this.single) this.state = 'control';
  }
  command(byte) {
    this.cmd.push(byte);
    const need = SSD_ARGS[this.cmd[0]] || 0;
    if (this.cmd.length <= need) return;
    const [c, a, b] = this.cmd;
    this.cmd = [];
    this.version++;
    if (c === 0x20) this.mode = a & 3;
    else if (c === 0x21) { this.colStart = a & 127; this.colEnd = b & 127; this.col = this.colStart; }
    else if (c === 0x22) { this.pageStart = a & 7; this.pageEnd = b & 7; this.page = this.pageStart; }
    else if (c >= 0xb0 && c <= 0xb7) this.page = c & 7;
    else if (c <= 0x0f) this.col = (this.col & 0xf0) | c;
    else if (c >= 0x10 && c <= 0x1f) this.col = (this.col & 0x0f) | ((c & 0x0f) << 4);
    else if (c === 0xae || c === 0xaf) this.on = c === 0xaf;
    else if (c === 0xa6 || c === 0xa7) this.invert = c === 0xa7;
    else if (c === 0xa0 || c === 0xa1) this.flipX = c === 0xa0;
    else if (c === 0xc0 || c === 0xc8) this.flipY = c === 0xc0;
  }
  data(byte) {
    this.ram[this.page * 128 + (this.col & 127)] = byte;
    this.version++;
    if (this.mode === 0) {
      if (++this.col > this.colEnd) {
        this.col = this.colStart;
        if (++this.page > this.pageEnd) this.page = this.pageStart;
      }
    } else if (this.mode === 1) {
      if (++this.page > this.pageEnd) {
        this.page = this.pageStart;
        if (++this.col > this.colEnd) this.col = this.colStart;
      }
    } else {
      this.col = (this.col + 1) & 127;
    }
  }
  pixel(x, y) {
    const cx = this.flipX ? 127 - x : x, cy = this.flipY ? 63 - y : y;
    const bit = (this.ram[(cy >> 3) * 128 + cx] >> (cy & 7)) & 1;
    return this.invert ? bit ^ 1 : bit;
  }
}

/* ---------- Адресные светодиоды WS2812 (NeoPixel) ---------- */
/* Бит кодируется длиной импульса: «0» ≈ 0.35 мкс, «1» ≈ 0.7 мкс; пауза > 50 мкс — защёлка кадра */
export function attachNeoPixel(io, pin, count, onFrame) {
  let rise = -1, lastFall = -1, bits = 0, nbits = 0, frame = [], dirty = false;
  const latch = () => {
    if (!dirty) return;
    dirty = false;
    onFrame(frame.slice(0, count));
  };
  const off = io.onEdge(pin, (level, t) => {
    if (level === 1) {
      if (lastFall >= 0 && t - lastFall > 50e-6) { latch(); frame = []; bits = 0; nbits = 0; }
      rise = t;
    } else if (level === 0 && rise >= 0) {
      const high = t - rise;
      lastFall = t;
      bits = (bits << 1) | (high > 0.55e-6 ? 1 : 0);
      if (++nbits === 24) {
        frame.push({g: (bits >> 16) & 255, r: (bits >> 8) & 255, b: bits & 255});
        bits = 0; nbits = 0; dirty = true;
      }
    }
  });
  return {off, poll(now) { if (dirty && now - lastFall > 50e-6) latch(); }};
}

/* ---------- ИК-пульт: протокол NEC на выходе приёмника (активный низкий уровень) ---------- */
export const NEC_KEYS = [
  ['CH-', 0x45], ['CH', 0x46], ['CH+', 0x47], ['⏮', 0x44], ['⏭', 0x40], ['⏯', 0x43],
  ['−', 0x07], ['+', 0x15], ['EQ', 0x09], ['0', 0x16], ['100+', 0x19], ['200+', 0x0d],
  ['1', 0x0c], ['2', 0x18], ['3', 0x5e], ['4', 0x08], ['5', 0x1c], ['6', 0x5a], ['7', 0x42], ['8', 0x52], ['9', 0x4a],
];

export function necWave(address, command) {
  const steps = [[0, 9000], [1, 4500]];
  const bytes = [address & 255, ~address & 255, command & 255, ~command & 255];
  for (const byte of bytes) {
    for (let bit = 0; bit < 8; bit++) steps.push([0, 562], [1, (byte >> bit) & 1 ? 1687 : 562]);
  }
  steps.push([0, 562]);
  return steps;
}

/* ---------- Радиопульт 433 МГц: RCSwitch, протокол 1 (импульс 350 мкс), 24 бита ---------- */
export const RF_KEYS = [['A', 5592332], ['B', 5592512], ['C', 5592323], ['D', 5592368]];

export function rcSwitchWave(code, bits = 24, pulse = 350, repeats = 6) {
  const sync = [[1, pulse], [0, pulse * 31]];
  const steps = [...sync];
  for (let r = 0; r < repeats; r++) {
    for (let i = bits - 1; i >= 0; i--) {
      steps.push(...((code >> i) & 1 ? [[1, pulse * 3], [0, pulse]] : [[1, pulse], [0, pulse * 3]]));
    }
    steps.push(...sync);
  }
  return steps;
}

/* ---------- DHT22: на старт-импульс МК (низкий ≥ 0.8 мс) отвечает 40 битами ---------- */
export function dht22Bits(temperature, humidity) {
  const h = Math.round(humidity * 10) & 0xffff;
  let t = Math.round(Math.abs(temperature) * 10) & 0x7fff;
  if (temperature < 0) t |= 0x8000;
  const bytes = [h >> 8, h & 255, t >> 8, t & 255];
  bytes.push((bytes[0] + bytes[1] + bytes[2] + bytes[3]) & 255);
  const steps = [[1, 30], [0, 80], [1, 80]];
  for (const byte of bytes) for (let bit = 7; bit >= 0; bit--) steps.push([0, 50], [1, (byte >> bit) & 1 ? 70 : 26]);
  steps.push([0, 50]);
  return steps;
}

export function attachDht(io, pin, read) {
  let lowSince = -1;
  return io.onEdge(pin, (level, t) => {
    if (level === 0) { lowSince = t; return; }
    if (lowSince >= 0 && t - lowSince >= 0.0008) {
      const {temperature, humidity} = read();
      io.wave(pin, dht22Bits(temperature, humidity), 1);
    }
    lowSince = -1;
  });
}

/* ---------- HC-SR04: импульс ≥ 10 мкс на TRIG → эхо длиной 58 мкс на сантиметр ---------- */
export function attachUltrasonic(io, trig, echo, distance) {
  let rise = -1;
  io.setDigital(echo, 0);
  return io.onEdge(trig, (level, t) => {
    if (level === 1) { rise = t; return; }
    if (level === 0 && rise >= 0 && t - rise >= 8e-6) {
      const cm = Math.max(2, Math.min(400, distance()));
      io.wave(echo, [[0, 250], [1, cm * 58]], 0);
    }
    rise = -1;
  });
}

/* ---------- Сервопривод: импульс 544…2400 мкс → 0…180° ---------- */
export function servoAngle(pulseUs) {
  if (!pulseUs) return null;
  return Math.round(Math.max(0, Math.min(180, (pulseUs - 544) * 180 / 1856)));
}

/* ---------- Шаговый 28BYJ-48 через ULN2003: положение по набору включённых обмоток ---------- */
const COIL_STEP = {1: 0, 3: 1, 2: 2, 6: 3, 4: 4, 12: 5, 8: 6, 9: 7};  // маска IN1..IN4 → полушаг 0..7
export function stepperTracker() {
  let last = null, halfSteps = 0;
  return {
    update(mask) {
      const step = COIL_STEP[mask];
      if (step === undefined) return halfSteps;
      if (last !== null) {
        let delta = (step - last + 8) % 8;
        if (delta > 4) delta -= 8;
        halfSteps += delta;
      }
      last = step;
      return halfSteps;
    },
    get angle() { return halfSteps * 360 / 4096; },
  };
}
