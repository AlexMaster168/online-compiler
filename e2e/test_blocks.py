"""Браузерный e2e: блоки в стиле Scratch (Blockly -> Python).

    python e2e/test_blocks.py [http://127.0.0.1:8000]
"""
import os
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BASE, OUT, check, editor_value, errors, results, term_text, wait_until  # noqa: E402


def block_count(page):
    return page.evaluate("() => OCBlocks.workspace.getAllBlocks(false).length")


def wait_blocks(page):
    """Рабочая область создана и в ней есть блоки (CSS-селекторы Blockly неоднозначны: канвасов несколько)."""
    page.wait_for_function("() => window.OCBlocks && OCBlocks.workspace"
                           " && OCBlocks.workspace.getAllBlocks(false).length > 0", timeout=60000)


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script("try { if (!sessionStorage.getItem('oc-e2e')) { localStorage.clear(); "
                        "sessionStorage.setItem('oc-e2e', '1') } } catch (e) {}")
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and m.text != "Canceled" and errors.append(m.text))
    page.on("pageerror", lambda e: "Canceled" not in str(e) and errors.append(str(e)))
    page.goto(BASE + "/")
    page.wait_for_selector("#tabs .tab", timeout=30000)
    page.wait_for_selector("#terminal .xterm-rows", timeout=15000)

    page.click("#langButton")
    page.fill("#langSearch", "блоки")
    page.keyboard.press("Enter")
    wait_blocks(page)
    wait_until(page, lambda: "text_prompt" in editor_value(page), 20)
    check("starter program generated", "for count in range(3)" in editor_value(page), editor_value(page))
    check("code view is read-only", page.evaluate(
        "() => monaco.editor.getEditors()[0].getOption(monaco.editor.EditorOption.readOnly)"))
    check("tabs and format hidden", not page.is_visible("#tabs") and not page.is_visible("#formatBtn"))
    check("blocks fill the area", page.evaluate(
        "() => document.querySelector('#blocksArea .blocklySvg').getBoundingClientRect().height") > 200)

    # ---------- перетаскивание блока из меню ----------
    before = block_count(page)
    page.click("#blocksArea .blocklyToolboxCategory:has-text('Ввод и вывод')")
    page.wait_for_selector(".blocklyFlyout .blocklyDraggable", timeout=10000)
    source = page.locator(".blocklyFlyout .blocklyDraggable").first.bounding_box()
    area = page.locator("#blocksArea").bounding_box()
    page.mouse.move(source["x"] + 15, source["y"] + 12)
    page.mouse.down()
    page.mouse.move(area["x"] + area["width"] - 260, area["y"] + area["height"] - 90, steps=12)
    page.mouse.up()
    check("block dragged from toolbox", wait_until(page, lambda: block_count(page) > before, 5),
          (before, block_count(page)))
    check("generated code updated", wait_until(page, lambda: editor_value(page).count("print(") >= 3, 5),
          editor_value(page))

    # ---------- запуск ----------
    page.click("#runBtn")
    check("program asks name", wait_until(page, lambda: "Как тебя зовут?" in term_text(page), 60), term_text(page))
    page.click("#terminal")
    page.keyboard.type("Лёха")
    page.keyboard.press("Enter")
    page.wait_for_function("() => !document.getElementById('runBtn').classList.contains('stop')", timeout=60000)
    check("blocks program runs", "Привет, Лёха!" in term_text(page)
          and term_text(page).count("Блоки — это тоже программирование!") == 3, term_text(page))

    # ---------- код Python можно спрятать ----------
    page.click("#blocksCodeBtn")
    check("hide python code", not page.is_visible("#editor"))
    page.click("#blocksCodeBtn")
    check("show python code", page.is_visible("#editor"))

    # ---------- черновик и ссылка сохраняют блоки ----------
    count = block_count(page)
    page.wait_for_timeout(700)
    page.reload()
    wait_blocks(page)
    check("blocks survive reload", wait_until(page, lambda: block_count(page) == count, 20), (count, block_count(page)))
    page.click("#shareBtn")
    page.wait_for_url("**/s/*/", timeout=10000)
    other = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
    other.goto(page.url)
    wait_blocks(other)
    check("shared link opens blocks", wait_until(other, lambda: block_count(other) == count, 20))
    other.close()

    page.click("#themeBtn")
    page.wait_for_timeout(500)
    page.screenshot(path=f"{OUT}/blocks.png")

    # ---------- уход на обычный язык возвращает Monaco ----------
    page.click("#langButton")
    page.fill("#langSearch", "python")
    page.keyboard.press("Enter")
    page.wait_for_timeout(900)
    check("back to code editor", not page.is_visible("#blocksArea") and page.is_visible("#tabs") and not page.evaluate(
        "() => monaco.editor.getEditors()[0].getOption(monaco.editor.EditorOption.readOnly)"))

    check("no console errors", not errors, errors[:5])
    browser.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
