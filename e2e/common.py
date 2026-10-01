"""Общие хелперы браузерных e2e-тестов."""
import os
import sys
import time

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(OUT, exist_ok=True)
errors, results = [], []


def check(name, cond, extra=""):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name, "" if cond else str(extra)[:600],
          f"[errors so far: {len(errors)}]" if os.environ.get("E2E_TRACE") else "")


def wait_until(page, predicate, timeout=60):
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
    # Не быстрее человека: setValue через <0.5 с после создания модели ловит гонку sticky scroll в Monaco
    page.wait_for_timeout(900)


def set_code(page, code):
    page.evaluate("c => monaco.editor.getEditors()[0].getModel().setValue(c)", code)


def editor_value(page):
    return page.evaluate("() => monaco.editor.getEditors()[0].getValue()")


def tabs(page):
    return page.eval_on_selector_all("#tabs .tab .tab-name", "els => els.map(e => e.textContent)")


def markers(page):
    return page.evaluate("() => monaco.editor.getModelMarkers({owner: 'oc'}).map(m => m.startLineNumber)")


def term_text(page):
    return page.inner_text("#terminal .xterm-rows")


def batch_run(page):
    page.click("#runBtn")
    page.wait_for_function("() => !document.getElementById('runBtn').disabled && "
                           "!document.getElementById('statusBadge').hidden && "
                           "document.getElementById('statusBadge').textContent !== 'Выполняется…'", timeout=90000)


def console_run(page):
    page.click("#runBtn")
    page.wait_for_function("() => !document.getElementById('runBtn').classList.contains('stop')", timeout=90000)
