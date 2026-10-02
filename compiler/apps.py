from django.apps import AppConfig


class CompilerConfig(AppConfig):
    name = "compiler"

    def ready(self):
        from . import signals  # noqa: F401 — регистрирует сброс кеша при изменении проектов
