"""Браузерный e2e этапа C: почта и сброс пароля, настройки аккаунта, видимость проектов, профиль.

    python e2e/test_profiles.py [http://127.0.0.1:8000] [путь-к-логу-сервера]

Письма в разработке печатаются в консоль сервера (EMAIL_HOST не задан) — ссылку для сброса тест
берёт из лога. Путь к логу: второй аргумент или переменная OC_SERVER_LOG.
Вход через GitHub / Google без настоящих ключей не проверить — его покрывают Django-тесты с подменой сети.
"""
import email
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BASE, OUT, check, errors, results, wait_until  # noqa: E402

SERVER_LOG = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("OC_SERVER_LOG", "")
STAMP = str(int(time.time()))[-6:]
USER, EMAIL = f"profile_{STAMP}", f"profile_{STAMP}@example.com"
PASSWORD, NEW_PASSWORD = "Krepkiy-parol-42", "Novyi-parol-77"


def new_page(browser, **kwargs):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, **kwargs)
    ctx.add_init_script("try { if (!sessionStorage.getItem('oc-e2e')) { localStorage.clear(); "
                        "sessionStorage.setItem('oc-e2e', '1') } } catch (e) {}")
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and m.text != "Canceled" and "status of 40" not in m.text
            and errors.append(m.text))
    page.on("pageerror", lambda e: "Canceled" not in str(e) and errors.append(str(e)))
    return page


def ready(page, url="/"):
    page.goto(BASE + url)
    page.wait_for_selector("#tabs .tab", timeout=30000)
    page.wait_for_function("() => window.monaco && monaco.editor.getEditors().length", timeout=30000)


def submit_auth(page):
    page.click("#authSubmit")
    page.wait_for_function("() => !document.getElementById('authDialog').open"
                           " || !document.getElementById('authError').hidden"
                           " || !document.getElementById('authOk').hidden", timeout=15000)


def reset_link_from_log():
    """Console-бэкенд печатает письмо целиком, а тело с кириллицей по стандарту MIME — в base64.
    Берём последнее письмо (они разделены строкой из 79 дефисов) и раскодируем его."""
    with open(SERVER_LOG, encoding="utf-8", errors="replace") as f:
        chunks = [c for c in f.read().split("-" * 79) if "Subject:" in c]
    if not chunks:
        return None
    raw = chunks[-1][chunks[-1].index("Content-Type:"):]
    body = email.message_from_string(raw).get_payload(decode=True).decode("utf-8")
    links = re.findall(r"http://\S+/reset/[^\s/]+/[^\s/]+/", body)
    return links[-1] if links else None


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = new_page(browser)
    ready(page)

    # ---------- регистрация с почтой ----------
    page.click("#loginBtn")
    check("oauth buttons hidden without keys", not page.is_visible("#oauthButtons"))
    check("forgot link in login mode", page.is_visible("#forgotBtn"))
    page.click("#authForm [data-auth=register]")
    check("email field in register mode", page.is_visible("#authEmailField") and not page.is_visible("#forgotBtn"))
    page.fill("#authForm [name=username]", USER)
    page.fill("#authForm [name=email]", EMAIL)
    page.fill("#authForm [name=password]", PASSWORD)
    submit_auth(page)
    check("registered", page.is_visible("#userBtn"),
          page.inner_text("#authError") if page.is_visible("#authError") else "")

    # ---------- проект: видимость и профиль ----------
    page.click(".monaco-editor")
    page.keyboard.press("Control+s")
    page.wait_for_url("**/s/*/", timeout=10000)
    pid = page.url.rstrip("/").rsplit("/", 1)[-1]
    page.click("#projectTitle")
    page.fill(".project-title-input", "Мой публичный")
    page.keyboard.press("Enter")
    check("visibility select for owner", page.is_visible("#visibilitySelect")
          and page.input_value("#visibilitySelect") == "unlisted")
    page.select_option("#visibilitySelect", "public")
    page.wait_for_timeout(600)
    profile = new_page(browser)
    profile.goto(f"{BASE}/u/{USER}/")
    check("public project in profile", "Мой публичный" in profile.inner_text(".profile"),
          profile.inner_text("body")[:300])
    profile.screenshot(path=f"{OUT}/profile.png")
    profile.click(".profile-card")
    profile.wait_for_selector("#projectInfo:not([hidden])", timeout=30000)
    check("profile card opens project", f"/s/{pid}/" in profile.url and profile.is_visible("#forkBtn"))
    check("owner link to profile", f"/u/{USER}/" in profile.inner_html("#projectMeta"))

    page.select_option("#visibilitySelect", "private")
    page.wait_for_timeout(600)
    status = profile.evaluate(f"fetch('/s/{pid}/').then(r => r.status)")
    check("private project 404 for others", status == 404, status)
    profile.goto(f"{BASE}/u/{USER}/")
    check("private project not in profile", "Мой публичный" not in profile.inner_text(".profile"))
    page.click("#userBtn")
    page.click("#myProjectsBtn")
    page.wait_for_selector("#projectsList li.item", timeout=10000)
    check("private badge in my projects", "приватный" in page.inner_text("#projectsList"))
    page.keyboard.press("Escape")

    # ---------- настройки аккаунта ----------
    page.click("#userBtn")
    page.click("#accountSettingsBtn")
    check("account dialog shows email", page.input_value("#emailForm [name=email]") == EMAIL)
    page.fill("#emailForm [name=email]", f"new_{EMAIL}")
    page.fill("#emailForm [name=password]", "wrong")
    page.click("#emailForm button[type=submit]")
    check("email change needs password", wait_until(page, lambda: page.is_visible("#accountError"), 5))
    page.fill("#emailForm [name=email]", EMAIL)
    page.fill("#emailForm [name=password]", PASSWORD)
    page.click("#emailForm button[type=submit]")
    check("email saved", wait_until(page, lambda: page.is_visible("#accountOk"), 5))
    page.click("#accountClose")

    # ---------- сброс пароля по почте ----------
    page.click("#userBtn")
    page.click("#logoutBtn")
    wait_until(page, lambda: page.is_visible("#loginBtn"), 5)
    page.click("#loginBtn")
    page.click("#forgotBtn")
    check("reset mode shows only email", page.is_visible("#authEmailField")
          and not page.is_visible("#authPasswordField") and not page.is_visible("#authUsernameField"))
    page.fill("#authForm [name=email]", EMAIL.upper())
    submit_auth(page)
    check("reset request acknowledged", page.is_visible("#authOk"), page.inner_text("#authOk"))
    link = None
    if SERVER_LOG:
        end = time.time() + 10
        while time.time() < end and not link:
            link = reset_link_from_log()
            time.sleep(0.3)
    check("reset email printed with link", link, SERVER_LOG or "лог сервера не передан")
    if link:
        fresh = new_page(browser)
        fresh.goto(link)
        fresh.wait_for_selector("#resetDialog[open]", timeout=30000)
        fresh.fill("#resetForm [name=password]", NEW_PASSWORD)
        fresh.click("#resetForm button[type=submit]")
        check("logged in after reset", wait_until(fresh, lambda: fresh.is_visible("#userBtn"), 10)
              and fresh.url.rstrip("/") == BASE)
        fresh.goto(link)
        fresh.wait_for_selector("#resetDialog[open]", timeout=30000)
        fresh.fill("#resetForm [name=password]", "Esche-odin-99")
        fresh.click("#resetForm button[type=submit]")
        check("reset link is single-use", wait_until(fresh, lambda: fresh.is_visible("#resetError"), 10))
        page.keyboard.press("Escape")
        page.click("#loginBtn")
        page.click("#authForm [data-auth=login]")
        page.fill("#authForm [name=username]", USER)
        page.fill("#authForm [name=password]", NEW_PASSWORD)
        submit_auth(page)
        check("login with new password", page.is_visible("#userBtn"))

    mobile = new_page(browser)
    mobile.set_viewport_size({"width": 390, "height": 844})
    mobile.goto(f"{BASE}/u/{USER}/")
    check("profile mobile: no overflow", not mobile.evaluate("document.documentElement.scrollWidth > innerWidth"))

    check("no console errors", not errors, errors[:5])
    browser.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
