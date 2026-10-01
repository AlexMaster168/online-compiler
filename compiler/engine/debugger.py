"""Отладка: интерактивная сессия + DAP-клиент к отладчику языка.

Программа работает так же, как в консоли (ввод-вывод — через терминал), только стартует
под отладочным сервером. Сразу после фазы `run` подключаемся к нему по DAP:

    Docker: `docker exec -i <контейнер> <connect>` — DAP идёт по stdio (сети у контейнера нет)
    Local:  TCP 127.0.0.1:<port> (только Python + debugpy)

События для браузера (в дополнение к событиям консоли):
    {"type": "debug_ready"}
    {"type": "debug_stopped", "reason", "description", "threadId", "frameId", "frames": [...], "scopes": [...]}
    {"type": "debug_continued"}
    {"type": "debug_error", "error": "..."}
"""
from __future__ import annotations

import importlib.util
import logging
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time

from . import docker, local
from .dap import DapClient, DapError
from .interactive import Session
from .process import StreamProcess
from .workspace import Workspace

log = logging.getLogger(__name__)

MAX_VARIABLES = 200
MAX_FRAMES = 64
# gdbserver пишет свои сообщения в тот же терминал, что и программа
# До подключения клиента программа стоит на входе и ничего не печатает — всё до этой строки шум
_STARTUP_END = {
    "gdb": re.compile(r"Remote debugging from host [^\r\n]*\r?\n"),
    "delve": re.compile(r"API server listening at: [^\r\n]*\r?\n"),
    "jdi": re.compile(r"Listening for transport dt_socket at address: \d+\r?\n"),
}
_GDBSERVER_NOISE = re.compile(
    r"(?m)^(?:Child exited with status -?\d+|Child terminated with signal = [^\r\n]*"
    r"|Killing process\(es\):[^\r\n]*|Detaching from process \d+)\r?\n?")
# Регистры процессора — много и редко нужны: показываем по клику
LAZY_SCOPES = {"registers"}
# С какими причинами остановка — «настоящая» (её показываем), а с какими — служебная после подключения
USER_STOP_REASONS = {"breakpoint", "step", "exception", "function breakpoint", "data breakpoint",
                     "instruction breakpoint", "goto"}


JDI_SOURCE = docker.SANDBOX_DIR / "jdi" / "OcJdiAdapter.java"
JDI_CLASSES = docker.SANDBOX_DIR / "jdi" / "classes"
_jdi_lock = threading.Lock()


def local_debug_supported(lang) -> bool:
    if lang.slug == "python":
        return importlib.util.find_spec("debugpy") is not None
    # JVM-языки: свой адаптер собирается локальным JDK (JDI входит в состав JDK)
    return bool(lang.debug and lang.debug.kind == "jdi" and shutil.which("javac") and shutil.which("java"))


def ensure_local_jdi() -> None:
    """Собирает OcJdiAdapter локальным javac (один раз, пересобирает при изменении исходника)."""
    with _jdi_lock:
        target = JDI_CLASSES / "OcJdiAdapter.class"
        if target.exists() and target.stat().st_mtime >= JDI_SOURCE.stat().st_mtime:
            return
        JDI_CLASSES.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run([shutil.which("javac"), "-encoding", "UTF-8", "-d", str(JDI_CLASSES), str(JDI_SOURCE)],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if proc.returncode != 0:
            raise DapError(f"Не собрался Java-адаптер отладчика: {(proc.stdout + proc.stderr)[-400:]}")


def debug_backend(lang, cfg: dict) -> str | None:
    mode = cfg["BACKEND"]
    if mode in ("auto", "docker") and docker.debug_available(lang, cfg):
        return docker.NAME
    if mode in ("auto", "local") and local_debug_supported(lang) and local.is_available(lang):
        return local.NAME
    return None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class DebugSession(Session):
    def __init__(self, slug: str, code: str, files: dict[str, str] | None, emit,
                 breakpoints: dict[str, list[int]] | None = None, cfg: dict | None = None,
                 args: list[str] | None = None):
        super().__init__(slug, code, files, emit, cfg, args)
        self.breakpoints = {name: sorted({int(x) for x in lines if int(x) > 0})
                            for name, lines in (breakpoints or {}).items()}
        self.dap: DapClient | None = None
        self.port = 0
        self._transport_close = None
        self._initialized = threading.Event()
        self._ready = threading.Event()
        self._first_stop_pending = False
        self._thread_id: int | None = None
        self._kind = ""
        self._startup_buffer: str | None = ""  # None — стартовый шум gdbserver уже отфильтрован

    # ---------- настройки сессии ----------

    @property
    def timeout(self) -> float:
        return self.cfg["DEBUG_TIMEOUT"]

    @property
    def cpu_limit(self) -> float:
        return self.cfg["DEBUG_CPU_SECONDS"]

    def _select_backend(self) -> str | None:
        return debug_backend(self.lang, self.cfg)

    def _unavailable_message(self) -> str:
        if self.lang.debug is None and not local_debug_supported(self.lang):
            return f"Отладка для {self.lang.name} пока не поддерживается"
        if self.lang.debug and not docker.daemon_available(self.cfg):
            return "Для отладки нужен Docker — запусти Docker Desktop"
        return f"Отладчик для {self.lang.name} не собран: python manage.py build_sandbox"

    def _docker_argv(self, ws: Workspace, name: str) -> list[str]:
        from .languages import source_files
        self.port = 40000 + int.from_bytes(os.urandom(2), "big") % 20000
        self._kind = self.lang.debug.kind
        return docker.debug_argv(self.lang, ws, name, self.cfg, source_files(self.lang, list(self.files)), self.port,
                                 self.args)

    def _docker_memory_mb(self) -> int:
        return max(self.lang.debug.memory_mb, self.lang.docker.memory_mb or 0)

    def _docker_compiles(self) -> bool:
        return bool(self.lang.debug.compile)

    def _local_argv(self, ws: Workspace) -> list[str]:
        self.port = _free_port()
        if self.lang.slug == "python":
            self._kind = "debugpy"
            return [sys.executable, "-X", "utf8", "-X", "frozen_modules=off", "-u", "-m", "debugpy",
                    "--listen", f"127.0.0.1:{self.port}", "--wait-for-client", self.lang.filename, *self.args]
        # JVM: обычная команда запуска + JDWP-агент сразу после `java`
        self._kind = "jdi"
        argv = local.run_argv(self.lang, ws, self.args)
        argv.insert(1, f"-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=127.0.0.1:{self.port}")
        return argv

    def _local_compile(self, ws: Workspace, env: dict[str, str]):
        return local.compile_project(self.lang, self.files, ws, env, self.cfg, debug=True)

    def _filter_output(self, stream: str, text: str) -> str:
        startup = _STARTUP_END.get(self._kind)
        if startup is None:
            return text
        if self._startup_buffer is not None:
            self._startup_buffer += text
            match = startup.search(self._startup_buffer)
            if not match:
                return ""
            text, self._startup_buffer = self._startup_buffer[match.end():], None
        return _GDBSERVER_NOISE.sub("", text) if self._kind == "gdb" else text

    def _on_phase(self, phase: str) -> None:
        if phase == "run":
            threading.Thread(target=self._attach, name="dap-attach", daemon=True).start()

    # ---------- управление ----------

    def kill(self) -> None:
        super().kill()
        self._close_dap()

    def _finish(self, result) -> None:
        self._close_dap()
        super()._finish(result)

    def _close_dap(self) -> None:
        if self.dap is not None:
            self.dap.close()
        if self._transport_close is not None:
            try:
                self._transport_close()
            except Exception:
                pass

    # ---------- подключение ----------

    def _attach(self) -> None:
        try:
            if self.backend == docker.NAME:
                self._connect_docker()
            else:
                self._connect_local()
            self._handshake()
        except Exception as exc:
            if self.done.is_set() or self._stopped.is_set():
                return
            log.warning("Debug attach failed: %s", exc)
            self.emit({"type": "debug_error", "error": f"Отладчик не подключился: {exc}"})
            self.kill()

    def _connect_docker(self) -> None:
        argv = docker.debug_connect_argv(self.lang, self._container, self.cfg, self.port)
        stderr: list[bytes] = []
        self.dap = DapClient(write=lambda data: proc.write(data), on_event=self._on_event)
        proc = StreamProcess(argv, cwd=str(self._ws.path), env=None,
                             on_stdout=self.dap.feed, on_stderr=stderr.append)
        self._transport_close = proc.close

        def watch() -> None:
            code = proc.wait()
            if not self.done.is_set() and not self._stopped.is_set() and self.dap and not self.dap.closed.is_set():
                tail = b"".join(stderr).decode("utf-8", "replace").strip()[-300:]
                if not self._ready.is_set():
                    self.emit({"type": "debug_error",
                               "error": f"Отладчик завершился (код {code}){': ' + tail if tail else ''}"})
                self.dap.close()
        threading.Thread(target=watch, name="dap-watch", daemon=True).start()

    def _connect_local(self) -> None:
        if self._kind == "jdi":
            self._connect_local_jdi()
            return
        deadline = time.monotonic() + 20
        while True:
            try:
                sock = socket.create_connection(("127.0.0.1", self.port), timeout=2)
                break
            except OSError:
                if time.monotonic() > deadline or self.done.is_set():
                    raise DapError("debugpy не открыл порт")
                time.sleep(0.1)
        sock.settimeout(None)
        self.dap = dap = DapClient(write=sock.sendall, on_event=self._on_event)

        def read() -> None:
            try:
                while chunk := sock.recv(65536):
                    dap.feed(chunk)
            except OSError:
                pass
            dap.close()
        threading.Thread(target=read, name="dap-socket", daemon=True).start()
        self._transport_close = sock.close

    def _connect_local_jdi(self) -> None:
        """Локальный JDK: адаптер — отдельный процесс, DAP по его stdio (как через docker exec)."""
        ensure_local_jdi()
        argv = [shutil.which("java"), "-Xmx128m", "-XX:+UseSerialGC", "-XX:TieredStopAtLevel=1",
                "-cp", str(JDI_CLASSES), "OcJdiAdapter", str(self.port), self._ws.path.as_posix()]
        self.dap = DapClient(write=lambda data: proc.write(data), on_event=self._on_event)
        proc = StreamProcess(argv, cwd=str(self._ws.path), env=None, on_stdout=self.dap.feed,
                             on_stderr=lambda chunk: None)
        self._transport_close = proc.close

    def _handshake(self) -> None:
        dap, kind = self.dap, self._kind
        caps = dap.request("initialize", {
            "clientID": "online-compiler", "clientName": "Online Compiler", "adapterID": kind,
            "linesStartAt1": True, "columnsStartAt1": True, "pathFormat": "path",
            "supportsVariableType": True, "supportsRunInTerminalRequest": False, "locale": "ru",
        }, timeout=60)
        attach_args = {
            "debugpy": {"justMyCode": True, "showReturnValue": True, "redirectOutput": False, "subProcess": False},
            "gdb": {"target": f"127.0.0.1:{self.port}", "program": f"{docker.CODE_DIR}/main"},
            "delve": {"mode": "remote", "stopOnEntry": False},
            "jdi": {"port": self.port},
        }[kind]
        # gdb и delve подключаются к уже остановленной на входе программе — её надо отпустить
        self._first_stop_pending = kind in ("gdb", "delve")
        attach = dap.request_async("attach", attach_args)
        if not self._initialized.wait(30):
            raise DapError("не пришло событие initialized")
        for name in list(self.breakpoints):
            self._set_breakpoints(name, self.breakpoints[name])
        if caps.get("supportsConfigurationDoneRequest", True):
            dap.request("configurationDone", {}, timeout=30)
        attach.wait(60)
        self._ready.set()
        self.emit({"type": "debug_ready"})
        if self._first_stop_pending:
            # Если адаптер не прислал stopped после подключения — значит программа уже идёт
            threading.Timer(3.0, self._release_entry_stop).start()

    def _release_entry_stop(self) -> None:
        if self._first_stop_pending:
            self._first_stop_pending = False
            try:
                self.dap.request("continue", {"threadId": self._thread_id or self._any_thread()}, timeout=10)
            except DapError:
                pass  # уже бежит

    # ---------- события отладчика ----------

    def _on_event(self, message: dict) -> None:
        event, body = message.get("event"), message.get("body") or {}
        if event == "initialized":
            self._initialized.set()
        elif event == "stopped":
            self._on_stopped(body)
        elif event == "continued":
            self.emit({"type": "debug_continued"})
        elif event in ("terminated", "exited") and self._kind == "delve":
            # delve с --accept-multiclient не гасит сервер сам, даже когда программа завершилась
            self.dap.request_async("disconnect", {"terminateDebuggee": True})
        elif event == "output" and body.get("category") in ("stdout", "stderr"):
            self._output(body["category"], body.get("output", "").encode("utf-8"))

    def _on_stopped(self, body: dict) -> None:
        reason = body.get("reason", "")
        self._thread_id = body.get("threadId") or self._thread_id or self._any_thread()
        if self._first_stop_pending and reason not in USER_STOP_REASONS:
            self._first_stop_pending = False
            self.dap.request_async("continue", {"threadId": self._thread_id})
            return
        self._first_stop_pending = False
        try:
            trace = self.dap.request("stackTrace", {"threadId": self._thread_id, "startFrame": 0,
                                                    "levels": MAX_FRAMES})
        except DapError as exc:
            self.emit({"type": "debug_error", "error": str(exc)})
            return
        frames = []
        for frame in trace.get("stackFrames", []):
            source = frame.get("source") or {}
            file = self._to_project(source.get("path") or source.get("name") or "")
            frames.append({"id": frame["id"], "name": frame.get("name", "?"), "file": file,
                           "line": frame.get("line", 0), "column": frame.get("column", 0)})
        top = next((f for f in frames if f["file"]), frames[0] if frames else None)
        try:
            scopes = self.frame_scopes(top["id"]) if top else []
        except DapError:
            scopes = []  # переменные подгрузятся по клику; саму остановку показываем в любом случае
        self.emit({
            "type": "debug_stopped", "reason": reason,
            "description": body.get("description") or body.get("text") or "",
            "threadId": self._thread_id, "frameId": top["id"] if top else None,
            "frames": frames, "scopes": scopes,
        })

    def _any_thread(self) -> int:
        try:
            threads = self.dap.request("threads", timeout=10).get("threads") or []
            return threads[0]["id"] if threads else 1
        except DapError:
            return 1

    # ---------- пути ----------

    def _remote_path(self, name: str) -> str:
        if self.backend == docker.NAME:
            return f"{docker.CODE_DIR}/{name}"
        return str(self._ws.path / name)

    def _to_project(self, path: str) -> str | None:
        if not path:
            return None
        norm = path.replace("\\", "/")
        prefixes = [f"{docker.CODE_DIR}/", "./"]
        if self._ws is not None:
            prefixes.append(self._ws.path.as_posix() + "/")
        project = {self.lang.filename, *self.files}
        lowered = {name.lower(): name for name in project}
        for prefix in prefixes:
            if norm.lower().startswith(prefix.lower()):
                norm = norm[len(prefix):]
                break
        return lowered.get(norm.lower())

    # ---------- запросы из браузера ----------

    def _set_breakpoints(self, name: str, lines: list[int]) -> list[dict]:
        body = self.dap.request("setBreakpoints", {
            "source": {"path": self._remote_path(name), "name": os.path.basename(name)},
            "breakpoints": [{"line": line} for line in lines],
            "lines": lines,
        })
        return [{"line": bp.get("line"), "verified": bp.get("verified", False), "message": bp.get("message", "")}
                for bp in body.get("breakpoints", [])]

    def frame_scopes(self, frame_id: int) -> list[dict]:
        scopes = []
        for scope in (self.dap.request("scopes", {"frameId": frame_id}).get("scopes") or [])[:4]:
            name = scope.get("name", "")
            lazy = name.lower() in LAZY_SCOPES or (self._kind == "gdb" and name.lower() == "globals")
            item = {"name": name, "ref": scope.get("variablesReference", 0),
                    "expensive": bool(scope.get("expensive")) or lazy, "variables": None}
            if item["ref"] and not item["expensive"]:
                item["variables"] = self.variables(item["ref"])
            scopes.append(item)
        return scopes

    def variables(self, ref: int) -> list[dict]:
        body = self.dap.request("variables", {"variablesReference": ref})
        return [{"name": v.get("name", ""), "value": v.get("value", ""), "type": v.get("type", ""),
                 "ref": v.get("variablesReference", 0)}
                for v in (body.get("variables") or [])[:MAX_VARIABLES]]

    def request(self, command: str, args: dict) -> dict:
        """Запрос из браузера. Бросает DapError — её показываем пользователю."""
        if self.dap is None or not self._ready.is_set():
            if command == "setBreakpoints":  # до подключения просто запоминаем
                self.breakpoints[args["file"]] = sorted({int(x) for x in args.get("lines", [])})
                return {"breakpoints": []}
            raise DapError("Отладчик ещё не подключился")
        if command in ("continue", "next", "stepIn", "stepOut"):
            self.dap.request(command, {"threadId": self._thread_id or self._any_thread()})
            self.emit({"type": "debug_continued"})
            return {}
        if command == "pause":
            self.dap.request("pause", {"threadId": self._thread_id or self._any_thread()})
            return {}
        if command == "setBreakpoints":
            name = args["file"]
            self.breakpoints[name] = sorted({int(x) for x in args.get("lines", [])})
            return {"breakpoints": self._set_breakpoints(name, self.breakpoints[name])}
        if command == "scopes":
            return {"scopes": self.frame_scopes(int(args["frameId"]))}
        if command == "variables":
            return {"variables": self.variables(int(args["ref"]))}
        if command == "evaluate":
            body = self.dap.request("evaluate", {"expression": str(args["expression"])[:500],
                                                 "frameId": args.get("frameId"), "context": "watch"})
            return {"result": body.get("result", ""), "type": body.get("type", ""),
                    "ref": body.get("variablesReference", 0)}
        raise DapError(f"Неизвестная команда отладчика: {command}")
