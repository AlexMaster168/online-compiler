"""Check standalone ESP32 example C syntax against the real oc_hw.h interface (Docker gcc:14)."""
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compiler.library.esp32 import PROJECTS  # noqa: E402

header = Path(__file__).resolve().parents[1] / 'compiler/engine/sandbox/esp32/main/oc_hw.h'
with tempfile.TemporaryDirectory(prefix='oc-esp32-syntax-') as directory:
    root = Path(directory)
    (root / 'oc_hw.h').write_text(header.read_text(encoding='utf-8'), encoding='utf-8')
    for project in PROJECTS:
        (root / f"{project['id']}.c").write_text(project['code'], encoding='utf-8')
    subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--read-only',
                    '-v', f'{root}:/work:ro', 'gcc:14', 'sh', '-c',
                    'gcc -std=c11 -Wall -Wextra -Werror -fsyntax-only -I/work /work/*.c'], check=True)
print(f'{len(PROJECTS)} ESP32 source examples: C syntax and oc_hw.h signatures OK')
