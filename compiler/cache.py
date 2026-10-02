"""Кеш дорогих чтений поверх Django cache (в проде — Redis, см. REDIS_URL в settings).

Что кешируется:
  * каталог языков — на каждый запрос он опрашивает Docker о наличии образов;
  * библиотека алгоритмов — файлы на диске, меняются только с деплоем;
  * чтение проекта по ссылке и публичный профиль — сбрасываются сигналами при сохранении/удалении.

Кеш — ускорение, а не источник правды: если Redis недоступен, всё считается напрямую,
а сайт продолжает работать (ошибка пишется в лог один раз в минуту, а не на каждый запрос).
"""
from __future__ import annotations

import logging
import time
from typing import Any, Callable

from django.core.cache import cache

log = logging.getLogger(__name__)
_MISSING = object()
_last_error_logged = 0.0

# Сколько живут записи (сек). Каталог языков короткий: образ могли только что скачать.
LANGUAGES_TTL = 15
LIBRARY_TTL = 60 * 60
SNIPPET_TTL = 10 * 60
PROFILE_TTL = 5 * 60


def _log_failure(action: str, exc: Exception) -> None:
    global _last_error_logged
    now = time.monotonic()
    if now - _last_error_logged > 60:
        _last_error_logged = now
        log.warning("Кеш недоступен (%s): %s — работаем без кеша", action, exc)


def safe_get(key: str, default: Any = None) -> Any:
    try:
        return cache.get(key, default)
    except Exception as exc:  # Redis лежит / сеть — это не повод отдавать 500
        _log_failure("get", exc)
        return default


def safe_set(key: str, value: Any, timeout: int) -> None:
    try:
        cache.set(key, value, timeout)
    except Exception as exc:
        _log_failure("set", exc)


def safe_delete(*keys: str) -> None:
    try:
        cache.delete_many(list(keys))
    except Exception as exc:
        _log_failure("delete", exc)


def cached(key: str, timeout: int, produce: Callable[[], Any]) -> Any:
    """Значение из кеша или produce() с записью в кеш. None тоже кешируется."""
    value = safe_get(key, _MISSING)
    if value is _MISSING:
        value = produce()
        safe_set(key, value, timeout)
    return value


def rate_hit(key: str, limit: int, window: int = 60) -> bool:
    """Счётчик запросов в окне; True — лимит превышен. При недоступном кеше лимит не применяем:
    лучше пропустить лишний запуск, чем положить весь сайт вместе с Redis."""
    if limit <= 0:
        return False
    try:
        cache.add(key, 0, timeout=window)
        try:
            return cache.incr(key) > limit
        except ValueError:  # ключ успел истечь между add и incr
            cache.set(key, 1, timeout=window)
            return False
    except Exception as exc:
        _log_failure("rate limit", exc)
        return False


# ---------- ключи ----------

def snippet_key(snippet_id: str) -> str:
    return f"snippet:{snippet_id}"


def profile_key(user_id: int) -> str:
    return f"profile:{user_id}"


def invalidate_snippet(snippet_id: str, owner_id: int | None = None) -> None:
    keys = [snippet_key(snippet_id)]
    if owner_id:
        keys.append(profile_key(owner_id))
    safe_delete(*keys)
