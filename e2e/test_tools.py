"""Браузерный e2e этапа 3: аргументы, Beautify, zip, настройки отступов, Vim / Emacs.

    python e2e/test_tools.py [http://127.0.0.1:8000]

Нужен запущенный сервер, Docker (Rust-форматтер, C) и интернет (WASM-форматтеры и monaco-vim грузятся с CDN).
"""
import io
import os
import sys
import zipfile

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (  # noqa: E402
    BASE, OUT, batch_run, check, choose, console_run, editor_value, errors, results, set_code, term_text, wait_until,
)


def model_options(page):
    return page.evaluate("() => { const o = monaco.editor.getEditors()[0].getModel().getOptions();"
                         " return [o.tabSize, o.insertSpaces]; }")


def format_and_wait(page, before, timeout=60):
    page.click("#formatBtn")
    return wait_until(page, lambda: editor_value(page) != before, timeout)


def settings_set(page, name, value):
    page.click("#settingsBtn")
    page.select_option(f"#settingsForm [name={name}]", value)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    ctx.add_init_script("try { if (!sessionStorage.getItem('oc-e2e')) { localStorage.clear(); "
                        "sessionStorage.setItem('oc-e2e', '1') } } catch (e) {}")
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and m.text != "Canceled" and errors.append(m.text))
    page.on("pageerror", lambda e: "Canceled" not in str(e) and errors.append(str(e)))
    page.goto(BASE + "/")
    page.wait_for_selector("#tabs .tab", timeout=30000)
    page.wait_for_selector("#terminal .xterm-rows", timeout=15000)

    # ---------- аргументы командной строки ----------
    choose(page, "python")
    set_code(page, "import sys\nprint('ARGS', sys.argv[1:])\n")
    page.fill("#argsInput", '-n 5 "два слова"')
    console_run(page)
    check("console: args reach program", "ARGS ['-n', '5', 'два слова']" in term_text(page), term_text(page))
    page.click("#modeBatch")
    page.fill("#argsInput", "x 'y z'")
    batch_run(page)
    check("batch: args reach program", "ARGS ['x', 'y z']" in page.inner_text("#output"), page.inner_text("#output"))
    page.fill("#argsInput", '"broken')
    batch_run(page)
    check("bad quotes reported", "кавычка" in page.inner_text("#output"), page.inner_text("#output"))
    # браузер сам пишет в консоль «400 Bad Request» на этот запрос — это ожидаемо
    errors[:] = [e for e in errors if "status of 400" not in e]
    page.fill("#argsInput", "keep me")
    page.click("#modeConsole")

    # ---------- Beautify ----------
    set_code(page, "import sys\ndef f( a,b ):\n  return a+b\nx=[1,2,\n3]\nprint('ARGS', sys.argv[1:], f(1,2), x)\n")
    before = editor_value(page)
    check("python: ruff formats", format_and_wait(page, before)
          and "def f(a, b):\n    return a + b\n" in editor_value(page) and "x = [1, 2, 3]" in editor_value(page),
          editor_value(page))
    page.click(".monaco-editor")
    page.keyboard.press("Control+z")
    check("undo reverts format in one step", editor_value(page) == before, editor_value(page))
    page.keyboard.press("Shift+Alt+F")
    check("Shift+Alt+F formats", wait_until(page, lambda: editor_value(page) != before, 30), editor_value(page))

    settings_set(page, "tabSize", "2")
    check("tab size applied to model", model_options(page) == [2, True], model_options(page))
    settings_set(page, "indent", "tabs")
    set_code(page, "def f():\n    return 1\n")
    format_and_wait(page, "def f():\n    return 1\n")
    check("ruff uses tabs from settings", editor_value(page) == "def f():\n\treturn 1\n", repr(editor_value(page)))
    settings_set(page, "indent", "spaces")
    settings_set(page, "tabSize", "4")

    cases = [
        ("c", "#include <stdio.h>\nint main(void){int a=1;if(a){printf(\"%d\\n\",a);}return 0;}\n",
         "    if (a) {"),
        ("javascript", "const f=(a,b)=>{return a+b}\nconsole.log( f(1,2) )\n", "const f = (a, b) => {"),
        ("go", "package main\nimport \"fmt\"\nfunc main(){\nfmt.Println(\"hi\")\n}\n", "\tfmt.Println(\"hi\")"),
        ("java", "public class Main{public static void main(String[] a){System.out.println(1);}}\n",
         "public static void main"),
        ("rust", "fn main(){let x=1;println!(\"{}\",x)}\n", "    let x = 1;"),
        ("sql", "select a,b from t where a>1;\n", "select"),
    ]
    for slug, code, expected in cases:
        choose(page, slug)
        set_code(page, code)
        ok = format_and_wait(page, code, 90)
        check(f"{slug}: formatted", ok and expected in editor_value(page), editor_value(page)[:300])

    choose(page, "haskell")
    check("no formatter -> button disabled", page.is_disabled("#formatBtn"), page.get_attribute("#formatBtn", "title"))

    # ---------- zip ----------
    choose(page, "python")
    page.click("#newFileBtn")
    page.fill(".tab-input", "lib/util.py")
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    set_code(page, "VALUE = 'Лёха'\n")
    with page.expect_download() as dl:
        page.click("#downloadBtn")
    download = dl.value
    data = open(download.path(), "rb").read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = sorted(zf.namelist())
        util = zf.read("lib/util.py").decode() if "lib/util.py" in names else ""
    check("zip has project files", names == ["lib/util.py", "main.py"] and "Лёха" in util, names)
    check("zip file name", download.suggested_filename == "python-project.zip", download.suggested_filename)

    # ---------- args в черновике и в ссылке ----------
    page.click("#tabs .tab >> nth=0")
    page.wait_for_timeout(600)
    page.reload()
    page.wait_for_selector("#tabs .tab >> nth=1", timeout=30000)
    check("args survive reload (draft)", page.input_value("#argsInput") == "keep me", page.input_value("#argsInput"))
    check("settings survive reload", page.evaluate("JSON.parse(localStorage.getItem('oc:settings')).tabSize") == 4)
    page.click(".monaco-editor")
    page.keyboard.press("Control+s")
    page.wait_for_url("**/s/*/", timeout=10000)
    other = browser.new_context().new_page()
    other.goto(page.url)
    other.wait_for_selector("#tabs .tab >> nth=1", timeout=30000)
    check("shared snippet keeps args", other.input_value("#argsInput") == "keep me", other.input_value("#argsInput"))
    other.close()

    # ---------- Vim ----------
    choose(page, "python")
    set_code(page, "first = 1\nsecond = 2\nprint(first)\n")
    settings_set(page, "keymap", "vim")
    check("vim status bar shown", wait_until(page, lambda: page.is_visible("#vimStatus")
                                             and "NORMAL" in page.inner_text("#vimStatus").upper(), 30),
          page.inner_text("#vimStatus") if page.is_visible("#vimStatus") else "hidden")
    page.click(".monaco-editor .view-line >> nth=0")
    page.keyboard.press("Escape")
    page.keyboard.press("g")
    page.keyboard.press("g")
    page.keyboard.press("d")
    page.keyboard.press("d")
    check("vim dd deletes line", editor_value(page) == "second = 2\nprint(first)\n", repr(editor_value(page)))
    page.keyboard.press("u")
    check("vim u undoes", editor_value(page).startswith("first = 1"), repr(editor_value(page)))
    page.keyboard.press("Control+Enter")
    page.wait_for_function("() => !document.getElementById('runBtn').classList.contains('stop')", timeout=60000)
    check("Ctrl+Enter still runs in vim mode", wait_until(page, lambda: "Программа завершилась" in term_text(page), 30),
          term_text(page))
    page.screenshot(path=f"{OUT}/tools_vim.png")

    # ---------- Emacs ----------
    settings_set(page, "keymap", "emacs")
    check("vim disposed, emacs badge", not page.is_visible("#vimStatus")
          and wait_until(page, lambda: page.inner_text("#keymapInfo") == "EMACS", 30))
    page.click(".monaco-editor .view-line >> nth=0")
    page.keyboard.press("Control+a")
    page.keyboard.press("Control+e")
    col = page.evaluate("() => monaco.editor.getEditors()[0].getPosition().column")
    check("emacs C-e goes to line end", col == len("first = 1") + 1, col)
    settings_set(page, "keymap", "default")
    check("default keymap restores", not page.is_visible("#keymapInfo"))

    page.click("#settingsBtn")
    page.screenshot(path=f"{OUT}/tools_settings.png")
    page.keyboard.press("Escape")

    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto(BASE + "/")
    mobile.wait_for_selector("#tabs .tab", timeout=30000)
    check("mobile: no horizontal overflow", not mobile.evaluate("document.documentElement.scrollWidth > innerWidth"))
    mobile.screenshot(path=f"{OUT}/tools_mobile.png", full_page=True)

    check("no console errors", not errors, errors[:5])
    browser.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
