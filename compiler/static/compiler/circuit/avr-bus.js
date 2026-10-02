/* Шина ножек Arduino Uno поверх avr8js: детали схемы читают выходы процессора и подают сигналы на входы.
   Время — эмулируемое (такты / 16 МГц), поэтому длительности импульсов точные, как на настоящей плате. */

export const F_CPU = 16e6;

/* D0–D7 → порт D, D8–D13 → порт B, A0–A5 → порт C */
export function pinLocation(id) {
  if (id[0] === 'A') return {port: 'C', bit: Number(id.slice(1)), adc: Number(id.slice(1))};
  const n = Number(id.slice(1));
  if (n < 8) return {port: 'D', bit: n};
  return {port: 'B', bit: n - 8};
}

const pinId = (port, bit) => port === 'C' ? `A${bit}` : `D${port === 'D' ? bit : bit + 8}`;

/* Скважность и частота по фронтам: для ШИМ-светодиодов, моторов, сервы и пищалки */
class Meter {
  constructor() { this.level = null; this.rise = -1; this.fall = -1; this.period = 0; this.high = 0; this.edge = -1; }
  update(level, t) {
    if (level === this.level) return;
    if (level === 1) {
      if (this.rise >= 0) this.period = t - this.rise;
      this.rise = t;
    } else if (level === 0 && this.rise >= 0 && this.level === 1) {
      this.high = t - this.rise;
      this.fall = t;
    }
    this.level = level;
    this.edge = t;
  }
  read(now) {
    const level = this.level;
    // Нет фронтов дольше пары периодов (или 50 мс) — сигнал постоянный
    const stale = this.edge < 0 || now - this.edge > Math.max(0.05, this.period * 2.5);
    if (stale || !this.period) return {level, duty: level === 1 ? 1 : 0, freq: 0, pulse: 0};
    return {level, duty: Math.min(1, this.high / this.period), freq: 1 / this.period, pulse: this.high * 1e6};
  }
}

export class AvrBus {
  /* ports: {B, C, D} — AVRIOPort; adc — AVRADC; twi — AVRTWI (необязательно) */
  constructor({cpu, ports, adc, twi, configs}) {
    this.kind = 'avr';
    this.cpu = cpu;
    this.ports = ports;
    this.adc = adc;
    this.meters = {};
    this.handlers = {};
    this.waves = {};
    this.inputs = {};
    this.devices = {};
    for (const [name, port] of Object.entries(ports)) {
      const ddrAddr = configs[name].DDR;
      const old = {ddr: 0, value: 0};
      port.addListener((value) => {
        const ddr = cpu.data[ddrAddr];
        const changed = ((value ^ old.value) | (ddr ^ old.ddr)) & 0xff;
        old.value = value; old.ddr = ddr;
        if (!changed) return;
        const t = this.now();
        for (let bit = 0; bit < 8; bit++) {
          if (!(changed & (1 << bit))) continue;
          const id = pinId(name, bit);
          const level = ddr & (1 << bit) ? (value >> bit) & 1 : null;
          (this.meters[id] ||= new Meter()).update(level, t);
          const list = this.handlers[id];
          if (list) for (const fn of list) fn(level, t);
        }
      });
    }
    // Входы без внешнего сигнала читаются как 1 — будто включена подтяжка (как у кнопки на INPUT_PULLUP)
    for (const port of Object.values(ports)) for (let bit = 0; bit < 8; bit++) port.setPin(bit, true);
    if (twi) this.attachI2C(twi);
  }

  now() { return this.cpu.cycles / F_CPU; }

  /* Состояние выхода: level 0/1 (null — ножка настроена на вход), скважность, частота, ширина импульса (мкс) */
  read(id) {
    const meter = this.meters[id];
    return meter ? meter.read(this.now()) : {level: null, duty: 0, freq: 0, pulse: 0};
  }

  /* Колбэк на каждое изменение выхода: fn(level | null, время в секундах) */
  onEdge(id, fn) {
    (this.handlers[id] ||= []).push(fn);
    return () => { this.handlers[id] = this.handlers[id].filter(f => f !== fn); };
  }

  setDigital(id, value) {
    const {port, bit} = pinLocation(id);
    this.inputs[id] = value;
    this.ports[port].setPin(bit, value == null ? true : Boolean(value));
  }

  setAnalog(id, volts) {
    const {adc} = pinLocation(id);
    if (adc == null || !this.adc) return;
    this.adc.channelValues[adc] = Math.max(0, Math.min(5, volts));
    this.setDigital(id, volts > 2.5);
  }

  /* Через us микросекунд эмулируемого времени */
  after(us, fn) {
    const cb = () => fn();
    this.cpu.addClockEvent(cb, Math.max(1, Math.round(us * F_CPU / 1e6)));
    return () => this.cpu.clearClockEvent(cb);
  }

  /* Подать на вход последовательность [[уровень, мкс], …], затем держать idle. Новая волна отменяет старую. */
  wave(id, steps, idle = 1) {
    this.waves[id]?.();
    let index = 0, cancel = null, stopped = false;
    const next = () => {
      if (stopped) return;
      if (index >= steps.length) { this.setDigital(id, idle); this.waves[id] = null; return; }
      const [level, us] = steps[index++];
      this.setDigital(id, level);
      cancel = this.after(us, next);
    };
    this.waves[id] = () => { stopped = true; cancel?.(); };
    next();
  }

  /* Замкнуть две ножки (кнопка клавиатуры): вход читает уровень выхода, иначе — подтяжку */
  connect(a, b, closed) {
    const key = [a, b].sort().join('-');
    this.links ||= new Map();
    if (closed) this.links.set(key, [a, b]); else this.links.delete(key);
    this.syncLinks(a); this.syncLinks(b);
    if (!this.linkWatch?.has(a)) this.watchLink(a);
    if (!this.linkWatch?.has(b)) this.watchLink(b);
  }

  watchLink(id) {
    this.linkWatch ||= new Set();
    this.linkWatch.add(id);
    this.onEdge(id, () => {
      for (const [x, y] of this.links.values()) {
        if (x === id) this.syncLinks(y);
        if (y === id) this.syncLinks(x);
      }
    });
  }

  syncLinks(id) {
    let level = true;
    for (const [x, y] of this.links?.values() || []) {
      const peer = x === id ? y : y === id ? x : null;
      if (peer == null) continue;
      const out = this.meters[peer]?.level;
      if (out === 0) level = false;
    }
    const {port, bit} = pinLocation(id);
    this.ports[port].setPin(bit, level);
  }

  /* Устройства на шине I2C (TWI): {start(write), write(byte), read() → byte, stop()} по 7-битному адресу */
  i2c(address, device) { this.devices[address] = device; }

  attachI2C(twi) {
    let current = null;
    twi.eventHandler = {
      start: () => twi.completeStart(),
      stop: () => { current?.stop?.(); current = null; twi.completeStop(); },
      connectToSlave: (address, write) => {
        current = this.devices[address] || null;
        current?.start?.(write);
        twi.completeConnect(Boolean(current));
      },
      writeByte: (value) => { current?.write?.(value); twi.completeWrite(Boolean(current)); },
      readByte: () => twi.completeRead(current?.read?.() ?? 0xff),
    };
  }

  stop() {
    for (const cancel of Object.values(this.waves)) cancel?.();
    this.handlers = {};
  }
}
