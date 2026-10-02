/* Шина ножек ESP32: QEMU ножки наружу не выводит, поэтому прошивка с мостом oc_hw.c сообщает о них строками
   «@OC …» в Serial, а схема отвечает строками «@IN …» во вход UART (протокол — в oc_hw.c). */

const gpio = id => Number(String(id).replace('GPIO', ''));

export class Esp32Bus {
  constructor(send) {
    this.kind = 'esp32';
    this.send = send;
    this.levels = {};
    this.pwm = {};
    this.handlers = {};
    this.messages = {};
    this.inputs = new Map();  // последние уровни входов — переотправляются, если прошивка начала слушать позже
    this.resend = setInterval(() => { for (const line of this.inputs.values()) this.send(line); }, 1500);
  }

  now() { return performance.now() / 1000; }

  /* Строка телеметрии из Serial; true — строка служебная и в консоль не идёт */
  line(text) {
    if (text === '@OC HELLO') {  // прошивка начала читать входы — сразу шлём их состояние
      for (const line of this.inputs.values()) this.send(line);
      return true;
    }
    let m = text.match(/^@OC D (\d+) ([01])$/);
    if (m) { this.level(`GPIO${m[1]}`, Number(m[2])); return true; }
    m = text.match(/^@OC P (\d+) (\d+) (\d+)$/);
    if (m) {
      const id = `GPIO${m[1]}`, duty = Number(m[2]) / 10000, freq = Number(m[3]);
      this.pwm[id] = {duty, freq};
      this.fire(id, duty > 0 ? 1 : 0);
      return true;
    }
    m = text.match(/^@OC (LCD|NEO) (.*)$/);
    if (m) { for (const fn of this.messages[m[1]] || []) fn(m[2]); return true; }
    // Старый формат прошивок до схемы: @OC LED 1 / @OC SERVO 90
    m = text.match(/^@OC LED ([01])$/);
    if (m) { this.level('GPIO2', Number(m[1])); return true; }
    m = text.match(/^@OC SERVO (\d{1,3})$/);
    if (m) {
      const angle = Math.min(180, Number(m[1]));
      this.pwm.GPIO18 = {duty: (544 + angle * 1856 / 180) / 20000, freq: 50};
      this.fire('GPIO18', 1);
      return true;
    }
    return text.startsWith('@OC ');
  }

  level(id, value) {
    delete this.pwm[id];
    if (this.levels[id] === value) return;
    this.levels[id] = value;
    this.fire(id, value);
  }

  fire(id, value) {
    for (const fn of this.handlers[id] || []) fn(value, this.now());
  }

  read(id) {
    const pwm = this.pwm[id];
    if (pwm) {
      const pulse = pwm.freq ? pwm.duty / pwm.freq * 1e6 : 0;
      return {level: pwm.duty > 0 ? 1 : 0, duty: pwm.duty, freq: pwm.duty > 0 ? pwm.freq : 0, pulse};
    }
    const level = this.levels[id];
    return {level: level ?? null, duty: level === 1 ? 1 : 0, freq: 0, pulse: 0};
  }

  onEdge(id, fn) {
    (this.handlers[id] ||= []).push(fn);
    return () => { this.handlers[id] = this.handlers[id].filter(f => f !== fn); };
  }

  onMessage(type, fn) {
    (this.messages[type] ||= []).push(fn);
    return () => { this.messages[type] = this.messages[type].filter(f => f !== fn); };
  }

  input(key, line) {
    this.inputs.set(key, line);
    this.send(line);
  }

  setDigital(id, value) { this.input(`D${id}`, `@IN D ${gpio(id)} ${value == null || value ? 1 : 0}`); }

  setAnalog(id, volts) {
    this.input(`A${id}`, `@IN A ${gpio(id)} ${Math.round(Math.max(0, Math.min(3.3, volts)) * 1000)}`);
  }

  connect(a, b, closed) { this.send(`@IN SW ${gpio(a)} ${gpio(b)} ${closed ? 1 : 0}`); }

  /* Разовые события деталей: ИК и радиопульт */
  event(type, value) { this.send(`@IN ${type} ${value}`); }

  /* Постоянные значения датчиков: расстояние, DHT */
  value(key, line) { this.input(key, line); }

  stop() {
    clearInterval(this.resend);
    this.handlers = {};
    this.messages = {};
  }
}
