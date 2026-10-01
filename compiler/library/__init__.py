"""Библиотека алгоритмов: одни и те же 15 задач на каждом языке.

Код лежит в code/<slug>/<id><расширение главного файла>. У каждой задачи один эталонный вывод
(expected.json) на все языки — по нему `manage.py check_library` и тесты проверяют каждый сниппет.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ..engine.languages import get_language

CODE_DIR = Path(__file__).parent / "code"
EXPECTED_FILE = Path(__file__).parent / "expected.json"


@dataclass(frozen=True)
class Algorithm:
    id: str
    title: str
    category: str
    description: str


CATEGORIES = ("Сортировки", "Поиск", "Математика", "Графы", "Динамическое программирование", "Рекурсия")

ALGORITHMS: tuple[Algorithm, ...] = (
    Algorithm("bubble_sort", "Сортировка пузырьком", "Сортировки",
              "Соседние элементы меняются местами, пока массив не станет упорядоченным. O(n²)"),
    Algorithm("quick_sort", "Быстрая сортировка", "Сортировки",
              "Разбиение Ломуто вокруг опорного элемента и рекурсия по частям. В среднем O(n log n)"),
    Algorithm("merge_sort", "Сортировка слиянием", "Сортировки",
              "Делим массив пополам, сортируем половины и сливаем. Всегда O(n log n), стабильная"),
    Algorithm("binary_search", "Бинарный поиск", "Поиск",
              "Поиск в отсортированном массиве делением отрезка пополам. O(log n)"),
    Algorithm("sieve", "Решето Эратосфена", "Математика",
              "Все простые числа до N: вычёркиваем кратные каждого простого. O(n log log n)"),
    Algorithm("gcd_lcm", "НОД и НОК", "Математика",
              "Алгоритм Евклида для НОД, НОК через НОД: lcm(a, b) = a / gcd(a, b) * b"),
    Algorithm("fibonacci", "Числа Фибоначчи", "Математика",
              "Итеративно, без экспоненциальной рекурсии: первые 15 чисел и F(50)"),
    Algorithm("factorial", "Факториал", "Рекурсия",
              "Рекурсивное определение n! = n · (n − 1)!; 20! ещё помещается в 64 бита"),
    Algorithm("power_mod", "Быстрое возведение в степень", "Математика",
              "a^n по модулю за O(log n): возводим в квадрат и смотрим на биты показателя"),
    Algorithm("bfs", "Поиск в ширину (BFS)", "Графы",
              "Обход графа очередью: порядок обхода и кратчайшие расстояния в рёбрах"),
    Algorithm("dfs", "Поиск в глубину (DFS)", "Графы",
              "Рекурсивный обход графа: идём вглубь, пока есть непосещённые соседи"),
    Algorithm("dijkstra", "Алгоритм Дейкстры", "Графы",
              "Кратчайшие пути во взвешенном графе с неотрицательными весами. Вариант O(V²)"),
    Algorithm("lcs", "Наибольшая общая подпоследовательность", "Динамическое программирование",
              "Таблица dp[i][j] — длина LCS префиксов двух строк. O(n·m)"),
    Algorithm("knapsack", "Рюкзак 0/1", "Динамическое программирование",
              "Максимальная ценность предметов в рюкзаке ограниченной вместимости. O(n·W)"),
    Algorithm("hanoi", "Ханойские башни", "Рекурсия",
              "Перенести n дисков: n − 1 на вспомогательный стержень, самый большой — на целевой, остальные сверху"),
)
BY_ID = {a.id: a for a in ALGORITHMS}


@cache
def expected() -> dict[str, str]:
    return json.loads(EXPECTED_FILE.read_text(encoding="utf-8"))


def extension(slug: str) -> str:
    lang = get_language(slug)
    return Path(lang.filename).suffix if lang else ""


def snippet_path(slug: str, algorithm_id: str) -> Path:
    return CODE_DIR / slug / f"{algorithm_id}{extension(slug)}"


def get_code(slug: str, algorithm_id: str) -> str | None:
    if algorithm_id not in BY_ID or get_language(slug) is None:
        return None
    path = snippet_path(slug, algorithm_id)
    return path.read_text(encoding="utf-8") if path.exists() else None


def catalog(slug: str) -> list[dict]:
    """Задачи, для которых есть код на этом языке, в порядке манифеста."""
    if get_language(slug) is None:
        return []
    return [
        {"id": a.id, "title": a.title, "category": a.category, "description": a.description}
        for a in ALGORITHMS if snippet_path(slug, a.id).exists()
    ]


def normalize_output(text: str) -> str:
    """Сравниваем без хвостовых пробелов строк и пустых строк в конце — их по-разному печатают языки."""
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").strip("\n").split("\n"))


def program_output(slug: str, stdout: str) -> str:
    """Текст, который сверяется с эталоном.

    SQL-раннер печатает результаты SELECT таблицами с рамками — для сверки берём ячейки строк данных
    (первая колонка), а рамки, заголовки и «(N rows)» отбрасываем.
    """
    if slug != "sql":
        return normalize_output(stdout)
    lines, rows, state = stdout.replace("\r\n", "\n").split("\n"), [], "out"
    for line in lines:
        if line.startswith("+"):
            # граница: перед заголовком -> после заголовка -> после данных
            state = {"out": "header", "header_done": "data", "data": "out"}.get(state, state)
        elif line.startswith("|"):
            if state == "header":
                state = "header_done"
            elif state == "data":
                rows.append(line.strip("|").split(" | ")[0].strip())
    return normalize_output("\n".join(rows))
