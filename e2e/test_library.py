"""Браузерный e2e: библиотека примеров и новые языки (подсветка, запуск).

    python e2e/test_library.py [http://127.0.0.1:8000]
"""
import os
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (  # noqa: E402
    BASE, OUT, check, choose, console_run, editor_value, errors, results, set_code, term_text, wait_until,
)


def open_library(page):
    page.click("#libraryBtn")
    page.wait_for_selector("#libraryList .library-item", timeout=10000)


def token_classes(page, line=1):
    """CSS-классы токенов строки в Monaco: если подсветка работает, их больше одного вида."""
    return page.evaluate("""line => {
        const rows = [...document.querySelectorAll('.monaco-editor .view-line')];
        const row = rows[line - 1];
        return row ? [...new Set([...row.querySelectorAll('span span')].map(s => s.className))] : [];
    }""", line)


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script("try { if (!sessionStorage.getItem('oc-e2e')) { localStorage.clear(); "
                        "sessionStorage.setItem('oc-e2e', '1') } } catch (e) {}")
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and m.text != "Canceled" and errors.append(m.text))
    page.on("pageerror", lambda e: "Canceled" not in str(e) and errors.append(str(e)))
    page.on("dialog", lambda d: d.accept())
    page.goto(BASE + "/")
    page.wait_for_selector("#tabs .tab", timeout=30000)
    page.wait_for_selector("#terminal .xterm-rows", timeout=15000)

    # ---------- языки ----------
    page.click("#langButton")
    count = page.eval_on_selector_all("#langList li[data-slug]", "e => e.length")
    page.keyboard.press("Escape")
    check("43 language/editor entries in picker", count == 43, count)

    # ---------- библиотека ----------
    choose(page, "python")
    open_library(page)
    titles = page.eval_on_selector_all("#libraryList .l-title", "e => e.map(x => x.textContent)")
    groups = page.eval_on_selector_all("#libraryList h4", "e => e.map(x => x.textContent)")
    check("library lists 15 algorithms", len(titles) == 15, titles)
    check("library grouped by category", groups[:2] == ["Сортировки", "Поиск"], groups)
    page.fill("#librarySearch", "дейкстр")
    page.wait_for_timeout(300)
    titles = page.eval_on_selector_all("#libraryList .l-title", "e => e.map(x => x.textContent)")
    check("library search", titles == ["Алгоритм Дейкстры"], titles)
    page.screenshot(path=f"{OUT}/library_dialog.png")
    page.click("#libraryList .library-item")
    check("example inserted", wait_until(page, lambda: "heapq" in editor_value(page), 10), editor_value(page)[:200])
    console_run(page)
    check("example runs", "Dijkstra from 0: 0 3 1 4 7" in term_text(page), term_text(page))

    set_code(page, "print('мой код')\n")
    page.wait_for_timeout(500)
    open_library(page)
    page.click("#libraryList .library-item:has-text('Ханойские башни')")
    check("own code replaced after confirm", wait_until(page, lambda: "hanoi" in editor_value(page), 10))

    # ---------- новые языки: подсветка и запуск примера ----------
    for slug, needle, expected in [
        ("cobol", "PROGRAM-ID", "Total moves: 7"),
        ("fortran", "program", "Total moves: 7"),
        ("zig", "const std", "Total moves: 7"),
    ]:
        choose(page, slug)
        open_library(page)
        page.click("#libraryList .library-item:has-text('Ханойские башни')")
        wait_until(page, lambda: needle in editor_value(page), 10)
        page.wait_for_timeout(500)
        styled = max(len(token_classes(page, i)) for i in range(1, 8))
        check(f"{slug}: highlighted", styled >= 2, styled)
        console_run(page)
        check(f"{slug}: example runs", expected in term_text(page), term_text(page)[-400:])
    page.screenshot(path=f"{OUT}/library_zig.png")

    check("no console errors", not errors, errors[:5])
    browser.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
