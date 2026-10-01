"""Beautify на сервере — для языков, у которых нет WASM-форматтера для браузера (Rust, Elixir).

Форматтер запускается в той же песочнице, что и код: без сети, read-only, nobody. Код идёт на stdin,
отформатированный — из stdout. Большинство языков форматируются прямо в браузере (см. app.js).
"""
from __future__ import annotations

import uuid

from . import docker
from .languages import FormatSpec, get_language
from .process import run_limited
from .workspace import Workspace

FORMAT_TIMEOUT = 20


class FormatError(Exception):
    pass


def server_formatter(slug: str) -> FormatSpec | None:
    lang = get_language(slug)
    return lang.formatter if lang and isinstance(lang.formatter, FormatSpec) else None


def format_code(slug: str, code: str, cfg: dict) -> str:
    lang = get_language(slug)
    spec = server_formatter(slug)
    if spec is None:
        raise FormatError(f"Для {lang.name if lang else slug} серверного форматтера нет")
    if not docker.daemon_available(cfg):
        raise FormatError("Для форматирования нужен Docker")
    if not docker.image_present(spec.image, cfg):
        hint = "build_sandbox native" if spec.image.startswith("oc-") else f"pull_images {slug}"
        raise FormatError(f"Образ форматтера {spec.image} не собран: python manage.py {hint}")

    name = f"oc-fmt-{uuid.uuid4().hex[:12]}"
    with Workspace() as ws:
        argv = docker._base_argv(lang, ws, name, cfg, memory_mb=512) + [spec.image, "sh", "-c", spec.command]
        try:
            outcome = run_limited(argv, cwd=str(ws.path), stdin=code.encode("utf-8"),
                                  timeout=FORMAT_TIMEOUT, max_output=cfg["MAX_CODE_BYTES"] * 2)
        finally:
            docker.kill_container(name, cfg)
    if outcome.timed_out:
        raise FormatError(f"Форматтер не уложился в {FORMAT_TIMEOUT} с")
    if outcome.exit_code != 0 or outcome.output_exceeded:
        err = outcome.stderr.decode("utf-8", "replace").strip() or outcome.stdout.decode("utf-8", "replace").strip()
        raise FormatError("Не удалось отформатировать — в коде синтаксическая ошибка?\n" + err[-1500:])
    return outcome.stdout.decode("utf-8", "replace")
