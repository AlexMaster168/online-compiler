"""Браузерный e2e отладчика. Нужны: запущенный сервер (start.bat), Docker и `manage.py build_sandbox`.

    python e2e/test_debugger.py [http://127.0.0.1:8000]
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(OUT, exist_ok=True)
errors, results = [], []


def check(name, cond, extra=""):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name, "" if cond else str(extra)[:700])


def term_text(page):
    return page.inner_text("#terminal .xterm-rows")


def wait_until(page, predicate, timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        page.wait_for_timeout(150)
    return False


def choose(page, name):
    page.click("#langButton")
    page.fill("#langSearch", name)
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)


def set_code(page, code):
    page.evaluate("c => monaco.editor.getEditors()[0].getModel().setValue(c)", code)


def click_gutter(page, line):
    """Клик по полю брейкпоинтов слева от номера строки."""
    x, y = page.evaluate("""line => {
        const ed = monaco.editor.getEditors()[0];
        const rect = ed.getDomNode().getBoundingClientRect();
        const layout = ed.getLayoutInfo();
        const top = ed.getTopForLineNumber(line) - ed.getScrollTop();
        return [rect.left + layout.glyphMarginLeft + 8, rect.top + top + 10];
    }""", line)
    page.mouse.click(x, y)
    page.wait_for_timeout(150)


def breakpoints(page):
    return page.evaluate("""() => {
        const m = monaco.editor.getEditors()[0].getModel();
        return m.getAllDecorations().filter(d => d.options.glyphMarginClassName === 'oc-bp')
                .map(d => d.range.startLineNumber).sort((a, b) => a - b);
    }""")


def current_line(page):
    return page.evaluate("""() => {
        const m = monaco.editor.getEditors()[0].getModel();
        const d = m.getAllDecorations().find(d => d.options.glyphMarginClassName === 'oc-current-arrow');
        return d ? d.range.startLineNumber : null;
    }""")


def state(page):
    return page.inner_text("#dbgState")


def wait_paused(page, timeout=120):
    return wait_until(page, lambda: page.is_visible("#debugToolbar") and not page.is_disabled("#dbgStepOver"), timeout)


PY = ("def square(x):\n    y = x * x\n    return y\n\nname = input('Имя: ')\ntotal = 0\n"
      "for i in range(3):\n    total += square(i)\nprint('Привет,', name, total)\n")
C = ('#include <stdio.h>\nint square(int x) {\n    int y = x * x;\n    return y;\n}\nint main(void) {\n'
     '    int total = 0;\n    for (int i = 0; i < 3; i++) total += square(i);\n    printf("total=%d\\n", total);\n'
     '    return 0;\n}\n')
JAVA = ('public class Main {\n    static int square(int x) {\n        int y = x * x;\n        return y;\n    }\n'
        '    public static void main(String[] args) {\n        int[] data = {3, 4};\n        int total = 0;\n'
        '        for (int v : data) total += square(v);\n        System.out.println("total=" + total);\n    }\n}\n')

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script("try { localStorage.clear() } catch (e) {}")
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and m.text != "Canceled" and errors.append(m.text))
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE + "/")
    page.wait_for_selector("#tabs .tab", timeout=30000)

    # ---------- Python ----------
    choose(page, "python")
    check("debug button visible for Python", page.is_visible("#debugBtn"))
    set_code(page, PY)
    click_gutter(page, 2)
    check("gutter click sets breakpoint", breakpoints(page) == [2], breakpoints(page))
    click_gutter(page, 9)
    click_gutter(page, 9)
    check("second click removes breakpoint", breakpoints(page) == [2], breakpoints(page))

    page.click("#debugBtn")
    check("debug toolbar + panel shown", page.is_visible("#debugToolbar") and page.is_visible("#debugPanel"))
    check("program prompt in console", wait_until(page, lambda: "Имя: " in term_text(page)), term_text(page))
    page.click("#terminal")
    page.keyboard.type("Лёха")
    page.keyboard.press("Enter")
    check("paused at breakpoint", wait_paused(page), state(page))
    check("current line arrow on line 2", current_line(page) == 2, current_line(page))
    check("call stack shows square <- module",
          "square" in page.inner_text("#dbgFrames") and "main.py:8" in page.inner_text("#dbgFrames"),
          page.inner_text("#dbgFrames"))
    check("variables show x: 0", "x:\n0" in page.inner_text("#dbgVars") or "x: 0" in page.inner_text("#dbgVars").replace("\n", " "),
          page.inner_text("#dbgVars"))

    page.fill("#watchInput", "x * 10 + 1")
    page.press("#watchInput", "Enter")
    check("watch evaluates", wait_until(page, lambda: "x * 10 + 1 =1" in page.inner_text("#dbgWatches").replace(" \n", "").replace("\n", ""), 15),
          page.inner_text("#dbgWatches"))
    page.screenshot(path=f"{OUT}/debug_python_paused.png")

    page.keyboard.press("F10")
    check("F10 steps to line 3", wait_until(page, lambda: current_line(page) == 3, 20), current_line(page))
    page.keyboard.press("F5")
    check("F5 continues to next hit (x=1)",
          wait_until(page, lambda: current_line(page) == 2 and "1" in page.inner_text("#dbgVars"), 20),
          page.inner_text("#dbgVars"))
    check("watch re-evaluated (x=1 -> 11)", wait_until(page, lambda: "11" in page.inner_text("#dbgWatches"), 15),
          page.inner_text("#dbgWatches"))

    # Наведение мышкой на переменную во время паузы
    pos = page.evaluate("""() => {
        const ed = monaco.editor.getEditors()[0];
        const p = ed.getScrolledVisiblePosition({lineNumber: 2, column: 9});
        const r = ed.getDomNode().getBoundingClientRect();
        return [r.left + p.left + 3, r.top + p.top + 8];
    }""")
    page.mouse.move(pos[0] - 20, pos[1])
    page.mouse.move(pos[0], pos[1], steps=5)
    visible_hovers = "els => els.filter(e => e.offsetParent !== null).map(e => e.innerText).join(' | ')"
    check("hover shows variable value",
          wait_until(page, lambda: "x = 1" in page.eval_on_selector_all(".monaco-hover", visible_hovers), 10),
          page.eval_on_selector_all(".monaco-hover", visible_hovers))

    click_gutter(page, 2)  # убираем брейкпоинт прямо во время сессии
    page.keyboard.press("F5")
    check("program finishes after breakpoint removed",
          wait_until(page, lambda: "Программа завершилась" in term_text(page), 30), term_text(page))
    check("toolbar hidden after exit", wait_until(page, lambda: not page.is_visible("#debugToolbar"), 5))
    check("output correct", "Привет, Лёха 5" in term_text(page), term_text(page))

    # ---------- C (gdb) ----------
    choose(page, "c")
    set_code(page, C)
    click_gutter(page, 3)
    page.click("#debugBtn")
    check("C: paused in square", wait_paused(page) and current_line(page) == 3, (state(page), current_line(page)))
    check("C: frames square <- main", "square" in page.inner_text("#dbgFrames") and "main" in page.inner_text("#dbgFrames"),
          page.inner_text("#dbgFrames"))
    page.click("#dbgFrames li >> nth=1")  # кадр main
    check("C: selecting caller frame jumps to line 8",
          wait_until(page, lambda: "total" in page.inner_text("#dbgVars"), 15), page.inner_text("#dbgVars"))
    page.keyboard.press("Shift+F11")
    check("C: step out returns to main", wait_until(page, lambda: current_line(page) == 8, 20), current_line(page))
    page.screenshot(path=f"{OUT}/debug_c.png")
    page.click("#dbgStop")
    check("C: stop ends session", wait_until(page, lambda: not page.is_visible("#debugToolbar"), 20)
          and "Остановлено" in term_text(page), term_text(page))

    # ---------- Java (свой JDI-адаптер) ----------
    choose(page, "java")
    set_code(page, JAVA)
    click_gutter(page, 3)
    page.click("#debugBtn")
    check("Java: paused in square", wait_paused(page) and current_line(page) == 3, (state(page), current_line(page)))
    check("Java: x = 3", "3" in page.inner_text("#dbgVars"), page.inner_text("#dbgVars"))
    page.click("#dbgFrames li >> nth=1")
    page.wait_for_timeout(800)
    tree = page.inner_text("#dbgVars")
    check("Java: caller frame has data array", "int[2]" in tree, tree)
    page.click("#dbgVars .dbg-var:has-text('data')")
    check("Java: array expands to elements", wait_until(page, lambda: "[1]:" in page.inner_text("#dbgVars"), 10),
          page.inner_text("#dbgVars"))
    page.screenshot(path=f"{OUT}/debug_java.png")
    click_gutter(page, 3)
    page.keyboard.press("F5")
    check("Java: finishes with total=25", wait_until(page, lambda: "total=25" in term_text(page), 30), term_text(page))

    check("no console errors", not errors, errors[:5])
    browser.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
