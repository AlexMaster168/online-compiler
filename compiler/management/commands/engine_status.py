from django.conf import settings
from django.core.management.base import BaseCommand

from compiler.engine import LANGUAGES, docker, local, pick_backend


class Command(BaseCommand):
    help = "Показывает, какие языки доступны и через какой бэкенд они запустятся."

    def handle(self, *args, **options):
        cfg = settings.EXECUTOR
        daemon = docker.daemon_available(cfg, ttl=0)
        self.stdout.write(f"Режим: {cfg['BACKEND']}   Docker-демон: {'да' if daemon else 'нет'}\n")
        self.stdout.write(f"{'язык':<12}{'бэкенд':<9}{'docker-образ':<48}локально")
        for lang in LANGUAGES:
            image = lang.docker.image if lang.docker else "-"
            if lang.docker and daemon:
                image += " ✓" if docker.image_present(lang.docker.image, cfg) else " (не скачан)"
            backend = pick_backend(lang, cfg) or "—"
            style = self.style.SUCCESS if backend != "—" else self.style.WARNING
            self.stdout.write(style(
                f"{lang.slug:<12}{backend:<9}{image:<48}{'да' if local.is_available(lang) else 'нет'}"))
