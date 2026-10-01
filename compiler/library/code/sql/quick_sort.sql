-- Быстрая сортировка в SQL: каждая строка CTE — отрезок массива и «путь» к нему в дереве рекурсии.
-- Отрезок делится на три: меньше опоры (путь + '0'), сама опора ('1'), не меньше опоры ('2').
-- Отрезки из одного элемента, упорядоченные по пути, — это и есть отсортированный массив.
WITH RECURSIVE qs(path, seg) AS (
    SELECT '', json('[10, 7, 8, 9, 1, 5, 3]')
    UNION ALL
    SELECT path || '0',
           (SELECT json_group_array(value) FROM json_each(seg) WHERE key > 0 AND value < seg ->> 0)
    FROM qs WHERE json_array_length(seg) > 1
    UNION ALL
    SELECT path || '1', json_array(seg ->> 0)
    FROM qs WHERE json_array_length(seg) > 1
    UNION ALL
    SELECT path || '2',
           (SELECT json_group_array(value) FROM json_each(seg) WHERE key > 0 AND value >= seg ->> 0)
    FROM qs WHERE json_array_length(seg) > 1
)
SELECT 'Sorted: ' || group_concat(seg ->> 0, ' ') AS result
FROM (SELECT seg FROM qs WHERE json_array_length(seg) = 1 ORDER BY path);
