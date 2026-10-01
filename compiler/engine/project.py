"""Мультифайловые проекты: проверка имён и состава дополнительных файлов."""
from __future__ import annotations

import re

from .languages import Language

MAX_FILES = 20
MAX_DEPTH = 4
_SEGMENT = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.+-]{0,63}$")
# Имена, которые движок создаёт сам: бинарник, артефакты сборки, служебные файлы
_RESERVED = {"main", "main.exe", "main.jar", "out", "obj", "bin", "main.csproj", "__utf8console.cs"}


class ProjectError(ValueError):
    pass


def validate_files(lang: Language, files: dict[str, str], max_bytes: int, main_code: str = "") -> None:
    if len(files) > MAX_FILES:
        raise ProjectError(f"Максимум {MAX_FILES} дополнительных файлов")

    reserved = _RESERVED | {name.lower() for name, _ in lang.extra_files}
    seen: dict[str, str] = {lang.filename.lower(): lang.filename}
    total = len(main_code.encode("utf-8"))

    for name, content in files.items():
        if not isinstance(name, str) or not isinstance(content, str):
            raise ProjectError("Файл должен быть парой name/content со строками")
        parts = name.split("/")
        if len(parts) > MAX_DEPTH or not all(_SEGMENT.match(p) for p in parts):
            raise ProjectError(
                f"Недопустимое имя файла «{name}»: латиница, цифры, _ . + -, папки через /, "
                f"не больше {MAX_DEPTH} уровней")
        if parts[0].lower() in reserved:
            raise ProjectError(f"Имя «{name}» зарезервировано движком")
        key = name.lower()
        if key in seen:
            raise ProjectError(f"Файл «{name}» уже есть в проекте")
        seen[key] = name
        total += len(content.encode("utf-8"))

    # a.py и a.py/b.py одновременно не создать: один и тот же путь не может быть файлом и папкой
    for key in seen:
        prefix = key.split("/")
        for depth in range(1, len(prefix)):
            if "/".join(prefix[:depth]) in seen:
                raise ProjectError(f"«{'/'.join(prefix[:depth])}» не может быть одновременно файлом и папкой")

    if total > max_bytes:
        raise ProjectError(f"Проект больше {max_bytes // 1024} КБ")
