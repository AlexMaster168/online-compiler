"""Отладчик на уровне движка: брейкпоинты, стек, переменные, шаги, живой ввод.

Нужен Docker и собранные образы (`manage.py build_sandbox`), иначе тесты пропускаются.
Python ещё проверяется локально через debugpy.
"""
import threading
import time
from unittest import skipUnless

from django.conf import settings
from django.test import SimpleTestCase

from .engine import docker, get_language
from .engine.debugger import DebugSession, local_debug_supported

CFG = settings.EXECUTOR


def _docker_debug(slug: str) -> bool:
    return docker.debug_available(get_language(slug), CFG)


class Harness:
    """Запускает отладочную сессию и даёт удобно ждать событий."""

    def __init__(self, backend: str, slug: str, code: str, breakpoints: dict, files: dict | None = None):
        self.events: list[dict] = []
        self.out = ""
        self.cond = threading.Condition()
        self.session = DebugSession(slug, code, files, self._on, breakpoints=breakpoints,
                                    cfg={**CFG, "BACKEND": backend})
        self.session.start()

    def _on(self, event: dict) -> None:
        with self.cond:
            self.events.append(event)
            if event["type"] == "output" and event["stream"] != "compile":
                self.out += event["data"]
            self.cond.notify_all()

    def wait(self, predicate, what: str, timeout: float = 120):
        with self.cond:
            self.cond.wait_for(lambda: predicate() or self.session.done.is_set(), timeout)
        if not predicate():
            tail = [e for e in self.events if e["type"] != "output"][-5:]
            raise AssertionError(f"Не дождались: {what}. Последние события: {tail}. Вывод: {self.out[-300:]!r}")

    def stops(self) -> list[dict]:
        return [e for e in self.events if e["type"] == "debug_stopped"]

    def wait_stop(self, count: int, what: str) -> dict:
        self.wait(lambda: len(self.stops()) >= count, what)
        return self.stops()[count - 1]

    def finish(self, timeout: float = 60):
        self.session.done.wait(timeout)
        if self.session.result is None:
            self.session.kill()
            self.session.done.wait(20)
        return self.session.result

    @staticmethod
    def variables(stop: dict) -> dict[str, str]:
        return {v["name"]: v["value"] for scope in stop["scopes"] for v in (scope["variables"] or [])}


# Одна и та же программа на каждом языке: square(x) вызывается в цикле, перед ним — ввод имени
PROGRAMS = {
    "python": ("def square(x):\n    y = x * x\n    return y\n\nname = input('Имя: ')\ntotal = 0\n"
               "for i in range(3):\n    total += square(i)\nprint('Привет,', name, total)\n", 2, 9),
    "c": ('#include <stdio.h>\nint square(int x) {\n    int y = x * x;\n    return y;\n}\nint main(void) {\n'
          '    char name[32];\n    printf("Имя: ");\n    scanf("%31s", name);\n    int total = 0;\n'
          '    for (int i = 0; i < 3; i++) total += square(i);\n    printf("Привет, %s %d\\n", name, total);\n'
          '    return 0;\n}\n', 3, 12),
    "cpp": ('#include <iostream>\n#include <string>\nint square(int x) {\n    int y = x * x;\n    return y;\n}\n'
            'int main() {\n    std::string name;\n    std::cout << "Имя: " << std::flush;\n    std::cin >> name;\n'
            '    int total = 0;\n    for (int i = 0; i < 3; i++) total += square(i);\n'
            '    std::cout << "Привет, " << name << " " << total << std::endl;\n}\n', 4, 13),
    "rust": ('use std::io::{self, Write};\nfn square(x: i32) -> i32 {\n    let y = x * x;\n    y\n}\nfn main() {\n'
             '    print!("Имя: ");\n    io::stdout().flush().unwrap();\n    let mut name = String::new();\n'
             '    io::stdin().read_line(&mut name).unwrap();\n    let mut total = 0;\n'
             '    for i in 0..3 { total += square(i); }\n    println!("Привет, {} {}", name.trim(), total);\n}\n',
             3, 13),
    "go": ('package main\n\nimport "fmt"\n\nfunc square(x int) int {\n\ty := x * x\n\treturn y\n}\n\n'
           'func main() {\n\tvar name string\n\tfmt.Print("Имя: ")\n\tfmt.Scan(&name)\n\ttotal := 0\n'
           '\tfor i := 0; i < 3; i++ {\n\t\ttotal += square(i)\n\t}\n\tfmt.Println("Привет,", name, total)\n}\n',
           6, 18),
    "java": ('import java.util.Scanner;\npublic class Main {\n    static int square(int x) {\n        int y = x * x;\n'
             '        return y;\n    }\n    public static void main(String[] args) {\n'
             '        Scanner in = new Scanner(System.in);\n        System.out.print("Имя: ");\n'
             '        String name = in.next();\n        int total = 0;\n'
             '        for (int i = 0; i < 3; i++) total += square(i);\n'
             '        System.out.println("Привет, " + name + " " + total);\n    }\n}\n', 4, 13),
    "kotlin": ('fun square(x: Int): Int {\n    val y = x * x\n    return y\n}\n\nfun main() {\n    print("Имя: ")\n'
               '    val name = readLine()!!.trim()\n    var total = 0\n    for (i in 0 until 3) total += square(i)\n'
               '    println("Привет, $name $total")\n}\n', 2, 11),
}


class DebugScenarioMixin:
    """Сценарий: ввод → стоп в square → переменные/evaluate → шаг → снять точку → стоп в конце → выход."""

    backend = "docker"

    def run_scenario(self, slug: str):
        code, line_in_square, line_at_end = PROGRAMS[slug]
        filename = get_language(slug).filename
        h = Harness(self.backend, slug, code, {filename: [line_in_square, line_at_end]})
        h.wait(lambda: any(e["type"] == "debug_ready" for e in h.events), "подключение отладчика")
        h.wait(lambda: "Имя: " in h.out, "приглашение программы")
        self.assertTrue(h.out.startswith("Имя: "), f"служебный шум отладчика в выводе: {h.out!r}")
        h.session.write("Лёха\n")

        stop = h.wait_stop(1, "брейкпоинт в square")
        self.assertEqual(stop["reason"], "breakpoint")
        top = stop["frames"][0]
        self.assertEqual((top["file"], top["line"]), (filename, line_in_square))
        self.assertIn("square", top["name"])
        self.assertGreaterEqual(len(stop["frames"]), 2)
        self.assertEqual(h.variables(stop).get("x"), "0")
        self.assertEqual(h.session.request("evaluate", {"expression": "x + 40", "frameId": stop["frameId"]})["result"],
                         "40")

        h.session.request("next", {})
        stop = h.wait_stop(2, "шаг")
        self.assertEqual(stop["frames"][0]["file"], filename)
        self.assertGreater(stop["frames"][0]["line"], line_in_square)

        # Убираем точку в square на лету — следующая остановка уже в конце программы
        h.session.request("setBreakpoints", {"file": filename, "lines": [line_at_end]})
        h.session.request("continue", {})
        stop = h.wait_stop(3, "брейкпоинт в конце")
        self.assertEqual(stop["frames"][0]["line"], line_at_end)
        self.assertEqual(h.variables(stop).get("total"), "5")
        self.assertIn("Лёха", h.variables(stop).get("name", ""))

        h.session.request("continue", {})
        result = h.finish()
        self.assertEqual(result.status, "ok", result.message)
        self.assertIn("Привет, Лёха 5", h.out)
        self.assertNotRegex(h.out, r"Child exited|Listening on port|API server listening")
        self.assertFalse([e for e in h.events if e["type"] == "debug_error"])
        return h


class DockerDebugTests(DebugScenarioMixin, SimpleTestCase):
    @skipUnless(_docker_debug("python"), "нет oc-debug-python")
    def test_python(self):
        self.run_scenario("python")

    @skipUnless(_docker_debug("c"), "нет oc-debug-native")
    def test_c(self):
        self.run_scenario("c")

    @skipUnless(_docker_debug("cpp"), "нет oc-debug-native")
    def test_cpp(self):
        self.run_scenario("cpp")

    @skipUnless(_docker_debug("rust"), "нет oc-debug-native")
    def test_rust(self):
        self.run_scenario("rust")

    @skipUnless(_docker_debug("go"), "нет oc-debug-go")
    def test_go(self):
        self.run_scenario("go")

    @skipUnless(_docker_debug("java"), "нет oc-debug-jvm")
    def test_java(self):
        self.run_scenario("java")

    @skipUnless(_docker_debug("kotlin"), "нет oc-debug-jvm")
    def test_kotlin(self):
        self.run_scenario("kotlin")

    @skipUnless(_docker_debug("java"), "нет oc-debug-jvm")
    def test_java_objects_arrays_and_uncaught_exception(self):
        code = ('import java.util.*;\npublic class Main {\n    int count = 7;\n'
                '    public static void main(String[] args) {\n        int[] arr = {10, 20, 30};\n'
                '        List<String> list = new ArrayList<>(List.of("а", "б"));\n        Main m = new Main();\n'
                '        System.out.println(arr.length + list.size() + m.count);\n'
                '        Object boom = null;\n        boom.toString();\n    }\n}\n')
        h = Harness("docker", "java", code, {"Main.java": [8]})
        stop = h.wait_stop(1, "брейкпоинт")
        values = h.variables(stop)
        self.assertEqual(values["arr"], "int[3]")
        self.assertEqual(values["list"], "ArrayList size=2")
        arr_ref = next(v["ref"] for s in stop["scopes"] for v in s["variables"] if v["name"] == "arr")
        self.assertEqual([v["value"] for v in h.session.request("variables", {"ref": arr_ref})["variables"]],
                         ["10", "20", "30"])

        def evaluate(expression):
            return h.session.request("evaluate", {"expression": expression, "frameId": stop["frameId"]})["result"]
        self.assertEqual(evaluate("arr[1] * 2 + m.count"), "47")
        self.assertEqual(evaluate("arr.length"), "3")
        h.session.request("continue", {})
        stop = h.wait_stop(2, "непойманное исключение")
        self.assertEqual(stop["reason"], "exception")
        self.assertIn("NullPointerException", stop["description"])
        self.assertEqual(stop["frames"][0]["line"], 10)
        h.session.request("continue", {})
        result = h.finish()
        self.assertEqual(result.status, "runtime_error")

    @skipUnless(_docker_debug("cpp"), "нет oc-debug-native")
    def test_cpp_std_types_are_pretty_printed(self):
        code = ('#include <string>\n#include <vector>\n#include <iostream>\nint main() {\n'
                '    std::string name = "Лёха";\n    std::vector<int> v = {1, 2, 3};\n'
                '    std::cout << name << v.size() << std::endl;\n}\n')
        h = Harness("docker", "cpp", code, {"main.cpp": [7]})
        stop = h.wait_stop(1, "брейкпоинт")
        values = h.variables(stop)
        self.assertIn("Лёха", values["name"])
        self.assertIn("3", values["v"])  # std::vector of length 3
        h.session.kill()
        h.finish()

    @skipUnless(_docker_debug("python"), "нет oc-debug-python")
    def test_stop_kills_session_fast(self):
        h = Harness("docker", "python", "import time\nprint('go', flush=True)\ntime.sleep(120)\n", {})
        h.wait(lambda: "go" in h.out, "старт программы")
        started = time.monotonic()
        h.session.kill()
        result = h.finish(30)
        self.assertEqual(result.status, "stopped")
        self.assertLess(time.monotonic() - started, 10)


@skipUnless(local_debug_supported(get_language("python")), "нет debugpy в venv")
class LocalDebugTests(DebugScenarioMixin, SimpleTestCase):
    backend = "local"

    def test_python(self):
        self.run_scenario("python")

    @skipUnless(local_debug_supported(get_language("java")), "нет локального JDK")
    def test_java(self):
        self.run_scenario("java")
