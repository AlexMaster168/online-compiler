import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from compiler.engine import docker

SCRATCH_DIR = Path(__file__).resolve().parents[2] / "static" / "scratch"

# Собираем официальный open-source редактор Scratch 3 (scratch-gui) из исходников в контейнере node:20.
# Единственная правка исходников: виртуальная машина Scratch становится доступна как window.ocVM —
# через неё страница /scratch/ загружает проект в редактор и забирает .sb3 для сохранения.
BUILD_SCRIPT = r"""
set -e
git clone --depth 1 --branch develop https://github.com/scratchfoundation/scratch-gui /src
cd /src
PATCH='if (typeof window !== "undefined") window.ocVM = defaultVM;'
sed -i "/^defaultVM.attachStorage(storage);/a $PATCH" src/reducers/vm.js
grep -q 'window.ocVM' src/reducers/vm.js || { echo 'не удалось пропатчить vm.js'; exit 1; }
npm ci --no-audit --no-fund
NODE_OPTIONS=--max-old-space-size=4096 npm run build
rm -rf /out/*
cp -r build/. /out/
# Source maps и демо-страницы (blocks-only, player, compatibility-testing) не нужны: 274 МБ -> ~96 МБ
find /out -name '*.map' -delete
rm -f /out/blocks-only.html /out/blocksonly.js /out/compatibility-testing.html /out/compatibilitytesting.js \
      /out/player.html /out/player.js
"""


class Command(BaseCommand):
    help = ("Собирает редактор Scratch 3 (scratch-gui) из исходников в compiler/static/scratch/. "
            "Нужны Docker и сеть, сборка идёт 10–20 минут.")

    def handle(self, *args, **options):
        cfg = settings.EXECUTOR
        if not docker.daemon_available(cfg, ttl=0):
            raise CommandError("Docker-демон недоступен — запусти Docker Desktop")
        SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        self.stdout.write(f"-> scratch-gui -> {SCRATCH_DIR} (долго: npm ci + webpack) ...")
        self.stdout.flush()
        proc = subprocess.run(
            [docker._docker(cfg), "run", "--rm", "-v", f"{SCRATCH_DIR}:/out", "node:20", "bash", "-c", BUILD_SCRIPT],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0 or not (SCRATCH_DIR / "index.html").exists():
            self.stderr.write((proc.stdout + proc.stderr)[-3000:])
            raise CommandError("Сборка Scratch не удалась")
        self.stdout.write(self.style.SUCCESS("ok: " + ", ".join(sorted(p.name for p in SCRATCH_DIR.iterdir())[:8])))
