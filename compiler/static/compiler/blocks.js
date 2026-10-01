/* Блоки в стиле Scratch: Blockly + генератор Python. Подключается до app.js и отдаёт window.OCBlocks.

   Проект блоков хранится как два файла: blocks.json (сериализованные блоки) и main.py (сгенерированный код).
   app.js кладёт их в обычную модель проекта, поэтому запуск, сохранение и шаринг работают как у любого языка.
*/
(() => {
  "use strict";

  const BLOCKLY = "https://cdn.jsdelivr.net/npm/blockly@13.3.0";
  // Порядок важен: ядро, стандартные блоки, генератор Python, русские подписи
  const SCRIPTS = ["blockly_compressed.js", "blocks_compressed.js", "python_compressed.js", "msg/ru.js"];

  // Цвета категорий — как в Scratch, чтобы блоки узнавались с первого взгляда
  const COLORS = {
    logic: "#4C97FF", loops: "#FFAB19", math: "#59C059", text: "#9966FF",
    lists: "#FF661A", variables: "#FF8C1A", functions: "#FF6680",
  };
  COLORS.io = COLORS.text;  // «напечатать» и «запросить» — текстовые блоки, пусть и категория будет того же цвета

  // Стили блоков Blockly -> цвета категорий: полоска в меню и сам блок совпадают
  const BLOCK_STYLES = {
    logic_blocks: COLORS.logic, loop_blocks: COLORS.loops, math_blocks: COLORS.math, text_blocks: COLORS.text,
    list_blocks: COLORS.lists, variable_blocks: COLORS.variables, variable_dynamic_blocks: COLORS.variables,
    procedure_blocks: COLORS.functions,
  };

  const block = (type, extra = {}) => ({ kind: "block", type, ...extra });
  const shadowNum = (n) => ({ shadow: { type: "math_number", fields: { NUM: n } } });
  const shadowText = (t) => ({ shadow: { type: "text", fields: { TEXT: t } } });

  const TOOLBOX = {
    kind: "categoryToolbox",
    contents: [
      { kind: "category", name: "Ввод и вывод", colour: COLORS.io, contents: [
        block("text_print", { inputs: { TEXT: shadowText("Привет!") } }),
        block("text_prompt_ext", { fields: { TYPE: "TEXT" }, inputs: { TEXT: shadowText("Как тебя зовут?") } }),
        block("text_prompt_ext", { fields: { TYPE: "NUMBER" }, inputs: { TEXT: shadowText("Введи число:") } }),
      ] },
      { kind: "category", name: "Логика", colour: COLORS.logic, contents: [
        block("controls_if"), block("controls_if", { extraState: { hasElse: true } }),
        block("logic_compare"), block("logic_operation"), block("logic_negate"), block("logic_boolean"),
      ] },
      { kind: "category", name: "Циклы", colour: COLORS.loops, contents: [
        block("controls_repeat_ext", { inputs: { TIMES: shadowNum(10) } }),
        block("controls_whileUntil"),
        block("controls_for", { inputs: { FROM: shadowNum(1), TO: shadowNum(10), BY: shadowNum(1) } }),
        block("controls_forEach"), block("controls_flow_statements"),
      ] },
      { kind: "category", name: "Математика", colour: COLORS.math, contents: [
        block("math_number"), block("math_arithmetic", { inputs: { A: shadowNum(1), B: shadowNum(1) } }),
        block("math_single"), block("math_modulo", { inputs: { DIVIDEND: shadowNum(10), DIVISOR: shadowNum(3) } }),
        block("math_random_int", { inputs: { FROM: shadowNum(1), TO: shadowNum(100) } }),
        block("math_round"), block("math_number_property"),
      ] },
      { kind: "category", name: "Текст", colour: COLORS.text, contents: [
        block("text"), block("text_join"), block("text_length"), block("text_isEmpty"),
        block("text_changeCase"), block("text_indexOf"), block("text_charAt"),
      ] },
      { kind: "category", name: "Списки", colour: COLORS.lists, contents: [
        block("lists_create_with"), block("lists_create_with", { extraState: { itemCount: 0 } }),
        block("lists_repeat", { inputs: { NUM: shadowNum(5) } }), block("lists_length"),
        block("lists_getIndex"), block("lists_setIndex"), block("lists_sort"),
      ] },
      { kind: "sep" },
      { kind: "category", name: "Переменные", colour: COLORS.variables, custom: "VARIABLE" },
      { kind: "category", name: "Функции", colour: COLORS.functions, custom: "PROCEDURE" },
    ],
  };

  // Стартовая программа: спросить имя, поздороваться, повторить фразу — видно и ввод, и цикл
  const STARTER = {
    blocks: { languageVersion: 0, blocks: [{
      type: "variables_set", x: 40, y: 40, fields: { VAR: { id: "name" } },
      inputs: { VALUE: { block: { type: "text_prompt_ext", fields: { TYPE: "TEXT" },
        inputs: { TEXT: { shadow: { type: "text", fields: { TEXT: "Как тебя зовут? " } } } } } } },
      next: { block: {
        type: "text_print",
        inputs: { TEXT: { block: { type: "text_join", extraState: { itemCount: 3 }, inputs: {
          ADD0: { block: { type: "text", fields: { TEXT: "Привет, " } } },
          ADD1: { block: { type: "variables_get", fields: { VAR: { id: "name" } } } },
          ADD2: { block: { type: "text", fields: { TEXT: "!" } } },
        } } } },
        next: { block: {
          type: "controls_repeat_ext",
          inputs: {
            TIMES: { shadow: { type: "math_number", fields: { NUM: 3 } } },
            DO: { block: { type: "text_print", inputs: { TEXT: { shadow: { type: "text",
              fields: { TEXT: "Блоки — это тоже программирование!" } } } } } },
          },
        } },
      } },
    }] },
    variables: [{ name: "name", id: "name" }],
  };

  let loading = null;
  let workspace = null;
  let onChange = () => {};
  let silent = false;  // во время load() изменения не считаются правкой пользователя

  // UMD-сборки Blockly при живом AMD-загрузчике Monaco зарегистрировались бы как AMD-модули.
  // Поэтому забираем код fetch-ем и выполняем глобально, на это время спрятав define.
  async function evalGlobal(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
    const code = await res.text();
    const savedDefine = window.define;
    window.define = undefined;
    try {
      (0, eval)(code);  // непрямой eval — выполнение в глобальной области
    } finally {
      window.define = savedDefine;
    }
  }

  function ensureLoaded() {
    if (!loading) {
      loading = (async () => {
        for (const file of SCRIPTS) await evalGlobal(`${BLOCKLY}/${file}`);
        if (!window.Blockly || !window.python) throw new Error("Blockly не загрузился");
      })();
      loading.catch(() => { loading = null; });  // при сетевой ошибке дадим попробовать ещё раз
    }
    return loading;
  }

  function theme(dark) {
    const B = window.Blockly;
    return B.Theme.defineTheme(dark ? "oc-dark" : "oc-light", {
      base: B.Themes.Classic,
      blockStyles: Object.fromEntries(Object.entries(BLOCK_STYLES).map(([name, colour]) => [name, { colourPrimary: colour }])),
      componentStyles: dark ? {
        workspaceBackgroundColour: "#171a22", toolboxBackgroundColour: "#1d212b", toolboxForegroundColour: "#e6e8ee",
        flyoutBackgroundColour: "#262b37", flyoutForegroundColour: "#e6e8ee", flyoutOpacity: 0.96,
        scrollbarColour: "#4a5163", insertionMarkerColour: "#ffffff", cursorColour: "#9b82ff",
      } : {
        workspaceBackgroundColour: "#ffffff", toolboxBackgroundColour: "#f7f8fa", toolboxForegroundColour: "#1a1d24",
        flyoutBackgroundColour: "#eceef3", flyoutForegroundColour: "#1a1d24", flyoutOpacity: 0.96,
      },
      fontStyle: { family: "Inter, system-ui, sans-serif", size: 12 },
    });
  }

  function generate() {
    const python = window.python.pythonGenerator.workspaceToCode(workspace);
    const json = JSON.stringify(window.Blockly.serialization.workspaces.save(workspace));
    return { json, python: python.trim() ? python : "# Собери программу из блоков слева\n" };
  }

  async function mount(container, options) {
    await ensureLoaded();
    onChange = options.onChange || onChange;
    if (workspace) return workspace;
    workspace = window.Blockly.inject(container, {
      toolbox: TOOLBOX,
      renderer: "zelos",  // круглые «пазлы», как в Scratch
      theme: theme(options.dark),
      trashcan: true,
      zoom: { controls: true, wheel: true, startScale: 0.85, maxScale: 2, minScale: 0.4 },
      grid: { spacing: 24, length: 2, colour: options.dark ? "#262b37" : "#e1e4ea", snap: true },
      move: { scrollbars: true, drag: true, wheel: false },
    });
    workspace.addChangeListener((e) => {
      if (silent || e.isUiEvent) return;
      const { json, python } = generate();
      onChange(json, python);
    });
    return workspace;
  }

  // Загрузить блоки из JSON (или стартовую программу); вернуть {json, python} для модели проекта
  function load(jsonText) {
    const B = window.Blockly;
    let state = STARTER;
    if (jsonText) {
      try { state = JSON.parse(jsonText); } catch { state = STARTER; }
    }
    silent = true;
    try {
      workspace.clear();
      try {
        B.serialization.workspaces.load(state, workspace);
      } catch {
        B.serialization.workspaces.load(STARTER, workspace);  // испорченный blocks.json — не роняем редактор
      }
      workspace.scrollCenter();
    } finally {
      silent = false;
    }
    return generate();
  }

  function setDark(dark) {
    if (workspace) workspace.setTheme(theme(dark));
  }

  function resize() {
    // На следующем кадре: размер контейнера к этому моменту уже посчитан браузером
    if (workspace) requestAnimationFrame(() => window.Blockly.svgResize(workspace));
  }

  window.OCBlocks = { ensureLoaded, mount, load, setDark, resize, get workspace() { return workspace; } };
})();
