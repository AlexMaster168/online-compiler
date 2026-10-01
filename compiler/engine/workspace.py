from __future__ import annotations

import locale
import os
import shutil
import stat
import tempfile
import time
from pathlib import Path


def _fallback_encoding() -> str:
    if os.name == "nt":
        try:
            import ctypes
            return f"cp{ctypes.windll.kernel32.GetOEMCP()}"
        except (OSError, AttributeError):
            pass
    return locale.getpreferredencoding(False) or "latin-1"


_FALLBACK = _fallback_encoding()


def decode_output(data: bytes) -> str:
    """UTF-8, а если не декодируется — OEM/локальная кодировка (старые Windows-консольные программы)."""
    if not data:
        return ""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = data.decode(_FALLBACK)
        except (UnicodeDecodeError, LookupError):
            text = data.decode("utf-8", errors="replace")
    return text.replace("\r\n", "\n")


class Workspace:
    """Изолированная временная папка под один запуск. Удаляется при выходе из with."""

    def __init__(self, prefix: str = "oc-"):
        self.path = Path(tempfile.mkdtemp(prefix=prefix)).resolve()
        # Для docker: процесс в контейнере работает под nobody и должен писать в папку
        os.chmod(self.path, 0o777)

    def write(self, name: str, content: str) -> Path:
        target = (self.path / name).resolve()
        if self.path not in target.parents:
            raise ValueError(f"Недопустимое имя файла: {name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode("utf-8"))
        os.chmod(target, 0o666)
        return target

    def clean(self, text: str, container_path: str | None = None) -> str:
        """Прячем пути хоста/контейнера — в трейсбеках остаётся просто main.py."""
        # Сначала длинные варианты с разделителем, иначе останется "\main.py"
        for prefix in (str(self.path) + os.sep, str(self.path) + "/", str(self.path)):
            text = text.replace(prefix, "")
        if container_path:
            text = text.replace(container_path.rstrip("/") + "/", "")
        return text

    def __enter__(self) -> Workspace:
        return self

    def __exit__(self, *exc) -> None:
        # Windows может ещё пару мгновений держать файлы убитого процесса
        for attempt in range(5):
            try:
                shutil.rmtree(self.path, onexc=_force_remove)
                return
            except OSError:
                time.sleep(0.1 * (attempt + 1))
        shutil.rmtree(self.path, ignore_errors=True)


def _force_remove(func, path, _exc) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)
