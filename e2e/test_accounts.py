"""Браузерный e2e этапа 4: регистрация, вход, сохранение проекта, переименование, форк, «Мои проекты».

    python e2e/test_accounts.py [http://127.0.0.1:8000]

Нужен запущенный сервер. Пользователи создаются с уникальными именами — тест можно гонять повторно.
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (  # noqa: E402
    BASE, OUT, check, choose, console_run, editor_value, errors, results, set_code, wait_until,
)

STAMP = str(int(time.time()))[-6:]
ALICE, BOB, PASSWORD = f"alice_{STAMP}", f"Боб_{STAMP}", "Krepkiy-parol-42"
INIT = ("try { if (!sessionStorage.getItem('oc-e2e')) { localStorage.clear(); "
        "sessionStorage.setItem('oc-e2e', '1') } } catch (e) {}")


def new_page(browser, **kwargs):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, **kwargs)
    ctx.add_init_script(INIT)
    ctx.grant_permissions(["clipboard-read", "clipboard-write"])
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and m.text != "Canceled" and "status of 40" not in m.text
            and errors.append(m.text))
    page.on("pageerror", lambda e: "Canceled" not in str(e) and errors.append(str(e)))
    return page


def ready(page, url="/"):
    page.goto(BASE + url)
    page.wait_for_selector("#tabs .tab", timeout=30000)
    page.wait_for_function("() => window.monaco && monaco.editor.getEditors().length", timeout=30000)


def auth(page, mode, username, password):
    if not page.is_visible("#authDialog"):
        page.click("#loginBtn")
    page.click(f"#authForm [data-auth={mode}]")
    page.fill("#authForm [name=username]", username)
    page.fill("#authForm [name=password]", password)
    page.click("#authSubmit")
    # Хеширование пароля (PBKDF2) занимает около секунды — ждём исход, а не фиксированное время
    page.wait_for_function("() => !document.getElementById('authDialog').open"
                           " || !document.getElementById('authError').hidden", timeout=15000)


def api_get(page, url):
    return page.evaluate("u => fetch(u, {credentials: 'same-origin'}).then(r => r.json())", url)


def project_id(page):
    return page.url.rstrip("/").rsplit("/", 1)[-1]


def save(page):
    page.click(".monaco-editor")
    page.keyboard.press("Control+s")
    page.wait_for_timeout(800)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = new_page(browser)
    ready(page)

    # ---------- аноним ----------
    check("anon: login button", page.is_visible("#loginBtn") and not page.is_visible("#userBtn"))
    check("anon: share label", page.inner_text("#shareLabel") == "Поделиться")
    choose(page, "python")
    set_code(page, "print('до входа')\n")
    console_run(page)

    # ---------- регистрация ----------
    auth(page, "register", ALICE, "123")
    check("weak password rejected", page.is_visible("#authError"), page.inner_text("#authError"))
    auth(page, "register", ALICE, PASSWORD)
    check("registered and logged in", page.is_visible("#userBtn") and page.inner_text("#userName") == ALICE
          and not page.is_visible("#authDialog"))
    check("share becomes save", page.inner_text("#shareLabel") == "Сохранить")
    page.click("#historyToggle")
    check("anonymous history moved to account",
          wait_until(page, lambda: "до входа" in page.inner_text("#historyList"), 10), page.inner_text("#historyList"))
    page.click("#historyClose")
    set_code(page, "print('после входа')\n")
    console_run(page)
    runs = api_get(page, "/api/history/")["items"]
    check("console run after login is in account history", runs and runs[0]["preview"] == "print('после входа')",
          runs[:2])

    # ---------- сохранение и переименование ----------
    page.fill("#argsInput", "-v")
    save(page)
    check("save creates project URL", "/s/" in page.url, page.url)
    pid = project_id(page)
    check("project bar shown, untitled, editable", page.is_visible("#projectInfo")
          and page.inner_text("#projectTitle") == "Без названия" and not page.is_visible("#forkBtn"))
    page.click("#projectTitle")
    page.fill(".project-title-input", "Мой проект")
    page.keyboard.press("Enter")
    check("rename", wait_until(page, lambda: page.inner_text("#projectTitle") == "Мой проект", 10))
    check("rename persisted", api_get(page, f"/api/snippets/{pid}/")["title"] == "Мой проект")

    set_code(page, "print('версия 2')\n")
    check("dirty marker after edit", wait_until(page, lambda: page.is_visible("#projectDirty"), 5))
    save(page)
    data = api_get(page, f"/api/snippets/{pid}/")
    check("save in place keeps URL", project_id(page) == pid, page.url)
    check("saved content", data["code"] == "print('версия 2')\n" and data["args"] == "-v", data)
    check("dirty cleared", not page.is_visible("#projectDirty"))

    # ---------- чужой проект и форк ----------
    bob = new_page(browser)
    ready(bob, f"/s/{pid}/")
    check("visitor sees owner and fork button", bob.is_visible("#forkBtn")
          and ALICE in bob.inner_text("#projectMeta") and editor_value(bob) == "print('версия 2')\n",
          bob.inner_text("#projectMeta"))
    bob.click("#forkBtn")
    check("fork asks to log in", bob.is_visible("#authDialog") and "форк" in bob.inner_text("#authHint"))
    auth(bob, "register", BOB, PASSWORD)
    check("still not owner after login", bob.is_visible("#forkBtn"))
    set_code(bob, "print('правка Боба')\n")
    bob.click("#forkBtn")
    check("fork gets new URL", wait_until(bob, lambda: project_id(bob) != pid, 10), bob.url)
    fork_id = project_id(bob)
    fork = api_get(bob, f"/api/snippets/{fork_id}/")
    check("fork keeps edits made before forking", fork["code"] == "print('правка Боба')\n" and fork["is_owner"], fork)
    check("fork meta links source", "форк от" in bob.inner_text("#projectMeta")
          and not bob.is_visible("#forkBtn"), bob.inner_text("#projectMeta"))
    check("original untouched", api_get(bob, f"/api/snippets/{pid}/")["code"] == "print('версия 2')\n")

    page.reload()
    page.wait_for_selector("#projectInfo:not([hidden])", timeout=30000)
    check("owner sees fork count", "1 форк" in page.inner_text("#projectMeta"), page.inner_text("#projectMeta"))

    # ---------- «Мои проекты» ----------
    page.click("#resetBtn")
    check("new project leaves project", page.url.rstrip("/") == BASE and not page.is_visible("#projectInfo"), page.url)
    page.click("#userBtn")
    page.click("#myProjectsBtn")
    page.wait_for_selector("#projectsList li.item", timeout=10000)
    titles = page.eval_on_selector_all("#projectsList .p-title", "e => e.map(x => x.textContent)")
    check("my projects lists own project", titles == ["Мой проект"], titles)
    check("list meta", "1 форк" in page.inner_text("#projectsList li.item"), page.inner_text("#projectsList"))
    page.fill("#projectsSearch", "нет-такого")
    check("search filters", wait_until(page, lambda: "Ничего не нашлось" in page.inner_text("#projectsList"), 5))
    page.fill("#projectsSearch", "мой")
    page.wait_for_selector("#projectsList li.item", timeout=5000)
    page.click("#projectsList li.item")
    check("open from list", wait_until(page, lambda: project_id(page) == pid, 10)
          and editor_value(page) == "print('версия 2')\n" and page.input_value("#argsInput") == "-v")
    page.screenshot(path=f"{OUT}/accounts_project.png")

    bob.on("dialog", lambda d: d.accept())
    bob.click("#userBtn")
    bob.click("#myProjectsBtn")
    bob.wait_for_selector("#projectsList li.item", timeout=10000)
    bob.screenshot(path=f"{OUT}/accounts_projects_dialog.png")
    bob.click("#projectsList li.item .p-delete")
    check("delete project", wait_until(bob, lambda: "Пока пусто" in bob.inner_text("#projectsList"), 10))
    check("deleting open project leaves it", not bob.is_visible("#projectInfo") and bob.url.rstrip("/") == BASE)
    check("fork gone on server", bob.evaluate(f"fetch('/api/snippets/{fork_id}/').then(r => r.status)") == 404)

    # ---------- выход и вход ----------
    page.click("#userBtn")
    page.click("#logoutBtn")
    check("logout", wait_until(page, lambda: page.is_visible("#loginBtn"), 5)
          and page.inner_text("#shareLabel") == "Поделиться")
    check("after logout project is read-only", page.is_visible("#forkBtn"))
    auth(page, "login", ALICE, "wrong-password")
    check("wrong password message", "Неверный" in page.inner_text("#authError"))
    auth(page, "login", ALICE.upper(), PASSWORD)
    check("login is case-insensitive", page.is_visible("#userBtn") and not page.is_visible("#forkBtn"))

    mobile = new_page(browser)
    mobile.set_viewport_size({"width": 390, "height": 844})
    ready(mobile, f"/s/{pid}/")
    check("mobile: no horizontal overflow", not mobile.evaluate("document.documentElement.scrollWidth > innerWidth"))
    mobile.screenshot(path=f"{OUT}/accounts_mobile.png", full_page=True)

    check("no console errors", not errors, errors[:5])
    browser.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
