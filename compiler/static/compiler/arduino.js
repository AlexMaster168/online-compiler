import {CPU, avrInstruction, AVRTimer, timer0Config, timer1Config, timer2Config,
  AVRIOPort, portBConfig, portCConfig, portDConfig, AVRUSART, usart0Config,
  AVRADC, adcConfig} from 'https://cdn.jsdelivr.net/npm/avr8js@0.21.0/+esm';

const $ = id => document.getElementById(id);
const examples = {
  blink: 'void setup() {\n  pinMode(13, OUTPUT);\n  Serial.begin(9600);\n}\nvoid loop() {\n  digitalWrite(13, HIGH);\n  Serial.println("LED ON");\n  delay(500);\n  digitalWrite(13, LOW);\n  Serial.println("LED OFF");\n  delay(500);\n}\n',
  button: 'void setup() {\n  pinMode(13, OUTPUT);\n  pinMode(2, INPUT_PULLUP);\n}\nvoid loop() {\n  digitalWrite(13, digitalRead(2) == LOW);\n}\n',
  analog: 'void setup() {\n  Serial.begin(9600);\n}\nvoid loop() {\n  Serial.println(analogRead(A0));\n  delay(250);\n}\n',
  servo: '#include <Servo.h>\nServo motor;\nvoid setup(){motor.attach(9);}\nvoid loop(){motor.write(0);delay(1000);motor.write(90);delay(1000);motor.write(180);delay(1000);}\n',
  lcd: '#include <LiquidCrystal.h>\nLiquidCrystal lcd(12,11,5,4,3,2);\nvoid setup(){lcd.begin(16,2);lcd.print("Hello Arduino!");}\nvoid loop(){lcd.setCursor(0,1);lcd.print(millis()/1000);delay(200);}\n'
};
let cpu, portD, adc, usart, running = false, timer;
let project = JSON.parse($('project-data').textContent);
$('title').value = project?.title || '';
$('code').value = project?.code || localStorage.getItem('oc:arduino:code') || examples.blink;
$('save').onclick = async () => {
  $('save').disabled = true;
  try {
    const csrf = document.cookie.split('; ').find(x => x.startsWith('csrftoken='))?.split('=')[1];
    const response = await fetch('/api/arduino/save/', {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':csrf || ''},
      body:JSON.stringify({code:$('code').value,title:$('title').value,id:project?.is_owner ? project.id : ''})});
    const data = await response.json(); if (!response.ok) throw Error(data.error);
    project = data; history.replaceState(null,'',data.url);
    $('status').textContent = 'Проект сохранён: '+location.href;
  } catch(error) {$('status').textContent = error.message;}
  finally {$('save').disabled = false;}
};
$('code').oninput = () => localStorage.setItem('oc:arduino:code', $('code').value);
$('example').onchange = () => {
  if ($('code').value !== examples[$('example').value] && !confirm('Заменить текущий скетч примером?')) return;
  $('code').value = examples[$('example').value]; $('code').oninput();
};
function stop() { running = false; clearTimeout(timer); $('stop').disabled = true; $('run').disabled = false; }
$('stop').onclick = () => {stop(); $('status').textContent = 'Остановлен';};
function loadHex(hex) {
  const memory = new Uint8Array(32768); let base = 0;
  for (const line of hex.trim().split(/\r?\n/)) {
    const bytes = line.slice(1).match(/../g).map(x => parseInt(x,16));
    if (line[0] !== ':' || bytes.reduce((a,b) => a+b,0) % 256) throw Error('Повреждён HEX');
    const [length, hi, lo, type] = bytes;
    if (type === 4) base = (bytes[4]*256+bytes[5])*65536;
    if (type === 0) memory.set(bytes.slice(4,4+length), base+hi*256+lo);
  }
  return new Uint16Array(memory.buffer);
}
function execute() {
  if (!running) return;
  const until = cpu.cycles + 160000;
  while (cpu.cycles < until) {avrInstruction(cpu); cpu.tick();}
  $('clock').textContent = (cpu.cycles / 16000000).toFixed(2)+' с';
  timer = setTimeout(execute,0);
}
function start(hex) {
  $('led').classList.remove('on');
  $('servo').textContent = '0°';
  $('servoHorn')?.setAttribute('transform','rotate(-90 130 48)');
  cpu = new CPU(loadHex(hex));
  for (const config of [timer0Config,timer1Config,timer2Config]) new AVRTimer(cpu,config);
  const portB = new AVRIOPort(cpu,portBConfig); new AVRIOPort(cpu,portCConfig);
  portD = new AVRIOPort(cpu,portDConfig); portD.setPin(2,true);
  adc = new AVRADC(cpu,adcConfig); adc.channelValues[0] = Number($('pot').value)*5/1023;
  usart = new AVRUSART(cpu,usart0Config,16000000);
  usart.onByteTransmit = byte => {
    $('serial').textContent = ($('serial').textContent + String.fromCharCode(byte)).slice(-24000);
    $('serial').scrollTop = $('serial').scrollHeight;
  };
  portB.addListener(value => $('led').classList.toggle('on',Boolean(value & 32)));
  let pulseStart = 0, fourBit = false, nibble = null, address = 0;
  const cells = Array(80).fill(' ');
  $('lcd').textContent = '                \n                ';
  portB.addListener((value, old) => {
    if ((value & 2) && !(old & 2)) pulseStart = cpu.cycles;
    if (!(value & 2) && (old & 2)) {
      const microseconds = (cpu.cycles-pulseStart)/16;
      const angle = Math.round(Math.max(0,Math.min(180,(microseconds-544)*180/1856)));
      $('servo').textContent = angle+'°';
      $('servoHorn')?.setAttribute('transform',`rotate(${angle-90} 130 48)`);
    }
    if (!(value & 8) && (old & 8)) {
      const data = cpu.data[portDConfig.PORT];
      const half = ((data>>5)&1) | (((data>>4)&1)<<1) | (((data>>3)&1)<<2) | (((data>>2)&1)<<3);
      if (!fourBit) {if (half === 2) fourBit = true; return;}
      if (nibble === null) {nibble = half; return;}
      const byte = nibble*16+half; nibble = null;
      if (value & 16) {cells[address] = String.fromCharCode(byte); address = (address+1)%80;}
      else if (byte & 128) address = byte & 127;
      else if (byte === 1) {cells.fill(' '); address = 0;}
      else if (byte === 2) address = 0;
      $('lcd').textContent = cells.slice(0,16).join('')+'\n'+cells.slice(64,80).join('');
    }
  });
  running = true; $('stop').disabled = false; execute();
}
$('run').onclick = async () => {
  stop(); $('run').disabled = true; $('status').textContent = 'Собираю прошивку…'; $('serial').textContent = '';
  try {
    const csrf = document.cookie.split('; ').find(x => x.startsWith('csrftoken='))?.split('=')[1];
    const response = await fetch('/api/arduino/compile/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf || ''},body:JSON.stringify({code:$('code').value})});
    const data = await response.json(); $('log').textContent = data.log || '';
    if (!response.ok) throw Error(data.error || 'Ошибка сборки');
    start(data.hex); $('status').textContent = 'Прошивка работает';
  } catch (error) {stop(); $('status').textContent = error.message;}
};
$('button').onpointerdown = event => {event.currentTarget.setPointerCapture(event.pointerId); portD?.setPin(2,false);};
for (const event of ['pointerup','pointercancel','lostpointercapture']) $('button').addEventListener(event,()=>portD?.setPin(2,true));
$('pot').oninput = () => {
  const value = Number($('pot').value);
  if (adc) adc.channelValues[0] = value*5/1023;
  $('potKnob')?.setAttribute('transform',`rotate(${value*270/1023-135} 70 49)`);
};
$('send').onsubmit = event => {
  event.preventDefault(); if (!running) return;
  const bytes = new TextEncoder().encode($('input').value+'\n'); let i = 0;
  const send = () => {if (!running || i === bytes.length) return; if (usart.writeByte(bytes[i])) i++; setTimeout(send,2);};
  send(); $('input').value = '';
};
$('download').onclick = () => {
  const url = URL.createObjectURL(new Blob([$('code').value],{type:'text/plain'}));
  const link = document.createElement('a'); link.href = url; link.download = 'sketch.ino'; link.click(); URL.revokeObjectURL(url);
};
window.addEventListener('pagehide',stop);
