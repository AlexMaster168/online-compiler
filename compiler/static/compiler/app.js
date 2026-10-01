/* Online Compiler — фронтенд. Без фреймворков: Monaco + ванильный JS. */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const MONACO_BASE = window.MONACO_BASE;

  const STATUS = {
    ok:             { label: "Успешно",            kind: "ok" },
    compile_error:  { label: "Ошибка компиляции",  kind: "err" },
    runtime_error:  { label: "Ошибка выполнения",  kind: "err" },
    timeout:        { label: "Лимит времени",      kind: "warn" },
    memory_limit:   { label: "Лимит памяти",       kind: "warn" },
    output_limit:   { label: "Лимит вывода",       kind: "warn" },
    unavailable:    { label: "Недоступно",         kind: "warn" },
    internal_error: { label: "Сбой движка",        kind: "err" },
  };

  // Должно совпадать с compiler/engine/project.py
  const MAX_FILES = 20;
  const MAX_DEPTH = 4;
  const SEGMENT_RE = /^[A-Za-z0-9_][A-Za-z0-9_.+-]{0,63}$/;
  const RESERVED = new Set(["main", "main.exe", "main.jar", "out", "obj", "bin", "main.csproj", "__utf8console.cs"]);

  const state = {
    languages: [],
    bySlug: {},
    lang: null,
    editor: null,
    monaco: null,
    running: false,
    lastResult: null,
    fontSize: 14,
    wrap: false,
    limits: null,
    files: [],       // [{ name, model, decorations }], files[0] — главный файл языка
    active: 0,
    pending: null,   // проект, который надо открыть, когда Monaco догрузится
    mode: "console", // console — живой ввод через WebSocket, batch — stdin заранее
    lastByMode: {},  // последний результат в каждом режиме
  };

  // ---------- storage (может быть недоступно в приватном режиме) ----------
  const store = {
    get(key, fallback = null) {
      try { const v = localStorage.getItem("oc:" + key); return v === null ? fallback : JSON.parse(v); }
      catch { return fallback; }
    },
    set(key, value) {
      try { localStorage.setItem("oc:" + key, JSON.stringify(value)); } catch { /* ignore */ }
    },
  };

  // ---------- helpers ----------
  const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const stripAnsi = (s) => s.replace(/\x1b\[[0-9;?]*[ -\/]*[@-~]/g, "");
  const formatBytes = (n) => n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(1)} KB` : `${(n / 1048576).toFixed(1)} MB`;
  const formatMs = (ms) => ms == null ? "—" : ms < 1000 ? `${ms} мс` : `${(ms / 1000).toFixed(2)} с`;
  const formatKb = (kb) => kb == null ? "—" : kb < 1024 ? `${kb} КБ` : `${(kb / 1024).toFixed(1)} МБ`;
  const pluralFiles = (n) => `${n} ${n % 10 === 1 && n % 100 !== 11 ? "файл" : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? "файла" : "файлов"}`;
  const ICON_CLOSE = `<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>`;

  function csrfToken() {
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  async function api(url, body, method) {
    const opts = body === undefined && !method ? {} : {
      method: method || "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      body: body === undefined ? undefined : JSON.stringify(body),
    };
    const res = await fetch(url, { credentials: "same-origin", ...opts });
    let data = null;
    try { data = await res.json(); } catch { /* not json */ }
    if (!res.ok) throw new Error((data && data.error) || `HTTP ${res.status}`);
    return data;
  }

  let toastTimer = null;
  function toast(text) {
    const el = $("toast");
    el.textContent = text;
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { el.hidden = true; }, 2600);
  }

  // Monaco при удалении модели отменяет задачи воркеров и роняет безвредный reject "Canceled"
  window.addEventListener("unhandledrejection", (e) => {
    if (e.reason && (e.reason.name === "Canceled" || e.reason.message === "Canceled")) e.preventDefault();
  });

  const readJsonScript = (id) => {
    try { return JSON.parse($(id).textContent); } catch { return null; }
  };

  // ---------- theme ----------
  function currentTheme() {
    return document.documentElement.dataset.theme;
  }
  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    if (state.monaco) state.monaco.editor.setTheme(theme === "light" ? "oc-light" : "oc-dark");
  }
  applyTheme(store.get("theme") || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"));

  // ---------- project model ----------
  const fileNames = () => state.files.map((f) => f.name);
  const activeFile = () => state.files[state.active];

  function projectPayload() {
    const [main, ...rest] = state.files;
    return {
      code: main ? main.model.getValue() : "",
      files: rest.map((f) => ({ name: f.name, content: f.model.getValue() })),
      args: $("argsInput").value.trim(),
    };
  }

  function monacoLanguageFor(name) {
    const lower = name.toLowerCase();
    const lang = state.lang;
    if (lang) {
      const mainExt = lang.filename.slice(lang.filename.lastIndexOf(".")).toLowerCase();
      if (lower.endsWith(mainExt) || (lang.sources || []).some((ext) => lower.endsWith(ext))) return lang.monaco;
    }
    if (/\.(h|hpp|hh|hxx)$/.test(lower)) return lang?.slug === "c" ? "c" : "cpp";
    for (const l of state.monaco.languages.getLanguages()) {
      if ((l.extensions || []).some((ext) => lower.endsWith(ext.toLowerCase()))) return l.id;
    }
    return "plaintext";
  }

  // Маркеры живут по URI дольше модели — без очистки старая ошибка всплывёт на новом файле с тем же именем
  function disposeModel(model) {
    state.monaco.editor.setModelMarkers(model, "oc", []);
    model.dispose();
  }

  function createFile(name, content) {
    const { monaco } = state;
    // URI как у настоящего файла — TS/JS-воркер видит импорты между вкладками
    const uri = monaco.Uri.parse(`file:///project/${name}`);
    const stale = monaco.editor.getModel(uri);
    if (stale) disposeModel(stale);
    const model = monaco.editor.createModel(content, monacoLanguageFor(name), uri);
    // Код исполняется в Linux: CRLF из Windows-файлов ломает bash-скрипты и т.п.
    model.setEOL(monaco.editor.EndOfLineSequence.LF);
    model.updateOptions(indentOptions());
    model.onDidChangeContent(scheduleDraftSave);
    return { name, model, decorations: [], bpIds: [] };
  }

  // Полностью заменяет проект: главный файл + дополнительные (+ брейкпоинты из черновика)
  function setProject({ code, files = [], breakpoints = {}, args = "" }) {
    $("argsInput").value = typeof args === "string" ? args : "";
    if (!state.monaco) { state.pending = { code, files, breakpoints, args }; return; }
    // Сначала отвязываем модель от редактора: иначе асинхронные виджеты (sticky scroll)
    // досчитываются по уже уничтоженной модели и падают с «Illegal value for lineNumber»
    state.editor.setModel(null);
    state.files.forEach((f) => disposeModel(f.model));
    state.files = [createFile(state.lang.filename, code), ...files.map((f) => createFile(f.name, f.content))];
    for (const file of state.files) {
      const lines = (breakpoints[file.name] || []).filter((l) => Number.isInteger(l) && l >= 1 && l <= file.model.getLineCount());
      if (lines.length) setFileBreakpoints(file, lines);
    }
    openFile(0);
    if (isBlocks()) syncBlocksFromProject();
  }

  function openFile(index) {
    const file = state.files[index];
    if (!file) return;
    state.active = index;
    state.editor.setModel(file.model);
    renderTabs();
    updateStatus();
    state.editor.focus();
  }

  function validateName(name, exceptIndex = -1) {
    if (!name) return "Введи имя файла";
    const parts = name.split("/");
    if (parts.length > MAX_DEPTH || !parts.every((p) => SEGMENT_RE.test(p))) {
      return "Латиница, цифры, _ . + -; папки через /";
    }
    if (RESERVED.has(parts[0].toLowerCase())) return `«${parts[0]}» зарезервировано`;
    const lower = name.toLowerCase();
    const names = fileNames().map((n) => n.toLowerCase());
    if (names.some((n, i) => i !== exceptIndex && n === lower)) return "Такой файл уже есть";
    const conflict = names.some((n, i) => i !== exceptIndex && (n.startsWith(lower + "/") || lower.startsWith(n + "/")));
    if (conflict) return "Путь не может быть и файлом, и папкой";
    return null;
  }

  function suggestName() {
    const ext = state.lang.filename.slice(state.lang.filename.lastIndexOf("."));
    const base = { ".java": "Helper", ".cs": "Helper", ".kt": "Helper", ".c": "utils", ".cpp": "utils" }[ext] || "utils";
    for (let i = 0; ; i++) {
      const name = `${base}${i || ""}${ext}`;
      if (!validateName(name)) return name;
    }
  }

  // Встроенное поле ввода имени прямо в полосе вкладок (без модалок)
  function promptName({ initial, anchor, onSubmit }) {
    const input = document.createElement("input");
    input.className = "tab-input";
    input.value = initial;
    input.spellcheck = false;
    input.setAttribute("aria-label", "Имя файла");
    if (anchor) anchor.replaceWith(input); else $("tabs").appendChild(input);
    input.focus();
    const dot = initial.lastIndexOf(".");
    input.setSelectionRange(0, dot > 0 ? dot : initial.length);

    let done = false;
    const finish = (commit) => {
      if (done) return;
      const name = input.value.trim();
      if (commit) {
        const error = onSubmit(name);
        if (error) { input.classList.add("invalid"); input.title = error; toast(error); input.focus(); return; }
      }
      done = true;
      renderTabs();
    };
    input.addEventListener("input", () => input.classList.remove("invalid"));
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); finish(true); }
      else if (e.key === "Escape") { e.preventDefault(); done = true; renderTabs(); state.editor?.focus(); }
    });
    input.addEventListener("blur", () => setTimeout(() => { if (!done) { done = true; renderTabs(); } }, 0));
    input.scrollIntoView({ inline: "nearest", block: "nearest" });
  }

  function addFile(name, content = "") {
    const error = validateName(name);
    if (error) return error;
    if (state.files.length - 1 >= MAX_FILES) return `Максимум ${MAX_FILES} дополнительных файлов`;
    state.files.push(createFile(name, content));
    openFile(state.files.length - 1);
    scheduleDraftSave();
    return null;
  }

  function newFile() {
    if (!state.monaco) return;
    promptName({ initial: suggestName(), onSubmit: (name) => addFile(name) });
  }

  function renameFile(index) {
    if (index === 0) { toast(`${state.lang.filename} — главный файл, его имя задаёт язык`); return; }
    const tab = $("tabs").querySelector(`.tab[data-i="${index}"]`);
    promptName({
      initial: state.files[index].name,
      anchor: tab,
      onSubmit: (name) => {
        if (name === state.files[index].name) return null;
        const error = validateName(name, index);
        if (error) return error;
        const old = state.files[index];
        const oldLines = bpLines(old);
        state.files[index] = createFile(name, old.model.getValue());
        if (oldLines.length) setFileBreakpoints(state.files[index], oldLines);  // брейкпоинты едут вместе с файлом
        openFile(index);       // сначала переключаем редактор на новую модель,
        disposeModel(old.model);  // и только потом уничтожаем старую
        scheduleDraftSave();
        return null;
      },
    });
  }

  function deleteFile(index) {
    if (index === 0) return;
    const file = state.files[index];
    if (file.model.getValueLength() > 0 && !confirm(`Удалить ${file.name}?`)) return;
    state.files.splice(index, 1);
    openFile(Math.min(state.active >= index ? state.active - 1 : state.active, state.files.length - 1));
    disposeModel(file.model);  // после переключения редактора — см. setProject
    scheduleDraftSave();
  }

  function renderTabs() {
    const { monaco } = state;
    $("tabs").innerHTML = state.files.map((f, i) => {
      const hasError = monaco && monaco.editor.getModelMarkers({ owner: "oc", resource: f.model.uri })
        .some((m) => m.severity === monaco.MarkerSeverity.Error);
      const cls = ["tab", i === state.active && "active", i === 0 && "main", hasError && "err"].filter(Boolean).join(" ");
      const title = i === 0 ? "Главный файл — с него стартует программа" : "Двойной клик — переименовать";
      return `<div class="${cls}" role="tab" aria-selected="${i === state.active}" data-i="${i}" title="${title}">
        <span class="tab-dot"></span><span class="tab-name">${escapeHtml(f.name)}</span>
        ${i ? `<button class="tab-close" data-close="${i}" aria-label="Удалить ${escapeHtml(f.name)}">${ICON_CLOSE}</button>` : ""}
      </div>`;
    }).join("");
    $("tabs").querySelector(".tab.active")?.scrollIntoView({ inline: "nearest", block: "nearest" });
  }

  $("tabs").addEventListener("click", (e) => {
    const close = e.target.closest("[data-close]");
    if (close) { e.stopPropagation(); deleteFile(+close.dataset.close); return; }
    const tab = e.target.closest(".tab");
    if (tab && +tab.dataset.i !== state.active) openFile(+tab.dataset.i);
  });
  $("tabs").addEventListener("dblclick", (e) => {
    const tab = e.target.closest(".tab");
    if (tab) renameFile(+tab.dataset.i);
  });
  $("tabs").addEventListener("auxclick", (e) => {
    const tab = e.target.closest(".tab");
    if (tab && e.button === 1) deleteFile(+tab.dataset.i); // средняя кнопка, как в браузере
  });
  $("newFileBtn").addEventListener("click", newFile);

  // ---------- upload / drag & drop ----------
  async function importFiles(list) {
    if (!state.monaco) return;
    const maxBytes = (state.limits?.max_code_kb || 256) * 1024;
    let added = 0;
    const problems = [];
    for (const file of list) {
      const name = file.name.replace(/\s+/g, "_");
      if (file.size > maxBytes) { problems.push(`${file.name}: больше ${maxBytes / 1024} КБ`); continue; }
      const text = await file.text();
      if (text.includes("\0")) { problems.push(`${file.name}: бинарный файл`); continue; }

      const existing = fileNames().findIndex((n) => n.toLowerCase() === name.toLowerCase());
      if (existing >= 0) {
        state.files[existing].model.setValue(text);
        openFile(existing);
        added++;
        continue;
      }
      const error = addFile(name, text);
      if (error) problems.push(`${file.name}: ${error}`); else added++;
    }
    if (problems.length) toast(problems.join(" · "));
    else if (added) toast(`Добавлено: ${pluralFiles(added)}`);
  }

  $("uploadBtn").addEventListener("click", () => $("fileInput").click());
  $("fileInput").addEventListener("change", async (e) => {
    await importFiles([...e.target.files]);
    e.target.value = "";
  });

  (function initDrop() {
    const pane = document.querySelector(".editor-pane");
    let depth = 0;
    const hasFiles = (e) => [...(e.dataTransfer?.types || [])].includes("Files");
    pane.addEventListener("dragenter", (e) => {
      if (!hasFiles(e)) return;
      e.preventDefault();
      depth++;
      $("dropHint").hidden = false;
    });
    pane.addEventListener("dragover", (e) => { if (hasFiles(e)) e.preventDefault(); });
    pane.addEventListener("dragleave", () => { if (--depth <= 0) { depth = 0; $("dropHint").hidden = true; } });
    pane.addEventListener("drop", (e) => {
      if (!hasFiles(e)) return;
      e.preventDefault();
      depth = 0;
      $("dropHint").hidden = true;
      importFiles([...e.dataTransfer.files]);
    });
  })();

  // ---------- diagnostics: "utils.c:3:5: error: ..." → маркеры в нужном файле ----------
  function locationRegex(names) {
    // Длинные имена первыми, чтобы lib/util.py не матчился как util.py
    const alt = [...names].sort((a, b) => b.length - a.length).map(escapeRe).join("|");
    return new RegExp(
      `File "(?:[^"]*[\\\\/])?(${alt})", line (\\d+)` +
      `|(?<![\\w.-])(${alt})(?::(\\d+)(?::(\\d+))?|\\((\\d+),(\\d+)\\)| on line (\\d+)| line (\\d+))`,
      "g",
    );
  }
  const pickFile = (m) => m[1] || m[3];
  const pickLine = (m) => +(m[2] || m[4] || m[6] || m[8] || m[9]);
  const pickCol = (m) => +(m[5] || m[7] || 0);

  function parseDiagnostics(text, names, source) {
    if (!text || !names.length) return [];
    const lines = stripAnsi(text).split("\n");
    const re = locationRegex(names);
    const found = [];
    let header = "";
    const errorLine = [...lines].reverse().find((l) => /^\s*[\w.$]*(Error|Exception|error)\b.*:/.test(l)) || "";

    lines.forEach((raw, i) => {
      const line = raw.trim();
      if (/^(error|warning)(\[\w+\])?:\s*(.+)/i.test(line)) header = line;
      re.lastIndex = 0;
      const m = re.exec(raw);
      if (!m) return;
      let message = raw.slice(m.index + m[0].length).replace(/^[\s:,]+/, "").trim();
      // Haskell/rust: сообщение на следующей строке или в заголовке выше
      if (!message || /^(error|warning)(\s*\[[^\]]*\])?:?$/i.test(message) || /^in\s/.test(message)) {
        const next = (lines[i + 1] || "").trim();
        message = header || errorLine || (next && !next.startsWith("|") ? `${message} ${next}`.trim() : "") || message;
      }
      if (m[1] && errorLine) message = errorLine.trim(); // Python traceback
      const severity = /warning/i.test(message) ? "warning" : /^note/i.test(message) ? "info" : "error";
      found.push({ file: pickFile(m), line: pickLine(m), col: pickCol(m), message: message || "Ошибка", severity });
    });

    if (source === "runtime" && found.length) {
      // Для трейсбеков нужен один кадр: у Python — последний, у остальных — первый
      return [/File "/.test(text) ? found[found.length - 1] : found[0]];
    }
    const seen = new Set();
    return found.filter((d) => {
      const key = `${d.file}:${d.line}:${d.col}:${d.message}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function setMarkers(result) {
    const { monaco } = state;
    if (!monaco || !state.files.length) return;
    const names = fileNames();
    const diags = result ? [
      ...parseDiagnostics(result.compile_output, names, "compile"),
      ...parseDiagnostics(result.status === "ok" ? "" : result.stderr, names, "runtime"),
    ] : [];
    const sev = { error: monaco.MarkerSeverity.Error, warning: monaco.MarkerSeverity.Warning, info: monaco.MarkerSeverity.Info };

    for (const file of state.files) {
      const model = file.model;
      const maxLine = model.getLineCount();
      const markers = diags.filter((d) => d.file === file.name && d.line >= 1 && d.line <= maxLine).map((d) => ({
        startLineNumber: d.line, endLineNumber: d.line,
        startColumn: d.col > 0 ? d.col : model.getLineFirstNonWhitespaceColumn(d.line) || 1,
        endColumn: model.getLineMaxColumn(d.line),
        message: d.message, severity: sev[d.severity],
      }));
      monaco.editor.setModelMarkers(model, "oc", markers);
      file.decorations = model.deltaDecorations(file.decorations, markers
        .filter((mk) => mk.severity === monaco.MarkerSeverity.Error)
        .map((mk) => ({
          range: new monaco.Range(mk.startLineNumber, 1, mk.startLineNumber, 1),
          options: { isWholeLine: true, className: "oc-error-line" },
        })));
    }
    renderTabs();
  }

  function revealLocation(fileName, line, col) {
    const { editor, monaco } = state;
    if (!editor) return;
    const index = state.files.findIndex((f) => f.name === fileName);
    if (index >= 0 && index !== state.active) openFile(index);
    editor.revealLineInCenter(line);
    editor.setPosition({ lineNumber: line, column: col || 1 });
    editor.focus();
    const flash = editor.createDecorationsCollection([{
      range: new monaco.Range(line, 1, line, 1), options: { isWholeLine: true, className: "oc-flash-line" },
    }]);
    setTimeout(() => flash.clear(), 900);
  }

  // Экранирует текст и превращает "utils.py:12" в кликабельные ссылки на файл и строку
  function linkify(text) {
    const clean = stripAnsi(text);
    const names = fileNames();
    if (!names.length) return escapeHtml(clean);
    let html = "";
    let last = 0;
    for (const m of clean.matchAll(locationRegex(names))) {
      html += escapeHtml(clean.slice(last, m.index));
      html += `<span class="loc-link" data-file="${escapeHtml(pickFile(m))}" data-line="${pickLine(m)}" data-col="${pickCol(m)}">${escapeHtml(m[0])}</span>`;
      last = m.index + m[0].length;
    }
    return html + escapeHtml(clean.slice(last));
  }

  // ---------- output ----------
  function setBadge(status) {
    const badge = $("statusBadge");
    if (!status) { badge.hidden = true; return; }
    const s = status === "running" ? { label: "Выполняется…", kind: "run" } : STATUS[status] || { label: status, kind: "warn" };
    badge.textContent = s.label;
    badge.className = `status-badge ${s.kind}`;
    badge.hidden = false;
  }

  function renderResult(result) {
    state.lastResult = result;
    const out = $("output");
    const parts = [];
    const info = STATUS[result.status] || { kind: "warn" };

    if (result.message && result.status !== "ok") {
      parts.push(`<div class="out-msg ${info.kind === "err" ? "err" : "warn"}">${escapeHtml(result.message)}</div>`);
    }
    if (result.compile_output && result.compile_output.trim()) {
      parts.push(`<div class="out-section"><div class="out-label">Компилятор</div><div class="out-compile">${linkify(result.compile_output)}</div></div>`);
    }
    if (result.stdout) {
      parts.push(`<div class="out-section"><div class="out-label">stdout</div><div>${linkify(result.stdout)}</div></div>`);
    }
    if (result.stderr) {
      parts.push(`<div class="out-section"><div class="out-label">stderr</div><div class="out-stderr">${linkify(result.stderr)}</div></div>`);
    }
    if (result.truncated) {
      parts.push(`<div class="out-msg warn" style="margin-top:12px">Вывод обрезан</div>`);
    }
    if (!result.stdout && !result.stderr && result.status === "ok") {
      parts.push(`<div class="out-empty">Программа завершилась без вывода</div>`);
    }
    out.innerHTML = parts.join("");
    out.scrollTop = 0;
    renderMeta(result);
  }

  // Бейдж, метрики и маркеры ошибок — общие для обоих режимов
  function renderMeta(result) {
    state.lastResult = result;
    state.lastByMode[state.mode] = result;
    setBadge(result.status);
    $("metrics").hidden = false;
    $("mTime").textContent = formatMs(result.time_ms);
    $("mMem").textContent = formatKb(result.memory_kb);
    $("mExit").textContent = result.exit_code ?? "—";
    $("backendInfo").textContent = result.backend ? `через ${result.backend}` : "";
    setMarkers(result);
  }

  $("output").addEventListener("click", (e) => {
    const link = e.target.closest(".loc-link");
    if (link) revealLocation(link.dataset.file, +link.dataset.line, +link.dataset.col);
  });

  // ---------- run ----------
  let tickTimer = null;

  function setRunning(on, { stoppable = false } = {}) {
    state.running = on;
      if (!on) document.getElementById("esp32Preview")?.remove();
    const btn = $("runBtn");
    const label = $("runLabel");
    clearInterval(tickTimer);
    btn.classList.toggle("running", on && !stoppable);
    btn.classList.toggle("stop", on && stoppable);
    btn.disabled = on && !stoppable;
    btn.title = on && stoppable ? "Остановить (Ctrl+Enter)" : "Запустить (Ctrl+Enter)";
    $("modeConsole").disabled = $("modeBatch").disabled = on;
    updateDebugButton();
    if (!on) { label.textContent = "Запустить"; return; }
    const started = performance.now();
    const tick = () => {
      const s = ((performance.now() - started) / 1000).toFixed(1);
      label.textContent = stoppable ? `Стоп · ${s} с` : `${s} с`;
    };
    tick();
    tickTimer = setInterval(tick, 100);
  }

  function run() {
    if (!state.editor || !state.lang) return;
      if (state.lang.slug === "esp32" && state.mode !== "console") {
        setMode("console");
      }
    if (state.mode === "console") {
      if (state.running) consoleSend({ type: "kill" });
      else runConsole();
    } else if (!state.running) {
      runBatch();
    }
  }

  async function runBatch() {
    setRunning(true);
    setBadge("running");
    try {
      const result = await api("/api/run/", {
        language: state.lang.slug,
        ...projectPayload(),
        stdin: $("stdin").value,
      });
      renderResult(result);
      refreshHistory();
    } catch (err) {
      renderResult({ status: "internal_error", message: err.message, stdout: "", stderr: "", compile_output: "" });
    } finally {
      setRunning(false);
    }
  }

  // ---------- интерактивная консоль (xterm.js + WebSocket) ----------
  const ANSI = {
    dim: (s) => `\x1b[2m${s}\x1b[22m`,
    yellow: (s) => `\x1b[33m${s}\x1b[39m`,
    red: (s) => `\x1b[31m${s}\x1b[39m`,
    green: (s) => `\x1b[32m${s}\x1b[39m`,
  };
  const cons = { term: null, fit: null, socket: null, line: "", lastCR: false, transcript: { compile: "", out: "" } };

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function terminalTheme() {
    const light = currentTheme() === "light";
    return {
      background: cssVar("--term-bg"),
      foreground: cssVar("--text"),
      cursor: cssVar("--accent"),
      cursorAccent: cssVar("--term-bg"),
      selectionBackground: light ? "#6a4cf533" : "#7c5cff55",
      black: light ? "#1a1d24" : "#262b37",
      red: cssVar("--err"),
      green: cssVar("--ok"),
      yellow: cssVar("--warn"),
      blue: cssVar("--info"),
      magenta: light ? "#a23fd1" : "#c792ea",
      cyan: light ? "#0f8b9c" : "#5fd7e8",
      white: light ? "#4b5263" : "#e6e8ee",
    };
  }

  function ensureTerminal() {
    if (cons.term) return cons.term;
    if (typeof window.Terminal !== "function") {
      toast("Не загрузился xterm.js — консоль недоступна, переключаю на «Stdin заранее»");
      setMode("batch");
      return null;
    }
    const term = new window.Terminal({
      fontFamily: "'JetBrains Mono', Consolas, monospace",
      fontSize: Math.max(11, state.fontSize - 1),
      lineHeight: 1.25,
      cursorBlink: true,
      convertEol: true,
      scrollback: 5000,
      allowProposedApi: true,
      theme: terminalTheme(),
    });
    cons.fit = new window.FitAddon.FitAddon();
    term.loadAddon(cons.fit);
    // Открываем терминал только когда загрузился JetBrains Mono: xterm кеширует ширину каждого символа при первой
    // отрисовке, и буквы, нарисованные запасным Consolas (он уже), потом растягиваются и уезжают за правый край.
    // Вывод, пришедший до открытия, xterm буферизует сам. Шрифт не грузится дольше 2 с — открываем с запасным
    let opened = false;
    const open = () => {
      if (opened) return;
      opened = true;
      term.open($("terminal"));
      requestAnimationFrame(() => { try { cons.fit.fit(); } catch { /* скрыт */ } });
    };
    Promise.race([
      document.fonts ? document.fonts.load(`${term.options.fontSize}px 'JetBrains Mono'`) : Promise.resolve(),
      new Promise((resolve) => setTimeout(resolve, 2000)),
    ]).then(open, open);
    new ResizeObserver(() => { try { cons.fit.fit(); } catch { /* скрыт или ещё не открыт */ } }).observe($("terminalWrap"));

    term.attachCustomKeyEventHandler((e) => {
      if (e.type !== "keydown") return true;
      const mod = e.ctrlKey || e.metaKey;
      if (mod && e.key === "Enter") { e.preventDefault(); run(); return false; }
      if (mod && (e.key === "s" || e.key === "S")) { e.preventDefault(); save(); return false; }
      if (mod && (e.key === "c" || e.key === "C") && term.hasSelection()) {
        navigator.clipboard?.writeText(term.getSelection()).catch(() => {});
        return false;
      }
      if (mod && (e.key === "v" || e.key === "V")) return false; // пусть браузер вставит → onData
      return true;
    });
    term.onData(onTerminalInput);

    // "main.c:12" в выводе кликабельно, как и в режиме stdin
    term.registerLinkProvider({
      provideLinks(y, callback) {
        const line = term.buffer.active.getLine(y - 1);
        const names = fileNames();
        if (!line || !names.length) return callback(undefined);
        const text = line.translateToString(true);
        const links = [];
        for (const m of text.matchAll(locationRegex(names))) {
          const file = pickFile(m), ln = pickLine(m), col = pickCol(m);
          links.push({
            range: { start: { x: m.index + 1, y }, end: { x: m.index + m[0].length, y } },
            text: m[0],
            decorations: { underline: true, pointerCursor: true },
            activate: () => revealLocation(file, ln, col),
          });
        }
        callback(links.length ? links : undefined);
      },
    });

    cons.term = term;
    term.writeln(ANSI.dim("Интерактивная консоль. Ctrl+Enter — запуск/стоп, Ctrl+C — прервать, Ctrl+D — конец ввода."));
    return term;
  }

  // Локальное редактирование строки: символы видны сразу, в программу уходит целая строка по Enter
  function onTerminalInput(data) {
    const term = cons.term;
    if (!state.running) return;
    if (data.startsWith("\x1b")) return; // стрелки и прочие escape-последовательности не поддерживаем
    for (const ch of data) {
      if (ch === "\n" && cons.lastCR) { cons.lastCR = false; continue; }
      cons.lastCR = ch === "\r";
      if (ch === "\r" || ch === "\n") {
        term.write("\r\n");
        consoleSend({ type: "stdin", data: cons.line + "\n" });
        cons.line = "";
      } else if (ch === "\x7f" || ch === "\b") {
        if (cons.line) {
          cons.line = [...cons.line].slice(0, -1).join("");
          term.write("\b \b");
        }
      } else if (ch === "\x15") { // Ctrl+U — стереть строку
        term.write("\b \b".repeat([...cons.line].length));
        cons.line = "";
      } else if (ch === "\x04") { // Ctrl+D
        if (cons.line) { consoleSend({ type: "stdin", data: cons.line }); cons.line = ""; }
        term.write(ANSI.dim("^D"));
        consoleSend({ type: "eof" });
      } else if (ch === "\x03") { // Ctrl+C без выделения
        term.write(ANSI.dim("^C"));
        cons.line = "";
        consoleSend({ type: "interrupt" });
      } else if (ch >= " " || ch === "\t") {
        cons.line += ch;
        term.write(ch);
      }
    }
  }

  function consoleSend(message) {
    if (cons.socket && cons.socket.readyState === WebSocket.OPEN) cons.socket.send(JSON.stringify(message));
  }

  function openSocket() {
    return new Promise((resolve, reject) => {
      if (cons.socket && cons.socket.readyState === WebSocket.OPEN) return resolve(cons.socket);
      const socket = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/run/`);
      socket.onopen = () => { cons.socket = socket; resolve(socket); };
      socket.onerror = () => reject(new Error("Не удалось подключиться к консоли"));
      socket.onmessage = (e) => onConsoleEvent(JSON.parse(e.data));
      socket.onclose = () => {
        if (cons.socket === socket) cons.socket = null;
        if (state.running && state.mode === "console") {
          cons.term?.writeln("\r\n" + ANSI.red("Соединение с сервером потеряно"));
          setBadge("internal_error");
          setRunning(false);
        }
      };
    });
  }

  async function runConsole({ debug = false } = {}) {
    const term = ensureTerminal();
    if (!term) return;
    term.reset();
    window.OCEsp32Hardware?.reset();
    cons.line = "";
    cons.transcript = { compile: "", out: "" };
    setMarkers(null);
    setBadge("running");
    $("metrics").hidden = true;
    if (debug) startDebugUI(); else hideDebugPanel();
    setRunning(true, { stoppable: true });
    try {
      await openSocket();
    } catch (err) {
      term.writeln(ANSI.red(err.message));
      setBadge("internal_error");
      setRunning(false);
      if (debug) endDebugUI();
      return;
    }
    const payload = { language: state.lang.slug, ...projectPayload() };
    if (debug) consoleSend({ type: "debug_start", ...payload, breakpoints: allBreakpoints() });
    else consoleSend({ type: "start", ...payload });
    term.focus();
  }

  function onConsoleEvent(ev) {
    const term = cons.term;
    if (!term) return;
      if (ev.type === "esp32_preview") {
        let link = document.getElementById("esp32Preview");
        if (!link) {
          link = document.createElement("a"); link.id = "esp32Preview";
          link.className = "btn ghost"; link.target = "_blank"; link.rel = "noopener noreferrer";
          link.textContent = "Открыть сайт ESP32";
          $("runBtn").parentElement.appendChild(link);
        }
        if (/^\/esp32-preview\/[A-Za-z0-9_-]+\/$/.test(ev.url)) link.href = ev.url;
        return;
      }
    if (ev.type === "debug_reply") { onDebugReply(ev); return; }
    if (ev.type.startsWith("debug_")) { onDebugEvent(ev); return; }
    if (ev.type === "phase") {
      if (ev.phase === "prepare") term.writeln(ANSI.dim("Готовлю песочницу (один раз, ~10 с)…"));
      else if (ev.phase === "compile") term.writeln(ANSI.dim("Компиляция…"));
    } else if (ev.type === "output") {
      if (ev.stream === "compile") {
        cons.transcript.compile += ev.data;
        term.write(ANSI.yellow(ev.data));
      } else {
        cons.transcript.out += ev.data;
        if (state.lang.slug === "esp32") window.OCEsp32Hardware?.feed(ev.data);
        term.write(ev.stream === "stderr" ? ANSI.red(ev.data) : ev.data);
      }
    } else if (ev.type === "exit") {
      finishConsole(ev);
    } else if (ev.type === "error") {
      term.writeln(ANSI.red(ev.error));
      if (state.running) { setBadge("internal_error"); setRunning(false); }
      if (dbg.active) endDebugUI();
    }
  }

  function exitSummary(result) {
    const parts = [];
    if (result.exit_code != null) parts.push(`код ${result.exit_code}`);
    if (result.time_ms != null) parts.push(formatMs(result.time_ms));
    if (result.memory_kb != null) parts.push(formatKb(result.memory_kb));
    const tail = parts.length ? ` · ${parts.join(" · ")}` : "";
    if (result.status === "ok") return ANSI.green("── Программа завершилась") + ANSI.dim(tail);
    const text = result.message || (STATUS[result.status] || {}).label || result.status;
    const color = (STATUS[result.status] || {}).kind === "err" ? ANSI.red : ANSI.yellow;
    return color(`── ${text}`) + ANSI.dim(tail);
  }

  function finishConsole(result) {
    const term = cons.term;
    cons.line = "";
    if (dbg.active) endDebugUI();
    term.write((term.buffer.active.cursorX ? "\r\n" : "") + "\r\n" + exitSummary(result) + "\r\n");
    renderMeta({ ...result, stderr: result.stderr || result.stdout });
    setRunning(false);
    refreshHistory();
  }

  // История / сниппеты в режиме консоли — показываем расшифровку сессии в терминале
  function showInTerminal(result) {
    const term = ensureTerminal();
    if (!term) return;
    term.reset();
    window.OCEsp32Hardware?.reset();
    if (result.compile_output) term.write(ANSI.yellow(result.compile_output));
    if (result.stdout) term.write(result.stdout);
    if (result.stderr && result.stderr !== result.stdout) term.write(ANSI.red(result.stderr));
    term.write((term.buffer.active.cursorX ? "\r\n" : "") + "\r\n" + exitSummary(result) + "\r\n");
  }

  function setMode(mode) {
    if (state.running) return;
    state.mode = mode === "batch" ? "batch" : "console";
    store.set("mode", state.mode);
    const isConsole = state.mode === "console";
    $("modeConsole").classList.toggle("on", isConsole);
    $("modeBatch").classList.toggle("on", !isConsole);
    $("modeConsole").setAttribute("aria-selected", String(isConsole));
    $("modeBatch").setAttribute("aria-selected", String(!isConsole));
    $("sidePane").classList.toggle("console-mode", isConsole);
    $("terminalWrap").hidden = !isConsole;
    $("output").hidden = isConsole;
    if (isConsole && ensureTerminal()) requestAnimationFrame(() => { cons.fit?.fit(); });
    // Бейдж и метрики — про то, что сейчас на экране, а не про прогон в другом режиме
    const last = state.lastByMode[state.mode];
    if (last) {
      renderMeta(last);
    } else {
      setBadge(null);
      $("metrics").hidden = true;
      setMarkers(null);
    }
  }
  $("modeConsole").addEventListener("click", () => setMode("console"));
  $("modeBatch").addEventListener("click", () => setMode("batch"));

  // ---------- отладчик (DAP через WebSocket) ----------
  const dbg = {
    active: false,     // идёт отладочная сессия
    ready: false,      // отладчик подключился
    stopped: null,     // последнее событие debug_stopped, если программа на паузе
    frameId: null,     // выбранный кадр стека
    seq: 0,
    pending: new Map(),
    current: null,     // { file, ids } — декорации текущей строки
    watches: store.get("watches", []),
  };
  const STOP_REASONS = {
    breakpoint: "Брейкпоинт", step: "Шаг", pause: "Пауза", exception: "Исключение", entry: "Старт",
    "function breakpoint": "Брейкпоинт", goto: "Переход",
  };

  // --- брейкпоинты: декорации в моделях, двигаются вместе с кодом при правках ---
  function bpLines(file) {
    const lines = new Set();
    for (const id of file.bpIds || []) {
      const range = file.model.getDecorationRange(id);
      if (range) lines.add(range.startLineNumber);
    }
    return [...lines].sort((a, b) => a - b);
  }

  function setFileBreakpoints(file, lines) {
    const { monaco } = state;
    file.bpIds = file.model.deltaDecorations(file.bpIds || [], lines.map((line) => ({
      range: new monaco.Range(line, 1, line, 1),
      options: {
        glyphMarginClassName: "oc-bp",
        glyphMarginHoverMessage: { value: "Брейкпоинт — клик, чтобы убрать" },
        stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges,
      },
    })));
  }

  function allBreakpoints() {
    const result = {};
    for (const file of state.files) {
      const lines = bpLines(file);
      if (lines.length) result[file.name] = lines;
    }
    return result;
  }

  function toggleBreakpoint(file, line) {
    if (!file) return;
    const lines = bpLines(file);
    const next = lines.includes(line) ? lines.filter((l) => l !== line) : [...lines, line].sort((a, b) => a - b);
    setFileBreakpoints(file, next);
    scheduleDraftSave();
    if (dbg.active) debugRequest("setBreakpoints", { file: file.name, lines: next }).catch((err) => toast(err.message));
  }

  // --- запросы к отладчику: ответ приходит debug_reply с тем же id ---
  function debugRequest(command, args = {}) {
    return new Promise((resolve, reject) => {
      const id = ++dbg.seq;
      dbg.pending.set(id, { resolve, reject });
      consoleSend({ type: "debug", id, command, args });
      setTimeout(() => {
        if (dbg.pending.delete(id)) reject(new Error("Отладчик не ответил"));
      }, 30000);
    });
  }

  function onDebugReply(ev) {
    const waiter = dbg.pending.get(ev.id);
    if (!waiter) return;
    dbg.pending.delete(ev.id);
    if (ev.error) waiter.reject(new Error(ev.error));
    else waiter.resolve(ev.body || {});
  }

  // --- состояние UI ---
  function setDebugState(text, paused = false) {
    $("dbgState").textContent = text;
    $("dbgState").classList.toggle("paused", paused);
    const stopped = Boolean(dbg.stopped);
    for (const id of ["dbgContinue", "dbgStepOver", "dbgStepInto", "dbgStepOut"]) $(id).disabled = !stopped;
    $("dbgPause").disabled = stopped || !dbg.ready;
  }

  function startDebugUI() {
    dbg.active = true;
    dbg.ready = false;
    dbg.stopped = null;
    dbg.frameId = null;
    $("debugToolbar").hidden = false;
    $("debugPanel").hidden = false;
    $("sidePane").classList.add("debug-mode");
    $("dbgReason").textContent = "";
    $("dbgFrames").innerHTML = `<li class="muted">—</li>`;
    $("dbgVars").innerHTML = `<li class="muted">Программа ещё не остановилась</li>`;
    setDebugState("Запуск…");
    renderWatches();
  }

  function endDebugUI() {
    dbg.active = false;
    dbg.ready = false;
    dbg.stopped = null;
    clearCurrentLine();
    $("debugToolbar").hidden = true;
    for (const waiter of dbg.pending.values()) waiter.reject(new Error("Сессия отладки завершена"));
    dbg.pending.clear();
    $("dbgReason").textContent = "сессия завершена";
  }

  function hideDebugPanel() {
    $("debugPanel").hidden = true;
    $("sidePane").classList.remove("debug-mode");
    cons.fit?.fit();
  }
  $("dbgHide").addEventListener("click", hideDebugPanel);

  // --- текущая строка ---
  function clearCurrentLine() {
    if (dbg.current) {
      const file = state.files.find((f) => f.name === dbg.current.file);
      if (file && !file.model.isDisposed()) file.model.deltaDecorations(dbg.current.ids, []);
      dbg.current = null;
    }
  }

  function showLine(fileName, line, kind) {
    const { monaco } = state;
    clearCurrentLine();
    const index = state.files.findIndex((f) => f.name === fileName);
    if (index < 0 || !line) return;
    if (index !== state.active) openFile(index);
    const file = state.files[index];
    const ids = file.model.deltaDecorations([], [{
      range: new monaco.Range(line, 1, line, 1),
      options: kind === "frame"
        ? { isWholeLine: true, className: "oc-frame-line" }
        : { isWholeLine: true, className: "oc-current-line", glyphMarginClassName: "oc-current-arrow" },
    }]);
    dbg.current = { file: fileName, ids };
    state.editor.revealLineInCenterIfOutsideViewport(line);
  }

  // --- события сессии ---
  function onDebugEvent(ev) {
    if (ev.type === "debug_ready") {
      dbg.ready = true;
      setDebugState("Выполняется");
      if (!Object.keys(allBreakpoints()).length) {
        cons.term?.writeln(ANSI.dim("Брейкпоинтов нет — поставь их кликом слева от номера строки или жми Пауза (F6)."));
      }
    } else if (ev.type === "debug_stopped") {
      dbg.stopped = ev;
      onStopped(ev);
    } else if (ev.type === "debug_continued") {
      dbg.stopped = null;
      clearCurrentLine();
      $("dbgReason").textContent = "";
      setDebugState("Выполняется");
      setBadge("running");
    } else if (ev.type === "debug_error") {
      cons.term?.writeln(ANSI.red(ev.error));
      toast(ev.error);
    }
  }

  function onStopped(ev) {
    const label = STOP_REASONS[ev.reason] || ev.reason || "Пауза";
    $("dbgReason").textContent = ev.description || label;
    setDebugState(label, true);
    const badge = $("statusBadge");
    badge.textContent = "Пауза";
    badge.className = "status-badge warn";
    badge.hidden = false;
    const top = ev.frames.find((f) => f.id === ev.frameId) || ev.frames[0];
    dbg.frameId = top ? top.id : null;
    if (top && top.file) showLine(top.file, top.line, "current");
    renderFrames(ev.frames, dbg.frameId);
    renderScopes(ev.scopes);
    evaluateWatches();
    if (ev.reason === "exception") cons.term?.writeln("\r\n" + ANSI.red(`⏸ ${ev.description || "Исключение"}`));
  }

  // --- стек ---
  function renderFrames(frames, activeId) {
    const list = $("dbgFrames");
    list.innerHTML = "";
    if (!frames.length) { list.innerHTML = `<li class="muted">—</li>`; return; }
    for (const frame of frames) {
      const li = document.createElement("li");
      li.className = [frame.id === activeId && "active", !frame.file && "external"].filter(Boolean).join(" ");
      const name = document.createElement("span");
      name.className = "fr-name";
      name.textContent = frame.name;
      const loc = document.createElement("span");
      loc.className = "fr-loc";
      loc.textContent = frame.file ? `${frame.file}:${frame.line}` : "внешний код";
      li.append(name, loc);
      if (frame.file) li.addEventListener("click", () => selectFrame(frame, frames));
      list.appendChild(li);
    }
  }

  async function selectFrame(frame, frames) {
    if (!dbg.stopped) return;
    dbg.frameId = frame.id;
    renderFrames(frames, frame.id);
    const isTop = frame.id === dbg.stopped.frameId;
    showLine(frame.file, frame.line, isTop ? "current" : "frame");
    try {
      const { scopes } = await debugRequest("scopes", { frameId: frame.id });
      renderScopes(scopes);
      evaluateWatches();
    } catch (err) { toast(err.message); }
  }

  // --- дерево переменных (ленивое раскрытие) ---
  function renderScopes(scopes) {
    const root = $("dbgVars");
    root.innerHTML = "";
    if (!scopes || !scopes.length) { root.innerHTML = `<li class="muted">Нет переменных</li>`; return; }
    scopes.forEach((scope, i) => {
      root.appendChild(varNode({ name: scope.name, value: "", ref: scope.ref }, {
        scope: true, children: scope.variables, open: i === 0 || scope.variables != null && scopes.length === 1,
      }));
    });
  }

  function varNode(variable, { scope = false, children = null, open = false } = {}) {
    const li = document.createElement("li");
    const row = document.createElement("div");
    row.className = "dbg-var";
    const twist = document.createElement("span");
    twist.className = "twist";
    const name = document.createElement("span");
    name.className = "v-name" + (scope ? " scope" : "");
    name.textContent = scope ? variable.name : `${variable.name}:`;
    row.append(twist, name);
    if (!scope) {
      const value = document.createElement("span");
      value.className = "v-value";
      value.textContent = variable.value;
      value.title = variable.value;
      row.appendChild(value);
      if (variable.type) {
        const type = document.createElement("span");
        type.className = "v-type";
        type.textContent = variable.type;
        row.appendChild(type);
      }
    }
    li.appendChild(row);
    if (!variable.ref) return li;

    const sub = document.createElement("ul");
    sub.hidden = true;
    li.appendChild(sub);
    let loaded = false;
    const fill = (items) => {
      sub.innerHTML = "";
      if (!items.length) sub.innerHTML = `<li class="muted">пусто</li>`;
      for (const item of items) sub.appendChild(varNode(item));
      loaded = true;
    };
    const toggle = async () => {
      const opening = sub.hidden;
      sub.hidden = !opening;
      twist.textContent = opening ? "▾" : "▸";
      if (opening && !loaded) {
        sub.innerHTML = `<li class="muted">загрузка…</li>`;
        try { fill((await debugRequest("variables", { ref: variable.ref })).variables || []); }
        catch (err) { sub.innerHTML = ""; const e = document.createElement("li"); e.className = "muted"; e.textContent = err.message; sub.appendChild(e); }
      }
    };
    twist.textContent = "▸";
    row.style.cursor = "pointer";
    row.addEventListener("click", toggle);
    if (children) fill(children);
    if (open) { sub.hidden = false; twist.textContent = "▾"; if (!children) toggle(); }
    return li;
  }

  // --- watch ---
  function renderWatches(results = {}) {
    const list = $("dbgWatches");
    list.innerHTML = "";
    dbg.watches.forEach((expr, i) => {
      const li = document.createElement("li");
      const e = document.createElement("span");
      e.className = "w-expr";
      e.textContent = `${expr} =`;
      const v = document.createElement("span");
      const r = results[expr];
      v.className = "w-value" + (r && r.error ? " error" : "");
      v.textContent = r ? (r.error || r.result) : (dbg.stopped ? "…" : "—");
      v.title = v.textContent;
      const rm = document.createElement("button");
      rm.className = "w-remove";
      rm.type = "button";
      rm.title = "Убрать";
      rm.textContent = "×";
      rm.addEventListener("click", () => {
        dbg.watches.splice(i, 1);
        store.set("watches", dbg.watches);
        renderWatches(results);
      });
      li.append(e, v, rm);
      list.appendChild(li);
    });
  }

  async function evaluateWatches() {
    if (!dbg.stopped || !dbg.watches.length) { renderWatches(); return; }
    const results = {};
    renderWatches(results);
    await Promise.all(dbg.watches.map(async (expr) => {
      try { results[expr] = await debugRequest("evaluate", { expression: expr, frameId: dbg.frameId }); }
      catch (err) { results[expr] = { error: err.message }; }
    }));
    renderWatches(results);
  }

  $("watchForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const expr = $("watchInput").value.trim();
    if (!expr) return;
    if (!dbg.watches.includes(expr)) dbg.watches.push(expr);
    store.set("watches", dbg.watches);
    $("watchInput").value = "";
    evaluateWatches();
  });

  // --- управление ---
  function debugCommand(command) {
    if (!dbg.active) return;
    if (command === "stop") { consoleSend({ type: "kill" }); return; }
    if (command === "pause" ? dbg.stopped : !dbg.stopped) return;
    debugRequest(command).catch((err) => toast(err.message));
  }
  $("dbgContinue").addEventListener("click", () => debugCommand("continue"));
  $("dbgPause").addEventListener("click", () => debugCommand("pause"));
  $("dbgStepOver").addEventListener("click", () => debugCommand("next"));
  $("dbgStepInto").addEventListener("click", () => debugCommand("stepIn"));
  $("dbgStepOut").addEventListener("click", () => debugCommand("stepOut"));
  $("dbgStop").addEventListener("click", () => debugCommand("stop"));

  function startDebug() {
    if (state.running || !state.lang?.debuggable) return;
    if (state.mode !== "console") setMode("console");
    runConsole({ debug: true });
  }
  $("debugBtn").addEventListener("click", startDebug);

  // F5/F6/F9/F10/F11 как в IDE; браузерные F5 (перезагрузка) и F11 (полный экран) глушим
  function onDebugKey(e) {
    const key = e.key;
    if (!["F5", "F6", "F9", "F10", "F11"].includes(key)) return false;
    e.preventDefault();
    if (key === "F9") {
      const pos = state.editor?.getPosition();
      if (pos) toggleBreakpoint(activeFile(), pos.lineNumber);
    } else if (key === "F5") {
      if (e.shiftKey) debugCommand("stop");
      else if (dbg.active) debugCommand("continue");
      else startDebug();
    } else if (key === "F6") debugCommand("pause");
    else if (key === "F10") debugCommand("next");
    else if (key === "F11") debugCommand(e.shiftKey ? "stepOut" : "stepIn");
    return true;
  }

  // Наведение на переменную во время паузы — показываем значение
  function registerDebugHover(monaco) {
    const ids = new Set(state.languages.map((l) => l.monaco));
    for (const id of ids) {
      monaco.languages.registerHoverProvider(id, {
        async provideHover(model, position) {
          if (!dbg.stopped) return null;
          const word = model.getWordAtPosition(position);
          if (!word) return null;
          // Захватываем цепочку a.b.c слева от слова
          const line = model.getLineContent(position.lineNumber);
          let start = word.startColumn - 1;
          while (start > 0 && /[\w.$]/.test(line[start - 1])) start--;
          const expression = line.slice(start, word.endColumn - 1).replace(/^\.+/, "");
          if (!expression || /^\d/.test(expression)) return null;
          try {
            const r = await debugRequest("evaluate", { expression, frameId: dbg.frameId });
            return {
              range: new monaco.Range(position.lineNumber, start + 1, position.lineNumber, word.endColumn),
              contents: [{ value: "```\n" + `${expression} = ${r.result}` + (r.type ? `  (${r.type})` : "") + "\n```" }],
            };
          } catch { return null; }
        },
      });
    }
  }

  function updateDebugButton() {
    const lang = state.lang;
    const btn = $("debugBtn");
    btn.hidden = !lang || !lang.debuggable;
    btn.disabled = state.running;
    btn.title = lang && lang.debuggable ? `Отладка (F5) — через ${lang.debug_backend}` : "Отладка недоступна для этого языка";
  }

  // ---------- history ----------
  const timeAgo = (iso) => {
    const s = Math.max(0, (Date.now() - new Date(iso)) / 1000);
    if (s < 60) return "только что";
    if (s < 3600) return `${Math.floor(s / 60)} мин назад`;
    if (s < 86400) return `${Math.floor(s / 3600)} ч назад`;
    return new Date(iso).toLocaleDateString("ru-RU");
  };

  async function refreshHistory() {
    if ($("history").hidden) return;
    try {
      const { items } = await api("/api/history/");
      const list = $("historyList");
      if (!items.length) {
        list.innerHTML = `<li class="muted pad">Пока пусто — запусти что-нибудь</li>`;
        return;
      }
      list.innerHTML = items.map((it) => {
        const kind = (STATUS[it.status] || { kind: "warn" }).kind;
        const lang = state.bySlug[it.language];
        const files = it.file_count > 1 ? `<span class="muted">${pluralFiles(it.file_count)}</span>` : "";
        return `<li class="item" data-id="${it.id}">
          <div class="h-top"><span class="dot ${kind}"></span><span class="h-lang">${escapeHtml(lang ? lang.name : it.language)}</span>
          <span class="muted">${formatMs(it.time_ms)}</span>${files}<span class="h-time">${timeAgo(it.created_at)}</span></div>
          <div class="h-code">${escapeHtml(it.preview || "…")}</div></li>`;
      }).join("");
    } catch { /* история не критична */ }
  }

  $("historyList").addEventListener("click", async (e) => {
    const item = e.target.closest("li.item");
    if (!item) return;
    try {
      const ex = await api(`/api/executions/${item.dataset.id}/`);
      leaveProject();
      selectLanguage(ex.language, { code: ex.code, files: ex.files || [], args: ex.args || "" });
      $("stdin").value = ex.stdin;
      if (state.mode === "console") { showInTerminal(ex); renderMeta(ex); } else renderResult(ex);
      if (matchMedia("(max-width: 860px)").matches) $("history").hidden = true;
    } catch (err) { toast(err.message); }
  });

  function toggleHistory(show) {
    const el = $("history");
    el.hidden = show === undefined ? !el.hidden : !show;
    store.set("history", !el.hidden);
    if (!el.hidden) refreshHistory();
    state.editor?.layout();
  }
  $("historyToggle").addEventListener("click", () => toggleHistory());
  $("historyClose").addEventListener("click", () => toggleHistory(false));

  // ---------- drafts: свой проект для каждого языка ----------
  function drafts() { return store.get("drafts", {}); }
  function draftFor(lang) {
    const d = drafts()[lang.slug];
    if (typeof d === "string") return { code: d, files: [] }; // старый формат — только код
    if (!d || typeof d.code !== "string") return null;
    return {
      code: d.code,
      files: Array.isArray(d.files) ? d.files : [],
      breakpoints: d.breakpoints && typeof d.breakpoints === "object" ? d.breakpoints : {},
      args: typeof d.args === "string" ? d.args : "",
    };
  }
  function saveDraft() {
    if (!state.lang || !state.files.length) return;
    const all = drafts();
    const project = { ...projectPayload(), breakpoints: allBreakpoints() };
    const pristine = project.code === state.lang.template && !project.files.length
      && !Object.keys(project.breakpoints).length && !project.args;
    if (pristine) delete all[state.lang.slug];
    else all[state.lang.slug] = project;
    store.set("drafts", all);
    renderDirty();
  }
  let draftTimer = null;
  function scheduleDraftSave() {
    clearTimeout(draftTimer);
    draftTimer = setTimeout(saveDraft, 400);
  }

  // ---------- language picker ----------
  function selectLanguage(slug, project) {
    const lang = state.bySlug[slug] || state.languages[0];
    if (!lang) return;
    if (state.lang && state.files.length) { clearTimeout(draftTimer); saveDraft(); }
    state.lang = lang;
    window.OCEsp32Hardware?.select(lang.slug);
    store.set("lang", lang.slug);

    $("langLabel").textContent = lang.name;
    $("langVersion").textContent = lang.version;
    $("langDot").className = `lang-dot ${lang.available ? "on" : "off"}`;
    $("langButton").title = lang.available ? `Запуск через ${lang.backend}` : "Язык сейчас недоступен на сервере";
    $("backendInfo").textContent = lang.available ? `через ${lang.backend}` : "недоступен";

    applyEditorMode();
    setProject(project || draftFor(lang) || { code: lang.template, files: [] });
    renderLangList();
    updateDebugButton();
    maybeRegisterHover();
  }

  // Ховер отладчика регистрируется, когда есть и Monaco, и список языков (грузятся параллельно)
  let hoverRegistered = false;
  function maybeRegisterHover() {
    if (hoverRegistered || !state.monaco || !state.languages.length) return;
    hoverRegistered = true;
    registerDebugHover(state.monaco);
  }

  function renderLangList() {
    const q = $("langSearch").value.trim().toLowerCase();
    // Точное совпадение → начало имени → вхождение: «java» не должен выдавать первым JavaScript
    const rank = (l) => {
      const name = l.name.toLowerCase();
      if (name === q || l.slug === q) return 0;
      if (name.startsWith(q) || l.slug.startsWith(q)) return 1;
      return name.includes(q) || l.slug.includes(q) ? 2 : -1;
    };
    const items = !q ? state.languages : state.languages
      .map((l, i) => ({ l, r: rank(l), i }))
      .filter((x) => x.r >= 0)
      .sort((a, b) => a.r - b.r || a.i - b.i)
      .map((x) => x.l);
    $("langList").innerHTML = items.map((l, i) => `
      <li role="option" data-slug="${l.slug}" class="${l.slug === state.lang?.slug ? "selected" : ""} ${l.available ? "" : "unavailable"} ${i === 0 && q ? "active" : ""}">
        <span class="lang-dot ${l.available ? "on" : "off"}"></span>
        <span class="lang-name">${escapeHtml(l.name)}</span>
        ${l.compiled ? `<span class="tag">compiled</span>` : ""}
        <span class="lang-meta">${escapeHtml(l.version)}</span>
      </li>`).join("") + scratchItem(q) || `<li class="muted">Ничего не нашлось</li>`;
  }

  // Scratch 3 — отдельный редактор со сценой и спрайтами: пункт меню ведёт на его страницу
  function scratchItem(q) {
    const arduino = (!q || "arduino ардуино uno".includes(q))
      ? '<li class="lang-link" data-href="/arduino/"><span class="lang-dot on"></span><span>Arduino Uno</span></li>' : '';
    if (q && !"scratch 3 скретч".includes(q)) return arduino;
    return `<li class="lang-link" data-href="/scratch/"><span class="lang-dot on"></span>
      <span class="lang-name">Scratch 3</span><span class="tag">сцена и спрайты</span>
      <span class="lang-meta">открыть ↗</span></li>` + arduino;
  }

  function openMenu(open) {
    $("langMenu").hidden = !open;
    $("langButton").setAttribute("aria-expanded", String(open));
    if (open) {
      $("langSearch").value = "";
      renderLangList();
      $("langSearch").focus();
      $("langList").querySelector(".selected")?.scrollIntoView({ block: "nearest" });
    }
  }

  $("langButton").addEventListener("click", () => openMenu($("langMenu").hidden));
  $("langSearch").addEventListener("input", renderLangList);
  $("langList").addEventListener("click", (e) => {
    const link = e.target.closest("li[data-href]");
    if (link) { location.href = link.dataset.href; return; }
    const li = e.target.closest("li[data-slug]");
    if (!li) return;
    if (li.dataset.slug !== state.lang?.slug) leaveProject();
    selectLanguage(li.dataset.slug);
    openMenu(false);
    state.editor?.focus();
  });
  $("langSearch").addEventListener("keydown", (e) => {
    const options = [...$("langList").querySelectorAll("li[data-slug]")];
    let idx = options.findIndex((o) => o.classList.contains("active"));
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      idx = e.key === "ArrowDown" ? Math.min(options.length - 1, idx + 1) : Math.max(0, idx - 1);
      options.forEach((o, i) => o.classList.toggle("active", i === idx));
      options[idx]?.scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter") {
      e.preventDefault(); // иначе этот же Enter долетит в редактор, получивший фокус
      const target = options[idx] || options[0];
      if (target) {
        if (target.dataset.slug !== state.lang?.slug) leaveProject();
        selectLanguage(target.dataset.slug);
        openMenu(false);
        state.editor?.focus();
      }
    } else if (e.key === "Escape") {
      openMenu(false);
      $("langButton").focus();
    }
  });
  document.addEventListener("click", (e) => {
    if (!$("langPicker").contains(e.target)) openMenu(false);
  });

  // ---------- toolbar ----------
  $("runBtn").addEventListener("click", run);
  $("shareBtn").addEventListener("click", save);
  $("resetBtn").addEventListener("click", () => {
    if (!state.editor || !state.lang) return;
    const extra = state.files.length - 1;
    if (extra > 0 && !confirm(`Сбросить проект к шаблону? Дополнительные файлы (${extra}) удалятся.`)) return;
    setProject({ code: state.lang.template, files: [] });
    scheduleDraftSave();
    $("stdin").value = "";
    leaveProject();
    toast(`Шаблон ${state.lang.name}`);
  });
  $("themeBtn").addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    applyTheme(next);
    store.set("theme", next);
    window.OCBlocks?.setDark(next === "dark");
    if (cons.term) cons.term.options.theme = terminalTheme();
  });
  $("stdinClear").addEventListener("click", () => { $("stdin").value = ""; });
  $("argsInput").addEventListener("input", scheduleDraftSave);
  $("stdin").addEventListener("input", scheduleDraftSave);
  $("argsInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.ctrlKey && !e.metaKey) { e.preventDefault(); if (!state.running) run(); }
  });
  $("clearOut").addEventListener("click", () => {
    if (state.mode === "console" && cons.term) {
      if (state.running) { cons.term.clear(); return; } // идущую программу не трогаем, чистим только экран
      cons.term.reset();
    }
    $("output").innerHTML = "";
    $("metrics").hidden = true;
    setBadge(null);
    setMarkers(null);
  });
  $("copyOut").addEventListener("click", async () => {
    const r = state.lastResult;
    const text = state.mode === "console"
      ? cons.transcript.compile + cons.transcript.out
      : r ? [r.compile_output, r.stdout, r.stderr].filter(Boolean).join("\n") : "";
    if (!text) return;
    try { await navigator.clipboard.writeText(text); toast("Вывод скопирован"); } catch { toast("Не удалось скопировать"); }
  });

  function setFontSize(size) {
    state.fontSize = Math.min(28, Math.max(10, size));
    store.set("fontSize", state.fontSize);
    state.editor?.updateOptions({ fontSize: state.fontSize });
    if (cons.term) { cons.term.options.fontSize = Math.max(11, state.fontSize - 1); cons.fit?.fit(); }
    $("output").style.fontSize = `${state.fontSize - 1}px`;
  }
  $("fontUp").addEventListener("click", () => setFontSize(state.fontSize + 1));
  $("fontDown").addEventListener("click", () => setFontSize(state.fontSize - 1));

  function setWrap(on) {
    state.wrap = on;
    store.set("wrap", on);
    $("wrapBtn").classList.toggle("on", on);
    state.editor?.updateOptions({ wordWrap: on ? "on" : "off" });
    $("output").classList.toggle("nowrap", !on);
  }
  $("wrapBtn").addEventListener("click", () => setWrap(!state.wrap));

  document.addEventListener("keydown", (e) => {
    const mod = e.ctrlKey || e.metaKey;
    if (onDebugKey(e)) return;
    if (mod && e.key === "Enter") { e.preventDefault(); run(); }
    else if (mod && (e.key === "s" || e.key === "S")) { e.preventDefault(); save(); }
  });

  function updateStatus() {
    const { editor } = state;
    const file = activeFile();
    if (!editor || !file) return;
    const pos = editor.getPosition() || { lineNumber: 1, column: 1 };
    $("cursorPos").textContent = `Ln ${pos.lineNumber}, Col ${pos.column}`;
    const total = state.files.reduce((sum, f) => sum + new Blob([f.model.getValue()]).size, 0);
    $("codeSize").textContent = state.files.length > 1
      ? `${pluralFiles(state.files.length)} · ${formatBytes(total)}`
      : formatBytes(total);
    updateFormatButton();
  }

  // ---------- настройки редактора ----------
  const SETTINGS_DEFAULTS = { keymap: "default", indent: "spaces", tabSize: 4, clangStyle: "LLVM", minimap: null };
  const settings = { ...SETTINGS_DEFAULTS, ...(store.get("settings", {}) || {}) };

  function indentOptions() {
    return { tabSize: Number(settings.tabSize) || 4, insertSpaces: settings.indent !== "tabs" };
  }
  const minimapOn = () => (settings.minimap === null ? innerWidth > 1200 : !!settings.minimap);

  function applySettings() {
    store.set("settings", settings);
    for (const file of state.files) file.model.updateOptions(indentOptions());
    state.editor?.updateOptions({ minimap: { enabled: minimapOn(), renderCharacters: false, scale: 1 } });
    setKeymap(settings.keymap);
  }

  function fillSettingsForm() {
    const form = $("settingsForm");
    form.keymap.value = settings.keymap;
    form.indent.value = settings.indent;
    form.tabSize.value = String(settings.tabSize);
    form.clangStyle.value = settings.clangStyle;
    form.fontSize.value = String(state.fontSize);
    form.wrap.checked = state.wrap;
    form.minimap.checked = minimapOn();
  }

  $("settingsBtn").addEventListener("click", () => {
    fillSettingsForm();
    $("settingsDialog").showModal();
  });
  $("settingsForm").addEventListener("change", (e) => {
    const { name, value, checked } = e.target;
    if (name === "fontSize") { setFontSize(Number(value) || 14); return; }
    if (name === "wrap") { setWrap(checked); return; }
    if (name === "minimap") settings.minimap = checked;
    else if (name === "tabSize") settings.tabSize = Number(value);
    else if (name in settings) settings[name] = value;
    applySettings();
  });
  // Клик по подложке закрывает диалог
  $("settingsDialog").addEventListener("click", (e) => {
    if (e.target === $("settingsDialog")) $("settingsDialog").close();
  });
  $("settingsDialog").addEventListener("close", () => state.editor?.focus());

  // ---------- Vim / Emacs ----------
  // Оба расширения — AMD-модули: грузим тем же загрузчиком, что и Monaco, и только когда их выбрали
  const keymap = { kind: "default", mode: null, loading: null };

  function loadAmd(name) {
    return new Promise((resolve, reject) => require([name], resolve, reject));
  }

  async function setKeymap(kind) {
    if (!state.editor) return; // применится после загрузки редактора
    if (keymap.kind === kind && (kind === "default" || keymap.mode)) return;
    keymap.mode?.dispose();
    keymap.mode = null;
    keymap.kind = kind;
    const status = $("vimStatus");
    // Значок режима — только когда раскладка реально подключена, иначе первые нажатия уходят в пустоту
    status.hidden = true;
    status.textContent = "";
    $("keymapInfo").hidden = true;
    if (kind === "default") return;
    try {
      const ticket = (keymap.loading = Symbol(kind));
      const mod = await loadAmd(kind === "vim" ? "monaco-vim" : "monaco-emacs");
      if (keymap.loading !== ticket || keymap.kind !== kind) return; // пока грузили, выбрали другое
      if (kind === "vim") {
        keymap.mode = mod.initVimMode(state.editor, status);
      } else {
        const ext = new mod.EmacsExtension(state.editor);
        ext.start();
        keymap.mode = ext;
      }
      status.hidden = kind !== "vim";
      $("keymapInfo").textContent = kind === "vim" ? "VIM" : "EMACS";
      $("keymapInfo").hidden = false;
    } catch (err) {
      keymap.kind = "default";
      $("keymapInfo").hidden = true;
      status.hidden = true;
      toast(`Не удалось загрузить режим ${kind}: ${err.message || err}`);
    }
  }

  // ---------- Beautify ----------
  // WASM-сборки настоящих форматтеров (ruff, clang-format, biome, gofmt…) — грузятся с CDN по первому требованию
  // и работают прямо в браузере; Rust и Elixir форматирует сервер в песочнице.
  const WASM_FMT_BASE = "https://cdn.jsdelivr.net/npm/@wasm-fmt";
  const FORMATTERS = {
    ruff: {
      module: "ruff_fmt@0.15.20/ruff_fmt_web.js",
      run: (m, code, name, o) => m.format(code, name, { indent_style: o.insertSpaces ? "space" : "tab", indent_width: o.tabSize }),
    },
    clang: {
      module: "clang-format@23.1.1/clang-format-web.js",
      run: (m, code, name, o) => m.format(code, name.toLowerCase().replace(/^.*\//, ""),
        `{BasedOnStyle: ${settings.clangStyle}, IndentWidth: ${o.tabSize}, TabWidth: ${o.tabSize}, `
        + `UseTab: ${o.insertSpaces ? "Never" : "ForIndentation"}, ColumnLimit: 100, SortIncludes: Never}`),
    },
    biome: {
      module: "biome_fmt@0.2.9/biome_fmt_web.js",
      run: (m, code, name, o) => m.format(code, /\.tsx?$/i.test(name) ? "index.ts" : "index.js",
        { indentStyle: o.insertSpaces ? "space" : "tab", indentWidth: o.tabSize }),
    },
    gofmt: { module: "gofmt@0.7.3/gofmt_web.js", run: (m, code) => m.format(code) },
    sql: {
      module: "sql_fmt@0.2.2/sql_fmt_web.js",
      run: (m, code, name, o) => m.format(code, { indent_style: o.insertSpaces ? "space" : "tab", indent_width: o.tabSize }),
    },
    lua: {
      module: "lua_fmt@0.3.3/lua_fmt_web.js",
      run: (m, code, name, o) => m.format(code, { indent_style: o.insertSpaces ? "space" : "tab", indent_width: o.tabSize }),
    },
    shfmt: {
      module: "shfmt@0.2.7/shfmt_web.js",
      run: (m, code, name, o) => m.format(code, name, { indent: o.insertSpaces ? o.tabSize : 0 }),
    },
    dart: { module: "dart_fmt@0.4.0/dart_fmt_web.js", run: (m, code, name) => m.format(code, name) },
  };
  const FORMATTER_BY_EXT = [
    [/\.py$/i, "ruff"], [/\.(c|h|cc|cpp|cxx|hh|hpp|hxx|java|cs)$/i, "clang"], [/\.(m?js|ts)$/i, "biome"],
    [/\.go$/i, "gofmt"], [/\.sql$/i, "sql"], [/\.lua$/i, "lua"], [/\.(sh|bash)$/i, "shfmt"], [/\.dart$/i, "dart"],
  ];
  const fmtModules = {};

  function loadFormatter(id) {
    if (!fmtModules[id]) {
      fmtModules[id] = import(`${WASM_FMT_BASE}/${FORMATTERS[id].module}`)
        .then(async (m) => { await m.default(); return m; })
        .catch((err) => { delete fmtModules[id]; throw err; });
    }
    return fmtModules[id];
  }

  // Чем форматировать файл: WASM-форматтер по расширению, серверный — для главного языка проекта (Rust, Elixir),
  // встроенный форматтер Monaco — для JSON/CSS/HTML
  function formatterFor(file) {
    if (!file) return null;
    const hit = FORMATTER_BY_EXT.find(([re]) => re.test(file.name));
    if (hit) return { kind: "wasm", id: hit[1] };
    const lang = state.lang;
    if (lang?.formatter === "server" && monacoLanguageFor(file.name) === lang.monaco) return { kind: "server" };
    if (["json", "css", "scss", "less", "html"].includes(file.model.getLanguageId())) return { kind: "monaco" };
    return null;
  }

  function updateFormatButton() {
    const btn = $("formatBtn");
    const file = activeFile();
    const fmt = formatterFor(file);
    btn.disabled = !fmt;
    btn.title = fmt ? "Отформатировать файл (Shift+Alt+F)"
      : `Для ${file ? file.name : "этого файла"} форматтера нет`;
  }

  let formatting = false;
  async function formatActive() {
    const { editor } = state;
    const file = activeFile();
    const fmt = formatterFor(file);
    if (!editor || !file || formatting) return;
    if (!fmt) { toast(`Для ${file.name} форматтера нет`); return; }
    if (fmt.kind === "monaco") { await editor.getAction("editor.action.formatDocument")?.run(); return; }

    const model = file.model;
    const source = model.getValue();
    const versionBefore = model.getAlternativeVersionId();
    formatting = true;
    $("formatBtn").classList.add("on");
    try {
      let result;
      if (fmt.kind === "server") {
        result = (await api("/api/format/", { language: state.lang.slug, code: source })).code;
      } else {
        const mod = await loadFormatter(fmt.id);
        result = FORMATTERS[fmt.id].run(mod, source, file.name, indentOptions());
      }
      if (model.isDisposed() || model.getAlternativeVersionId() !== versionBefore) return; // пока форматировали, код поменяли
      if (result === source) { toast("Уже отформатировано"); return; }
      // Через executeEdits — чтобы Ctrl+Z откатил форматирование одним шагом
      editor.pushUndoStop();
      editor.executeEdits("oc-format", [{ range: model.getFullModelRange(), text: result }]);
      editor.pushUndoStop();
      toast("Отформатировано");
    } catch (err) {
      const msg = String(err?.message || err).split("\n").slice(0, 3).join(" ");
      toast(`Не отформатировалось: ${msg}`);
    } finally {
      formatting = false;
      $("formatBtn").classList.remove("on");
    }
  }
  $("formatBtn").addEventListener("click", formatActive);

  // ---------- скачать проект ----------
  async function downloadZip() {
    if (!state.lang || !state.files.length) return;
    try {
      const { code, files } = projectPayload();
      const res = await fetch("/api/zip/", {
        method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
        body: JSON.stringify({ language: state.lang.slug, code, files }),
      });
      if (!res.ok) {
        let msg = `HTTP ${res.status}`;
        try { msg = (await res.json()).error || msg; } catch { /* не JSON */ }
        throw new Error(msg);
      }
      const name = (res.headers.get("Content-Disposition") || "").match(/filename="([^"]+)"/)?.[1] || "project.zip";
      const url = URL.createObjectURL(await res.blob());
      const a = Object.assign(document.createElement("a"), { href: url, download: name });
      document.body.append(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch (err) {
      toast("Не удалось скачать: " + err.message);
    }
  }
  $("downloadBtn").addEventListener("click", downloadZip);

  // ---------- аккаунт и проекты ----------
  // project — открытый по ссылке /s/<id>/ проект (как его отдал сервер), saved — его снимок на момент сохранения
  const account = { user: readJsonScript("user-data"), project: null, saved: null, authMode: "login" };
  // Что страница знает о входе: включённые OAuth-провайдеры, ссылка сброса пароля, ошибка входа через соцсеть
  const auth = { providers: [], reset: null, error: "", ...(readJsonScript("auth-data") || {}) };

  const snap = ({ language, code, files = [], args = "", stdin = "" }) =>
    JSON.stringify([language, code, files.map((f) => [f.name, f.content]), args || "", stdin || ""]);
  const editorSnap = () => snap({ language: state.lang?.slug, ...projectPayload(), stdin: $("stdin").value });
  const isDirty = () => !!(account.project?.is_owner && state.files.length && editorSnap() !== account.saved);
  const pluralForks = (n) => (n % 10 === 1 && n % 100 !== 11 ? "форк" : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? "форка" : "форков");

  function setCurrentProject(project) {
    account.project = project;
    account.saved = project ? snap(project) : null;
    renderProject();
  }

  function leaveProject() {
    if (!account.project) return;
    setCurrentProject(null);
    history.replaceState(null, "", "/");
  }

  function renderDirty() {
    $("projectDirty").hidden = !isDirty();
  }

  function renderProject() {
    const p = account.project;
    const own = !!p?.is_owner;
    $("shareLabel").textContent = account.user ? "Сохранить" : "Поделиться";
    $("shareBtn").title = !account.user ? "Поделиться ссылкой (Ctrl+S)"
      : own ? "Сохранить проект (Ctrl+S)" : p ? "Сохранить к себе — форк с твоими правками (Ctrl+S)"
        : "Сохранить в «Мои проекты» (Ctrl+S)";
    $("projectInfo").hidden = !p;
    if (!p) return;
    const title = $("projectTitle");
    title.textContent = p.title || "Без названия";
    title.classList.toggle("untitled", !p.title);
    title.classList.toggle("editable", own);
    title.title = own ? "Переименовать проект" : p.title || "";
    const meta = [];
    if (p.owner && !own) meta.push(`<a href="/u/${encodeURIComponent(p.owner)}/">@${escapeHtml(p.owner)}</a>`);
    if (p.forked_from) {
      meta.push(`форк от <a href="${escapeHtml(p.forked_from.url)}">${escapeHtml(p.forked_from.title || p.forked_from.id)}</a>`);
    }
    if (p.forks) meta.push(`${p.forks} ${pluralForks(p.forks)}`);
    $("projectMeta").innerHTML = meta.join(" · ");
    $("forkBtn").hidden = own;
    $("visibilitySelect").hidden = !own;
    if (own) $("visibilitySelect").value = p.visibility || "unlisted";
    renderDirty();
  }

  $("visibilitySelect").addEventListener("change", async (e) => {
    const p = account.project;
    if (!p?.is_owner) return;
    const labels = { public: "Проект публичный — он виден в твоём профиле", unlisted: "Проект открывается только по ссылке",
      private: "Проект приватный — его видишь только ты" };
    try {
      const saved = await api(`/api/snippets/${p.id}/`, { visibility: e.target.value }, "PATCH");
      account.project = { ...account.project, visibility: saved.visibility };
      toast(labels[saved.visibility]);
    } catch (err) {
      e.target.value = p.visibility || "unlisted";
      toast("Не удалось сменить видимость: " + err.message);
    }
  });

  function renderAccount() {
    const { user } = account;
    $("loginBtn").hidden = !!user;
    $("userBtn").hidden = !user;
    if (user) {
      $("userName").textContent = user.username;
      $("userAvatar").textContent = [...user.username][0] || "?";
      $("userBtn").title = `Аккаунт: ${user.username}`;
    }
    renderProject();
  }

  const currentBody = () => ({ language: state.lang.slug, ...projectPayload(), stdin: $("stdin").value });

  async function copyLink(url, what) {
    const full = new URL(url, location.origin).href;
    try { await navigator.clipboard.writeText(full); toast(`${what}, ссылка скопирована: ${full}`); }
    catch { toast(`${what}: ${full}`); }
  }

  // Ctrl+S: свой проект — сохранить на месте; чужой — форк с правками; без аккаунта — анонимная ссылка
  async function save() {
    if (!state.editor || !state.lang) return;
    const p = account.project;
    try {
      if (account.user && p && !p.is_owner) { await fork(); return; }
      if (account.user && p?.is_owner) {
        setCurrentProject(await api(`/api/snippets/${p.id}/`, currentBody(), "PATCH"));
        toast("Сохранено");
        return;
      }
      const project = await api("/api/snippets/", { ...currentBody(), title: p?.title || "" });
      history.replaceState(null, "", project.url);
      setCurrentProject(project);
      await copyLink(project.url, account.user ? "Проект сохранён" : "Готово");
    } catch (err) {
      toast("Не удалось сохранить: " + err.message);
    }
  }

  async function fork() {
    const p = account.project;
    if (!p) return;
    if (!account.user) { openAuth("login", "Войди, чтобы сделать форк — он попадёт в твои проекты"); return; }
    try {
      const edited = editorSnap() !== account.saved;
      let copy = await api(`/api/snippets/${p.id}/fork/`, {});
      // Правки, сделанные до форка, не теряем — сразу сохраняем их в копию
      if (edited) copy = await api(`/api/snippets/${copy.id}/`, currentBody(), "PATCH");
      history.replaceState(null, "", copy.url);
      setCurrentProject(copy);
      toast("Форк готов — теперь это твой проект");
    } catch (err) {
      toast("Не удалось сделать форк: " + err.message);
    }
  }
  $("forkBtn").addEventListener("click", fork);

  // Переименование: клик по названию своего проекта
  $("projectTitle").addEventListener("click", () => {
    const p = account.project;
    if (!p?.is_owner) return;
    const btn = $("projectTitle");
    const input = Object.assign(document.createElement("input"), {
      className: "project-title-input", value: p.title, maxLength: 200, placeholder: "Название проекта",
    });
    btn.hidden = true;
    btn.after(input);
    input.focus();
    input.select();
    let done = false;
    const finish = async (commit) => {
      if (done) return;
      done = true;
      const title = input.value.trim();
      input.remove();
      btn.hidden = false;
      if (!commit || title === p.title) return;
      try {
        const saved = await api(`/api/snippets/${p.id}/`, { title }, "PATCH");
        account.project = { ...account.project, title: saved.title };
        renderProject();
      } catch (err) { toast("Не удалось переименовать: " + err.message); }
    };
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); finish(true); }
      else if (e.key === "Escape") { e.preventDefault(); finish(false); }
    });
    input.addEventListener("blur", () => finish(true));
  });

  // ---------- вход / регистрация ----------
  // Режимы: login, register и reset («Забыли пароль?» — только поле почты)
  function setAuthMode(mode) {
    account.authMode = mode;
    const form = $("authForm");
    form.querySelectorAll("[data-auth]").forEach((b) => b.classList.toggle("on", b.dataset.auth === mode));
    $("authSubmit").textContent = { login: "Войти", register: "Зарегистрироваться", reset: "Прислать ссылку" }[mode];
    form.password.autocomplete = mode === "login" ? "current-password" : "new-password";
    $("authUsernameField").hidden = mode === "reset";
    $("authPasswordField").hidden = mode === "reset";
    $("authEmailField").hidden = mode === "login";
    $("authEmailLabel").innerHTML = mode === "reset" ? "Почта, указанная в аккаунте"
      : 'Почта <span class="muted">(для сброса пароля, необязательно)</span>';
    $("forgotBtn").hidden = mode !== "login";
    $("oauthButtons").hidden = mode === "reset" || !auth.providers.length;
    $("authError").hidden = true;
    $("authOk").hidden = true;
  }

  function openAuth(mode = "login", hint = "") {
    setAuthMode(mode);
    $("authHint").textContent = hint || "Проекты сохраняются в аккаунт, история запусков — тоже.";
    $("authDialog").showModal();
    $("authForm").username.focus();
  }

  async function onAuthChanged(user) {
    account.user = user;
    if (account.project) {
      account.project = { ...account.project, is_owner: !!user && account.project.owner === user.username };
    }
    renderAccount();
    // Сессия сменилась — консоль должна переподключиться, иначе запуски запишутся в старую
    if (!state.running && cons.socket) cons.socket.close();
    refreshHistory();
  }

  $("authForm").querySelectorAll("[data-auth]").forEach((b) => b.addEventListener("click", () => setAuthMode(b.dataset.auth)));
  $("authClose").addEventListener("click", () => $("authDialog").close());
  $("authDialog").addEventListener("click", (e) => { if (e.target === $("authDialog")) $("authDialog").close(); });
  $("authForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const submit = $("authSubmit");
    submit.disabled = true;
    try {
      if (account.authMode === "reset") {
        await api("/api/auth/password-reset/", { email: form.email.value.trim() });
        $("authOk").textContent = "Если к этой почте привязан аккаунт, письмо со ссылкой уже в пути. Проверь и «Спам».";
        $("authOk").hidden = false;
        $("authError").hidden = true;
        return;
      }
      const { user } = await api(`/api/auth/${account.authMode}/`, {
        username: form.username.value.trim(), password: form.password.value,
        ...(account.authMode === "register" ? { email: form.email.value.trim() } : {}),
      });
      form.password.value = "";
      $("authDialog").close();
      await onAuthChanged(user);
      toast(account.authMode === "login" ? `Привет, ${user.username}!` : `Аккаунт ${user.username} создан`);
      // Пришли со страницы Scratch (?login=1&next=...) — возвращаемся. Только локальные пути: не открытый редирект
      if (account.afterLogin && /^\/(?!\/)/.test(account.afterLogin)) location.href = account.afterLogin;
    } catch (err) {
      $("authError").textContent = err.message;
      $("authError").hidden = false;
    } finally {
      submit.disabled = false;
    }
  });
  $("loginBtn").addEventListener("click", () => openAuth("login"));
  $("forgotBtn").addEventListener("click", () => {
    setAuthMode("reset");
    $("authForm").email.focus();
  });

  function toggleUserMenu(open) {
    $("userMenu").hidden = !open;
    $("userBtn").setAttribute("aria-expanded", String(open));
  }
  $("userBtn").addEventListener("click", () => toggleUserMenu($("userMenu").hidden));
  document.addEventListener("click", (e) => { if (!$("account").contains(e.target)) toggleUserMenu(false); });
  $("profileBtn").addEventListener("click", () => {
    if (account.user) location.href = `/u/${encodeURIComponent(account.user.username)}/`;
  });
  $("accountSettingsBtn").addEventListener("click", () => {
    toggleUserMenu(false);
    openAccountSettings();
  });
  $("logoutBtn").addEventListener("click", async () => {
    toggleUserMenu(false);
    try {
      await api("/api/auth/logout/", {});
      await onAuthChanged(null);
      toast("Ты вышел из аккаунта");
    } catch (err) { toast(err.message); }
  });

  // ---------- вход через GitHub / Google ----------
  function initOAuthButtons() {
    for (const link of $("oauthButtons").querySelectorAll("[data-provider]")) {
      const enabled = auth.providers.some((p) => p.id === link.dataset.provider);
      link.hidden = !enabled;
      // next — вернуться туда же (например, на открытый проект) после входа
      link.href = `/auth/${link.dataset.provider}/login/?next=${encodeURIComponent(location.pathname)}`;
    }
  }

  // ---------- новый пароль по ссылке из письма ----------
  function openResetConfirm() {
    $("resetError").hidden = true;
    $("resetDialog").showModal();
    $("resetForm").password.focus();
  }
  $("resetForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const { user } = await api("/api/auth/password-reset/confirm/", {
        uid: auth.reset.uid, token: auth.reset.token, password: e.target.password.value,
      });
      e.target.password.value = "";
      $("resetDialog").close();
      history.replaceState(null, "", "/");  // ссылка одноразовая — убираем её из адресной строки
      await onAuthChanged(user);
      toast(`Пароль обновлён, ${user.username}!`);
    } catch (err) {
      $("resetError").textContent = err.message;
      $("resetError").hidden = false;
    }
  });
  $("resetClose").addEventListener("click", () => {
    $("resetDialog").close();
    history.replaceState(null, "", "/");
  });

  // ---------- настройки аккаунта ----------
  function accountMessage(ok, text) {
    $("accountOk").hidden = !ok;
    $("accountError").hidden = ok;
    (ok ? $("accountOk") : $("accountError")).textContent = text;
  }

  function openAccountSettings() {
    const { user } = account;
    if (!user) return;
    const emailForm = $("emailForm");
    emailForm.email.value = user.email || "";
    emailForm.password.value = "";
    $("passwordForm").reset();
    // Аккаунт из GitHub / Google без пароля: текущий пароль не спрашиваем, а пароль можно задать впервые
    for (const field of $("accountDialog").querySelectorAll("[data-needs-password]")) field.hidden = !user.has_password;
    $("newPasswordLabel").textContent = user.has_password ? "Новый пароль" : "Задать пароль (сейчас вход только через соцсеть)";
    $("passwordSubmit").textContent = user.has_password ? "Сменить пароль" : "Задать пароль";
    const titles = { github: "GitHub", google: "Google" };
    $("accountProviders").hidden = !user.providers.length;
    $("accountProviders").textContent = `Привязан вход через: ${user.providers.map((p) => titles[p] || p).join(", ")}`;
    $("accountOk").hidden = true;
    $("accountError").hidden = true;
    $("accountDialog").showModal();
  }

  $("emailForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const { user } = await api("/api/auth/me/", {
        email: e.target.email.value.trim(), password: e.target.password.value,
      }, "PATCH");
      account.user = user;
      e.target.password.value = "";
      accountMessage(true, user.email ? `Почта сохранена: ${user.email}` : "Почта удалена из аккаунта");
    } catch (err) { accountMessage(false, err.message); }
  });

  $("passwordForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const { user } = await api("/api/auth/password/", {
        old_password: e.target.old_password.value, new_password: e.target.new_password.value,
      });
      account.user = user;
      openAccountSettings();  // перерисовываем: у аккаунта без пароля теперь появились поля «текущий пароль»
      accountMessage(true, "Пароль сохранён");
    } catch (err) { accountMessage(false, err.message); }
  });
  $("accountClose").addEventListener("click", () => $("accountDialog").close());
  $("accountDialog").addEventListener("click", (e) => { if (e.target === $("accountDialog")) $("accountDialog").close(); });

  // ---------- «Мои проекты» ----------
  let projectsQueryTimer = null;
  const visibilityBadge = (v) => (v === "public" ? '<span class="badge public">публичный</span>'
    : v === "private" ? '<span class="badge private">приватный</span>' : "");
  async function loadProjects() {
    const list = $("projectsList");
    const q = $("projectsSearch").value.trim();
    try {
      const { items } = await api(`/api/projects/?q=${encodeURIComponent(q)}`);
      if (!items.length) {
        list.innerHTML = `<li class="muted pad">${q ? "Ничего не нашлось" : "Пока пусто — нажми «Сохранить» (Ctrl+S), и проект появится здесь"}</li>`;
        return;
      }
      list.innerHTML = items.map((it) => {
        const lang = it.language === "scratch" ? { name: "Scratch 3" }
          : it.language === "arduino" ? { name: "Arduino Uno" } : state.bySlug[it.language];
        const forks = it.forks ? `<span>${it.forks} ${pluralForks(it.forks)}</span>` : "";
        const files = it.file_count > 1 ? `<span>${pluralFiles(it.file_count)}</span>` : "";
        return `<li class="item ${account.project?.id === it.id ? "current" : ""}" data-id="${escapeHtml(it.id)}" data-url="${escapeHtml(it.url)}">
          <span class="lang-dot on"></span>
          <div class="p-main">
            <div class="p-title ${it.title ? "" : "untitled"}">${escapeHtml(it.title || "Без названия")}</div>
            <div class="p-meta"><span>${escapeHtml(lang ? lang.name : it.language)}</span>${visibilityBadge(it.visibility)}${files}${forks}
              <span>изменён ${timeAgo(it.updated_at)}</span></div>
          </div>
          <button class="icon-btn small p-delete" title="Удалить проект" aria-label="Удалить проект">
            <svg viewBox="0 0 24 24"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>
          </button></li>`;
      }).join("");
    } catch (err) {
      list.innerHTML = `<li class="muted pad">${escapeHtml(err.message)}</li>`;
    }
  }

  async function openProject(id, url) {
    if (url?.startsWith("/scratch/") || url?.startsWith("/arduino/")) { location.href = url; return; }
    try {
      const p = await api(`/api/snippets/${encodeURIComponent(id)}/`);
      selectLanguage(p.language, { code: p.code, files: p.files || [], args: p.args || "" });
      $("stdin").value = p.stdin || "";
      history.replaceState(null, "", p.url);
      setCurrentProject(p);
      $("projectsDialog").close();
    } catch (err) { toast("Не удалось открыть: " + err.message); }
  }

  $("myProjectsBtn").addEventListener("click", () => {
    toggleUserMenu(false);
    $("projectsSearch").value = "";
    $("projectsList").innerHTML = `<li class="muted pad">Загружаю…</li>`;
    $("projectsDialog").showModal();
    $("projectsSearch").focus();
    loadProjects();
  });
  $("projectsSearch").addEventListener("input", () => {
    clearTimeout(projectsQueryTimer);
    projectsQueryTimer = setTimeout(loadProjects, 200);
  });
  $("projectsClose").addEventListener("click", () => $("projectsDialog").close());
  $("projectsDialog").addEventListener("click", (e) => { if (e.target === $("projectsDialog")) $("projectsDialog").close(); });
  $("projectsList").addEventListener("click", async (e) => {
    const item = e.target.closest("li.item");
    if (!item) return;
    if (e.target.closest(".p-delete")) {
      const title = item.querySelector(".p-title").textContent;
      if (!confirm(`Удалить проект «${title}»? Ссылка на него перестанет работать.`)) return;
      try {
        await api(`/api/snippets/${encodeURIComponent(item.dataset.id)}/`, undefined, "DELETE");
        if (account.project?.id === item.dataset.id) leaveProject();
        loadProjects();
      } catch (err) { toast("Не удалось удалить: " + err.message); }
      return;
    }
    openProject(item.dataset.id, item.dataset.url);
  });

  window.addEventListener("beforeunload", (e) => {
    if (isDirty()) { e.preventDefault(); e.returnValue = ""; }
  });

  // ---------- библиотека алгоритмов ----------
  const libraryCache = {};  // slug -> {categories, items}
  let libraryQueryTimer = null;

  async function loadLibrary(slug) {
    if (!libraryCache[slug]) libraryCache[slug] = await api(`/api/library/?language=${encodeURIComponent(slug)}`);
    return libraryCache[slug];
  }

  function renderLibrary(data) {
    const q = $("librarySearch").value.trim().toLowerCase();
    const match = (it) => !q || it.title.toLowerCase().includes(q) || it.description.toLowerCase().includes(q)
      || it.category.toLowerCase().includes(q);
    const groups = data.categories
      .map((category) => ({ category, items: data.items.filter((it) => it.category === category && match(it)) }))
      .filter((g) => g.items.length);
    $("libraryList").innerHTML = groups.length ? groups.map((g) => `
      <section class="library-group">
        <h4>${escapeHtml(g.category)}</h4>
        ${g.items.map((it) => `
          <button class="library-item" data-id="${escapeHtml(it.id)}">
            <div class="l-title">${escapeHtml(it.title)}</div>
            <div class="l-desc">${escapeHtml(it.description)}</div>
          </button>`).join("")}
      </section>`).join("")
      : `<p class="muted pad">${data.items.length ? "Ничего не нашлось" : "Для этого языка примеров пока нет"}</p>`;
  }

  async function openLibrary() {
    if (!state.lang) return;
    $("libraryTitle").textContent = `Примеры: ${state.lang.name}`;
    $("librarySearch").value = "";
    $("libraryList").innerHTML = `<p class="muted pad">Загружаю…</p>`;
    $("libraryDialog").showModal();
    $("librarySearch").focus();
    try {
      renderLibrary(await loadLibrary(state.lang.slug));
    } catch (err) {
      $("libraryList").innerHTML = `<p class="muted pad">${escapeHtml(err.message)}</p>`;
    }
  }

  async function insertExample(id) {
    const slug = state.lang.slug;
    try {
      const example = await api(`/api/library/${encodeURIComponent(slug)}/${encodeURIComponent(id)}/`);
      const current = state.files[0]?.model.getValue() ?? "";
      const hasOwnCode = state.files.length > 1 || (current.trim() && current !== state.lang.template);
      if (hasOwnCode && !confirm(`Заменить текущий код примером «${example.title}»? `
          + "Свой код сохрани (Ctrl+S), если он нужен.")) return;
      $("libraryDialog").close();
      leaveProject();
      setProject({ code: example.code, files: [] });
      scheduleDraftSave();
      toast(`${example.title} — жми Ctrl+Enter`);
    } catch (err) {
      toast("Не удалось открыть пример: " + err.message);
    }
  }

  $("libraryBtn").addEventListener("click", openLibrary);
  $("libraryClose").addEventListener("click", () => $("libraryDialog").close());
  $("libraryDialog").addEventListener("click", (e) => { if (e.target === $("libraryDialog")) $("libraryDialog").close(); });
  $("librarySearch").addEventListener("input", () => {
    clearTimeout(libraryQueryTimer);
    libraryQueryTimer = setTimeout(() => {
      const data = libraryCache[state.lang?.slug];
      if (data) renderLibrary(data);
    }, 120);
  });
  $("libraryList").addEventListener("click", (e) => {
    const item = e.target.closest(".library-item");
    if (item) insertExample(item.dataset.id);
  });

  // ---------- режим блоков ----------
  // Язык с editor === "blocks": слева Blockly, под ним — сгенерированный main.py (только чтение).
  // Блоки лежат в файле проекта blocks.json, так что сохранение, шаринг и черновики работают как обычно.
  const BLOCKS_FILE = "blocks.json";
  const isBlocks = () => state.lang?.editor === "blocks";
  let blocksSync = 0;  // номер последней загрузки: устаревшие асинхронные загрузки не перетирают новые

  function applyEditorMode() {
    const blocks = isBlocks();
    const pane = $("editor").closest(".editor-pane");
    pane.classList.toggle("blocks-mode", blocks);
    pane.classList.toggle("hide-code", blocks && !store.get("blocksShowCode", true));
    $("blocksArea").hidden = !blocks;
    $("blocksCodeBtn").hidden = !blocks;
    $("blocksCodeBtn").classList.toggle("on", store.get("blocksShowCode", true));
    state.editor?.updateOptions({ readOnly: blocks });
    state.editor?.layout();
  }

  function applyBlocks(json, python) {
    const [main] = state.files;
    if (!main) return;
    if (main.model.getValue() !== python) main.model.setValue(python);
    const file = state.files.find((f) => f.name === BLOCKS_FILE);
    if (file) {
      if (file.model.getValue() !== json) file.model.setValue(json);
    } else {
      state.files.push(createFile(BLOCKS_FILE, json));
    }
    scheduleDraftSave();
  }

  async function syncBlocksFromProject() {
    const ticket = ++blocksSync;
    try {
      await window.OCBlocks.mount($("blocksArea"), { dark: currentTheme() === "dark", onChange: applyBlocks });
      $("blocksArea").querySelector(".editor-loading")?.remove();
      if (ticket !== blocksSync || !isBlocks()) return;
      const saved = state.files.find((f) => f.name === BLOCKS_FILE)?.model.getValue();
      const { json, python } = window.OCBlocks.load(saved);
      applyBlocks(json, python);
      window.OCBlocks.resize();
    } catch (err) {
      toast("Не загрузились блоки: " + err.message);
    }
  }

  $("blocksCodeBtn").addEventListener("click", () => {
    store.set("blocksShowCode", !store.get("blocksShowCode", true));
    applyEditorMode();
    window.OCBlocks.resize();
  });
  new ResizeObserver(() => { if (isBlocks()) window.OCBlocks.resize(); }).observe($("blocksArea"));

  // ---------- resizable split ----------
  (function initSplit() {
    const gutter = $("gutter");
    const split = $("split");
    const saved = store.get("sideWidth");
    if (saved) split.style.setProperty("--side-width", `${saved}%`);
    const setWidth = (pct) => {
      pct = Math.min(70, Math.max(22, pct));
      split.style.setProperty("--side-width", `${pct}%`);
      store.set("sideWidth", pct);
      state.editor?.layout();
    };
    gutter.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      gutter.setPointerCapture(e.pointerId);
      gutter.classList.add("dragging");
      const rect = split.getBoundingClientRect();
      const move = (ev) => setWidth(((rect.right - ev.clientX) / rect.width) * 100);
      const up = () => {
        gutter.classList.remove("dragging");
        gutter.removeEventListener("pointermove", move);
        gutter.removeEventListener("pointerup", up);
      };
      gutter.addEventListener("pointermove", move);
      gutter.addEventListener("pointerup", up);
    });
    gutter.addEventListener("keydown", (e) => {
      const cur = parseFloat(getComputedStyle(split).getPropertyValue("--side-width")) || 40;
      if (e.key === "ArrowLeft") setWidth(cur + 2);
      if (e.key === "ArrowRight") setWidth(cur - 2);
    });
  })();

  // ---------- Monaco ----------
  // Подсветка языков, которых нет в Monaco: компактный Monarch по описанию (ключевые слова, комментарии, строки)
  const SIMPLE_LANGUAGES = {
    fortran: {
      ignoreCase: true, line: "!", strings: ["\"", "'"],
      keywords: ("program end module use implicit none integer real double precision complex logical character parameter "
        + "dimension allocatable allocate deallocate intent in out inout function subroutine call return if then else "
        + "elseif endif do enddo while exit cycle select case default contains type print write read stop result "
        + "recursive pure elemental interface save data go to format open close mod abs sqrt size len trim").split(" "),
    },
    asm: {
      line: ";", strings: ["\"", "'", "`"],
      keywords: ("mov movzx movsx lea push pop call ret jmp je jne jz jnz jg jge jl jle ja jae jb jbe cmp test add sub "
        + "imul mul idiv div inc dec neg and or xor not shl shr sar cqo cdq loop nop syscall leave enter "
        + "section global extern db dw dd dq resb resw resd resq equ times bits default rel wrt plt").split(" "),
      types: ("rax rbx rcx rdx rsi rdi rbp rsp r8 r9 r10 r11 r12 r13 r14 r15 eax ebx ecx edx esi edi ebp esp "
        + "r8d r9d r10d r11d r12d r13d r14d r15d ax bx cx dx al bl cl dl ah bh ch dh sil dil byte word dword qword").split(" "),
    },
    prolog: {
      line: "%", block: ["/*", "*/"], strings: ["\"", "'", "`"], upperIsType: true,
      keywords: ("is mod rem not true fail call findall bagof setof assert asserta assertz retract format write writeln "
        + "nl halt length append member msort sort nth0 nth1 between succ plus atom number var nonvar initialization").split(" "),
    },
    ocaml: {
      block: ["(*", "*)"], strings: ["\""],
      keywords: ("let in rec and if then else match with function fun type of module struct sig end open begin "
        + "val mutable for to downto do done while try raise exception when as not ref true false").split(" "),
      types: "int float string bool char unit list array option Printf List Array String Hashtbl Queue".split(" "),
    },
    erlang: {
      line: "%", strings: ["\""], upperIsType: true,
      keywords: ("module export import define record case of if when end fun receive after try catch throw "
        + "begin andalso orelse not and or div rem band bor bxor bsl bsr spawn true false").split(" "),
    },
    zig: {
      line: "//", strings: ["\""],
      keywords: ("const var fn pub return if else while for switch break continue defer errdefer try catch orelse "
        + "struct enum union error comptime inline export extern test undefined null true false and or unreachable").split(" "),
      types: "u8 u16 u32 u64 usize i8 i16 i32 i64 isize f32 f64 bool void anyerror type anytype".split(" "),
    },
    nim: {
      line: "#", block: ["#[", "]#"], strings: ["\""],
      keywords: ("proc func let var const if elif else while for in return result echo import from type object "
        + "ref seq array of case when break continue and or not div mod shl shr iterator yield discard true false").split(" "),
      types: "int int64 float string bool char seq openArray".split(" "),
    },
    d: {
      line: "//", block: ["/*", "*/"], strings: ["\"", "`"],
      keywords: ("import module void auto const immutable return if else while for foreach do switch case default "
        + "break continue struct class interface enum static ref in out new null true false this alias").split(" "),
      types: "int long uint ulong short byte ubyte bool char string double float size_t real".split(" "),
    },
    cobol: {
      ignoreCase: true, line: "*>", strings: ["\"", "'"],
      keywords: ("identification division program-id data working-storage section procedure pic value display "
        + "accept move to add subtract multiply divide giving compute if else end-if perform until varying from by "
        + "end-perform stop run function trim occurs times indexed using call evaluate when end-evaluate "
        + "other not greater less than equal and or is zero spaces").split(" "),
    },
    ada: {
      ignoreCase: true, line: "--", strings: ["\""],
      keywords: ("with use procedure function is begin end if then elsif else loop for in reverse while return "
        + "declare type array of range constant record package body new null and or not mod rem exit when "
        + "case others out access").split(" "),
      types: "integer natural positive float boolean character string".split(" "),
    },
    lisp: {
      line: ";", block: ["#|", "|#"], strings: ["\""],
      keywords: ("defun defvar defparameter defmacro let let* lambda if when unless cond case loop do dotimes dolist "
        + "progn setf setq return return-from and or not format funcall apply mapcar list cons car cdr nil t "
        + "make-array aref vector length push pop").split(" "),
    },
    groovy: {
      line: "//", block: ["/*", "*/"], strings: ["\"", "'"],
      keywords: ("def class interface enum static final void return if else for while in switch case default break "
        + "continue new null true false import package try catch finally throw this super println").split(" "),
      types: "int long double float boolean char String List Map Integer".split(" "),
    },
  };

  function registerSimpleLanguages(monaco) {
    const known = new Set(monaco.languages.getLanguages().map((l) => l.id));
    for (const [id, spec] of Object.entries(SIMPLE_LANGUAGES)) {
      if (known.has(id)) continue;
      // Ошибка в грамматике одного языка не должна ронять весь редактор — язык просто останется без подсветки
      try {
        registerSimpleLanguage(monaco, id, spec);
      } catch (err) {
        console.warn(`Подсветка ${id} не зарегистрирована:`, err);
      }
    }
  }

  function registerSimpleLanguage(monaco, id, spec) {
    monaco.languages.register({ id });
    const root = [];
    if (spec.line) root.push([new RegExp(`${escapeRe(spec.line)}.*$`), "comment"]);
    if (spec.block) root.push([new RegExp(escapeRe(spec.block[0])), "comment", "@comment"]);
    for (const q of spec.strings || []) {
      root.push([new RegExp(`${escapeRe(q)}(?:[^${escapeRe(q)}\\\\]|\\\\.)*${escapeRe(q)}`), "string"]);
    }
    root.push([/\b(?:0x[0-9a-fA-F_]+|\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?)\b/, "number"]);
    root.push([/[A-Za-z_][\w\-?!*]*/, {
      cases: {
        "@keywords": "keyword",
        "@types": "type",
        ...(spec.upperIsType ? { "[A-Z_].*": "type" } : {}),
        "@default": "identifier",
      },
    }]);
    root.push([/[{}()[\]]/, "@brackets"]);
    const comment = spec.block
      ? [[new RegExp(escapeRe(spec.block[1])), "comment", "@pop"], [/./, "comment"]]
      : [[/./, "comment", "@pop"]];
    monaco.languages.setMonarchTokensProvider(id, {
      ignoreCase: !!spec.ignoreCase,
      keywords: spec.keywords || [],
      types: spec.types || [],
      tokenizer: { root, comment },
    });
    monaco.languages.setLanguageConfiguration(id, {
      comments: { lineComment: spec.line, blockComment: spec.block },
      brackets: [["(", ")"], ["[", "]"], ["{", "}"]],
      autoClosingPairs: [{ open: "(", close: ")" }, { open: "[", close: "]" }, { open: "{", close: "}" },
        ...(spec.strings || []).map((q) => ({ open: q, close: q }))],
    });
  }

  function registerExtraLanguages(monaco) {
    // В Monaco нет Haskell — даём простой Monarch-токенайзер
    if (!monaco.languages.getLanguages().some((l) => l.id === "haskell")) {
      monaco.languages.register({ id: "haskell", extensions: [".hs"] });
      monaco.languages.setMonarchTokensProvider("haskell", {
        keywords: ["case", "class", "data", "default", "deriving", "do", "else", "foreign", "if", "import", "in",
          "infix", "infixl", "infixr", "instance", "let", "module", "newtype", "of", "then", "type", "where",
          "qualified", "as", "hiding"],
        tokenizer: {
          root: [
            [/--.*$/, "comment"],
            [/\{-/, "comment", "@comment"],
            [/"([^"\\]|\\.)*"/, "string"],
            [/'([^'\\]|\\.)'/, "string"],
            [/\b[A-Z][\w']*/, "type"],
            [/[a-z_][\w']*/, { cases: { "@keywords": "keyword", "@default": "identifier" } }],
            [/\d+(\.\d+)?/, "number"],
            [/[=<>!:|&+\-*/\\.$@~^%]+/, "operator"],
          ],
          comment: [[/[^{-]+/, "comment"], [/-\}/, "comment", "@pop"], [/[{-]/, "comment"]],
        },
      });
      monaco.languages.setLanguageConfiguration("haskell", {
        comments: { lineComment: "--", blockComment: ["{-", "-}"] },
        brackets: [["(", ")"], ["[", "]"], ["{", "}"]],
        autoClosingPairs: [{ open: "(", close: ")" }, { open: "[", close: "]" }, { open: "{", close: "}" }, { open: '"', close: '"' }],
      });
    }
  }

  function configureTypeScript(monaco) {
    // Импорты между вкладками ("./math") резолвятся как в обычном проекте
    const options = {
      target: monaco.languages.typescript.ScriptTarget.ESNext,
      module: monaco.languages.typescript.ModuleKind.ESNext,
      moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
      allowNonTsExtensions: true,
      allowJs: true,
      esModuleInterop: true,
    };
    monaco.languages.typescript.typescriptDefaults.setCompilerOptions(options);
    monaco.languages.typescript.javascriptDefaults.setCompilerOptions(options);
  }

  function defineThemes(monaco) {
    monaco.editor.defineTheme("oc-dark", {
      base: "vs-dark", inherit: true,
      rules: [
        { token: "comment", foreground: "6c7385", fontStyle: "italic" },
        { token: "keyword", foreground: "b69cff" },
        { token: "string", foreground: "8bd5a0" },
        { token: "number", foreground: "f5b74f" },
        { token: "type", foreground: "5ab0ff" },
      ],
      colors: {
        "editor.background": "#171a22",
        "editor.lineHighlightBackground": "#1d212b",
        "editorLineNumber.foreground": "#4a5163",
        "editorLineNumber.activeForeground": "#a4abbb",
        "editorGutter.background": "#171a22",
        "editor.selectionBackground": "#7c5cff44",
        "editorCursor.foreground": "#9b82ff",
        "editorIndentGuide.background1": "#262b37",
        "scrollbarSlider.background": "#34394966",
      },
    });
    monaco.editor.defineTheme("oc-light", {
      base: "vs", inherit: true,
      rules: [
        { token: "comment", foreground: "8a91a2", fontStyle: "italic" },
        { token: "keyword", foreground: "6a4cf5" },
        { token: "string", foreground: "12824f" },
        { token: "number", foreground: "b36b00" },
        { token: "type", foreground: "1f6fd0" },
      ],
      colors: {
        "editor.background": "#ffffff",
        "editor.lineHighlightBackground": "#f7f8fa",
        "editorLineNumber.foreground": "#b3b9c6",
        "editor.selectionBackground": "#6a4cf530",
        "editorCursor.foreground": "#6a4cf5",
      },
    });
  }

  function initMonaco() {
    window.MonacoEnvironment = {
      getWorkerUrl() {
        // Воркеры с CDN нельзя грузить напрямую (cross-origin) — оборачиваем в data: URL
        return `data:text/javascript;charset=utf-8,${encodeURIComponent(
          `self.MonacoEnvironment={baseUrl:'${MONACO_BASE}/'};importScripts('${MONACO_BASE}/vs/base/worker/workerMain.js');`,
        )}`;
      },
    };
    require.config({
      paths: {
        vs: `${MONACO_BASE}/vs`,
        "monaco-vim": "https://cdn.jsdelivr.net/npm/monaco-vim@0.4.4/dist/monaco-vim.umd",
        "monaco-emacs": "https://cdn.jsdelivr.net/npm/monaco-emacs@0.3.0/dist/monaco-emacs",
      },
    });
    require(["vs/editor/editor.main"], () => {
      const monaco = window.monaco;
      state.monaco = monaco;
      // monaco-vim (UMD) просит ESM-API редактора — отдаём ему уже загруженный глобальный monaco
      define("monaco-editor/esm/vs/editor/editor.api", [], () => monaco);
      // Отмена задач воркера при удалении модели — штатная ситуация, а Monaco пишет её в console.error
      // Это только косметика — ни при каких раскладах не должна ломать загрузку редактора
      require(["vs/base/common/errors"], (errors) => {
        try {
          const handler = errors.errorHandler;
          const original = handler?.unexpectedErrorHandler;
          const isCancel = errors.isCancellationError || ((err) => err?.name === "Canceled");
          if (typeof original === "function") {
            handler.unexpectedErrorHandler = (err) => { if (!isCancel(err)) original(err); };
          }
        } catch { /* другая сборка Monaco — оставляем как есть */ }
      }, () => { /* модуля нет — не критично */ });
      registerExtraLanguages(monaco);
      registerSimpleLanguages(monaco);
      configureTypeScript(monaco);
      defineThemes(monaco);
      $("editor").innerHTML = "";

      const editor = monaco.editor.create($("editor"), {
        model: null,
        theme: currentTheme() === "light" ? "oc-light" : "oc-dark",
        fontFamily: "'JetBrains Mono', Consolas, monospace",
        fontLigatures: true,
        fontSize: state.fontSize,
        lineHeight: 1.6,
        automaticLayout: true,
        minimap: { enabled: minimapOn(), renderCharacters: false, scale: 1 },
        scrollBeyondLastLine: false,
        smoothScrolling: true,
        cursorBlinking: "smooth",
        cursorSmoothCaretAnimation: "on",
        renderLineHighlight: "all",
        bracketPairColorization: { enabled: true },
        guides: { bracketPairs: "active", indentation: true },
        stickyScroll: { enabled: true },
        padding: { top: 12, bottom: 12 },
        wordWrap: state.wrap ? "on" : "off",
        detectIndentation: false, // отступ задаёт пользователь в настройках
        fixedOverflowWidgets: true,
        glyphMargin: true, // поле слева от номеров строк — под брейкпоинты
      });
      state.editor = editor;

      // Брейкпоинт — клик по полю слева или по номеру строки; при наведении — бледная точка-подсказка
      const T = monaco.editor.MouseTargetType;
      const inGutter = (target) => target && (target.type === T.GUTTER_GLYPH_MARGIN || target.type === T.GUTTER_LINE_NUMBERS);
      editor.onMouseDown((e) => {
        if (inGutter(e.target) && e.target.position && e.event.leftButton) {
          toggleBreakpoint(activeFile(), e.target.position.lineNumber);
        }
      });
      let hintIds = [];
      const setHint = (line) => {
        const file = activeFile();
        if (!file) return;
        const show = line && !bpLines(file).includes(line);
        hintIds = file.model.deltaDecorations(hintIds, show ? [{
          range: new monaco.Range(line, 1, line, 1), options: { glyphMarginClassName: "oc-bp-hint" },
        }] : []);
      };
      editor.onMouseMove((e) => setHint(inGutter(e.target) && e.target.position ? e.target.position.lineNumber : null));
      editor.onMouseLeave(() => setHint(null));
      editor.onDidChangeModel(() => { hintIds = []; });

      editor.addAction({
        id: "oc-run", label: "Запустить код", keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
        run: () => run(),
      });
      editor.addAction({
        id: "oc-share", label: "Поделиться ссылкой", keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS],
        run: () => save(),
      });
      editor.addAction({
        id: "oc-format", label: "Отформатировать файл (Beautify)",
        keybindings: [monaco.KeyMod.Shift | monaco.KeyMod.Alt | monaco.KeyCode.KeyF],
        contextMenuGroupId: "1_modification", contextMenuOrder: 1,
        run: () => formatActive(),
      });
      editor.addAction({
        id: "oc-new-file", label: "Новый файл в проекте", keybindings: [monaco.KeyMod.Alt | monaco.KeyCode.KeyN],
        run: () => newFile(),
      });

      editor.onDidChangeCursorPosition(updateStatus);
      editor.onDidChangeModelContent(updateStatus);

      const pending = state.pending;
      state.pending = null;
      applyEditorMode();
      if (pending) setProject(pending);
      maybeRegisterHover();
      setKeymap(settings.keymap);
    });
  }

  // ---------- bootstrap ----------
  async function boot() {
    const snippet = readJsonScript("snippet-data");
    state.limits = readJsonScript("limits-data");
    if (state.limits) {
      $("limitsInfo").textContent =
        `Лимиты: ${state.limits.run_timeout} с · ${state.limits.memory_mb} МБ · вывод ${state.limits.max_output_kb} КБ`;
    }
    state.fontSize = store.get("fontSize", 14);
    setFontSize(state.fontSize);
    setWrap(store.get("wrap", false));
    setMode(store.get("mode", "console"));
    if (store.get("history", false) && innerWidth > 860) $("history").hidden = false;

    renderAccount();
    initOAuthButtons();
    const params = new URLSearchParams(location.search);
    if (params.has("login") && !account.user) {
      account.afterLogin = params.get("next") || "";
      history.replaceState(null, "", location.pathname);
      openAuth("login", "Войди — и вернёмся туда, откуда пришли");
    }
    if (auth.reset) openResetConfirm();
    if (auth.error) {
      toast(auth.error);
      history.replaceState(null, "", location.pathname);
    }
    initMonaco(); // грузится параллельно со списком языков

    let data;
    try {
      data = await api("/api/languages/");
    } catch (err) {
      $("langLabel").textContent = "Сервер недоступен";
      toast("Не удалось загрузить языки: " + err.message);
      return;
    }
    state.languages = data.languages;
    state.bySlug = Object.fromEntries(data.languages.map((l) => [l.slug, l]));

    const firstAvailable = state.languages.find((l) => l.available) || state.languages[0];
    const stored = store.get("lang");
    const slug = snippet?.language || (state.bySlug[stored] ? stored : firstAvailable.slug);
    if (snippet) $("stdin").value = snippet.stdin || "";
    selectLanguage(slug, snippet ? { code: snippet.code, files: snippet.files || [], args: snippet.args || "" } : undefined);
    if (snippet) setCurrentProject(snippet);
    refreshHistory();
  }

  boot();
})();
