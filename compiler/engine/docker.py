"""Docker-бэкенд: каждый запуск — одноразовый контейнер без сети и с жёсткими лимитами."""
from __future__ import annotations

import math
import shlex
import subprocess
import threading
import time
import uuid
from pathlib import Path

from .languages import Language, source_files
from .process import run_limited
from .result import ExecutionResult, Status
from .workspace import Workspace, decode_output

NAME = "docker"
CODE_DIR = "/code"
_MARK_COMPILE_FAILED = ".oc_compile_failed"
_MARK_COMPILED = ".oc_compiled"
_COMPILE_LOG = ".oc_compile.log"
_TIMING = ".oc_time"
_MEMORY = ".oc_mem"
_STARTUP_GRACE = 15.0  # запас на старт контейнера

_lock = threading.Lock()
_daemon_cache: dict = {"ok": None, "at": 0.0}
_images_present: set[str] = set()


def _docker(cfg: dict) -> str:
    return cfg.get("DOCKER_BIN", "docker")


def daemon_available(cfg: dict, ttl: float = 15.0) -> bool:
    with _lock:
        if _daemon_cache["ok"] is not None and time.monotonic() - _daemon_cache["at"] < ttl:
            return _daemon_cache["ok"]
    try:
        ok = subprocess.run(
            [_docker(cfg), "info", "--format", "{{.ServerVersion}}"],
            capture_output=True, timeout=5,
        ).returncode == 0
    except (OSError, subprocess.SubprocessError):
        ok = False
    with _lock:
        _daemon_cache.update(ok=ok, at=time.monotonic())
    return ok


_images_cache: dict = {"names": frozenset(), "at": -1e9}


def _normalize(image: str) -> str:
    return image if ":" in image.rsplit("/", 1)[-1] else f"{image}:latest"


def _local_images(cfg: dict, ttl: float = 30.0) -> frozenset[str]:
    """Один вызов `docker images` на всех, а не inspect на каждый язык — каталог языков отдаётся мгновенно."""
    with _lock:
        if time.monotonic() - _images_cache["at"] < ttl:
            return _images_cache["names"]
    try:
        out = subprocess.run(
            [_docker(cfg), "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        names = frozenset(line.strip() for line in out.splitlines() if line.strip())
    except (OSError, subprocess.SubprocessError):
        names = frozenset()
    with _lock:
        _images_cache.update(names=names, at=time.monotonic())
    return names


def image_present(image: str, cfg: dict) -> bool:
    if image in _images_present:
        return True
    if _normalize(image) in _local_images(cfg):
        _images_present.add(image)
        return True
    return False


def is_available(lang: Language, cfg: dict) -> bool:
    return lang.docker is not None and daemon_available(cfg) and image_present(lang.docker.image, cfg)


def pull(image: str, cfg: dict) -> tuple[bool, str]:
    proc = subprocess.run([_docker(cfg), "pull", image], capture_output=True, text=True)
    if proc.returncode == 0:
        _images_present.add(image)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def with_args(cmd: str, args: list[str] | tuple[str, ...] = (), sep: str = "") -> str:
    """Дописывает аргументы командной строки программы, экранируя их для sh."""
    if not args:
        return cmd
    return " ".join([cmd, *([sep] if sep else []), *(shlex.quote(a) for a in args)])


def _script(lang: Language, run_timeout: float, sources: list[str] | None = None, args: list[str] = ()) -> str:
    spec = lang.docker
    seconds = max(1, math.ceil(run_timeout))
    lines = []
    if spec.compile:
        compile_cmd = spec.compile.replace("{sources}", " ".join(shlex.quote(s) for s in sources or [lang.filename]))
        lines.append(
            f"( {compile_cmd} ) >{_COMPILE_LOG} 2>&1 </dev/null "
            f"|| {{ echo $? > {_MARK_COMPILE_FAILED}; exit 0; }}"
        )
        lines.append(f": > {_MARK_COMPILED}")
    lines += [
        "read T0 _ </proc/uptime",
        f"timeout -s KILL {seconds} {with_args(spec.run, args)}",
        "RC=$?",
        "read T1 _ </proc/uptime",
        f'echo "$T0 $T1" > {_TIMING}',
        f"cat /sys/fs/cgroup/memory.peak > {_MEMORY} 2>/dev/null",
        "exit $RC",
    ]
    return "\n".join(lines)


def _base_argv(lang: Language, ws: Workspace, name: str, cfg: dict,
               mounts: list[tuple[str, str]] = (), color: bool = False,
               memory_mb: int | None = None, env: tuple[tuple[str, str], ...] | None = None) -> list[str]:
    """Общие флаги песочницы; дальше вызывающий дописывает образ и команду."""
    spec = lang.docker
    memory = memory_mb or spec.memory_mb or cfg["MEMORY_MB"]
    argv = [
        _docker(cfg), "run", "--rm", "-i",
        "--name", name,
        "--hostname", "sandbox",
        "--network", "none",
        "--memory", f"{memory}m", "--memory-swap", f"{memory}m",
        "--cpus", "1",
        "--pids-limit", "256",
        "--ulimit", "nofile=256:256",
        "--ulimit", "fsize=67108864:67108864",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--read-only",
        "--tmpfs", "/tmp:rw,exec,nosuid,size=256m",
        "--user", "65534:65534",
        "--log-driver", "none",
        "-v", f"{ws.path}:{CODE_DIR}",
        "-w", CODE_DIR,
        "-e", "HOME=/tmp", "-e", "TMPDIR=/tmp", "-e", "LANG=C.UTF-8",
        "-e", "TERM=xterm-256color" if color else "NO_COLOR=1",
        "-e", "DOTNET_CLI_HOME=/tmp", "-e", "NUGET_PACKAGES=/tmp/nuget",
    ]
    for host, container in mounts:
        argv += ["-v", f"{host}:{container}:ro"]
    for key, value in (spec.env if env is None else env):
        argv += ["-e", f"{key}={value}"]
    return argv


def _argv(lang: Language, ws: Workspace, name: str, cfg: dict, sources: list[str], args: list[str] = ()) -> list[str]:
    return _base_argv(lang, ws, name, cfg) + [lang.docker.image, "sh", "-c",
                                              _script(lang, cfg["RUN_TIMEOUT"], sources, args)]


def prepare(lang: Language, code: str, files: dict[str, str], ws: Workspace) -> None:
    ws.write(lang.filename, code)
    for fname, content in files.items():
        ws.write(fname, content)
    for fname, content in lang.extra_files:
        ws.write(fname, content.replace("{dotnet_major}", "8"))


def kill_container(name: str, cfg: dict) -> None:
    _force_remove(name, cfg)


# ---------- интерактивный режим и отладка ----------

SANDBOX_DIR = Path(__file__).parent / "sandbox"
HELPERS = {  # статические бинарники, которые монтируются в контейнеры
    "ptyrun": ["-lutil"],  # PTY для консоли
    "octcp": [],           # stdio <-> TCP для отладочных серверов (debugpy, delve)
}
PTYRUN_BINARY = SANDBOX_DIR / "ptyrun"
PTYRUN_IN_CONTAINER = "/opt/oc/ptyrun"
CONTROL_PREFIX = "@@OC "
_build_lock = threading.Lock()


def helper_mounts() -> list[tuple[str, str]]:
    return [(str(SANDBOX_DIR / name), f"/opt/oc/{name}") for name in HELPERS]


def ensure_helpers(cfg: dict) -> tuple[bool, str]:
    """Собирает статические хелперы в образе gcc (один раз, пересобирает при изменении исходника)."""
    with _build_lock:
        stale = [name for name in HELPERS
                 if not (SANDBOX_DIR / name).exists()
                 or (SANDBOX_DIR / name).stat().st_mtime < (SANDBOX_DIR / f"{name}.c").stat().st_mtime]
        if not stale:
            return True, "уже собраны"
        if not image_present("gcc:14", cfg):
            ok, out = pull("gcc:14", cfg)
            if not ok:
                return False, f"Не удалось скачать gcc:14 для сборки хелперов: {out[-300:]}"
        for name in stale:
            proc = subprocess.run(
                [_docker(cfg), "run", "--rm", "--network", "none", "-v", f"{SANDBOX_DIR}:/src", "-w", "/src", "gcc:14",
                 "gcc", "-static", "-O2", "-o", name, f"{name}.c", *HELPERS[name]],
                capture_output=True, text=True, timeout=300,
            )
            if proc.returncode != 0 or not (SANDBOX_DIR / name).exists():
                return False, f"Сборка {name} упала: {(proc.stdout + proc.stderr)[-500:]}"
        return True, "собраны: " + ", ".join(stale)


def ensure_ptyrun(cfg: dict) -> tuple[bool, str]:  # обратная совместимость
    return ensure_helpers(cfg)


def _session_script(compile_cmd: str | None, run_cmd: str, cfg: dict, cpu: float, wall: float) -> str:
    """Компиляция стримится в stderr вместе с управляющими строками `@@OC ...`,
    программа идёт через PTY в stdout. CPU ограничен ulimit -t, общее время — timeout."""
    cpu_s = max(1, math.ceil(cpu))
    wall_s = max(cpu_s, math.ceil(wall))
    lines = [f"emit() {{ printf '\\n{CONTROL_PREFIX}%s\\n' \"$*\" >&2; }}"]
    if compile_cmd:
        lines += [
            "emit phase compile",
            f"timeout -s KILL {math.ceil(cfg['COMPILE_TIMEOUT'])} sh -c {shlex.quote(compile_cmd)} "
            "</dev/null 1>&2 2>&1",
            "rc=$?",
            'if [ "$rc" -ne 0 ]; then emit compile_failed "$rc"; exit 0; fi',
        ]
    lines += [
        "emit phase run",
        f"ulimit -t {cpu_s} 2>/dev/null",
        "read T0 _ </proc/uptime",
        f"timeout -s KILL {wall_s} {PTYRUN_IN_CONTAINER} {run_cmd}",
        "RC=$?",
        "read T1 _ </proc/uptime",
        'emit exit "$RC" "$T0" "$T1" "$(cat /sys/fs/cgroup/memory.peak 2>/dev/null || echo 0)"',
        "exit 0",
    ]
    return "\n".join(lines)


def _with_sources(cmd: str | None, sources: list[str]) -> str | None:
    return cmd.replace("{sources}", " ".join(shlex.quote(s) for s in sources)) if cmd else None


def interactive_argv(lang: Language, ws: Workspace, name: str, cfg: dict, sources: list[str],
                     args: list[str] = ()) -> list[str]:
    spec = lang.docker
    script = _session_script(_with_sources(spec.compile, sources), with_args(spec.run, args), cfg,
                             cfg["RUN_TIMEOUT"], cfg["INTERACTIVE_TIMEOUT"])
    # В PTY цвета уместны — xterm.js их отрисует
    return _base_argv(lang, ws, name, cfg, helper_mounts(), color=True) + [spec.image, "sh", "-c", script]


def debug_argv(lang: Language, ws: Workspace, name: str, cfg: dict, sources: list[str], port: int,
               args: list[str] = ()) -> list[str]:
    """Как интерактивный режим, но программа стартует под отладочным сервером на 127.0.0.1:{port}."""
    spec = lang.debug
    launch = with_args(spec.launch.replace("{port}", str(port)), args, spec.args_separator)
    script = _session_script(_with_sources(spec.compile, sources), launch, cfg,
                             cfg["DEBUG_CPU_SECONDS"], cfg["DEBUG_TIMEOUT"])
    env = tuple(lang.docker.env) + tuple(spec.env)
    memory_mb = max(spec.memory_mb, lang.docker.memory_mb or 0)
    return _base_argv(lang, ws, name, cfg, helper_mounts(), color=True, memory_mb=memory_mb, env=env) + [
        spec.image, "sh", "-c", script]


def debug_connect_argv(lang: Language, name: str, cfg: dict, port: int) -> list[str]:
    """DAP через stdio `docker exec`: ждём, пока отладочный сервер начнёт слушать порт, и подключаемся."""
    listening = f":{port:04X} 00000000:0000 0A"
    command = lang.debug.connect.replace("{port}", str(port))
    script = (f"i=0; until grep -qi '{listening}' /proc/net/tcp 2>/dev/null; do "
              f"i=$((i+1)); [ $i -gt 600 ] && exit 97; sleep 0.05; done; exec {command}")
    return [_docker(cfg), "exec", "-i", name, "sh", "-c", script]


def debug_available(lang: Language, cfg: dict) -> bool:
    return lang.debug is not None and daemon_available(cfg) and image_present(lang.debug.image, cfg)


def _force_remove(name: str, cfg: dict) -> None:
    try:
        subprocess.run([_docker(cfg), "rm", "-f", name], capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        pass


def execute(lang: Language, code: str, stdin: str, cfg: dict,
            files: dict[str, str] | None = None, args: list[str] = ()) -> ExecutionResult:
    spec = lang.docker
    if not daemon_available(cfg):
        return ExecutionResult(Status.UNAVAILABLE, backend=NAME, message="Docker-демон недоступен")
    if not image_present(spec.image, cfg):
        return ExecutionResult(
            Status.UNAVAILABLE, backend=NAME,
            message=f"Образ {spec.image} не скачан. Выполни: python manage.py pull_images {lang.slug}",
        )

    name = f"oc-{uuid.uuid4().hex[:16]}"
    timeout = cfg["RUN_TIMEOUT"] + _STARTUP_GRACE + (cfg["COMPILE_TIMEOUT"] if spec.compile else 0)
    with Workspace() as ws:
        prepare(lang, code, files or {}, ws)

        try:
            outcome = run_limited(
                _argv(lang, ws, name, cfg, source_files(lang, list(files or {})), args),
                cwd=str(ws.path), stdin=stdin.encode("utf-8"),
                timeout=timeout, max_output=cfg["MAX_OUTPUT_BYTES"],
            )
        finally:
            _force_remove(name, cfg)

        def read(fname: str) -> str:
            path = ws.path / fname
            return decode_output(path.read_bytes()) if path.exists() else ""

        def clean(text: str) -> str:
            return ws.clean(text, CODE_DIR)

        compile_output = clean(read(_COMPILE_LOG))[: cfg["MAX_OUTPUT_BYTES"]]
        compiled = (ws.path / _MARK_COMPILED).exists()

        if (ws.path / _MARK_COMPILE_FAILED).exists():
            return ExecutionResult(
                Status.COMPILE_ERROR, compile_output=compile_output, backend=NAME,
                exit_code=_int(read(_MARK_COMPILE_FAILED)), message="Ошибка компиляции",
            )

        run_ms = _run_time(read(_TIMING))
        memory = _int(read(_MEMORY))
        stdout = clean(decode_output(outcome.stdout))
        stderr = clean(decode_output(outcome.stderr))
        base = dict(stdout=stdout, stderr=stderr, compile_output=compile_output, backend=NAME,
                    truncated=outcome.output_exceeded,
                    memory_kb=memory // 1024 if memory and not spec.compile else None)

        if outcome.timed_out:
            if spec.compile and not compiled:
                return ExecutionResult(Status.TIMEOUT, **base,
                                       message=f"Компиляция не уложилась в {cfg['COMPILE_TIMEOUT']:g} с")
            return ExecutionResult(Status.TIMEOUT, message=f"Превышен лимит времени ({cfg['RUN_TIMEOUT']:g} с)",
                                   time_ms=int(cfg["RUN_TIMEOUT"] * 1000), **base)
        if outcome.output_exceeded:
            return ExecutionResult(Status.OUTPUT_LIMIT, time_ms=run_ms,
                                   message=f"Слишком много вывода (лимит {cfg['MAX_OUTPUT_BYTES'] // 1024} КБ)", **base)
        if outcome.exit_code == 125 and not compiled and run_ms is None:
            return ExecutionResult(Status.INTERNAL_ERROR, message="Docker не смог запустить контейнер",
                                   exit_code=outcome.exit_code, **base)
        # Время внутри контейнера — честное, без учёта старта Docker. Проверяем до 137:
        # `timeout -s KILL` тоже даёт код 137, и это не OOM
        if run_ms is not None and run_ms >= cfg["RUN_TIMEOUT"] * 1000 - 50:
            return ExecutionResult(Status.TIMEOUT, message=f"Превышен лимит времени ({cfg['RUN_TIMEOUT']:g} с)",
                                   time_ms=run_ms, **base)
        if outcome.exit_code == 137:
            memory_mb = spec.memory_mb or cfg["MEMORY_MB"]
            return ExecutionResult(Status.MEMORY_LIMIT, exit_code=137, time_ms=run_ms,
                                   message=f"Превышен лимит памяти ({memory_mb} МБ)", **base)
        if outcome.exit_code != 0:
            return ExecutionResult(Status.RUNTIME_ERROR, exit_code=outcome.exit_code, time_ms=run_ms,
                                   message=f"Процесс завершился с кодом {outcome.exit_code}", **base)
        return ExecutionResult(Status.OK, exit_code=0, time_ms=run_ms, **base)


def _int(text: str) -> int | None:
    try:
        return int(text.strip())
    except ValueError:
        return None


def _run_time(text: str) -> int | None:
    try:
        t0, t1 = (float(x) for x in text.split())
        return int((t1 - t0) * 1000)
    except ValueError:
        return None


def shell_preview(lang: Language, run_timeout: float = 10) -> str:
    """Для отладки: как выглядит команда внутри контейнера."""
    return f"sh -c {shlex.quote(_script(lang, run_timeout))}"
