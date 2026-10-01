import secrets
import string

from django.conf import settings
from django.db import models

from .engine.languages import LANGUAGES

LANGUAGE_CHOICES = [(lang.slug, lang.name) for lang in LANGUAGES]
_ALPHABET = string.ascii_letters + string.digits


def short_id() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(10))


class Snippet(models.Model):
    """Проект с короткой ссылкой /s/<id>/.

    Без владельца — анонимный снимок, неизменяемый. С владельцем — проект из «Моих проектов»:
    владелец сохраняет его на месте (ссылка не меняется), остальные могут только форкнуть.
    """

    id = models.CharField(primary_key=True, max_length=16, default=short_id, editable=False)
    title = models.CharField("название", max_length=200, blank=True)
    language = models.CharField("язык", max_length=32, choices=LANGUAGE_CHOICES)
    code = models.TextField("код")
    # Дополнительные файлы проекта: [{"name": "utils.py", "content": "..."}]
    files = models.JSONField("файлы", default=list, blank=True)
    stdin = models.TextField("ввод", blank=True)
    args = models.CharField("аргументы", max_length=1000, blank=True)
    views = models.PositiveIntegerField("просмотры", default=0)
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="владелец", null=True, blank=True,
                              on_delete=models.CASCADE, related_name="snippets")
    forked_from = models.ForeignKey("self", verbose_name="форк от", null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="forks")
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["owner", "-updated_at"])]
        verbose_name = "сниппет"
        verbose_name_plural = "сниппеты"

    def __str__(self) -> str:
        return self.title or f"{self.get_language_display()} · {self.id}"

    def summary(self) -> dict:
        """Карточка для списка «Мои проекты» — без кода."""
        return {
            "id": self.id,
            "title": self.title,
            "language": self.language,
            "file_count": 1 + len(self.files),
            "views": self.views,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "url": f"/s/{self.id}/",
        }

    def to_dict(self, user=None) -> dict:
        source = self.forked_from
        return {
            **self.summary(),
            "code": self.code,
            "files": self.files,
            "stdin": self.stdin,
            "args": self.args,
            "owner": self.owner.get_username() if self.owner_id else None,
            "is_owner": bool(self.owner_id and user is not None and user.pk == self.owner_id),
            "forked_from": {
                "id": source.id, "title": source.title, "url": f"/s/{source.id}/",
                "owner": source.owner.get_username() if source.owner_id else None,
            } if source else None,
            "forks": self.forks.count(),
        }


class Execution(models.Model):
    """Каждый запуск кода — для истории и статистики."""

    class Status(models.TextChoices):
        OK = "ok", "Успешно"
        COMPILE_ERROR = "compile_error", "Ошибка компиляции"
        RUNTIME_ERROR = "runtime_error", "Ошибка выполнения"
        TIMEOUT = "timeout", "Превышено время"
        MEMORY_LIMIT = "memory_limit", "Превышена память"
        OUTPUT_LIMIT = "output_limit", "Слишком много вывода"
        STOPPED = "stopped", "Остановлено"
        UNAVAILABLE = "unavailable", "Недоступно"
        INTERNAL_ERROR = "internal_error", "Внутренняя ошибка"

    language = models.CharField("язык", max_length=32, choices=LANGUAGE_CHOICES, db_index=True)
    code = models.TextField("код")
    files = models.JSONField("файлы", default=list, blank=True)
    stdin = models.TextField("ввод", blank=True)
    args = models.CharField("аргументы", max_length=1000, blank=True)
    status = models.CharField("статус", max_length=32, choices=Status.choices, db_index=True)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    compile_output = models.TextField(blank=True)
    message = models.CharField(max_length=500, blank=True)
    exit_code = models.BigIntegerField(null=True, blank=True)  # на Windows коды бывают > 2^31
    time_ms = models.PositiveIntegerField("время, мс", null=True, blank=True)
    memory_kb = models.PositiveIntegerField("память, КБ", null=True, blank=True)
    backend = models.CharField(max_length=16, blank=True)
    truncated = models.BooleanField(default=False)
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="executions")
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField("запущен", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "запуск"
        verbose_name_plural = "запуски"
        indexes = [models.Index(fields=["session_key", "-created_at"])]

    def __str__(self) -> str:
        return f"#{self.pk} {self.language} {self.status}"

    def summary(self) -> dict:
        first_line = next((line for line in self.code.splitlines() if line.strip()), "")
        return {
            "id": self.pk,
            "language": self.language,
            "status": self.status,
            "time_ms": self.time_ms,
            "preview": first_line.strip()[:80],
            "file_count": 1 + len(self.files),
            "created_at": self.created_at.isoformat(),
        }

    def to_dict(self) -> dict:
        return {
            **self.summary(),
            "code": self.code,
            "files": self.files,
            "stdin": self.stdin,
            "args": self.args,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "compile_output": self.compile_output,
            "message": self.message,
            "exit_code": self.exit_code,
            "memory_kb": self.memory_kb,
            "backend": self.backend,
            "truncated": self.truncated,
        }
