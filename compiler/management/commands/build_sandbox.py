import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from compiler.engine import docker
from compiler.engine.languages import LANGUAGES

DOCKERFILE_DIRS = {"oc-debug-": docker.SANDBOX_DIR / "debug", "oc-lang-": docker.SANDBOX_DIR / "lang"}


class Command(BaseCommand):
    help = ("Собирает служебные компоненты Docker-песочницы: хелперы консоли (ptyrun, octcp), "
            "свои образы языков (oc-lang-*) и образы отладчиков (oc-debug-*). Для сборки образов нужна сеть.")

    def add_arguments(self, parser):
        parser.add_argument("targets", nargs="*",
                            help="что собрать: extra jvm native python go arduino esp32 (или lang-jvm, debug-jvm); "
                                 "без аргументов — всё")
        parser.add_argument("--no-debug", action="store_true", help="только хелперы, без образов")

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

        images: dict[str, list[str]] = {}
        for lang in LANGUAGES:
            for image in (lang.docker.image if lang.docker else None, lang.debug.image if lang.debug else None):
                if image and docker.is_own_image(image):
                    images.setdefault(image, [])
                    if lang.slug not in images[image]:
                        images[image].append(lang.slug)
        wanted = set(options["targets"])
        images["oc-lang-arduino:1"] = ["arduino"]
        failed = []
        for image, slugs in images.items():
            name = image.split(":")[0]
            prefix = next(p for p in DOCKERFILE_DIRS if name.startswith(p))
            short = name.removeprefix(prefix)
            if wanted and not wanted & {short, name.removeprefix("oc-")}:
                continue
            dockerfile = DOCKERFILE_DIRS[prefix] / f"{short}.Dockerfile"
            if not dockerfile.exists():
                self.stderr.write(f"   нет {dockerfile.name} — пропускаю")
                continue
            kind = "отладка" if prefix == "oc-debug-" else "языки"
            self.stdout.write(f"-> {image} ({kind}: {', '.join(slugs)}) ... ", ending="")
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
