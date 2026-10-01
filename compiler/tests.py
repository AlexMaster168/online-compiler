import json
import time
from unittest import skipUnless

from django.test import TestCase, TransactionTestCase, override_settings
from django.conf import settings

from . import engine
from .engine import local
from .engine.languages import LANGUAGES
from .models import Execution, Snippet

LOCAL = {**settings.EXECUTOR, "BACKEND": "local", "RUN_TIMEOUT": 5, "RATE_LIMIT_PER_MINUTE": 0}
python_available = local.is_available(engine.get_language("python"))


class RegistryTests(TestCase):
    def test_slugs_unique_and_complete(self):
        slugs = [lang.slug for lang in LANGUAGES]
        self.assertEqual(len(slugs), len(set(slugs)))
        for lang in LANGUAGES:
            self.assertTrue(lang.docker or lang.local, lang.slug)
            self.assertTrue(lang.template.strip(), lang.slug)
            self.assertNotIn("/", lang.filename)

    def test_sources_placeholder(self):
        from .engine import docker
        from .engine.languages import source_files
        cpp = engine.get_language("cpp")
        self.assertEqual(source_files(cpp, ["b.cpp", "a.hpp", "geo/pt.cpp"]), ["main.cpp", "b.cpp", "geo/pt.cpp"])
        go = engine.get_language("go")
        self.assertEqual(source_files(go, ["util.go", "sub/x.go"]), ["main.go", "util.go"])
        script = docker.shell_preview(cpp)
        self.assertNotIn("{sources}", script)

    def test_docker_script_wraps_run_in_timeout(self):
        from .engine import docker
        script = docker.shell_preview(engine.get_language("cpp"), run_timeout=7)
        self.assertIn("timeout -s KILL 7 ./main", script)
        self.assertIn("g++", script)


@override_settings(EXECUTOR=LOCAL)
@skipUnless(python_available, "нужен локальный python")
class EngineTests(TestCase):
    def test_hello(self):
        r = engine.execute("python", "print('Привет')")
        self.assertEqual(r.status, "ok")
        self.assertEqual(r.stdout, "Привет\n")
        self.assertEqual(r.backend, "local")

    def test_stdin(self):
        r = engine.execute("python", "print(sum(map(int, input().split())))", "20 22\n")
        self.assertEqual(r.stdout.strip(), "42")

    def test_timeout(self):
        started = time.monotonic()
        r = engine.execute("python", "while True: pass")
        self.assertEqual(r.status, "timeout")
        self.assertLess(time.monotonic() - started, 15)

    def test_output_limit(self):
        r = engine.execute("python", "while True: print('x' * 1000)")
        self.assertEqual(r.status, "output_limit")
        self.assertTrue(r.truncated)
        self.assertLessEqual(len(r.stdout), settings.EXECUTOR["MAX_OUTPUT_BYTES"])

    def test_runtime_error_hides_host_paths(self):
        r = engine.execute("python", "1/0")
        self.assertEqual(r.status, "runtime_error")
        self.assertIn('File "main.py", line 1', r.stderr)
        self.assertIn("ZeroDivisionError", r.stderr)

    @skipUnless(__import__("sys").platform == "win32", "лимит памяти локально — через Job Object")
    def test_memory_limit(self):
        r = engine.execute("python", "x = bytearray(3 * 1024 ** 3)")
        self.assertEqual(r.status, "memory_limit")

    def test_orphans_do_not_hang_the_run(self):
        code = ("import subprocess, sys\n"
                "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
                "print('done')")
        started = time.monotonic()
        r = engine.execute("python", code)
        self.assertEqual(r.status, "ok")
        self.assertLess(time.monotonic() - started, 10)

    def test_code_size_limit(self):
        r = engine.execute("python", "#" * (settings.EXECUTOR["MAX_CODE_BYTES"] + 1))
        self.assertEqual(r.status, "internal_error")

    def test_unknown_language(self):
        self.assertEqual(engine.execute("brainfuck++", "x").status, "unavailable")

    def test_sql(self):
        r = engine.execute("sql", "CREATE TABLE t(a); INSERT INTO t VALUES (1),(2); SELECT count(*) AS n FROM t;")
        self.assertEqual(r.status, "ok")
        self.assertIn("| n |", r.stdout)


@override_settings(EXECUTOR=LOCAL)
@skipUnless(python_available, "нужен локальный python")
class ApiTests(TestCase):
    def post(self, url, data, client=None):
        return (client or self.client).post(url, json.dumps(data), content_type="application/json")

    def test_index_renders(self):
        res = self.client.get("/")
        self.assertContains(res, "Online Compiler")
        self.assertIn("csrftoken", res.cookies)

    def test_languages(self):
        data = self.client.get("/api/languages/").json()
        slugs = {lang["slug"]: lang for lang in data["languages"]}
        self.assertTrue(slugs["python"]["available"])
        self.assertEqual(slugs["python"]["monaco"], "python")
        self.assertIn("run_timeout", data["limits"])

    def test_run_persists_execution(self):
        res = self.post("/api/run/", {"language": "python", "code": "print(input()[::-1])", "stdin": "abc"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["stdout"], "cba\n")
        execution = Execution.objects.get(pk=body["id"])
        self.assertEqual(execution.stdout, "cba\n")
        self.assertEqual(execution.status, "ok")

    def test_nul_bytes_are_storable(self):
        res = self.post("/api/run/", {"language": "python", "code": "print('a\\0b')"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Execution.objects.get(pk=res.json()["id"]).stdout, "a\\0b\n")

    def test_validation(self):
        cases = [
            ({"language": "nope", "code": "x"}, "Неизвестный язык"),
            ({"language": "python", "code": ""}, "обязательно"),
            ({"language": "python", "code": 123}, "строкой"),
        ]
        for payload, error in cases:
            res = self.post("/api/run/", payload)
            self.assertEqual(res.status_code, 400)
            self.assertIn(error, res.json()["error"])
        res = self.client.post("/api/run/", "not json", content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_get_not_allowed_on_run(self):
        self.assertEqual(self.client.get("/api/run/").status_code, 405)

    @override_settings(EXECUTOR={**LOCAL, "RATE_LIMIT_PER_MINUTE": 2})
    def test_rate_limit(self):
        from django.core.cache import cache
        cache.clear()
        codes = [self.post("/api/run/", {"language": "python", "code": "pass"}).status_code for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])

    def test_snippet_roundtrip(self):
        res = self.post("/api/snippets/", {"language": "python", "code": "print(1)", "stdin": "in", "title": "demo"})
        self.assertEqual(res.status_code, 201)
        sid = res.json()["id"]
        self.assertEqual(self.client.get(f"/api/snippets/{sid}/").json()["code"], "print(1)")
        page = self.client.get(f"/s/{sid}/")
        self.assertContains(page, "print(1)")
        self.assertEqual(Snippet.objects.get(pk=sid).views, 1)
        raw = self.client.get(f"/s/{sid}/raw/")
        self.assertEqual(raw.content.decode(), "print(1)")
        self.assertEqual(self.client.get("/s/doesnotexist/").status_code, 404)

    def test_history_is_per_session(self):
        from django.test import Client
        run_id = self.post("/api/run/", {"language": "python", "code": "print(42)"}).json()["id"]
        items = self.client.get("/api/history/").json()["items"]
        self.assertEqual([i["id"] for i in items], [run_id])
        self.assertEqual(self.client.get(f"/api/executions/{run_id}/").json()["stdout"], "42\n")

        stranger = Client()
        self.assertEqual(stranger.get("/api/history/").json()["items"], [])
        self.assertEqual(stranger.get(f"/api/executions/{run_id}/").status_code, 404)

    def test_run_multifile_project(self):
        res = self.post("/api/run/", {
            "language": "python",
            "code": "from lib.util import twice\nprint(twice(21))",
            "files": [{"name": "lib/util.py", "content": "def twice(x):\n    return x * 2\n"}],
        })
        body = res.json()
        self.assertEqual((body["status"], body["stdout"]), ("ok", "42\n"))
        execution = Execution.objects.get(pk=body["id"])
        self.assertEqual(execution.files, [{"name": "lib/util.py", "content": "def twice(x):\n    return x * 2\n"}])
        self.assertEqual(self.client.get("/api/history/").json()["items"][0]["file_count"], 2)

    def test_error_in_secondary_file_points_to_it(self):
        body = self.post("/api/run/", {
            "language": "python", "code": "import helper\nhelper.boom()",
            "files": [{"name": "helper.py", "content": "def boom():\n    raise RuntimeError('x')\n"}],
        }).json()
        self.assertIn('File "helper.py", line 2', body["stderr"])

    def test_bad_filenames_rejected(self):
        bad = ["../evil.py", "main.py", "a\\b.py", ".env", "out/x.py", "x" * 70 + ".py", "a/b/c/d/e.py"]
        for name in bad:
            res = self.post("/api/run/", {"language": "python", "code": "pass",
                                          "files": [{"name": name, "content": ""}]})
            self.assertEqual(res.status_code, 400, name)
        res = self.post("/api/run/", {"language": "python", "code": "pass", "files": [
            {"name": "a.py", "content": ""}, {"name": "a.py", "content": ""}]})
        self.assertEqual(res.status_code, 400)
        res = self.post("/api/run/", {"language": "python", "code": "pass", "files": "nope"})
        self.assertEqual(res.status_code, 400)

    def test_snippet_keeps_files(self):
        files = [{"name": "util.py", "content": "X = 1\n"}]
        sid = self.post("/api/snippets/", {"language": "python", "code": "import util", "files": files}).json()["id"]
        self.assertEqual(self.client.get(f"/api/snippets/{sid}/").json()["files"], files)

    def test_csrf_enforced(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        res = self.post("/api/run/", {"language": "python", "code": "print(1)"}, client=client)
        self.assertEqual(res.status_code, 403)


class ConsoleTests(TransactionTestCase):
    """Интерактивная консоль через WebSocket (локальный бэкенд — чтобы тест не зависел от Docker)."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    async def _connect(self, origin=b"http://localhost:8000"):
        from channels.testing import WebsocketCommunicator
        from config.asgi import application
        comm = WebsocketCommunicator(application, "/ws/run/", headers=[(b"origin", origin), (b"host", b"localhost")])
        connected, _ = await comm.connect()
        return comm, connected

    async def _collect_until(self, comm, predicate, timeout=60):
        events = []
        while True:
            ev = await comm.receive_json_from(timeout=timeout)
            events.append(ev)
            if predicate(ev, events):
                return events

    @override_settings(EXECUTOR=LOCAL)
    @skipUnless(python_available, "нужен локальный python")
    async def test_interactive_roundtrip(self):
        comm, connected = await self._connect()
        self.assertTrue(connected)
        await comm.send_json_to({"type": "start", "language": "python",
                                 "code": "n = input('Имя: ')\nprint('Привет,', n)"})
        out = lambda evs: "".join(e["data"] for e in evs if e["type"] == "output")  # noqa: E731
        events = await self._collect_until(comm, lambda ev, evs: "Имя: " in out(evs))
        self.assertIn({"type": "phase", "phase": "run"}, events)
        await comm.send_json_to({"type": "stdin", "data": "Лёха\n"})
        events += await self._collect_until(comm, lambda ev, evs: ev["type"] == "exit")
        exit_ev = events[-1]
        self.assertEqual(exit_ev["status"], "ok")
        self.assertIn("Привет, Лёха", out(events))
        execution = await Execution.objects.aget(pk=exit_ev["id"])
        self.assertEqual(execution.stdin, "Лёха\n")
        self.assertIn("Имя: Лёха\nПривет, Лёха", execution.stdout)
        await comm.disconnect()

    @override_settings(EXECUTOR=LOCAL)
    @skipUnless(python_available, "нужен локальный python")
    async def test_kill_and_validation(self):
        comm, _ = await self._connect()
        await comm.send_json_to({"type": "start", "language": "nope", "code": "x"})
        self.assertEqual((await comm.receive_json_from(timeout=10))["type"], "error")
        await comm.send_json_to({"type": "start", "language": "python",
                                 "code": "import time\nprint('go', flush=True)\ntime.sleep(60)"})
        await self._collect_until(comm, lambda ev, evs: ev["type"] == "output" and "go" in ev["data"])
        await comm.send_json_to({"type": "start", "language": "python", "code": "print(1)"})
        events = await self._collect_until(comm, lambda ev, evs: ev["type"] == "error", timeout=10)
        self.assertIn("уже запущена", events[-1]["error"])
        await comm.send_json_to({"type": "kill"})
        events = await self._collect_until(comm, lambda ev, evs: ev["type"] == "exit", timeout=20)
        self.assertEqual(events[-1]["status"], "stopped")
        await comm.disconnect()

    async def test_foreign_origin_rejected(self):
        comm, connected = await self._connect(origin=b"http://evil.example")
        self.assertFalse(connected)
