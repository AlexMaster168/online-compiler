/* Редактор схемы: палитра деталей, перетаскивание, провода к ножкам платы, настройки детали и «живые» детали
   во время работы прошивки. Схема — JSON {version, board, parts: [{id, type, x, y, pins, props, state}]}. */
import {BOARDS, pinCode} from './boards.js';
import {CATEGORIES, PARTS, PART_LIST} from './parts.js';

const WIRE_COLORS = ['#ef4444', '#f59e0b', '#22c55e', '#3b82f6', '#a855f7', '#ec4899', '#14b8a6', '#eab308'];
const IDLE = {level: null, duty: 0, freq: 0, pulse: 0};
const SAVED_STATE = ['value', 'light', 'celsius', 'cm', 't', 'h', 'on', 'blocked'];
const NEED_CAP = {out: 'out', in: 'in', analog: 'analog', int: 'int'};
const BOARD_AT = {x: 40, y: 250};
const MAX_PARTS = 40;

const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));

/* Фильтр свечения для светодиодов — один на страницу */
function ensureDefs() {
  if (document.getElementById('ocCircuitDefs')) return;
  document.body.insertAdjacentHTML('beforeend', `<svg id="ocCircuitDefs" width="0" height="0" style="position:absolute;width:0;height:0" aria-hidden="true">
    <defs><filter id="ocGlow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="5"/></filter></defs></svg>`);
}

const sizeOf = part => {
  const def = PARTS[part.type];
  return def.size ? def.size(part) : {w: def.w, h: def.h};
};
const controlRows = def => def.controlRows ?? (def.controls ? (def.type === 'dht22' ? 2 : 1) : 0);
const CONTROL_ROW = 24;

/* Порядок, в котором раздаются свободные ножки новым деталям */
const PIN_ORDER = {
  uno: ['D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'D13', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5'],
  esp32: [4, 5, 13, 14, 16, 17, 18, 19, 23, 25, 26, 27, 32, 33, 15, 12, 2, 21, 22, 34, 35, 36, 39].map(n => `GPIO${n}`),
};

export class Circuit {
  constructor(root, {board = 'uno', onChange = () => {}, onExample = null} = {}) {
    ensureDefs();
    this.root = root;
    this.board = BOARDS[board];
    this.onChange = onChange;
    this.onExample = onExample;
    this.parts = [];
    this.instances = new Map();
    this.io = null;
    this.zoom = 1;
    this.selected = null;
    this.muted = false;
    this.oscillators = new Map();
    this.build();
  }

  /* ---------- разметка ---------- */
  build() {
    this.root.classList.add('oc-circuit');
    this.root.innerHTML = `
      <div class="cc-bar">
        <button type="button" class="cc-add" aria-expanded="false">＋ Деталь</button>
        <span class="cc-hint">Клик по детали — ножки и пример кода</span>
        <span class="cc-spacer"></span>
        <button type="button" class="cc-icon" data-zoom="out" title="Мельче" aria-label="Мельче">−</button>
        <button type="button" class="cc-icon" data-zoom="fit" title="Вписать схему" aria-label="Вписать схему">⤢</button>
        <button type="button" class="cc-icon" data-zoom="in" title="Крупнее" aria-label="Крупнее">+</button>
        <button type="button" class="cc-icon cc-mute" title="Звук пищалки" aria-label="Звук пищалки" aria-pressed="true">🔊</button>
      </div>
      <div class="cc-palette" hidden></div>
      <div class="cc-view"><div class="cc-sizer"><div class="cc-stage">
        <div class="cc-boardart"></div><svg class="cc-wires"></svg><div class="cc-parts"></div>
      </div></div></div>
      <div class="cc-inspector" hidden></div>`;
    this.$ = sel => this.root.querySelector(sel);
    this.view = this.$('.cc-view');
    this.sizer = this.$('.cc-sizer');
    this.stage = this.$('.cc-stage');
    this.wires = this.$('.cc-wires');
    this.partsLayer = this.$('.cc-parts');
    this.inspector = this.$('.cc-inspector');
    this.palette = this.$('.cc-palette');

    this.$('.cc-add').addEventListener('click', () => this.togglePalette());
    this.root.querySelectorAll('[data-zoom]').forEach(b => b.addEventListener('click', () => {
      const z = b.dataset.zoom;
      this.setZoom(z === 'fit' ? this.fitZoom() : this.zoom * (z === 'in' ? 1.2 : 1 / 1.2));
    }));
    this.$('.cc-mute').addEventListener('click', () => {
      this.muted = !this.muted;
      this.$('.cc-mute').textContent = this.muted ? '🔇' : '🔊';
      this.$('.cc-mute').setAttribute('aria-pressed', String(!this.muted));
      if (this.muted) for (const id of this.oscillators.keys()) this.sound(id, 0);
    });
    this.stage.addEventListener('pointerdown', e => { if (e.target === this.stage || e.target.closest('.cc-boardart')) this.select(null); });
    this.root.addEventListener('keydown', e => {
      if ((e.key === 'Delete' || e.key === 'Backspace') && this.selected && !e.target.closest('input, select, textarea')) {
        this.remove(this.selected);
      }
    });
    new ResizeObserver(() => { if (!this.userZoom) this.setZoom(this.fitZoom(), false); }).observe(this.view);
    this.renderBoard();
    this.renderPalette();
  }

  renderBoard() {
    const art = this.$('.cc-boardart');
    art.innerHTML = this.board.art;
    Object.assign(art.style, {left: `${BOARD_AT.x}px`, top: `${BOARD_AT.y}px`, width: `${this.board.width}px`});
  }

  renderPalette() {
    const tiles = def => {
      const sample = this.newPart(def.type, false);
      const {w, h} = sizeOf(sample);
      const badge = def.esp32 === false && this.board.id === 'esp32' ? '<em>только Arduino</em>'
        : def.esp32 === 'helper' && this.board.id === 'esp32' ? '<em>через oc_hw.h</em>' : '';
      const disabled = def.esp32 === false && this.board.id === 'esp32' ? 'disabled' : '';
      return `<button type="button" class="cc-tile" data-type="${def.type}" ${disabled}>
        <svg viewBox="-4 -4 ${w + 8} ${h + 8}" aria-hidden="true">${def.art(sample)}</svg><span>${esc(def.title)}</span>${badge}</button>`;
    };
    this.palette.innerHTML = CATEGORIES.map(cat => {
      const defs = PART_LIST.filter(d => d.category === cat);
      return defs.length ? `<section><h4>${cat}</h4><div class="cc-tiles">${defs.map(tiles).join('')}</div></section>` : '';
    }).join('') + (this.board.id === 'esp32'
      ? '<p class="cc-note">ESP32 в эмуляторе: GPIO, ШИМ (LEDC) и АЦП работают через обычный ESP-IDF. Детали с пометкой «через oc_hw.h» управляются функциями oc_* — в «Вставить пример кода» они уже есть.</p>' : '');
    for (const tile of this.palette.querySelectorAll('.cc-tile')) {
      tile.addEventListener('click', () => {
        const part = this.add(tile.dataset.type);
        if (part) { this.togglePalette(false); this.select(part); this.scrollTo(part); }
      });
    }
  }

  togglePalette(open = this.palette.hidden) {
    this.palette.hidden = !open;
    this.$('.cc-add').setAttribute('aria-expanded', String(open));
  }

  /* ---------- модель ---------- */
  newPart(type, assign = true) {
    const def = PARTS[type];
    const part = {id: `${type}${Date.now().toString(36)}${Math.random().toString(36).slice(2, 5)}`, type, x: 0, y: 0, pins: {}, props: {}, state: {}};
    for (const [key, prop] of Object.entries(def.props || {})) part.props[key] = prop.default;
    // Один набор занятых ножек на всю деталь — иначе все её ножки получат одну и ту же свободную
    const used = assign ? this.usedPins() : null;
    if (assign) for (const pin of def.pins) part.pins[pin.id] = this.fixedPin(pin) || this.freePin(pin, used) || null;
    return part;
  }

  fixedPin(pin) {
    if (pin.need === 'sda') return this.board.i2c.sda;
    if (pin.need === 'scl') return this.board.i2c.scl;
    return null;
  }

  candidates(pin) {
    const cap = NEED_CAP[pin.need];
    const byId = Object.fromEntries(this.board.pins.map(p => [p.id, p]));
    const order = PIN_ORDER[this.board.id].map(id => byId[id]).filter(Boolean);
    return order.filter(p => !p.reserved && (!cap || p.caps.has(cap)));
  }

  usedPins(except = null) {
    const used = new Map();
    for (const part of this.parts) {
      if (part === except) continue;
      for (const [role, pin] of Object.entries(part.pins)) {
        const need = PARTS[part.type].pins.find(p => p.id === role)?.need;
        if (pin && need !== 'sda' && need !== 'scl') used.set(pin, part);
      }
    }
    return used;
  }

  freePin(pin, used = this.usedPins()) {
    const list = this.candidates(pin).filter(p => !used.has(p.id));
    const i2c = new Set(this.parts.some(p => PARTS[p.type].pins.some(x => x.need === 'sda')) ? Object.values(this.board.i2c) : []);
    const pick = list.filter(p => !i2c.has(p.id));
    const preferred = pin.prefer ? pick.filter(p => p.caps.has(pin.prefer)) : pick;
    const found = (preferred[0] || pick[0] || null)?.id || null;
    if (found) used.set(found, true);
    return found;
  }

  add(type, at = null) {
    if (this.parts.length >= MAX_PARTS) return null;
    const def = PARTS[type];
    if (!def || (def.esp32 === false && this.board.id === 'esp32')) return null;
    const part = this.newPart(type);
    Object.assign(part, at || this.freeSpot(part));
    this.parts.push(part);
    this.mount(part);
    this.layout();
    this.changed();
    return part;
  }

  remove(part) {
    this.unmount(part);
    this.parts = this.parts.filter(p => p !== part);
    if (this.selected === part) this.select(null);
    this.layout();
    this.changed();
  }

  /* Свободное место над или под платой */
  freeSpot(part) {
    const {w, h} = this.partBox(part);
    const boxes = this.parts.map(p => ({...this.partBox(p), x: p.x, y: p.y}));
    boxes.push({x: BOARD_AT.x - 10, y: BOARD_AT.y - 10, w: this.board.width + 20, h: this.board.height + 20});
    const hit = (x, y) => boxes.some(b => x < b.x + b.w + 16 && x + w + 16 > b.x && y < b.y + b.h + 16 && y + h + 16 > b.y);
    const rows = [BOARD_AT.y - h - 60, BOARD_AT.y + this.board.height + 70];
    for (let k = 1; k < 6; k++) rows.push(BOARD_AT.y - h - 60 - k * 150, BOARD_AT.y + this.board.height + 70 + k * 170);
    for (const y of rows) {
      if (y < 4) continue;
      for (let x = 4; x < 900; x += 12) if (!hit(x, y)) return {x, y};
    }
    return {x: 600, y: 20};
  }

  partBox(part) {
    const {w, h} = sizeOf(part);
    return {w, h: h + controlRows(PARTS[part.type]) * CONTROL_ROW};
  }

  load(diagram) {
    for (const part of this.parts) this.unmount(part);
    this.parts = [];
    for (const raw of (diagram?.parts || []).slice(0, MAX_PARTS)) {
      const def = PARTS[raw?.type];
      if (!def) continue;
      const part = this.newPart(raw.type, false);
      part.id = String(raw.id || part.id).slice(0, 40);
      part.x = Number(raw.x) || 0; part.y = Number(raw.y) || 0;
      for (const pin of def.pins) {
        const value = raw.pins?.[pin.id];
        part.pins[pin.id] = this.fixedPin(pin) || (this.board.pins.some(p => p.id === value) ? value : null);
      }
      for (const key of Object.keys(def.props || {})) {
        const value = raw.props?.[key];
        if (def.props[key].options.some(([v]) => v === value)) part.props[key] = value;
      }
      for (const key of SAVED_STATE) if (typeof raw.state?.[key] === 'number' || typeof raw.state?.[key] === 'boolean') part.state[key] = raw.state[key];
      this.parts.push(part);
      this.mount(part);
    }
    this.select(null);
    this.layout();
    this.setZoom(this.fitZoom(), false);
  }

  toJSON() {
    return {
      version: 1, board: this.board.id,
      parts: this.parts.map(p => ({
        id: p.id, type: p.type, x: Math.round(p.x), y: Math.round(p.y), pins: {...p.pins}, props: {...p.props},
        state: Object.fromEntries(SAVED_STATE.filter(k => p.state[k] !== undefined).map(k => [k, p.state[k]])),
      })),
    };
  }

  changed() {
    clearTimeout(this.saveTimer);
    this.saveTimer = setTimeout(() => this.onChange(this.toJSON()), 250);
  }

  /* ---------- детали на сцене ---------- */
  mount(part) {
    const def = PARTS[part.type];
    const {w, h} = sizeOf(part);
    const rows = controlRows(def);
    const el = document.createElement('div');
    el.className = 'cc-part';
    el.dataset.id = part.id;
    el.dataset.type = part.type;
    el.tabIndex = 0;
    el.setAttribute('role', 'button');
    el.setAttribute('aria-label', def.title);
    el.title = def.title;
    el.innerHTML = `${def.controls ? `<div class="cc-controls" style="height:${rows * CONTROL_ROW}px">${def.controls(part)}</div>` : ''}
      <svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}">${def.art(part)}</svg>`;
    this.partsLayer.appendChild(el);
    const ctx = this.context(part, el);
    this.instances.set(part.id, ctx);
    this.dragging(part, el);
    def.bind?.(ctx);
    def.render?.(ctx);
    def.idle?.(ctx);
    if (this.io) this.startPart(ctx);
    this.place(part);
  }

  unmount(part) {
    const ctx = this.instances.get(part.id);
    if (ctx) { this.stopPart(ctx); ctx.el.remove(); }
    this.sound(part.id, 0);
    this.instances.delete(part.id);
  }

  remount(part) {
    this.unmount(part);
    this.mount(part);
    this.layout();
  }

  place(part) {
    const el = this.instances.get(part.id)?.el;
    if (el) Object.assign(el.style, {left: `${part.x}px`, top: `${part.y}px`});
  }

  context(part, el) {
    const circuit = this;
    const def = PARTS[part.type];
    const ctx = {
      part, def, el, state: part.state, cleanups: [],
      get io() { return circuit.io; },
      q: role => el.querySelector(`[data-r="${role}"], [data-ctl="${role}"]`),
      pin: role => part.pins[role] || null,
      pinCode: role => pinCode(part.pins[role]),
      read: role => (circuit.io && part.pins[role] ? circuit.io.read(part.pins[role]) : IDLE),
      digital: (role, value) => { if (circuit.io && part.pins[role]) circuit.io.setDigital(part.pins[role], value ? 1 : 0); },
      volts: (role, volts) => { if (circuit.io && part.pins[role]) circuit.io.setAnalog(part.pins[role], volts); },
      analog: (role, fraction) => ctx.volts(role, fraction * circuit.board.adcVolts),
      apply: () => def.apply?.(ctx),
      render: () => def.render?.(ctx),
      changed: () => circuit.changed(),
      sound: freq => circuit.sound(part.id, freq),
      scale: () => circuit.zoom,
      cleanup: fn => { if (fn) ctx.cleanups.push(fn); },
      press: (target, fn) => {
        let down = false;
        target.addEventListener('pointerdown', e => {
          e.stopPropagation(); e.preventDefault();
          target.setPointerCapture(e.pointerId);
          down = true; fn(true);
        });
        const up = () => { if (down) { down = false; fn(false); } };
        for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) target.addEventListener(type, up);
      },
      flash: (roles, color, beam) => {
        const els = roles.map(r => ctx.q(r)).filter(Boolean);
        const old = els.map(e => e.getAttribute('fill'));
        els.forEach(e => e.setAttribute('fill', color));
        if (beam) ctx.q(beam)?.setAttribute('opacity', 1);
        setTimeout(() => { els.forEach((e, i) => e.setAttribute('fill', old[i])); if (beam) ctx.q(beam)?.setAttribute('opacity', 0); }, 180);
      },
    };
    return ctx;
  }

  startPart(ctx) {
    try { ctx.def.start?.(ctx); } catch (error) { console.error(ctx.def.type, error); }
  }

  stopPart(ctx) {
    for (const fn of ctx.cleanups.splice(0)) { try { fn(); } catch { /* деталь уже отключена */ } }
    ctx.poll = null;
    for (const key of ['lcd', 'oled', 'tracker']) delete ctx.state[key];
    try { ctx.def.idle?.(ctx); } catch (error) { console.error(error); }
    this.sound(ctx.part.id, 0);
  }

  /* ---------- перетаскивание ---------- */
  dragging(part, el) {
    let start = null;
    el.addEventListener('pointerdown', e => {
      if (e.button || e.target.closest('[data-ctl], input, select, button, label')) return;
      e.preventDefault();
      el.setPointerCapture(e.pointerId);
      start = {x: e.clientX, y: e.clientY, px: part.x, py: part.y, moved: false};
      el.focus({preventScroll: true});
    });
    el.addEventListener('pointermove', e => {
      if (!start) return;
      const dx = (e.clientX - start.x) / this.zoom, dy = (e.clientY - start.y) / this.zoom;
      if (!start.moved && Math.hypot(dx, dy) < 4) return;
      start.moved = true;
      part.x = Math.max(0, Math.round(start.px + dx));
      part.y = Math.max(0, Math.round(start.py + dy));
      this.place(part);
      this.drawWires();
    });
    const end = () => {
      if (!start) return;
      const moved = start.moved;
      start = null;
      if (moved) { this.layout(); this.changed(); } else this.select(part);
    };
    el.addEventListener('pointerup', end);
    el.addEventListener('pointercancel', end);
    el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); this.select(part); } });
  }

  /* ---------- провода и размеры сцены ---------- */
  pinAnchor(part, role) {
    const def = PARTS[part.type];
    const custom = def.pinPos?.(part)?.[role];
    const pin = def.pins.find(p => p.id === role);
    const [x, y] = custom || [pin.x, pin.y];
    return [part.x + x, part.y + y + controlRows(def) * CONTROL_ROW];
  }

  drawWires() {
    const bx = BOARD_AT.x, by = BOARD_AT.y;
    const paths = [], dots = [], labels = [];
    for (const part of this.parts) {
      PARTS[part.type].pins.forEach((pin, i) => {
        const [px, py] = this.pinAnchor(part, pin.id);
        labels.push(`<text x="${px}" y="${py + 11}" class="cc-pinlabel">${esc(pin.label)}</text>`);
        const boardPin = this.board.pins.find(p => p.id === part.pins[pin.id]);
        if (!boardPin) return;
        const color = WIRE_COLORS[i % WIRE_COLORS.length];
        const x1 = bx + boardPin.x, y1 = by + boardPin.y;
        const out = boardPin.side === 'top' ? -70 : 70;
        const selected = this.selected === part ? ' cc-wire-on' : '';
        paths.push(`<path class="cc-wire${selected}" d="M${x1} ${y1}C${x1} ${y1 + out} ${px} ${py + 60} ${px} ${py}" stroke="${color}"/>`);
        dots.push(`<circle cx="${x1}" cy="${y1}" r="4" fill="${color}" stroke="#0008"/>`);
      });
    }
    this.wires.innerHTML = paths.join('') + dots.join('') + labels.join('');
  }

  layout() {
    let w = BOARD_AT.x + this.board.width + 40, h = BOARD_AT.y + this.board.height + 120;
    for (const part of this.parts) {
      const box = this.partBox(part);
      w = Math.max(w, part.x + box.w + 30);
      h = Math.max(h, part.y + box.h + 30);
    }
    this.size = {w: Math.max(w, 520), h: Math.max(h, 560)};
    Object.assign(this.stage.style, {width: `${this.size.w}px`, height: `${this.size.h}px`});
    this.wires.setAttribute('width', this.size.w);
    this.wires.setAttribute('height', this.size.h);
    this.drawWires();
    this.setZoom(this.zoom, false);
  }

  /* Вся схема в окне: по ширине и по наибольшей высоте окна схемы (max-height из CSS) */
  fitZoom() {
    const width = this.view.clientWidth - 8;
    if (width <= 0 || !this.size) return 1;
    const maxHeight = parseFloat(getComputedStyle(this.view).maxHeight);
    const byHeight = Number.isFinite(maxHeight) ? (maxHeight - 8) / this.size.h : Infinity;
    return Math.min(1.25, Math.max(0.3, Math.min(width / this.size.w, byHeight)));
  }

  setZoom(z, user = true) {
    if (user) this.userZoom = true;
    this.zoom = Math.min(2.5, Math.max(0.25, z));
    this.stage.style.transform = `scale(${this.zoom})`;
    if (this.size) Object.assign(this.sizer.style, {width: `${this.size.w * this.zoom}px`, height: `${this.size.h * this.zoom}px`});
  }

  scrollTo(part) {
    this.view.scrollTo({left: part.x * this.zoom - 20, top: part.y * this.zoom - 20, behavior: 'smooth'});
  }

  /* ---------- настройки детали ---------- */
  select(part) {
    this.selected = part;
    for (const [id, ctx] of this.instances) ctx.el.classList.toggle('cc-selected', part?.id === id);
    this.drawWires();
    if (!part) { this.inspector.hidden = true; return; }
    const def = PARTS[part.type];
    const used = this.usedPins(part);
    const titleOf = p => PARTS[p.type].title;
    const pinRow = pin => {
      if (pin.need === 'sda' || pin.need === 'scl') {
        return `<div class="cc-row"><span>${pin.label}</span><b>${esc(this.board.pins.find(p => p.id === part.pins[pin.id])?.label || part.pins[pin.id])} (шина I2C)</b></div>`;
      }
      const options = this.candidates(pin).map(p => {
        const other = used.get(p.id);
        const pwm = p.caps.has('pwm') && this.board.id === 'uno' ? ' ~ШИМ' : '';
        return `<option value="${p.id}" ${part.pins[pin.id] === p.id ? 'selected' : ''}>${esc(p.id)}${pwm}${other ? ` · занят: ${esc(titleOf(other))}` : ''}</option>`;
      }).join('');
      const hint = pin.need === 'analog' ? ' (АЦП)' : pin.need === 'int' ? ' (прерывание)' : pin.prefer === 'pwm' ? ' (лучше ШИМ ~)' : '';
      return `<label class="cc-row"><span>${esc(pin.label)}${hint}</span><select data-pin="${pin.id}"><option value="">— не подключено —</option>${options}</select></label>`;
    };
    const propRow = ([key, prop]) => `<label class="cc-row"><span>${esc(prop.label)}</span><select data-prop="${key}">${prop.options.map(([v, label]) =>
      `<option value="${esc(v)}" ${part.props[key] === v ? 'selected' : ''}>${esc(label)}</option>`).join('')}</select></label>`;
    const note = def.note ? `<p class="cc-note">${esc(def.note)}</p>` : this.board.id === 'esp32' && def.esp32 === 'helper'
      ? '<p class="cc-note">В эмуляторе ESP32 эта деталь работает через функции oc_* из oc_hw.h — они есть в примере кода.</p>' : '';
    this.inspector.innerHTML = `<div class="cc-insp-head"><b>${esc(def.title)}</b><button type="button" class="cc-icon" data-act="close" aria-label="Закрыть">×</button></div>
      ${def.pins.map(pinRow).join('')}${Object.entries(def.props || {}).map(propRow).join('')}${note}
      <div class="cc-actions">${this.onExample ? '<button type="button" data-act="example">Вставить пример кода</button>' : ''}
      <button type="button" data-act="delete" class="cc-danger">Удалить</button></div>`;
    this.inspector.hidden = false;
    this.inspector.querySelector('[data-act="close"]').onclick = () => this.select(null);
    this.inspector.querySelector('[data-act="delete"]').onclick = () => this.remove(part);
    const example = this.inspector.querySelector('[data-act="example"]');
    if (example) example.onclick = () => this.onExample(def.example(role => pinCode(part.pins[role]), this.board.id, part), part);
    for (const select of this.inspector.querySelectorAll('select[data-pin]')) {
      select.onchange = () => { part.pins[select.dataset.pin] = select.value || null; this.restart(part); this.select(part); this.changed(); };
    }
    for (const select of this.inspector.querySelectorAll('select[data-prop]')) {
      select.onchange = () => {
        part.props[select.dataset.prop] = select.value;
        this.remount(part); this.select(part); this.changed();
      };
    }
  }

  restart(part) {
    const ctx = this.instances.get(part.id);
    if (!ctx || !this.io) { this.drawWires(); return; }
    this.stopPart(ctx);
    this.startPart(ctx);
    this.drawWires();
  }

  /* ---------- работа прошивки ---------- */
  run(io) {
    this.stop();
    this.io = io;
    this.audio();  // вызывается из клика «Запустить» — браузер разрешит звук
    for (const ctx of this.instances.values()) this.startPart(ctx);
    let last = performance.now();
    const tick = now => {
      if (this.io !== io) return;
      const dt = Math.min(0.1, (now - last) / 1000);
      last = now;
      for (const ctx of this.instances.values()) {
        try { ctx.poll?.(); ctx.def.frame?.(ctx, dt); } catch (error) { console.error(ctx.def.type, error); }
      }
      const builtin = this.board.builtinLed;
      const led = this.$(`.cc-boardart [data-r="${builtin.role}"]`);
      if (led) led.setAttribute('fill', io.read(builtin.pin).level === 1 ? '#ffb020' : '#5b4a2a');
      this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  }

  stop() {
    cancelAnimationFrame(this.raf);
    if (!this.io) return;
    this.io = null;
    for (const ctx of this.instances.values()) this.stopPart(ctx);
    const led = this.$(`.cc-boardart [data-r="${this.board.builtinLed.role}"]`);
    if (led) led.setAttribute('fill', '#5b4a2a');
  }

  /* ---------- звук пищалок ---------- */
  audio() {
    try {
      this.audioCtx ||= new (window.AudioContext || window.webkitAudioContext)();
      if (this.audioCtx.state === 'suspended') this.audioCtx.resume();
    } catch { this.audioCtx = null; }
    return this.audioCtx;
  }

  sound(id, freq) {
    let osc = this.oscillators.get(id);
    if (!freq || this.muted || !this.audioCtx) {
      if (osc) { osc.gain.gain.setTargetAtTime(0, this.audioCtx.currentTime, 0.01); osc.node.stop(this.audioCtx.currentTime + 0.05); this.oscillators.delete(id); }
      return;
    }
    const ac = this.audioCtx;
    if (!osc) {
      const node = ac.createOscillator(), gain = ac.createGain();
      node.type = 'square';
      gain.gain.value = 0;
      node.connect(gain).connect(ac.destination);
      node.start();
      gain.gain.setTargetAtTime(0.04, ac.currentTime, 0.01);
      osc = {node, gain, freq: 0};
      this.oscillators.set(id, osc);
    }
    if (Math.abs(osc.freq - freq) > 1) { osc.node.frequency.setValueAtTime(freq, ac.currentTime); osc.freq = freq; }
  }
}
