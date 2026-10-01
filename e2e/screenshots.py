"""Скриншоты для README: python e2e/screenshots.py [http://127.0.0.1:8000]

Нужны запущенный сервер, Docker и `manage.py build_sandbox` (для отладчика). Кладёт PNG в docs/screenshots/.
Создаёт (или переиспользует) демо-аккаунт в локальной базе — для снимка «Мои проекты».
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "screenshots")
os.makedirs(OUT, exist_ok=True)
DEMO_USER, DEMO_PASSWORD = "Лёха", "Demo-parol-2026"

HERO = '''from collections import Counter


def top_words(text: str, n: int = 3) -> list[tuple[str, int]]:
    words = [w.strip(".,!?").lower() for w in text.split()]
    return Counter(w for w in words if len(w) > 2).most_common(n)


name = input("Как тебя зовут? ")
text = input("Напиши фразу: ")
print(f"Привет, {name}! Самые частые слова:")
for word, count in top_words(text):
    print(f"  {word:<10} x{count}")
'''

DEBUG_C = '''#include <stdio.h>

typedef struct {
    const char *name;
    int score;
} Player;

int total_score(const Player *players, int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += players[i].score;
    }
    return sum;
}

int main(void) {
    Player team[] = {{"Лёха", 42}, {"Брат", 37}, {"Саня", 25}};
    int total = total_score(team, 3);
    printf("Итого: %d\\n", total);
    return 0;
}
'''

CPP_MAIN = '''#include <iostream>
#include "geometry.h"

int main() {
    Circle c{2.5};
    std::cout << "Площадь: " << c.area() << "\\n"
    return 0;
}
'''
CPP_HEADER = '''#pragma once

struct Circle {
    double r;
    double area() const { return 3.14159 * r * r; }
};
'''

RUST = '''use std::collections::HashMap;
fn main(){let args:Vec<String>=std::env::args().skip(1).collect();
let mut freq=HashMap::new();for a in &args{*freq.entry(a.as_str()).or_insert(0)+=1;}
let mut v:Vec<_>=freq.into_iter().collect();v.sort_by(|a,b|b.1.cmp(&a.1));
for (w,c) in v {println!("{w}: {c}");}}
'''


def wait_until(page, predicate, timeout=120):
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        page.wait_for_timeout(150)
    raise TimeoutError("не дождались состояния страницы")


def ready(page, url="/"):
    page.goto(BASE + url)
    page.wait_for_selector("#tabs .tab", timeout=30000)
    page.wait_for_function("() => window.monaco && monaco.editor.getEditors().length", timeout=30000)
    page.wait_for_selector("#terminal .xterm-rows", timeout=15000)


def choose(page, name):
    page.click("#langButton")
    page.fill("#langSearch", name)
    page.keyboard.press("Enter")
    page.wait_for_timeout(900)


def set_code(page, code):
    page.evaluate("c => monaco.editor.getEditors()[0].getModel().setValue(c)", code)
    page.evaluate("() => monaco.editor.getEditors()[0].setPosition({lineNumber: 1, column: 1})")


def term_text(page):
    return page.inner_text("#terminal .xterm-rows")


def type_in_terminal(page, text):
    page.click("#terminal")
    page.keyboard.type(text)
    page.keyboard.press("Enter")


def finished(page):
    page.wait_for_function("() => !document.getElementById('runBtn').classList.contains('stop')", timeout=120000)


def click_gutter(page, line):
    x, y = page.evaluate("""line => {
        const ed = monaco.editor.getEditors()[0];
        const rect = ed.getDomNode().getBoundingClientRect();
        const layout = ed.getLayoutInfo();
        const top = ed.getTopForLineNumber(line) - ed.getScrollTop();
        return [rect.left + layout.glyphMarginLeft + 8, rect.top + top + 10];
    }""", line)
    page.mouse.click(x, y)
    page.wait_for_timeout(150)


def shot(page, name):
    page.mouse.move(0, 0)
    page.evaluate("() => { const t = document.getElementById('toast'); if (t) t.hidden = true; }")
    page.wait_for_timeout(300)
    page.screenshot(path=os.path.join(OUT, name))
    print("saved", name)


def context(browser, theme="dark", **kwargs):
    ctx = browser.new_context(viewport={"width": 1440, "height": 860}, device_scale_factor=1, **kwargs)
    ctx.add_init_script(f"try {{ if (!sessionStorage.getItem('oc-shot')) {{ localStorage.clear(); "
                        f"localStorage.setItem('oc:theme', JSON.stringify('{theme}')); "
                        f"sessionStorage.setItem('oc-shot', '1') }} }} catch (e) {{}}")
    return ctx


with sync_playwright() as p:
    browser = p.chromium.launch()

    # 1. Главный экран: интерактивная консоль
    page = context(browser).new_page()
    ready(page)
    choose(page, "python")
    set_code(page, HERO)
    page.click("#runBtn")
    wait_until(page, lambda: "зовут?" in term_text(page))
    type_in_terminal(page, "Лёха")
    wait_until(page, lambda: "фразу:" in term_text(page))
    type_in_terminal(page, "код код компилятор работает и код летает, компилятор доволен")
    finished(page)
    shot(page, "console.png")

    # 2. Отладчик: брейкпоинт, переменные, стек, watch
    choose(page, "c")
    set_code(page, DEBUG_C)
    click_gutter(page, 11)
    page.click("#debugBtn")
    wait_until(page, lambda: page.is_visible("#debugToolbar") and not page.is_disabled("#dbgStepOver"), 180)
    page.click("#dbgContinue")  # вторая итерация — переменные интереснее
    page.wait_for_timeout(1500)
    wait_until(page, lambda: not page.is_disabled("#dbgStepOver"))
    page.click("#dbgVars .dbg-var:has-text('Locals') >> nth=0")
    page.wait_for_timeout(1000)
    page.fill("#watchInput", "players[i].score * 2")
    page.keyboard.press("Enter")
    page.wait_for_timeout(1500)
    page.evaluate("() => { const b = document.querySelector('.debug-body'); b.scrollTop = b.scrollHeight; }")
    shot(page, "debugger.png")
    page.click("#dbgStop")
    finished(page)

    # 3. Светлая тема, мультифайл, ошибка компиляции подсвечена в коде
    light = context(browser, "light").new_page()
    ready(light)
    light.click("#modeBatch")
    choose(light, "cpp")
    set_code(light, CPP_MAIN)
    light.click("#newFileBtn")
    light.fill(".tab-input", "geometry.h")
    light.keyboard.press("Enter")
    light.wait_for_timeout(300)
    set_code(light, CPP_HEADER)
    light.click("#tabs .tab >> nth=0")
    light.click("#runBtn")
    light.wait_for_function("() => document.getElementById('statusBadge').textContent === 'Ошибка компиляции'",
                            timeout=120000)
    light.wait_for_timeout(500)
    shot(light, "light-multifile.png")

    # 4. Beautify + аргументы + Vim
    choose(light, "rust")
    set_code(light, RUST)
    light.fill("#argsInput", "код брат код компилятор код")
    light.click("#formatBtn")
    wait_until(light, lambda: "    let args" in light.evaluate("() => monaco.editor.getEditors()[0].getValue()"))
    light.click("#runBtn")
    light.wait_for_function("() => document.getElementById('statusBadge').textContent === 'Успешно'", timeout=180000)
    light.click("#settingsBtn")
    light.select_option("#settingsForm [name=keymap]", "vim")
    light.keyboard.press("Escape")
    wait_until(light, lambda: light.is_visible("#vimStatus"))
    light.click(".monaco-editor .view-line >> nth=2")
    light.keyboard.press("Escape")
    shot(light, "format-args-vim.png")
    light.click("#settingsBtn")
    light.select_option("#settingsForm [name=keymap]", "default")
    shot(light, "settings.png")
    light.keyboard.press("Escape")

    # 5. Аккаунт: проект в шапке и «Мои проекты»
    acc = context(browser).new_page()
    ready(acc)
    acc.click("#loginBtn")
    acc.fill("#authForm [name=username]", DEMO_USER)
    acc.fill("#authForm [name=password]", DEMO_PASSWORD)
    acc.click("#authSubmit")
    acc.wait_for_function("() => !document.getElementById('authDialog').open"
                          " || !document.getElementById('authError').hidden", timeout=15000)
    if acc.is_visible("#authDialog"):  # первый запуск — регистрируем демо-аккаунт
        acc.click("#authForm [data-auth=register]")
        acc.click("#authSubmit")
        acc.wait_for_function("() => !document.getElementById('authDialog').open", timeout=15000)
    titles = [("Частотный анализ", "python", HERO), ("Турнирная таблица", "c", DEBUG_C),
              ("Геометрия на C++", "cpp", CPP_MAIN)]
    existing = acc.evaluate("() => fetch('/api/projects/').then(r => r.json()).then(d => d.items.map(i => i.title))")
    for title, lang, code in titles:
        if title in existing:
            continue
        acc.evaluate("""([title, lang, code]) => fetch('/api/snippets/', {method: 'POST', credentials: 'same-origin',
            headers: {'Content-Type': 'application/json',
                      'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)[1]},
            body: JSON.stringify({language: lang, code, title})})""", [title, lang, code])
    acc.click("#userBtn")
    acc.click("#myProjectsBtn")
    acc.wait_for_selector("#projectsList li.item", timeout=10000)
    acc.click("#projectsList li.item:has-text('Частотный анализ')")
    acc.wait_for_selector("#projectInfo:not([hidden])", timeout=10000)
    acc.click("#userBtn")
    acc.click("#myProjectsBtn")
    acc.wait_for_selector("#projectsList li.item.current", timeout=10000)
    shot(acc, "projects.png")

    # 6. Телефон
    mobile = context(browser).new_page()
    mobile.set_viewport_size({"width": 390, "height": 844})
    ready(mobile)
    choose(mobile, "python")
    set_code(mobile, 'name = input("Имя: ")\nprint(f"Привет, {name}!")\n')
    mobile.click("#runBtn")
    wait_until(mobile, lambda: "Имя:" in term_text(mobile))
    type_in_terminal(mobile, "Лёха")
    finished(mobile)
    mobile.evaluate("() => { document.activeElement?.blur(); window.scrollTo(0, 0); }")
    mobile.wait_for_timeout(300)
    mobile.screenshot(path=os.path.join(OUT, "mobile.png"), full_page=True)
    print("saved mobile.png")

    browser.close()
