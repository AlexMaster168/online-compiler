import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from compiler.engine import docker
from compiler.engine.languages import LANGUAGES

DEBUG_DIR = docker.SANDBOX_DIR / "debug"


class Command(BaseCommand):
    help = ("Собирает служебные компоненты Docker-песочницы: хелперы консоли (ptyrun, octcp) "
            "и образы отладчиков (debugpy, gdb, delve, JDI). Для сборки образов нужна сеть.")

    def add_arguments(self, parser):
        parser.add_argument("targets", nargs="*",
                            help="что собрать: python native go jvm kotlin; без аргументов — всё")
        parser.add_argument("--no-debug", action="store_true", help="только хелперы, без образов отладчиков")

    def handle(self, *args, **options):
        cfg = settings.EXECUTOR
        if not docker.daemon_available(cfg, ttl=0):
            raise CommandError("Docker-демон недоступен — запусти Docker Desktop")

        self.stdout.write("-> хелперы (ptyrun, octcp) ... ", ending="")
        self.stdout.flush()
        ok, message = docker.ensure_helpers(cfg)
        if not ok:
            self.stdout.write(self.style.ERROR("FAIL"))
            raise CommandError(message)
        self.stdout.write(self.style.SUCCESS(message))
        if options["no_debug"]:
            return

        images = {}
        for lang in LANGUAGES:
            if lang.debug:
                images.setdefault(lang.debug.image, []).append(lang.slug)
        wanted = set(options["targets"])
        failed = []
        for image, slugs in images.items():
            target = image.split(":")[0].removeprefix("oc-debug-")
            if wanted and target not in wanted:
                continue
            dockerfile = DEBUG_DIR / f"{target}.Dockerfile"
            if not dockerfile.exists():
                self.stderr.write(f"   нет {dockerfile.name} — пропускаю")
                continue
            self.stdout.write(f"-> {image} (отладка: {', '.join(slugs)}) ... ", ending="")
            self.stdout.flush()
            proc = subprocess.run(
                [docker._docker(cfg), "build", "-q", "-f", str(dockerfile), "-t", image, str(docker.SANDBOX_DIR)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            if proc.returncode == 0:
                self.stdout.write(self.style.SUCCESS("ok"))
            else:
                failed.append(image)
                self.stdout.write(self.style.ERROR("FAIL"))
                self.stderr.write((proc.stdout + proc.stderr)[-1500:])
        if failed:
            raise CommandError(f"Не собрались: {', '.join(failed)}")
