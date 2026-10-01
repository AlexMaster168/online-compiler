-- Бинарный поиск: каждая строка CTE — один шаг сужения отрезка [lo, hi] для своей цели.
-- Обе цели ищутся одновременно, а found заполняется на шаге, где элемент нашёлся.
WITH RECURSIVE
    arr(a) AS (SELECT json('[1, 3, 5, 7, 9, 11, 13, 15, 17, 19]')),
    targets(ord, target) AS (VALUES (1, 7), (2, 4)),
    search(ord, target, lo, hi, found) AS (
        SELECT ord, target, 0, json_array_length(a) - 1, NULL FROM targets, arr
        UNION ALL
        SELECT ord, target,
               CASE WHEN a ->> ((lo + hi) / 2) < target THEN (lo + hi) / 2 + 1 ELSE lo END,
               CASE WHEN a ->> ((lo + hi) / 2) > target THEN (lo + hi) / 2 - 1 ELSE hi END,
               CASE WHEN a ->> ((lo + hi) / 2) = target THEN (lo + hi) / 2 END
        FROM search, arr
        WHERE found IS NULL AND lo <= hi
    )
SELECT CASE WHEN found IS NOT NULL THEN 'Found ' || target || ' at index ' || found
            ELSE target || ' not found' END AS result
FROM search
WHERE found IS NOT NULL OR lo > hi
ORDER BY ord;
