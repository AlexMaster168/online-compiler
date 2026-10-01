"""Библиотека алгоритмов: полнота (каждый язык × каждая задача), API и разбор вывода SQL.

Сами сниппеты исполняет `manage.py check_library` — это ~600 запусков в песочнице. В тестах полный
прогон включается переменной окружения OC_LIBRARY_FULL=1, иначе гоняем по одному языку каждого типа.
"""
import os

from django.test import SimpleTestCase, TestCase

from . import engine, library
from .engine import docker
from .library import ALGORITHMS, expected, get_code, normalize_output, program_output


class LibraryCompletenessTests(SimpleTestCase):
    def test_every_language_has_every_algorithm(self):
        missing = [f"{lang.slug}/{a.id}" for lang in engine.LANGUAGES if lang.library for a in ALGORITHMS
                   if get_code(lang.slug, a.id) is None]
        self.assertEqual(missing, [])

    def test_manifest_and_expected_agree(self):
        self.assertEqual(set(expected()), {a.id for a in ALGORITHMS})
        self.assertEqual({a.category for a in ALGORITHMS}, set(library.CATEGORIES))

    def test_snippets_are_clean_text(self):
        for lang in engine.LANGUAGES:
            if not lang.library:
                continue
            for a in ALGORITHMS:
                code = get_code(lang.slug, a.id)
                self.assertNotIn("\r", code, f"{lang.slug}/{a.id}: CRLF")
                self.assertTrue(code.endswith("\n"), f"{lang.slug}/{a.id}: нет перевода строки в конце")
                self.assertNotIn("\t\n", code)

    def test_unknown_inputs(self):
        self.assertIsNone(get_code("python", "nope"))
        self.assertIsNone(get_code("nope", "bfs"))
        self.assertIsNone(get_code("python", "../../settings"))
        self.assertEqual(library.catalog("nope"), [])


class SqlOutputTests(SimpleTestCase):
    def test_table_cells_are_extracted(self):
        stdout = ("+--------------+\n| result       |\n+--------------+\n| GCD = 6      |\n| LCM = 144    |\n"
                  "+--------------+\n(2 rows)\n\n"
                  "+--------+\n| result |\n+--------+\n| x      |\n+--------+\n(1 rows)\n")
        self.assertEqual(program_output("sql", stdout), "GCD = 6\nLCM = 144\nx")

    def test_other_languages_only_normalize(self):
        self.assertEqual(program_output("python", "a  \r\nb\n\n"), "a\nb")
        self.assertEqual(normalize_output("\nx\n"), "x")


class LibraryApiTests(TestCase):
    def test_index(self):
        data = self.client.get("/api/library/?language=rust").json()
        self.assertEqual(len(data["items"]), len(ALGORITHMS))
        self.assertEqual(data["items"][0]["id"], "bubble_sort")
        self.assertEqual(data["categories"][0], "Сортировки")
        self.assertEqual(self.client.get("/api/library/?language=nope").status_code, 400)

    def test_item(self):
        data = self.client.get("/api/library/cobol/hanoi/").json()
        self.assertEqual(data["title"], "Ханойские башни")
        self.assertIn("RECURSIVE", data["code"])
        self.assertEqual(self.client.get("/api/library/cobol/nope/").status_code, 404)
        self.assertEqual(self.client.get("/api/library/nope/hanoi/").status_code, 404)


# Представители разных механизмов запуска: интерпретатор, компилятор, JVM, .NET, свой образ, SQL
SAMPLE_LANGUAGES = ["python", "c", "java", "csharp", "cobol", "sql"]
FULL = os.environ.get("OC_LIBRARY_FULL") == "1"


def _available(slug: str) -> bool:
    return docker.is_available(engine.get_language(slug), engine.config())


class LibraryRunTests(SimpleTestCase):
    """Сниппеты действительно печатают эталон. Полный прогон — OC_LIBRARY_FULL=1 (или check_library)."""

    def check_language(self, slug):
        failures = []
        for algorithm in ALGORITHMS:
            result = engine.execute(slug, get_code(slug, algorithm.id))
            got = program_output(slug, result.stdout)
            if result.status != "ok" or got != normalize_output(expected()[algorithm.id]):
                failures.append(f"{algorithm.id}: {result.status} {got[:200]!r} {result.message}")
        self.assertEqual(failures, [], slug)

    def test_languages(self):
        slugs = [lang.slug for lang in engine.LANGUAGES if lang.library] if FULL else SAMPLE_LANGUAGES
        checked = 0
        for slug in slugs:
            if not _available(slug):
                continue  # без образа язык не проверить — это не провал библиотеки
            with self.subTest(slug):
                self.check_language(slug)
            checked += 1
        if not checked:
            self.skipTest("нет Docker-образов ни для одного языка")


class TemplateRunTests(SimpleTestCase):
    """Шаблон «Привет, мир!» каждого языка компилируется и запускается в песочнице."""

    def test_every_template_runs(self):
        failures, checked = [], 0
        for lang in engine.LANGUAGES:
            if lang.slug == "esp32":
                continue  # Firmware template is a persistent server, tested through its interactive session.
            if not _available(lang.slug):
                continue
            result = engine.execute(lang.slug, lang.template)
            checked += 1
            # SQL печатает таблицу пользователей, остальные — приветствие
            marker = "Лёха" if lang.slug == "sql" else "Привет"
            if result.status != "ok" or marker not in result.stdout:
                failures.append(f"{lang.slug}: {result.status} {result.message} {result.compile_output[-200:]}")
        if not checked:
            self.skipTest("нет Docker-образов")
        self.assertEqual(failures, [])
