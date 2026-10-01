"""Собственный движок исполнения кода (без Judge0/Piston и прочих готовых API).

    from compiler.engine import execute
    result = execute("python", "print(1)", stdin="")
"""
from __future__ import annotations

import logging
import threading

from django.conf import settings

from . import docker, local
from .languages import LANGUAGES, FormatSpec, Language, get_language
from .project import ProjectError, validate_files
from .result import ExecutionResult, Status

__all__ = ["execute", "language_catalog", "pick_backend", "ExecutionResult", "Status", "LANGUAGES", "get_language",
           "ProjectError", "validate_files"]

log = logging.getLogger(__name__)

_semaphore: threading.BoundedSemaphore | None = None
_semaphore_lock = threading.Lock()


def config() -> dict:
    return settings.EXECUTOR


def _slots() -> threading.BoundedSemaphore:
    global _semaphore
    with _semaphore_lock:
        if _semaphore is None:
            _semaphore = threading.BoundedSemaphore(config()["MAX_CONCURRENT"])
        return _semaphore


def pick_backend(lang: Language, cfg: dict | None = None) -> str | None:
    """docker надёжнее (песочница), поэтому в режиме auto он приоритетнее локального."""
    cfg = cfg or config()
    mode = cfg["BACKEND"]
    if mode in ("auto", "docker") and docker.is_available(lang, cfg):
        return docker.NAME
    if mode in ("auto", "local") and local.is_available(lang):
        return local.NAME
    return None


def language_catalog() -> list[dict]:
    from .debugger import debug_backend  # поздний импорт: debugger импортирует этот пакет
    cfg = config()
    catalog = []
    for lang in LANGUAGES:
        backend = pick_backend(lang, cfg)
        catalog.append({
            "slug": lang.slug,
            "name": lang.name,
            "version": lang.version,
            "monaco": lang.monaco,
            "filename": lang.filename,
            "template": lang.template,
            "compiled": lang.compiled,
            "sources": list(lang.sources),
            "backend": backend,
            "available": backend is not None,
            "debug_backend": debug_backend(lang, cfg),
            "debuggable": debug_backend(lang, cfg) is not None,
            "formatter": "server" if isinstance(lang.formatter, FormatSpec) else lang.formatter,
        })
    return catalog


def _unavailable_message(lang: Language, cfg: dict) -> str:
    hints = []
    if lang.docker and cfg["BACKEND"] in ("auto", "docker"):
        if not docker.daemon_available(cfg):
            hints.append("запусти Docker")
        else:
            hints.append(f"скачай образ: python manage.py pull_images {lang.slug}")
    if lang.local and cfg["BACKEND"] in ("auto", "local"):
        hints.append("или установи локальный тулчейн")
    return f"{lang.name} сейчас недоступен — " + " ".join(hints) if hints else f"{lang.name} недоступен"


def execute(slug: str, code: str, stdin: str = "", files: dict[str, str] | None = None,
            args: list[str] | None = None) -> ExecutionResult:
    """files — дополнительные файлы проекта {путь: содержимое}, главный файл передаётся в code;
    args — аргументы командной строки программы."""
    cfg = config()
    lang = get_language(slug)
    if lang is None:
        return ExecutionResult(Status.UNAVAILABLE, message=f"Неизвестный язык: {slug}")
    if len(code.encode("utf-8")) > cfg["MAX_CODE_BYTES"]:
        return ExecutionResult(Status.INTERNAL_ERROR, message=f"Код больше {cfg['MAX_CODE_BYTES'] // 1024} КБ")
    files = files or {}
    try:
        validate_files(lang, files, cfg["MAX_CODE_BYTES"], code)
    except ProjectError as exc:
        return ExecutionResult(Status.INTERNAL_ERROR, message=str(exc))
    if len(stdin.encode("utf-8")) > cfg["MAX_STDIN_BYTES"]:
        return ExecutionResult(Status.INTERNAL_ERROR, message=f"Ввод больше {cfg['MAX_STDIN_BYTES'] // 1024} КБ")

    backend = pick_backend(lang, cfg)
    if backend is None:
        return ExecutionResult(Status.UNAVAILABLE, message=_unavailable_message(lang, cfg))

    slots = _slots()
    if not slots.acquire(timeout=30):
        return ExecutionResult(Status.UNAVAILABLE, backend=backend,
                               message="Сервер перегружен, попробуй через пару секунд")
    try:
        runner = docker if backend == docker.NAME else local
        return runner.execute(lang, code, stdin, lang.config(cfg), files, args or [])
    except Exception as exc:  # движок не должен ронять запрос — отдаём диагностику
        log.exception("Execution failed for %s via %s", slug, backend)
        return ExecutionResult(Status.INTERNAL_ERROR, backend=backend, message=f"Внутренняя ошибка движка: {exc}")
    finally:
        slots.release()
