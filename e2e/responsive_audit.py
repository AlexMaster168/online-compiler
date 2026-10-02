"""Аудит адаптивной вёрстки: все страницы и основные диалоги на телефонных и планшетных ширинах.

    python e2e/responsive_audit.py [http://127.0.0.1:8000]

Для каждой ширины проверяет горизонтальную прокрутку страницы и элементы, вылезающие за правый край,
и снимает скриншот в e2e/screenshots/responsive/. Выход с кодом 1, если что-то вылезло.
"""
import os
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BASE, OUT  # noqa: E402

WIDTHS = [(360, 740), (390, 844), (768, 1024), (1024, 768)]
SHOTS = os.path.join(OUT, "responsive")
os.makedirs(SHOTS, exist_ok=True)

# Элементы, которые вылезают за правый край экрана (кроме скрытых и прокручиваемых внутри контейнеров)
OVERFLOW_JS = """() => {
  const vw = document.documentElement.clientWidth;
  const bad = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const style = getComputedStyle(el);
    if (style.visibility === 'hidden' || style.position === 'fixed') continue;
    // внутри прокручиваемого контейнера вылезать можно — его и прокручивают
    let p = el.parentElement, scrolled = false;
    while (p && p !== document.body) {
      const ox = getComputedStyle(p).overflowX;
      if (ox === 'auto' || ox === 'scroll' || ox === 'hidden') { scrolled = true; break; }
      p = p.parentElement;
    }
    if (!scrolled && r.right > vw + 1) bad.push(`${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}`
      + `${el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : ''} → ${Math.round(r.right)}px`);
  }
  return {scroll: document.documentElement.scrollWidth > vw, vw, bad: bad.slice(0, 8)};
}"""

problems = []
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def audit(page, name, w):
    page.wait_for_timeout(400)
    result = page.evaluate(OVERFLOW_JS)
    status = "OK  " if not result["scroll"] and not result["bad"] else "FAIL"
    print(f"{status} {name:28} {w}px", "" if status == "OK  " else result)
    if status == "FAIL":
        problems.append((name, w, result))
    page.screenshot(path=os.path.join(SHOTS, f"{name}_{w}.png"), full_page=False)


def ready(page, url="/"):
    page.goto(BASE + url)
    page.wait_for_selector("#tabs .tab", timeout=30000)
    page.wait_for_function("() => window.monaco && monaco.editor.getEditors().length", timeout=30000)
    page.wait_for_timeout(600)


def choose(page, name):
    page.click("#langButton")
    page.fill("#langSearch", name)
    page.keyboard.press("Enter")
    page.wait_for_timeout(900)


with sync_playwright() as p:
    browser = p.chromium.launch()
    for w, h in WIDTHS:
        ctx = browser.new_context(viewport={"width": w, "height": h}, is_mobile=w < 700, has_touch=w < 700)
        page = ctx.new_page()
        ready(page)
        audit(page, "editor", w)
        page.click("#settingsBtn")
        audit(page, "dialog-settings", w)
        page.keyboard.press("Escape")
        page.click("#loginBtn")
        audit(page, "dialog-auth", w)
        page.keyboard.press("Escape")
        page.click("#libraryBtn")
        page.wait_for_selector("#libraryList .library-item", timeout=10000)
        audit(page, "dialog-library", w)
        page.keyboard.press("Escape")
        page.click("#modeBatch")
        audit(page, "editor-batch", w)
        page.click("#modeConsole")
        choose(page, "блоки")
        page.wait_for_function("() => window.OCBlocks && OCBlocks.workspace", timeout=60000)
        audit(page, "blocks", w)
        choose(page, "esp32")
        audit(page, "esp32", w)
        for name, url in [("profile", "/u/Лёха/"), ("scratch", "/scratch/"), ("arduino", "/arduino/")]:
            page.goto(BASE + url)
            page.wait_for_timeout(2500)
            audit(page, name, w)
        ctx.close()
    browser.close()

print(f"\nПроблем: {len(problems)}")
sys.exit(1 if problems else 0)
