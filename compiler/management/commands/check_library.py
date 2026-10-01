from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from compiler import engine
from compiler.library import ALGORITHMS, expected, get_code, normalize_output, program_output


class Command(BaseCommand):
    help = "Запускает сниппеты библиотеки алгоритмов и сверяет вывод с эталоном (expected.json)."

    def add_arguments(self, parser):
        parser.add_argument("languages", nargs="*", help="slug языков; без аргументов — все")
        parser.add_argument("--algo", action="append", default=[], help="только эти алгоритмы (можно несколько)")
        parser.add_argument("--jobs", type=int, default=settings.EXECUTOR["MAX_CONCURRENT"])

    def handle(self, *args, **options):
        slugs = options["languages"] or [lang.slug for lang in engine.LANGUAGES if lang.library]
        unknown = [s for s in slugs if engine.get_language(s) is None]
        if unknown:
            raise CommandError(f"Неизвестные языки: {', '.join(unknown)}")
        algos = [a.id for a in ALGORITHMS if not options["algo"] or a.id in options["algo"]]
        want = expected()

        jobs, missing = [], []
        for slug in slugs:
            for algo in algos:
                code = get_code(slug, algo)
                if code is None:
                    missing.append(f"{slug}/{algo}")
                else:
                    jobs.append((slug, algo, code))

        def run(job):
            slug, algo, code = job
            return slug, algo, engine.execute(slug, code)

        failed = []
        with ThreadPoolExecutor(max(1, options["jobs"])) as pool:
            for slug, algo, result in pool.map(run, jobs):
                got = program_output(slug, result.stdout)
                ok = result.status == "ok" and got == normalize_output(want[algo])
                if ok:
                    self.stdout.write(self.style.SUCCESS(f"ok   {slug}/{algo}"))
                    continue
                failed.append(f"{slug}/{algo}")
                details = result.message or ""
                if result.status != "ok":
                    details += "\n" + (result.compile_output + result.stderr)[-800:]
                else:
                    details += f"\nожидалось:\n{normalize_output(want[algo])}\nполучено:\n{got[:800]}"
                self.stdout.write(self.style.ERROR(f"FAIL {slug}/{algo} [{result.status}]") + "\n    "
                                  + details.strip().replace("\n", "\n    "))

        self.stdout.write(f"\nПроверено: {len(jobs)}, ошибок: {len(failed)}, нет кода: {len(missing)}")
        if missing:
            self.stdout.write("Нет кода: " + ", ".join(missing))
        if failed:
            raise CommandError("Не прошли: " + ", ".join(failed))
