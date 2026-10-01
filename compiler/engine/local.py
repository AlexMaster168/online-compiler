"""Локальный бэкенд: запускает код тулчейнами хоста под лимитами Job Object / rlimit.

ВНИМАНИЕ: это НЕ полноценная песочница — у кода есть доступ к файловой системе и сети
хоста. Годится для разработки; в проде используй docker-бэкенд.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from .languages import Language, source_files
from .process import IS_WINDOWS, run_limited
from .result import ExecutionResult, Status
from .workspace import Workspace, decode_output

NAME = "local"

_ENV_WHITELIST = {
    "PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "USERPROFILE", "HOME",
    "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432",
    "COMMONPROGRAMFILES", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "JAVA_HOME", "DOTNET_ROOT",
    "GOROOT", "GOPATH", "RUSTUP_HOME", "CARGO_HOME", "LANG", "LC_ALL",
}

_WINDOWS_CANDIDATES = {
    # Без этого на Windows `bash` может резолвиться в WSL-заглушку из System32
    "bash": [r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"],
}

# Для C#: заставляем консоль .NET писать в UTF-8 (по умолчанию на Windows — OEM-кодировка)
_CSHARP_UTF8 = """using System.Runtime.CompilerServices;
static class __Utf8Console
{
    [ModuleInitializer]
    internal static void Init()
    {
        try { System.Console.OutputEncoding = new System.Text.UTF8Encoding(false); } catch { }
    }
}
"""


@lru_cache(maxsize=None)
def resolve_tool(name: str) -> str | None:
    if name == "{python}":
        return sys.executable
    if IS_WINDOWS:
        for candidate in _WINDOWS_CANDIDATES.get(name, []):
            if os.path.isfile(candidate):
                return candidate
    return shutil.which(name)


@lru_cache(maxsize=1)
def dotnet_major() -> str:
    tool = resolve_tool("dotnet")
    if not tool:
        return "8"
    try:
        out = subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=15).stdout
        return out.strip().split(".")[0] or "8"
    except (OSError, subprocess.SubprocessError):
        return "8"


def _required_tools(lang: Language) -> list[str]:
    spec = lang.local
    tools = []
    for cmd in (spec.compile, spec.run):
        if cmd and cmd[0] != "{bin}":
            tools.append(cmd[0])
    return tools


def is_available(lang: Language) -> bool:
    return lang.local is not None and all(resolve_tool(t) for t in _required_tools(lang))


def _build_env(workdir: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k.upper() in _ENV_WHITELIST}
    env.update({
        "TEMP": workdir, "TMP": workdir, "TMPDIR": workdir,
        "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1",
        "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1", "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
        "MSBUILDDISABLENODEREUSE": "1", "NO_COLOR": "1", "TERM": "dumb",
    })
    return env


def _argv(cmd: tuple[str, ...], workdir: Path, sources: list[str] | None = None) -> list[str]:
    binary = str(workdir / ("main.exe" if IS_WINDOWS else "main"))
    argv = []
    for i, token in enumerate(cmd):
        if token == "{sources}":
            argv.extend(sources or [])
        elif token == "{bin}":
            argv.append(binary)
        elif i == 0:
            argv.append(resolve_tool(token) or token)
        else:
            argv.append(token.replace("{bin}", binary))
    return argv


# Интерактивный режим без PTY: заставляем интерпретаторы сбрасывать вывод сразу,
# иначе приглашение "Введите число: " появится только после ввода
_RUBY_SYNC = """$stdout.sync = true
$stderr.sync = true
"""
_PERL_SYNC = """package OcSync;
use IO::Handle;
STDOUT->autoflush(1);
STDERR->autoflush(1);
1;
"""


def prepare(lang: Language, code: str, files: dict[str, str], ws: Workspace,
            interactive: bool = False) -> dict[str, str]:
    """Кладёт проект и служебные файлы в рабочую папку, возвращает окружение для запуска."""
    service_files = dict(lang.extra_files)
    if lang.slug == "csharp":
        service_files["__utf8console.cs"] = _CSHARP_UTF8
    ws.write(lang.filename, code)
    for name, content in files.items():
        ws.write(name, content)
    for name, content in service_files.items():
        ws.write(name, content.replace("{dotnet_major}", dotnet_major()))

    env = _build_env(str(ws.path))
    if interactive:
        ws.write(".oc/sync.rb", _RUBY_SYNC)
        ws.write(".oc/OcSync.pm", _PERL_SYNC)
        env["RUBYOPT"] = f"-r{ws.path / '.oc' / 'sync.rb'}"
        env["PERL5LIB"] = str(ws.path / ".oc")
        env["PERL5OPT"] = "-MOcSync"
    return env


def compile_project(lang: Language, files: dict[str, str], ws: Workspace, env: dict[str, str],
                    cfg: dict, debug: bool = False) -> ExecutionResult | tuple[str, None]:
    """Сборка. Возвращает (вывод компилятора, None) при успехе или готовый ExecutionResult при провале."""
    spec = lang.local
    command = (spec.debug_compile if debug else None) or spec.compile
    if not command:
        return "", None
    outcome = run_limited(
        _argv(command, ws.path, source_files(lang, list(files))), cwd=str(ws.path), env=env,
        timeout=cfg["COMPILE_TIMEOUT"],
        memory_mb=spec.compile_memory_mb or max(cfg["MEMORY_MB"], 1024),
        max_output=cfg["MAX_OUTPUT_BYTES"], max_processes=64,
    )
    compile_output = ws.clean(decode_output(outcome.stdout) + decode_output(outcome.stderr))
    if outcome.timed_out:
        return ExecutionResult(Status.TIMEOUT, compile_output=compile_output, backend=NAME,
                               message=f"Компиляция не уложилась в {cfg['COMPILE_TIMEOUT']:g} с")
    if outcome.exit_code != 0:
        return ExecutionResult(Status.COMPILE_ERROR, compile_output=compile_output,
                               exit_code=outcome.exit_code, backend=NAME, message="Ошибка компиляции")
    return compile_output, None


def run_argv(lang: Language, ws: Workspace, args: list[str] = ()) -> list[str]:
    return _argv(lang.local.run, ws.path) + list(args)


def execute(lang: Language, code: str, stdin: str, cfg: dict,
            files: dict[str, str] | None = None, args: list[str] = ()) -> ExecutionResult:
    files = files or {}
    with Workspace() as ws:
        env = prepare(lang, code, files, ws)
        compiled = compile_project(lang, files, ws, env, cfg)
        if isinstance(compiled, ExecutionResult):
            return compiled
        compile_output, _ = compiled

        outcome = run_limited(
            run_argv(lang, ws, args), cwd=str(ws.path), env=env, stdin=stdin.encode("utf-8"),
            timeout=cfg["RUN_TIMEOUT"], memory_mb=cfg["MEMORY_MB"],
            max_output=cfg["MAX_OUTPUT_BYTES"], max_processes=32,
        )
        return ExecutionResult(
            status=_status(outcome),
            stdout=ws.clean(decode_output(outcome.stdout)),
            stderr=ws.clean(decode_output(outcome.stderr)),
            compile_output=compile_output,
            exit_code=None if outcome.timed_out else outcome.exit_code,
            time_ms=outcome.time_ms,
            memory_kb=outcome.peak_memory_bytes // 1024 if outcome.peak_memory_bytes else None,
            backend=NAME,
            message=_message(outcome, cfg),
            truncated=outcome.output_exceeded,
        )


def _status(outcome) -> Status:
    if outcome.timed_out:
        return Status.TIMEOUT
    if outcome.output_exceeded:
        return Status.OUTPUT_LIMIT
    if outcome.memory_exceeded:
        return Status.MEMORY_LIMIT
    if outcome.exit_code != 0:
        return Status.RUNTIME_ERROR
    return Status.OK


def _message(outcome, cfg: dict) -> str:
    if outcome.timed_out:
        return f"Превышен лимит времени ({cfg['RUN_TIMEOUT']:g} с)"
    if outcome.output_exceeded:
        return f"Слишком много вывода (лимит {cfg['MAX_OUTPUT_BYTES'] // 1024} КБ)"
    if outcome.memory_exceeded:
        return f"Превышен лимит памяти ({cfg['MEMORY_MB']} МБ)"
    if outcome.exit_code != 0:
        return f"Процесс завершился с кодом {outcome.exit_code}"
    return ""
