from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from compiler.engine import LANGUAGES, docker


class Command(BaseCommand):
    help = "Скачивает Docker-образы для языков. Без аргументов — все."

    def add_arguments(self, parser):
        parser.add_argument("languages", nargs="*", help="slug языков, например: python cpp go")

    def handle(self, *args, **options):
        cfg = settings.EXECUTOR
        if not docker.daemon_available(cfg, ttl=0):
            raise CommandError("Docker-демон недоступен — запусти Docker Desktop")
        wanted = set(options["languages"])
        unknown = wanted - {lang.slug for lang in LANGUAGES}
        if unknown:
            raise CommandError(f"Неизвестные языки: {', '.join(sorted(unknown))}")

        images = sorted({lang.docker.image for lang in LANGUAGES
                         if lang.docker and (not wanted or lang.slug in wanted)})
        own = [image for image in images if docker.is_own_image(image)]
        images = [image for image in images if not docker.is_own_image(image)]
        if own:
            self.stdout.write(f"Свои образы ({', '.join(own)}) не качаются, а собираются: "
                              "python manage.py build_sandbox")
        failed = []
        for image in images:
            self.stdout.write(f"→ {image} ... ", ending="")
            self.stdout.flush()
            ok, output = docker.pull(image, cfg)
            if ok:
                self.stdout.write(self.style.SUCCESS("ok"))
            else:
                failed.append(image)
                self.stdout.write(self.style.ERROR("FAIL"))
                self.stderr.write(output[-500:])
        if failed:
            raise CommandError(f"Не скачались: {', '.join(failed)}")
