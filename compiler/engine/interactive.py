"""Интерактивная сессия: программа работает вживую, ввод приходит по мере набора.

    session = Session("python", code, files, emit=callback)
    session.start()           # события летят в callback из фонового потока:
                              #   {"type": "phase", "phase": "prepare" | "compile" | "run"}
                              #   {"type": "output", "stream": "compile" | "stdout" | "stderr", "data": "..."}
                              #   {"type": "exit", **ExecutionResult.to_dict()}
    session.write("42\\n")     # ввод
    session.eof()              # Ctrl+D
    session.kill()             # стоп

Docker: программа в PTY (ptyrun), CPU ограничен ulimit -t, сессия — INTERACTIVE_TIMEOUT.
Local: пайпы + Job Object с лимитом CPU-времени.
"""
from __future__ import annotations

import codecs
import logging
import threading
import time
import uuid

from django.conf import settings

from . import docker, local
from .languages import get_language, source_files
from .process import StreamProcess
from .project import ProjectError, validate_files
from .result import ExecutionResult, Status
from .workspace import Workspace

log = logging.getLogger(__name__)

_slots: threading.BoundedSemaphore | None = None
_slots_lock = threading.Lock()


def _session_slots(cfg: dict) -> threading.BoundedSemaphore:
    global _slots
    with _slots_lock:
        if _slots is None:
            _slots = threading.BoundedSemaphore(cfg["MAX_INTERACTIVE_SESSIONS"])
        return _slots


class Session:
    def __init__(self, slug: str, code: str, files: dict[str, str] | None, emit, cfg: dict | None = None,
                 args: list[str] | None = None):
        self.cfg = cfg or settings.EXECUTOR
        self.slug = slug
        self.lang = get_language(slug)
        if self.lang is not None:
            self.cfg = self.lang.config(self.cfg)
        self.code = code
        self.files = files or {}
        self.args = list(args or [])
        self._emit = emit
        self.backend = ""
        self.result: ExecutionResult | None = None
        self.done = threading.Event()

        self._proc: StreamProcess | None = None
        self._container: str | None = None
        self._pty = False
        self._ws: Workspace | None = None
        self._stopped = threading.Event()
        self._overflow = threading.Event()
        self._out_bytes = 0
        self._lock = threading.Lock()
        self._decoders: dict[str, codecs.IncrementalDecoder] = {}
        self._transcript: list[str] = []
        self._stdin_log: list[str] = []
        self._compile_output: list[str] = []

    # ---------- публичное API (потокобезопасное) ----------

    def start(self) -> None:
        threading.Thread(target=self._main, name=f"session-{self.slug}", daemon=True).start()

    def write(self, text: str) -> None:
        proc = self._proc
        if proc is None or self.done.is_set():
            return
        with self._lock:
            self._stdin_log.append(text)
            self._transcript.append(text)
        proc.write(text.encode("utf-8"))

    def eof(self) -> None:
        proc = self._proc
        if proc is None or self.done.is_set():
            return
        if self._pty:
            proc.write(b"\x04")  # в PTY конец ввода — это Ctrl+D, а не закрытие пайпа
        else:
            proc.close_stdin()

    def interrupt(self) -> None:
        """Ctrl+C: в PTY — настоящий SIGINT программе, иначе просто стоп."""
        if self._pty and self._proc is not None:
            self._proc.write(b"\x03")
        else:
            self.kill()

    def kill(self) -> None:
        self._stopped.set()
        if self._proc is not None:
            self._proc.kill()
        if self._container:
            threading.Thread(target=docker.kill_container, args=(self._container, self.cfg), daemon=True).start()

    @property
    def stdin_text(self) -> str:
        return "".join(self._stdin_log)

    @property
    def transcript(self) -> str:
        return "".join(self._transcript).replace("\r\n", "\n")

    # ---------- внутреннее ----------

    def emit(self, event: dict) -> None:
        try:
            self._emit(event)
        except Exception:  # отвалившийся клиент не должен ронять сессию
            log.debug("emit failed", exc_info=True)

    def _output(self, stream: str, chunk: bytes) -> None:
        if self._overflow.is_set():
            return
        decoder = self._decoders.setdefault(stream, codecs.getincrementaldecoder("utf-8")(errors="replace"))
        text = decoder.decode(chunk)
        if not text:
            return
        if self._ws:
            text = self._ws.clean(text, docker.CODE_DIR)
        text = self._filter_output(stream, text)
        if not text:
            return
        with self._lock:
            self._out_bytes += len(chunk)
            if self._out_bytes > self.cfg["INTERACTIVE_MAX_OUTPUT_BYTES"]:
                self._overflow.set()
            self._transcript.append(text)
        self.emit({"type": "output", "stream": stream, "data": text})
        if self._overflow.is_set():
            self.kill()

    def _compile_text(self, text: str) -> None:
        if not text:
            return
        if self._ws:
            text = self._ws.clean(text, docker.CODE_DIR)
        self._compile_output.append(text)
        self.emit({"type": "output", "stream": "compile", "data": text})

    def _finish(self, result: ExecutionResult) -> None:
        result.backend = result.backend or self.backend
        if not result.compile_output:
            result.compile_output = "".join(self._compile_output)
        if not result.stdout:
            result.stdout = self.transcript
        self.result = result
        self.emit({"type": "exit", **result.to_dict()})
        self.done.set()

    def _main(self) -> None:
        cfg = self.cfg
        if self.lang is None:
            self._finish(ExecutionResult(Status.UNAVAILABLE, message=f"Неизвестный язык: {self.slug}"))
            return
        try:
            validate_files(self.lang, self.files, cfg["MAX_CODE_BYTES"], self.code)
        except ProjectError as exc:
            self._finish(ExecutionResult(Status.INTERNAL_ERROR, message=str(exc)))
            return

        self.backend = self._select_backend() or ""
        if not self.backend:
            self._finish(ExecutionResult(Status.UNAVAILABLE, message=self._unavailable_message()))
            return

        slots = _session_slots(cfg)
        if not slots.acquire(blocking=False):
            self._finish(ExecutionResult(Status.UNAVAILABLE,
                                         message="Все интерактивные слоты заняты, попробуй через минуту"))
            return
        try:
            with Workspace() as ws:
                self._ws = ws
                if self.backend == docker.NAME:
                    self._finish(self._run_docker(ws))
                else:
                    self._finish(self._run_local(ws))
        except Exception as exc:
            log.exception("Interactive session failed")
            self._finish(ExecutionResult(Status.INTERNAL_ERROR, message=f"Внутренняя ошибка движка: {exc}"))
        finally:
            if self._proc is not None:
                self._proc.close()
            slots.release()

    # ---------- точки расширения (переопределяет отладчик) ----------

    @property
    def timeout(self) -> float:
        return self.cfg["INTERACTIVE_TIMEOUT"]

    @property
    def cpu_limit(self) -> float:
        return self.cfg["RUN_TIMEOUT"]

    def _select_backend(self) -> str | None:
        from . import pick_backend  # поздний импорт: пакет импортирует этот модуль
        return pick_backend(self.lang, self.cfg)

    def _unavailable_message(self) -> str:
        from . import _unavailable_message
        return _unavailable_message(self.lang, self.cfg)

    def _docker_argv(self, ws: Workspace, name: str) -> list[str]:
        return docker.interactive_argv(self.lang, ws, name, self.cfg, source_files(self.lang, list(self.files)),
                                       self.args)

    def _docker_memory_mb(self) -> int:
        return self.lang.docker.memory_mb or self.cfg["MEMORY_MB"]

    def _docker_compiles(self) -> bool:
        return bool(self.lang.docker.compile)

    def _on_phase(self, phase: str) -> None:
        pass

    def _filter_output(self, stream: str, text: str) -> str:
        return text

    def _local_argv(self, ws: Workspace) -> list[str]:
        return local.run_argv(self.lang, ws, self.args)

    def _local_compile(self, ws: Workspace, env: dict[str, str]):
        return local.compile_project(self.lang, self.files, ws, env, self.cfg)

    # ---------- local ----------

    def _run_local(self, ws: Workspace) -> ExecutionResult:
        cfg, lang = self.cfg, self.lang
        env = local.prepare(lang, self.code, self.files, ws, interactive=True)
        if lang.local.compile:
            self.emit({"type": "phase", "phase": "compile"})
            compiled = self._local_compile(ws, env)
            if isinstance(compiled, ExecutionResult):
                self._compile_text(compiled.compile_output)
                compiled.compile_output = "".join(self._compile_output)
                return compiled
            self._compile_text(compiled[0])

        if self._stopped.is_set():
            return ExecutionResult(Status.STOPPED, message="Остановлено")
        self.emit({"type": "phase", "phase": "run"})
        self._proc = proc = StreamProcess(
            self._local_argv(ws), cwd=str(ws.path), env=env,
            on_stdout=lambda b: self._output("stdout", b), on_stderr=lambda b: self._output("stderr", b),
            memory_mb=cfg["MEMORY_MB"], max_processes=32, cpu_seconds=self.cpu_limit,
        )
        self._on_phase("run")
        deadline = time.monotonic() + self.timeout
        code = None
        while code is None:
            code = proc.wait(timeout=0.2)
            used = proc.cpu_now() if code is None else None
            if used is not None and used >= self.cpu_limit:
                proc.kill()
                proc.wait()
                return self._result(Status.TIMEOUT, proc, None,
                                    f"Превышен лимит процессорного времени ({self.cpu_limit:g} с)")
            if code is None and time.monotonic() > deadline:
                proc.kill()
                code = proc.wait()
                return self._result(Status.TIMEOUT, proc, None, f"Сессия длилась дольше {self.timeout:g} с")

        if self._overflow.is_set():
            return self._result(Status.OUTPUT_LIMIT, proc, code, self._overflow_message())
        if self._stopped.is_set():
            return self._result(Status.STOPPED, proc, code, "Остановлено")
        if proc.cpu_exceeded:
            return self._result(Status.TIMEOUT, proc, None,
                                f"Превышен лимит процессорного времени ({self.cpu_limit:g} с)")
        if proc.memory_exceeded:
            return self._result(Status.MEMORY_LIMIT, proc, code, f"Превышен лимит памяти ({cfg['MEMORY_MB']} МБ)")
        if code != 0:
            return self._result(Status.RUNTIME_ERROR, proc, code, f"Процесс завершился с кодом {code}")
        return self._result(Status.OK, proc, 0, "")

    def _result(self, status: Status, proc: StreamProcess, code: int | None, message: str) -> ExecutionResult:
        peak = getattr(proc, "peak_memory", None)
        return ExecutionResult(
            status, exit_code=code, message=message, time_ms=getattr(proc, "elapsed_ms", None),
            memory_kb=peak // 1024 if peak else None, truncated=self._overflow.is_set(),
        )

    def _overflow_message(self) -> str:
        return f"Слишком много вывода (лимит {self.cfg['INTERACTIVE_MAX_OUTPUT_BYTES'] // 1024} КБ)"

    # ---------- docker ----------

    def _run_docker(self, ws: Workspace) -> ExecutionResult:
        cfg, lang = self.cfg, self.lang
        if not docker.PTYRUN_BINARY.exists():
            self.emit({"type": "phase", "phase": "prepare"})
        ok, message = docker.ensure_helpers(cfg)
        if not ok:
            return ExecutionResult(Status.INTERNAL_ERROR, message=message)

        docker.prepare(lang, self.code, self.files, ws)
        self._container = name = f"oc-{uuid.uuid4().hex[:16]}"
        argv = self._docker_argv(ws, name)
        control: dict = {}
        stderr_state = {"buf": "", "blank": 0, "decoder": codecs.getincrementaldecoder("utf-8")(errors="replace")}

        def on_stderr(chunk: bytes) -> None:
            stderr_state["buf"] += stderr_state["decoder"].decode(chunk)
            *lines, stderr_state["buf"] = stderr_state["buf"].split("\n")
            for line in lines:
                self._stderr_line(line, control, stderr_state)

        self._pty = True
        self._proc = proc = StreamProcess(
            argv, cwd=str(ws.path), env=None,
            on_stdout=lambda b: self._output("stdout", b), on_stderr=on_stderr,
        )
        limit = self.timeout + (cfg["COMPILE_TIMEOUT"] if self._docker_compiles() else 0) + 30
        code = proc.wait(timeout=limit)
        if code is None:
            self.kill()
            code = proc.wait()
            return ExecutionResult(Status.TIMEOUT, message=f"Сессия длилась дольше {self.timeout:g} с")
        docker.kill_container(name, cfg)
        if stderr_state["buf"]:
            self._stderr_line(stderr_state["buf"], control, stderr_state)
        return self._docker_result(code, control)

    def _stderr_line(self, line: str, control: dict, state: dict) -> None:
        if line.startswith(docker.CONTROL_PREFIX):
            # emit() в скрипте ставит \n перед управляющей строкой — одну пустую строку съедаем
            state["blank"] = max(0, state["blank"] - 1)
            self._flush_blank(state)
            parts = line[len(docker.CONTROL_PREFIX):].split()
            kind, args = (parts[0], parts[1:]) if parts else ("", [])
            if kind == "phase" and args:
                self.emit({"type": "phase", "phase": args[0]})
                control["phase"] = args[0]
                self._on_phase(args[0])
            elif kind == "compile_failed":
                control["compile_failed"] = int(args[0]) if args and args[0].isdigit() else 1
            elif kind == "exit":
                control["exit"] = args
            return
        if not line.strip():
            state["blank"] += 1
            return
        self._flush_blank(state)
        if control.get("phase") in (None, "compile"):
            self._compile_text(line + "\n")
        else:
            self._output("stderr", (line + "\n").encode("utf-8"))

    def _flush_blank(self, state: dict) -> None:
        if state["blank"]:
            self._compile_text("\n" * state["blank"])
            state["blank"] = 0

    def _docker_result(self, cli_code: int, control: dict) -> ExecutionResult:
        cfg = self.cfg
        memory_limit_mb = self._docker_memory_mb()
        if "compile_failed" in control:
            rc = control["compile_failed"]
            if rc == 137:
                return ExecutionResult(Status.TIMEOUT,
                                       message=f"Компиляция не уложилась в {cfg['COMPILE_TIMEOUT']:g} с")
            return ExecutionResult(Status.COMPILE_ERROR, exit_code=rc, message="Ошибка компиляции")
        if "exit" not in control:
            if self._stopped.is_set():
                return ExecutionResult(Status.STOPPED, message="Остановлено")
            return ExecutionResult(Status.INTERNAL_ERROR, exit_code=cli_code,
                                   message="Контейнер завершился раньше времени" + (
                                       f" (docker вернул {cli_code})" if cli_code else ""))

        rc, t0, t1, mem = (control["exit"] + ["0", "0", "0", "0"])[:4]
        rc = int(rc) if rc.lstrip("-").isdigit() else None
        try:
            time_ms = int((float(t1) - float(t0)) * 1000)
        except ValueError:
            time_ms = None
        memory = int(mem) if mem.isdigit() else 0
        base = dict(exit_code=rc, time_ms=time_ms, truncated=self._overflow.is_set(),
                    memory_kb=memory // 1024 if memory and not self._docker_compiles() else None)

        if self._overflow.is_set():
            return ExecutionResult(Status.OUTPUT_LIMIT, message=self._overflow_message(), **base)
        if self._stopped.is_set():
            return ExecutionResult(Status.STOPPED, message="Остановлено", **base)
        if rc == 137:
            if memory and memory >= memory_limit_mb * 1024 * 1024 * 0.9:
                return ExecutionResult(Status.MEMORY_LIMIT, message=f"Превышен лимит памяти ({memory_limit_mb} МБ)",
                                       **base)
            if time_ms is not None and time_ms >= (self.timeout - 1) * 1000:
                return ExecutionResult(Status.TIMEOUT, message=f"Сессия длилась дольше {self.timeout:g} с",
                                       **base)
            return ExecutionResult(Status.TIMEOUT,
                                   message=f"Превышен лимит процессорного времени ({self.cpu_limit:g} с)", **base)
        if rc == 130:
            return ExecutionResult(Status.STOPPED, message="Прервано (Ctrl+C)", **base)
        if rc:
            return ExecutionResult(Status.RUNTIME_ERROR, message=f"Процесс завершился с кодом {rc}", **base)
        return ExecutionResult(Status.OK, message="", **base)
