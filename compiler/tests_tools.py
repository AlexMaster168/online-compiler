"""Этап 3: аргументы командной строки, Beautify на сервере, скачивание проекта zip-архивом."""
import io
import json
import zipfile
from unittest import skipUnless

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings

from . import engine
from .engine import docker
from .engine.debugger import DebugSession
from .engine.formatter import FormatError, format_code, server_formatter
from .models import Execution, Snippet
from .payload import BadRequest, args_field
from .tests import LOCAL, python_available

DOCKER = {**settings.EXECUTOR, "BACKEND": "docker", "RATE_LIMIT_PER_MINUTE": 0}
PRINT_ARGS = "import sys\nprint(sys.argv[1:])\n"
TRICKY = '-n 5 "два слова" \'$HOME\' ; rm -rf /'
TRICKY_ARGV = ["-n", "5", "два слова", "$HOME", ";", "rm", "-rf", "/"]


def _docker_image(slug: str) -> bool:
    return docker.is_available(engine.get_language(slug), DOCKER)


def _post(client, url, data):
    return client.post(url, json.dumps(data), content_type="application/json")


class ArgsParsingTests(SimpleTestCase):
    def test_shell_like_split(self):
        self.assertEqual(args_field({"args": TRICKY}), (TRICKY, TRICKY_ARGV))
        self.assertEqual(args_field({}), ("", []))
        self.assertEqual(args_field({"args": "  a   b  "}), ("a   b", ["a", "b"]))

    def test_rejects_bad_input(self):
        for bad in ('"не закрыта', "a\x00b", "x" * 1001, " ".join(["a"] * 65), 42):
            with self.assertRaises(BadRequest, msg=repr(bad)[:40]):
                args_field({"args": bad})

    def test_docker_quotes_args_for_shell(self):
        cmd = docker.with_args("./main", TRICKY_ARGV)
        self.assertEqual(cmd, "./main -n 5 'два слова' '$HOME' ';' rm -rf /")
        self.assertEqual(docker.with_args("dlv exec ./main", ["x"], "--"), "dlv exec ./main -- x")
        self.assertEqual(docker.with_args("./main", []), "./main")


@override_settings(EXECUTOR=LOCAL)
@skipUnless(python_available, "нужен локальный python")
class LocalArgsTests(TestCase):
    def test_run_with_args_is_stored(self):
        res = _post(self.client, "/api/run/", {"language": "python", "code": PRINT_ARGS, "args": TRICKY})
        body = res.json()
        self.assertEqual(body["status"], "ok", body)
        self.assertEqual(body["stdout"].strip(), repr(TRICKY_ARGV))
        execution = Execution.objects.get(pk=body["id"])
        self.assertEqual(execution.args, TRICKY)
        self.assertEqual(self.client.get(f"/api/executions/{execution.pk}/").json()["args"], TRICKY)

    def test_bad_args_400(self):
        res = _post(self.client, "/api/run/", {"language": "python", "code": "print(1)", "args": '"oops'})
        self.assertEqual(res.status_code, 400)
        self.assertIn("кавычка", res.json()["error"])

    def test_snippet_keeps_args(self):
        res = _post(self.client, "/api/snippets/", {"language": "python", "code": PRINT_ARGS, "args": "1 2"})
        snippet = Snippet.objects.get(pk=res.json()["id"])
        self.assertEqual(snippet.args, "1 2")
        self.assertEqual(self.client.get(f"/api/snippets/{snippet.pk}/").json()["args"], "1 2")

    def test_local_debug_passes_args(self):
        events = []
        session = DebugSession("python", PRINT_ARGS, None, events.append, breakpoints={},
                               cfg={**LOCAL, "BACKEND": "local"}, args=["a b", "c"])
        session.start()
        self.assertTrue(session.done.wait(90), "отладочная сессия не завершилась")
        out = "".join(e["data"] for e in events if e["type"] == "output" and e["stream"] != "compile")
        self.assertIn("['a b', 'c']", out)


class ZipTests(TestCase):
    def _names(self, res):
        self.assertEqual(res["Content-Type"], "application/zip")
        with zipfile.ZipFile(io.BytesIO(res.content)) as zf:
            return {name: zf.read(name).decode() for name in zf.namelist()}

    def test_project_zip(self):
        res = _post(self.client, "/api/zip/", {
            "language": "python", "code": "from lib.util import f\nprint(f())\n",
            "files": [{"name": "lib/util.py", "content": "def f():\n    return 'Лёха'\n"}],
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('filename="python-project.zip"', res["Content-Disposition"])
        files = self._names(res)
        self.assertEqual(set(files), {"main.py", "lib/util.py"})
        self.assertIn("Лёха", files["lib/util.py"])

    def test_zip_rejects_bad_paths(self):
        res = _post(self.client, "/api/zip/", {"language": "python", "code": "x",
                                               "files": [{"name": "../evil.py", "content": "x"}]})
        self.assertEqual(res.status_code, 400)

    def test_snippet_zip(self):
        snippet = Snippet.objects.create(language="go", code="package main\n", title="Мой проект: v2",
                                         files=[{"name": "util.go", "content": "package main\n"}])
        res = self.client.get(f"/s/{snippet.pk}/zip/")
        self.assertEqual(set(self._names(res)), {"main.go", "util.go"})
        self.assertIn('filename="v2.zip"', res["Content-Disposition"])  # кириллица вырезается, остаётся ASCII
        self.assertEqual(self.client.get("/s/nope/zip/").status_code, 404)


class FormatTests(TestCase):
    def test_catalog_exposes_formatters(self):
        langs = {lang["slug"]: lang for lang in engine.language_catalog()}
        self.assertEqual(langs["python"]["formatter"], "ruff")
        self.assertEqual(langs["cpp"]["formatter"], "clang")
        self.assertEqual(langs["rust"]["formatter"], "server")
        self.assertIsNone(langs["haskell"]["formatter"])
        self.assertIsNone(server_formatter("python"))

    def test_browser_languages_are_rejected_by_server(self):
        res = _post(self.client, "/api/format/", {"language": "python", "code": "x=1"})
        self.assertEqual(res.status_code, 400)

    @override_settings(EXECUTOR=DOCKER)
    @skipUnless(docker.image_present("oc-debug-native:1", DOCKER), "нет oc-debug-native (build_sandbox native)")
    def test_rustfmt(self):
        res = _post(self.client, "/api/format/", {"language": "rust", "code": 'fn main(){let x=1;println!("{}",x)}'})
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.json()["code"], 'fn main() {\n    let x = 1;\n    println!("{}", x)\n}\n')
        with self.assertRaises(FormatError):
            format_code("rust", "fn main( {", DOCKER)

    @override_settings(EXECUTOR=DOCKER)
    @skipUnless(_docker_image("elixir"), "нет образа elixir")
    def test_mix_format(self):
        res = _post(self.client, "/api/format/", {"language": "elixir", "code": "IO.puts( 1+2 )"})
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.json()["code"].strip(), "IO.puts(1 + 2)")


@override_settings(EXECUTOR=DOCKER)
class DockerArgsTests(TestCase):
    """В контейнере аргументы идут через sh -c — проверяем, что экранирование не ломается и не исполняется."""

    @skipUnless(_docker_image("c"), "нет образа gcc")
    def test_c_batch(self):
        code = ('#include <stdio.h>\nint main(int argc, char **argv) {\n'
                '    for (int i = 1; i < argc; i++) printf("[%s]", argv[i]);\n    return 0;\n}\n')
        result = engine.execute("c", code, args=TRICKY_ARGV)
        self.assertEqual(result.stdout, "".join(f"[{a}]" for a in TRICKY_ARGV), result)

    @skipUnless(_docker_image("python"), "нет образа python")
    def test_python_console(self):
        from .engine.interactive import Session
        events = []
        session = Session("python", PRINT_ARGS, None, events.append, cfg=DOCKER, args=TRICKY_ARGV)
        session.start()
        self.assertTrue(session.done.wait(90))
        self.assertEqual(session.result.status, "ok", session.result)
        self.assertIn(repr(TRICKY_ARGV), "".join(e["data"] for e in events if e["type"] == "output"))

    def _debug_output(self, slug, code, args):
        events = []
        session = DebugSession(slug, code, None, events.append, breakpoints={}, cfg=DOCKER, args=args)
        session.start()
        self.assertTrue(session.done.wait(180), f"отладка {slug} не завершилась")
        return "".join(e["data"] for e in events if e["type"] == "output" and e["stream"] != "compile")

    @skipUnless(docker.debug_available(engine.get_language("go"), DOCKER), "нет oc-debug-go")
    def test_go_debug_args_after_separator(self):
        code = 'package main\n\nimport (\n\t"fmt"\n\t"os"\n)\n\nfunc main() {\n\tfmt.Printf("%q\\n", os.Args[1:])\n}\n'
        self.assertIn('["-n" "два слова"]', self._debug_output("go", code, ["-n", "два слова"]))

    @skipUnless(docker.debug_available(engine.get_language("c"), DOCKER), "нет oc-debug-native")
    def test_c_debug_args(self):
        code = '#include <stdio.h>\nint main(int c, char **v) {\n    printf("%d:%s\\n", c, v[c - 1]);\n}\n'
        self.assertIn("3:два слова", self._debug_output("c", code, ["-x", "два слова"]))
