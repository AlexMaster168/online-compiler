"""Браузерный e2e основного UI: запуск, ошибки, мультифайл, консоль, история, шаринг, тема, мобилка.

    python e2e/test_ui.py [http://127.0.0.1:8000]

Нужен запущенный сервер. C/C++ идут через Docker — без него эти проверки упадут.
"""
import os
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    BASE, OUT, batch_run, check, choose, console_run, editor_value, errors, markers, results, set_code, tabs,
    term_text, wait_until,
)

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script("try { if (!sessionStorage.getItem('oc-e2e')) { localStorage.clear(); "
                        "sessionStorage.setItem('oc-e2e', '1') } } catch (e) {}")
    ctx.grant_permissions(["clipboard-read", "clipboard-write"])
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and m.text != "Canceled" and errors.append(m.text))
    page.on("pageerror", lambda e: "Canceled" not in str(e) and errors.append(str(e)))
    if os.environ.get("E2E_TRACE"):
        page.on("console", lambda m: m.type == "error" and print("TRACE", m.text, m.location,
                                                                  [a.json_value() for a in m.args][:2]))
        page.on("pageerror", lambda e: print("PAGEERROR", e.stack if hasattr(e, "stack") else e))
    page.goto(BASE + "/")
    page.wait_for_selector("#tabs .tab", timeout=30000)
    page.wait_for_selector("#terminal .xterm-rows", timeout=15000)

    # ---------- консоль (режим по умолчанию) ----------
    check("console mode by default", page.is_visible("#terminalWrap") and not page.is_visible("#stdinBlock"))
    choose(page, "python")
    set_code(page, 'n = input("Имя: ")\nprint("Привет,", n)\n')
    page.click("#runBtn")
    check("prompt before input", wait_until(page, lambda: "Имя: " in term_text(page)), term_text(page))
    page.click("#terminal")
    page.keyboard.type("Лёхх")
    page.keyboard.press("Backspace")
    page.keyboard.type("а")
    page.keyboard.press("Enter")
    page.wait_for_function("() => !document.getElementById('runBtn').classList.contains('stop')", timeout=60000)
    check("console run result", "Привет, Лёха" in term_text(page) and "Программа завершилась" in term_text(page),
          term_text(page))

    set_code(page, "import time\nprint('жду', flush=True)\ntime.sleep(60)\n")
    page.click("#runBtn")
    wait_until(page, lambda: "жду" in term_text(page))
    page.click("#runBtn")
    console_run(page)
    check("stop button", "Остановлено" in term_text(page), term_text(page))

    choose(page, "c")
    set_code(page, '#include <stdio.h>\nint main(void){int a;printf("a = ");scanf("%d",&a);printf("2a=%d\\n",2*a);}\n')
    page.click("#runBtn")
    check("C prompt via PTY", wait_until(page, lambda: "a = " in term_text(page), 120), term_text(page))
    page.click("#terminal")
    page.keyboard.type("21")
    page.keyboard.press("Enter")
    console_run(page)
    check("C result", "2a=42" in term_text(page), term_text(page))

    set_code(page, "int main(void) {\n    return undefined_var;\n}\n")
    console_run(page)
    check("compile error marker from console", 2 in markers(page), (markers(page), term_text(page)))

    # ---------- stdin заранее ----------
    page.click("#modeBatch")
    check("batch mode shows stdin", page.is_visible("#stdinBlock") and page.is_visible("#output"))
    choose(page, "python")
    set_code(page, "def f(n):\n    return 1 / n\n\nprint(f(int(input())))\n")
    page.fill("#stdin", "0")
    batch_run(page)
    check("runtime error badge", page.inner_text("#statusBadge") == "Ошибка выполнения")
    check("runtime marker on deepest frame (line 2)", markers(page)[:1] == [2], markers(page))
    page.fill("#stdin", "4")
    batch_run(page)
    check("batch run ok", "0.25" in page.inner_text("#output"), page.inner_text("#output"))

    choose(page, "java")
    set_code(page, 'public class Main {\n    public static void main(String[] a) {\n        int x = "строка";\n    }\n}\n')
    batch_run(page)
    check("java compile error", page.inner_text("#statusBadge") == "Ошибка компиляции")
    check("java marker line 3", 3 in markers(page), markers(page))
    check("cyrillic in javac output", "строка" in page.inner_text("#output"), page.inner_text("#output"))
    link = page.query_selector(".loc-link")
    if link:
        link.click()
        page.wait_for_timeout(200)
    check("location link jumps to line", page.evaluate("() => monaco.editor.getEditors()[0].getPosition().lineNumber") == 3)

    # ---------- мультифайл ----------
    choose(page, "python")
    page.click("#newFileBtn")
    page.fill(".tab-input", "lib/helper.py")
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    check("new file tab", "lib/helper.py" in tabs(page), tabs(page))
    set_code(page, "def greet(n):\n    return 'Привет, ' + n\n\ndef boom():\n    raise ValueError('ой')\n")
    page.click("#newFileBtn")
    page.fill(".tab-input", "../evil.py")
    page.keyboard.press("Enter")
    check("invalid name rejected", page.query_selector(".tab-input.invalid") is not None)
    page.keyboard.press("Escape")
    page.click("#tabs .tab >> nth=0")
    set_code(page, "from lib.helper import boom\nboom()\n")
    batch_run(page)
    check("error in secondary file marks its tab",
          page.query_selector("#tabs .tab.err .tab-name") is not None
          and page.inner_text("#tabs .tab.err .tab-name") == "lib/helper.py")
    page.click('.loc-link[data-file="lib/helper.py"] >> nth=-1')
    page.wait_for_timeout(200)
    check("link opens secondary file", page.inner_text("#tabs .tab.active .tab-name") == "lib/helper.py")

    upload = os.path.join(OUT, "uploaded_consts.py")
    with open(upload, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("VALUE = 42\n")
    page.set_input_files("#fileInput", upload)
    page.wait_for_timeout(400)
    check("upload adds tab", "uploaded_consts.py" in tabs(page), tabs(page))
    check("CRLF normalized on upload", editor_value(page) == "VALUE = 42\n", repr(editor_value(page)))
    page.dblclick("#tabs .tab:has-text('uploaded_consts.py')")
    page.fill(".tab-input", "consts.py")
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    page.click("#tabs .tab >> nth=0")
    set_code(page, "from consts import VALUE\nfrom lib.helper import greet\nprint(greet(str(VALUE)))\n")
    page.fill("#stdin", "")
    batch_run(page)
    check("multi-file run", "Привет, 42" in page.inner_text("#output"), page.inner_text("#output"))

    page.wait_for_timeout(600)
    page.reload()
    page.wait_for_selector("#tabs .tab >> nth=2", timeout=30000)
    check("draft (files) survives reload", tabs(page) == ["main.py", "lib/helper.py", "consts.py"], tabs(page))
    check("mode survives reload", page.is_visible("#stdinBlock"))

    page.click(".monaco-editor")
    page.keyboard.press("Control+s")
    page.wait_for_url("**/s/*/", timeout=10000)
    other = browser.new_context().new_page()
    other.goto(page.url)
    other.wait_for_selector("#tabs .tab >> nth=2", timeout=30000)
    check("shared snippet keeps files",
          other.eval_on_selector_all("#tabs .tab .tab-name", "e => e.map(x => x.textContent)")
          == ["main.py", "lib/helper.py", "consts.py"])
    other.close()

    page.on("dialog", lambda d: d.accept())
    page.click("#tabs .tab:has-text('consts.py')")
    page.click("#tabs .tab.active .tab-close")
    page.wait_for_timeout(200)
    check("delete tab", tabs(page) == ["main.py", "lib/helper.py"], tabs(page))

    # ---------- история, тема ----------
    page.click("#historyToggle")
    page.wait_for_selector("#historyList li.item", timeout=5000)
    check("history has runs", len(page.query_selector_all("#historyList li.item")) >= 5)
    page.click("#historyClose")
    before = page.evaluate("document.documentElement.dataset.theme")
    page.click("#themeBtn")
    check("theme toggles", page.evaluate("document.documentElement.dataset.theme") != before)
    page.screenshot(path=f"{OUT}/ui_desktop.png")

    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto(BASE + "/")
    mobile.wait_for_selector("#tabs .tab", timeout=30000)
    check("mobile: no horizontal overflow", not mobile.evaluate("document.documentElement.scrollWidth > innerWidth"))
    mobile.screenshot(path=f"{OUT}/ui_mobile.png", full_page=True)

    check("no console errors", not errors, errors[:5])
    browser.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
