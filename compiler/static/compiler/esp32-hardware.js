/* ESP32 в редакторе: схема с деталями над консолью.
 * Прошивка (мост oc_hw.c) пишет в Serial «@OC …» — эти строки прячем из консоли и двигаем ими детали;
 * детали отвечают строками «@IN …» во вход консоли. Схема хранится в проекте файлом diagram.json.
 * Классический скрипт: модули схемы подгружаются динамически, только когда выбран ESP32. */
(() => {
  const base = new URL('circuit/', document.currentScript.src).href;
  const DEFAULT = {parts: [
    {id: 'led2', type: 'led', x: 200, y: 120, pins: {A: 'GPIO2'}, props: {color: 'blue'}},
    {id: 'servo18', type: 'servo', x: 290, y: 90, pins: {SIG: 'GPIO18'}, props: {}},
  ]};

  const panel = document.createElement('section');
  panel.id = 'esp32Hardware';
  panel.className = 'esp32-panel';
  panel.hidden = true;
  panel.innerHTML = `<div class="esp32-head"><strong>Схема ESP32</strong>
    <span class="esp32-net" id="espNetwork">Сеть: ожидает запуска</span>
    <button type="button" class="chip" id="espToggle" aria-expanded="true">Свернуть</button></div>
    <div id="espCircuit"></div>`;
  document.getElementById('terminalWrap').before(panel);
  const css = document.createElement('link');
  css.rel = 'stylesheet';
  css.href = `${base}circuit.css`;
  document.head.appendChild(css);

  let circuit = null, bus = null, loading = null, pending = '', active = false;

  const diagramFromProject = () => {
    const text = window.OCProject?.getFile('diagram.json');
    if (!text) return DEFAULT;
    try { return JSON.parse(text); } catch { return DEFAULT; }
  };

  function ensure() {
    loading ||= Promise.all([import(`${base}editor.js`), import(`${base}esp32-bus.js`)]).then(([editor, busModule]) => {
      circuit = new editor.Circuit(document.getElementById('espCircuit'), {
        board: 'esp32',
        onChange: diagram => window.OCProject?.setFile('diagram.json', JSON.stringify(diagram, null, 1)),
        onExample: code => window.OCProject?.replaceMain(code),
      });
      circuit.Bus = busModule.Esp32Bus;
      circuit.load(diagramFromProject());
      return circuit;
    });
    return loading;
  }

  document.getElementById('espToggle').addEventListener('click', () => {
    const box = document.getElementById('espCircuit');
    box.hidden = !box.hidden;
    document.getElementById('espToggle').textContent = box.hidden ? 'Развернуть' : 'Свернуть';
    document.getElementById('espToggle').setAttribute('aria-expanded', String(!box.hidden));
  });

  /* Служебные строки — в схему, остальное — в консоль. Неполная строка, похожая на «@OC», ждёт продолжения. */
  function feed(text) {
    pending += text;
    let shown = '';
    let start = 0;
    for (let i = 0; i < pending.length; i++) {
      if (pending[i] !== '\n') continue;
      const raw = pending.slice(start, i + 1);
      const line = raw.replace(/\r?\n$/, '').replace(/\r/g, '');
      start = i + 1;
      if (line.includes('ESP32 HTTP ready:')) document.getElementById('espNetwork').textContent = line.slice(line.indexOf('ESP32 HTTP ready:'));
      if (line.startsWith('@IN ')) continue;  // эхо нашего ввода
      if (line.startsWith('@OC ')) { if (bus) bus.line(line); continue; }
      shown += raw;
    }
    const rest = pending.slice(start);
    // Хвост без перевода строки: если это может быть началом «@OC »/«@IN », придержим его до конца строки
    const head = rest.slice(0, 4);
    const maybeService = rest.startsWith('@') && ('@OC '.startsWith(head) || '@IN '.startsWith(head));
    if (maybeService && rest.length < 4096) {
      pending = rest;
    } else {
      shown += rest;
      pending = '';
    }
    return shown;
  }

  window.OCEsp32Hardware = {
    select(slug) {
      active = slug === 'esp32';
      panel.hidden = !active;
      this.reset();
      if (active) ensure().then(c => c.load(diagramFromProject()));
    },
    /* Проект открыт заново (черновик, сниппет, ссылка) — подхватываем его diagram.json */
    projectLoaded() { if (active && circuit) circuit.load(diagramFromProject()); },
    start(send) {
      if (!active) return;
      const run = c => {
        bus?.stop();
        bus = new c.Bus(send);
        c.run(bus);
      };
      // Схема уже загружена — запускаем сразу, чтобы не потерять первые строки телеметрии
      if (circuit) run(circuit); else ensure().then(run);
    },
    stop() {
      bus?.stop();
      bus = null;
      circuit?.stop();
    },
    reset() {
      pending = '';
      this.stop();
      document.getElementById('espNetwork').textContent = 'Сеть: ожидает запуска';
    },
    feed,
    /* Расшифровка из истории: без служебных строк */
    strip(text) { return String(text || '').split('\n').filter(l => !/^@(OC|IN) /.test(l.replace(/\r$/, ''))).join('\n'); },
  };
})();
