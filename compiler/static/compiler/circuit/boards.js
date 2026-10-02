/* Платы для схемы: картинка, координаты ножек и что каждая ножка умеет.
   Координаты — в единицах схемы (как viewBox картинки платы). */

const range = (n, f) => Array.from({length: n}, (_, i) => f(i));
const header = (x, y, count, step) => range(count, i =>
  `<rect x="${x + i * step}" y="${y}" width="13" height="13" rx="1" fill="#111d25" stroke="#82949e"/>` +
  `<rect x="${x + 4 + i * step}" y="${y + 4}" width="5" height="5" fill="#02070c"/>`).join('');

/* ---------- Arduino Uno ---------- */
const UNO_PWM = new Set([3, 5, 6, 9, 10, 11]);
const unoPins = [];
// Верхний разъём: D13 … D0 слева направо
for (let i = 0; i < 14; i++) {
  const n = 13 - i;
  unoPins.push({
    id: `D${n}`, label: `${n}`, x: 168 + i * 17 + 6.5, y: 22 + 6.5, side: 'top',
    caps: new Set(['digital', 'out', 'in', ...(UNO_PWM.has(n) ? ['pwm'] : []), ...(n === 2 || n === 3 ? ['int'] : [])]),
    reserved: n <= 1 ? 'Serial (RX/TX)' : '',
  });
}
// Нижний разъём: A0 … A5 (тоже цифровые; A4/A5 — SDA/SCL шины I2C)
for (let i = 0; i < 6; i++) {
  unoPins.push({
    id: `A${i}`, label: `A${i}`, x: 314 + i * 17 + 6.5, y: 227 + 6.5, side: 'bottom',
    caps: new Set(['digital', 'out', 'in', 'analog', ...(i === 4 ? ['sda'] : []), ...(i === 5 ? ['scl'] : [])]),
    reserved: '',
  });
}

const UNO_ART = `<svg viewBox="0 0 440 265" width="440" height="265" role="img" aria-label="Плата Arduino Uno">
<defs><linearGradient id="ocPcb" x2="1" y2="1"><stop stop-color="#098b9a"/><stop offset="1" stop-color="#005564"/></linearGradient>
<linearGradient id="ocMetal" x2="0" y2="1"><stop stop-color="#edf2f5"/><stop offset=".5" stop-color="#929eaa"/><stop offset="1" stop-color="#dbe2e7"/></linearGradient></defs>
<path d="M30 8H415L430 23V240L413 258H30Q14 258 14 242V25Q14 8 30 8" fill="url(#ocPcb)" stroke="#0eb2bd" stroke-width="3"/>
${[[38, 31], [401, 30], [38, 232], [400, 232]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r="8" fill="#092f38" stroke="#c6bf8d" stroke-width="4"/>`).join('')}
<g fill="none" stroke="#24a2a7" stroke-width="1.5" opacity=".6"><path d="M130 70H345V114H389M185 218V180H322V86M70 171H114V110H207M57 131H160V210H360M84 73H126V51H220"/></g>
<rect x="2" y="49" width="82" height="71" rx="6" fill="url(#ocMetal)" stroke="#606e7b" stroke-width="3"/><rect x="4" y="60" width="24" height="48" rx="3" fill="#374352"/><rect x="10" y="69" width="13" height="30" fill="#080f18"/>
<rect x="5" y="179" width="65" height="42" rx="5" fill="#18212b"/><circle cx="15" cy="200" r="12" fill="#03070b" stroke="#758693" stroke-width="3"/>
<rect x="132" y="79" width="40" height="40" rx="2" fill="#17212b" stroke="#778892"/>
<rect x="207" y="137" width="157" height="43" rx="5" fill="#121b25" stroke="#607380"/>
<g stroke="#acb6bc" stroke-width="5">${range(14, i => `<path d="M${215 + i * 11} 131v6m0 43v6"/>`).join('')}</g>
<text x="229" y="164" fill="#bbc6cb" font-family="monospace" font-size="11">ATMEGA328P</text>
${header(168, 22, 14, 17)}${header(163, 227, 8, 17)}${header(314, 227, 6, 17)}
<g fill="#d5f1f1" font-family="monospace" font-size="8.5" text-anchor="middle">
${range(14, i => `<text x="${168 + i * 17 + 6.5}" y="47">${13 - i}${UNO_PWM.has(13 - i) ? '~' : ''}</text>`).join('')}
${range(6, i => `<text x="${314 + i * 17 + 6.5}" y="222">A${i}</text>`).join('')}
<text x="231" y="222">POWER · 5V GND</text></g>
<text x="204" y="112" fill="#d9f8f8" font-family="system-ui" font-size="27" font-weight="700">UNO</text>
<text x="291" y="110" fill="#d9f8f8" font-size="13" font-family="system-ui">16 MHz</text>
<rect x="91" y="139" width="29" height="14" rx="7" fill="url(#ocMetal)"/>
<g data-r="builtin"><rect x="128" y="58" width="9" height="6" rx="1" fill="#5b4a2a" data-r="l13"/><text x="140" y="64" fill="#d5f1f1" font-size="8" font-family="monospace">L</text></g>
</svg>`;

/* ---------- ESP32 DevKit (30 ножек) ---------- */
// Сверху — правый ряд настоящей платы, снизу — левый (плата повёрнута USB вправо)
const ESP_TOP = ['3V3', '15', '2', '4', '16', '17', '5', '18', '19', 'GND', '21', '3', '1', '22', '23'];
const ESP_BOTTOM = ['VIN', 'GND', '13', '12', '14', '27', '26', '25', '33', '32', '35', '34', '39', '36', 'EN'];
const ESP_ADC = new Set([32, 33, 34, 35, 36, 39]);  // ADC1 — ADC2 занят Wi-Fi
const espPins = [];
const espPin = (name, x, y, side) => {
  const n = Number(name);
  if (!Number.isInteger(n)) return;  // питание и EN не подключаются
  const inputOnly = n >= 34;
  espPins.push({
    id: `GPIO${n}`, label: `${n}`, x, y, side,
    caps: new Set(['digital', 'in', 'pwm', 'int', ...(inputOnly ? [] : ['out']), ...(ESP_ADC.has(n) ? ['analog'] : []),
      ...(n === 21 ? ['sda'] : []), ...(n === 22 ? ['scl'] : [])]),
    reserved: n === 1 || n === 3 ? 'Serial (TX/RX)' : '',
  });
};
ESP_TOP.forEach((name, i) => espPin(name, 40 + i * 25 + 6.5, 14 + 6.5, 'top'));
ESP_BOTTOM.forEach((name, i) => espPin(name, 40 + i * 25 + 6.5, 186 + 6.5, 'bottom'));

const ESP_ART = `<svg viewBox="0 0 440 215" width="440" height="215" role="img" aria-label="Плата ESP32 DevKit">
<rect x="22" y="6" width="400" height="203" rx="10" fill="#152c29" stroke="#60948b" stroke-width="2"/>
${header(40, 14, 15, 25)}${header(40, 186, 15, 25)}
<g fill="#cfe7df" font-family="monospace" font-size="8.5" text-anchor="middle">
${ESP_TOP.map((n, i) => `<text x="${40 + i * 25 + 6.5}" y="40">${n}</text>`).join('')}
${ESP_BOTTOM.map((n, i) => `<text x="${40 + i * 25 + 6.5}" y="181">${n}</text>`).join('')}</g>
<rect x="60" y="56" width="190" height="102" rx="4" fill="#bdc4ca"/><rect x="60" y="56" width="52" height="102" fill="#263b31"/>
<path d="M98 62H72v12h22v12H72v12h22v12H72v12h22v12H72v12h22" fill="none" stroke="#d0b46e" stroke-width="3"/>
<text x="180" y="100" fill="#26333d" text-anchor="middle" font-size="15" font-family="system-ui" font-weight="700">ESPRESSIF</text>
<text x="180" y="120" fill="#26333d" text-anchor="middle" font-size="11" font-family="monospace">ESP-WROOM-32</text>
<rect x="290" y="88" width="38" height="38" fill="#10151e" stroke="#7f8a91"/>
<rect x="390" y="86" width="40" height="44" rx="3" fill="#b4bec6"/><rect x="398" y="96" width="30" height="24" fill="#17212c"/>
<circle cx="360" cy="70" r="8" fill="#737e88"/><circle cx="360" cy="146" r="8" fill="#737e88"/>
<text x="345" y="166" fill="#cfe7df" font-size="9" font-family="monospace">BOOT EN</text>
<rect x="340" y="104" width="10" height="7" rx="1" fill="#3a2020" data-r="led2"/><text x="337" y="100" fill="#cfe7df" font-size="8" font-family="monospace">IO2</text>
</svg>`;

export const BOARDS = {
  uno: {
    id: 'uno', title: 'Arduino Uno', art: UNO_ART, width: 440, height: 265, pins: unoPins,
    i2c: {sda: 'A4', scl: 'A5'}, vcc: '5V', logicVolts: 5, adcVolts: 5,
    builtinLed: {pin: 'D13', role: 'l13'},
  },
  esp32: {
    id: 'esp32', title: 'ESP32 DevKit', art: ESP_ART, width: 440, height: 215, pins: espPins,
    i2c: {sda: 'GPIO21', scl: 'GPIO22'}, vcc: '3V3', logicVolts: 3.3, adcVolts: 3.3,
    builtinLed: {pin: 'GPIO2', role: 'led2'},
  },
};

export function boardPin(board, id) {
  return board.pins.find(p => p.id === id) || null;
}

/* Номер ножки для кода: D13 → 13, A0 → A0, GPIO18 → 18 */
export function pinCode(id) {
  if (!id) return '?';
  if (id.startsWith('GPIO')) return id.slice(4);
  if (id.startsWith('D')) return id.slice(1);
  return id;
}
