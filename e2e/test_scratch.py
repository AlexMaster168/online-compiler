"""Браузерный e2e: Scratch 3 — редактор запускается, проекты сохраняются в аккаунт и открываются по ссылке.

    python e2e/test_scratch.py [http://127.0.0.1:8000]

Нужен собранный редактор: python manage.py build_scratch.
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BASE, OUT, check, errors, results, wait_until  # noqa: E402

STAMP = str(int(time.time()))[-6:]
USER, PASSWORD = f"scratch_{STAMP}", "Krepkiy-parol-42"


def new_page(browser):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.grant_permissions(["clipboard-read", "clipboard-write"])
    page = ctx.new_page()
    # Сам Scratch шумит в консоль (WebGL, расширения) — ловим только ошибки нашей страницы
    page.on("pageerror", lambda e: errors.append(str(e)))
    return page


def open_scratch(page, url="/scratch/"):
    page.goto(BASE + url)
    page.wait_for_function("() => window.ocScratch && window.ocScratch.vm", timeout=90000)
    page.wait_for_function("() => !document.getElementById('saveBtn').disabled", timeout=60000)


def sprite_names(page):
    return page.evaluate("() => ocScratch.vm.runtime.targets.filter(t => !t.isStage).map(t => t.getName())")


def rename_first_sprite(page, name):
    page.evaluate("""name => {
        const sprite = ocScratch.vm.runtime.targets.find(t => !t.isStage);
        ocScratch.vm.renameSprite(sprite.id, name);
    }""", name)


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--use-gl=swiftshader"])
    page = new_page(browser)

    # ---------- аноним: редактор и ссылка ----------
    open_scratch(page)
    check("scratch editor boots with default sprite", len(sprite_names(page)) >= 1, sprite_names(page))
    check("anonymous save is share", page.inner_text("#saveLabel") == "Поделиться")
    rename_first_sprite(page, "Кот Лёха")
    check("change marks dirty", wait_until(page, lambda: page.is_visible("#projectDirty"), 10))
    page.click("#saveBtn")
    check("saved to link", wait_until(page, lambda: "/scratch/" in page.url and page.url.rstrip("/") != f"{BASE}/scratch",
                                      30), page.url)
    shared = page.url
    page.screenshot(path=f"{OUT}/scratch.png")

    other = new_page(browser)
    open_scratch(other, shared.replace(BASE, ""))
    check("shared project loads", wait_until(other, lambda: "Кот Лёха" in sprite_names(other), 30), sprite_names(other))
    check("loaded project is clean", not other.is_visible("#projectDirty"))

    # ---------- аккаунт: сохранить к себе, переименовать, вернуться из «Моих проектов» ----------
    acc = new_page(browser)
    acc.goto(BASE + "/")
    acc.wait_for_selector("#tabs .tab", timeout=30000)
    acc.click("#loginBtn")
    acc.click("#authForm [data-auth=register]")
    acc.fill("#authForm [name=username]", USER)
    acc.fill("#authForm [name=password]", PASSWORD)
    acc.click("#authSubmit")
    acc.wait_for_function("() => !document.getElementById('authDialog').open", timeout=15000)
    acc.click("#langButton")
    acc.fill("#langSearch", "scratch")
    acc.wait_for_selector("#langList li[data-href='/scratch/']", timeout=5000)
    acc.click("#langList li[data-href='/scratch/']")
    acc.wait_for_url("**/scratch/", timeout=15000)
    open_scratch(acc)
    check("logged in: save label", acc.inner_text("#saveLabel") == "Сохранить")
    rename_first_sprite(acc, "Мой спрайт")
    acc.click("#saveBtn")
    check("saved to my projects", wait_until(acc, lambda: "/scratch/" in acc.url and acc.url.rstrip("/") != f"{BASE}/scratch",
                                             30), acc.url)
    own_url = acc.url
    acc.click("#projectTitle")
    acc.fill(".project-title-input", "Догонялки")
    acc.keyboard.press("Enter")
    check("rename scratch project", wait_until(acc, lambda: acc.inner_text("#projectTitle") == "Догонялки", 10))
    rename_first_sprite(acc, "Мой спрайт 2")
    acc.keyboard.press("Control+s")
    check("ctrl+s saves in place", wait_until(acc, lambda: not acc.is_visible("#projectDirty"), 20) and acc.url == own_url)

    acc.goto(BASE + "/")
    acc.wait_for_selector("#tabs .tab", timeout=30000)
    acc.click("#userBtn")
    acc.click("#myProjectsBtn")
    acc.wait_for_selector("#projectsList li.item", timeout=10000)
    check("scratch in my projects", "Scratch 3" in acc.inner_text("#projectsList"), acc.inner_text("#projectsList"))
    acc.click("#projectsList li.item:has-text('Догонялки')")
    acc.wait_for_url("**/scratch/**", timeout=15000)
    open_scratch(acc, acc.url.replace(BASE, ""))
    check("reopened from my projects", wait_until(acc, lambda: "Мой спрайт 2" in sprite_names(acc), 30),
          sprite_names(acc))

    # ---------- чужой проект: форк ----------
    open_scratch(acc, shared.replace(BASE, ""))
    check("foreign project offers fork", acc.inner_text("#saveLabel") == "Форк")
    acc.click("#saveBtn")
    check("fork gets own url", wait_until(acc, lambda: acc.url != shared and "/scratch/" in acc.url, 30), acc.url)
    check("fork meta", "форк от" in acc.inner_text("#projectMeta"))

    check("no page errors", not errors, errors[:5])
    browser.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
