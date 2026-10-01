"""Разбор и проверка запросов на запуск — общие для HTTP API и WebSocket-консоли."""
from __future__ import annotations

import json
import shlex
from dataclasses import dataclass, field
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

from . import engine
from .models import Execution


class BadRequest(Exception):
    pass


def json_body(request) -> dict:
    try:
        data = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise BadRequest("Тело запроса должно быть JSON")
    if not isinstance(data, dict):
        raise BadRequest("Ожидается JSON-объект")
    return data


def api(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except BadRequest as exc:
            return JsonResponse({"error": str(exc)}, status=400)
    return wrapper


def no_nul(text: str) -> str:
    """PostgreSQL не хранит NUL-байты в text — а программа вполне может их вывести."""
    return text.replace("\x00", "\\0")


def str_field(data: dict, name: str, *, required: bool = False, max_bytes: int | None = None) -> str:
    value = data.get(name, "")
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise BadRequest(f"Поле {name} должно быть строкой")
    if required and not value.strip():
        raise BadRequest(f"Поле {name} обязательно")
    if max_bytes is not None and len(value.encode("utf-8")) > max_bytes:
        raise BadRequest(f"Поле {name} больше {max_bytes // 1024} КБ")
    return value


def language_field(data: dict) -> str:
    slug = str_field(data, "language", required=True)
    if engine.get_language(slug) is None:
        raise BadRequest(f"Неизвестный язык: {slug}")
    return slug


def files_field(data: dict, slug: str, code: str) -> list[dict]:
    """Дополнительные файлы проекта: [{"name": ..., "content": ...}]."""
    raw = data.get("files") or []
    if not isinstance(raw, list):
        raise BadRequest("Поле files должно быть списком")
    files = []
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) \
                or not isinstance(item.get("content"), str):
            raise BadRequest("Каждый файл — объект со строками name и content")
        files.append({"name": item["name"], "content": no_nul(item["content"])})
    as_dict = {f["name"]: f["content"] for f in files}
    if len(as_dict) != len(files):
        raise BadRequest("Имена файлов повторяются")
    try:
        engine.validate_files(engine.get_language(slug), as_dict, settings.EXECUTOR["MAX_CODE_BYTES"], code)
    except engine.ProjectError as exc:
        raise BadRequest(str(exc))
    return files


MAX_ARGS_CHARS = 1000
MAX_ARGS = 64


def args_field(data: dict) -> tuple[str, list[str]]:
    """Аргументы командной строки строкой, как в шелле: `-n 5 "два слова"` -> ['-n', '5', 'два слова']."""
    raw = str_field(data, "args")
    if len(raw) > MAX_ARGS_CHARS:
        raise BadRequest(f"Аргументы длиннее {MAX_ARGS_CHARS} символов")
    if "\x00" in raw:
        raise BadRequest("В аргументах не может быть NUL")
    try:
        argv = shlex.split(raw, posix=True)
    except ValueError:
        raise BadRequest("В аргументах незакрытая кавычка")
    if len(argv) > MAX_ARGS:
        raise BadRequest(f"Больше {MAX_ARGS} аргументов")
    return raw.strip(), argv


@dataclass
class RunRequest:
    language: str
    code: str
    stdin: str
    files: list[dict]
    args: str = ""
    argv: list[str] = field(default_factory=list)

    @property
    def files_dict(self) -> dict[str, str]:
        return {f["name"]: f["content"] for f in self.files}


def parse_run(data: dict, *, with_stdin: bool = True) -> RunRequest:
    cfg = settings.EXECUTOR
    slug = language_field(data)
    code = str_field(data, "code", required=True, max_bytes=cfg["MAX_CODE_BYTES"])
    stdin = str_field(data, "stdin", max_bytes=cfg["MAX_STDIN_BYTES"]) if with_stdin else ""
    args, argv = args_field(data)
    return RunRequest(slug, code, stdin, files_field(data, slug, code), args, argv)


MAX_BREAKPOINTS_PER_FILE = 200


def parse_breakpoints(data: dict, req: RunRequest) -> dict[str, list[int]]:
    """{"main.py": [3, 7], ...} — только файлы проекта и положительные номера строк."""
    raw = data.get("breakpoints") or {}
    if not isinstance(raw, dict):
        raise BadRequest("Поле breakpoints должно быть объектом {файл: [строки]}")
    project = {engine.get_language(req.language).filename, *req.files_dict}
    result = {}
    for name, lines in raw.items():
        if name not in project:
            continue
        if not isinstance(lines, list) or not all(isinstance(x, int) and not isinstance(x, bool) for x in lines):
            raise BadRequest(f"Строки брейкпоинтов в {name} должны быть числами")
        result[name] = sorted({x for x in lines if x > 0})[:MAX_BREAKPOINTS_PER_FILE]
    return result


def rate_limited(client_ip: str | None, kind: str = "run") -> bool:
    limit = settings.EXECUTOR["RATE_LIMIT_PER_MINUTE"]
    if limit <= 0:
        return False
    key = f"rl:{kind}:{client_ip}"
    cache.add(key, 0, timeout=60)
    try:
        return cache.incr(key) > limit
    except ValueError:
        cache.set(key, 1, timeout=60)
        return False


def save_execution(req: RunRequest, result, *, session_key: str, client_ip: str | None,
                   stdin: str | None = None, user=None) -> Execution:
    return Execution.objects.create(
        language=req.language, code=no_nul(req.code), files=req.files,
        stdin=no_nul(req.stdin if stdin is None else stdin), args=req.args,
        status=str(result.status),
        stdout=no_nul(result.stdout), stderr=no_nul(result.stderr),
        compile_output=no_nul(result.compile_output), message=result.message[:500],
        exit_code=result.exit_code, time_ms=result.time_ms, memory_kb=result.memory_kb,
        backend=result.backend, truncated=result.truncated,
        session_key=session_key, client_ip=client_ip,
        user=user if user is not None and user.is_authenticated else None,
    )
