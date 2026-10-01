/* Страница Scratch 3: редактор во фрейме (scratch-gui, собранный с window.ocVM) + сохранение в наши проекты.
   Проект хранится как .sb3 в base64: загрузка — vm.loadProject(buffer), сохранение — vm.saveProjectSb3(). */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const read = (id) => { try { return JSON.parse($(id).textContent); } catch { return null; } };
  const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const user = read("user-data");
  let project = read("project-data");  // {id, title, owner, is_owner, visibility, forked_from, forks, url} или null
  let vm = null;
  let dirty = false;
  let loading = false;  // пока грузим проект в редактор, его события изменений — не правки пользователя
  let saving = false;

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
    try { data = await res.json(); } catch { /* не JSON */ }
    if (!res.ok) throw new Error((data && data.error) || `HTTP ${res.status}`);
    return data;
  }

  let toastTimer = null;
  function toast(text) {
    $("toast").textContent = text;
    $("toast").hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { $("toast").hidden = true; }, 3000);
  }

  const blobToBase64 = (blob) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });

  // Буфер создаём конструктором из окна фрейма: VM проверяет instanceof ArrayBuffer своего мира,
  // и «чужой» буфер из родительской страницы не узнаёт (уходит в парсер старого формата Scratch 1.4)
  function base64ToBuffer(b64, realm = window) {
    const bin = atob(b64);
    const bytes = new realm.Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return bytes.buffer;
  }

  // ---------- шапка ----------
  function setDirty(value) {
    dirty = value;
    $("projectDirty").hidden = !dirty;
  }

  function render() {
    const own = !!project?.is_owner;
    $("projectTitle").textContent = project ? project.title || "Без названия" : "Новый проект";
    $("projectTitle").classList.toggle("untitled", !project?.title);
    $("projectTitle").classList.toggle("editable", own);
    $("visibilitySelect").hidden = !own;
    if (own) $("visibilitySelect").value = project.visibility || "unlisted";
    const meta = [];
    if (project?.owner && !own) {
      meta.push(`<a href="/u/${encodeURIComponent(project.owner)}/">@${escapeHtml(project.owner)}</a>`);
    }
    if (project?.forked_from) {
      meta.push(`форк от <a href="${escapeHtml(project.forked_from.url)}">${escapeHtml(project.forked_from.title || project.forked_from.id)}</a>`);
    }
    $("projectMeta").innerHTML = meta.join(" · ");
    $("saveLabel").textContent = !user ? "Поделиться" : project && !own ? "Форк" : "Сохранить";
    $("saveBtn").title = !user ? "Сохранить и получить ссылку (Ctrl+S)"
      : project && !own ? "Сохранить к себе копию с твоими правками (Ctrl+S)" : "Сохранить (Ctrl+S)";
    $("accountLink").textContent = user ? user.username : "Войти";
    $("accountLink").href = user ? `/u/${encodeURIComponent(user.username)}/` : `/?login=1&next=${encodeURIComponent(location.pathname)}`;
  }

  // ---------- сохранение ----------
  async function save() {
    if (!vm || saving) return;
    saving = true;
    $("saveBtn").disabled = true;
    try {
      const sb3 = await blobToBase64(await vm.saveProjectSb3());
      if (user && project?.is_owner) {
        project = await api(`/api/scratch/${project.id}/`, { sb3 }, "PATCH");
        toast("Сохранено");
      } else if (user && project) {
        const copy = await api(`/api/snippets/${project.id}/fork/`, {});
        project = await api(`/api/scratch/${copy.id}/`, { sb3 }, "PATCH");
        history.replaceState(null, "", project.url);
        toast("Форк готов — теперь это твой проект");
      } else {
        project = await api("/api/scratch/", { sb3, title: project?.title || "" });
        history.replaceState(null, "", project.url);
        const link = new URL(project.url, location.origin).href;
        try { await navigator.clipboard.writeText(link); toast(`Сохранено, ссылка скопирована: ${link}`); }
        catch { toast(`Сохранено: ${link}`); }
      }
      delete project.sb3;
      setDirty(false);
      render();
    } catch (err) {
      toast("Не удалось сохранить: " + err.message);
    } finally {
      saving = false;
      $("saveBtn").disabled = false;
    }
  }
  $("saveBtn").addEventListener("click", save);

  // ---------- переименование и видимость ----------
  $("projectTitle").addEventListener("click", () => {
    if (!project?.is_owner) return;
    const btn = $("projectTitle");
    const input = Object.assign(document.createElement("input"), {
      className: "project-title-input", value: project.title, maxLength: 200, placeholder: "Название проекта",
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
      if (!commit || title === project.title) return;
      try {
        const saved = await api(`/api/scratch/${project.id}/`, { title }, "PATCH");
        project.title = saved.title;
        render();
      } catch (err) { toast("Не удалось переименовать: " + err.message); }
    };
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); finish(true); }
      else if (e.key === "Escape") { e.preventDefault(); finish(false); }
    });
    input.addEventListener("blur", () => finish(true));
  });

  $("visibilitySelect").addEventListener("change", async (e) => {
    try {
      const saved = await api(`/api/scratch/${project.id}/`, { visibility: e.target.value }, "PATCH");
      project.visibility = saved.visibility;
      toast({ public: "Проект публичный — он виден в твоём профиле", unlisted: "Проект открывается по ссылке",
        private: "Проект приватный — его видишь только ты" }[saved.visibility]);
    } catch (err) {
      e.target.value = project.visibility;
      toast("Не удалось сменить видимость: " + err.message);
    }
  });

  function onKey(e) {
    if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S")) {
      e.preventDefault();
      save();
    }
  }
  document.addEventListener("keydown", onKey);
  window.addEventListener("beforeunload", (e) => {
    if (dirty) { e.preventDefault(); e.returnValue = ""; }
  });

  // ---------- редактор ----------
  async function waitForVM(frame) {
    const deadline = Date.now() + 60000;
    while (Date.now() < deadline) {
      const candidate = frame.contentWindow && frame.contentWindow.ocVM;
      if (candidate) return candidate;
      await new Promise((r) => setTimeout(r, 200));
    }
    throw new Error("редактор Scratch не запустился");
  }

  async function init() {
    render();
    const frame = $("scratchFrame");
    if (!frame) return;  // редактор не собран — страница сама это объясняет
    try {
      vm = await waitForVM(frame);
      // Ctrl+S внутри фрейма до нас не доходит — слушаем и его документ (тот же origin)
      frame.contentWindow.document.addEventListener("keydown", onKey);
      if (project) {
        const data = await api(`/api/scratch/${project.id}/`);
        loading = true;
        await vm.loadProject(base64ToBuffer(data.sb3, frame.contentWindow));
      }
      vm.on("PROJECT_CHANGED", () => { if (!loading) setDirty(true); });
      $("saveBtn").disabled = false;
    } catch (err) {
      toast("Не удалось открыть проект: " + err.message);
    } finally {
      // события изменений от загрузки приходят асинхронно — снимаем флаг чуть позже
      setTimeout(() => { loading = false; }, 500);
      $("scratchLoading")?.remove();
    }
  }

  init();
  window.ocScratch = { save, get vm() { return vm; }, get project() { return project; } };  // для e2e-тестов
})();
