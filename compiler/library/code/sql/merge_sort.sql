-- Сортировка слиянием снизу вверх: серии ширины w = 1, 2, 4, ... сливаются попарно.
-- Переносим по одному элементу из массива a в буфер b двумя чередующимися шагами:
--   choose — решаем, откуда брать: t = 1 из левой серии, t = 0 из правой;
--   apply  — переносим элемент и двигаем указатели (lo — начало пары, i и j — указатели в сериях).
-- Когда проход закончен, буфер становится массивом, а ширина серий удваивается.
WITH RECURSIVE
    input(n) AS (SELECT 7),
    ms(phase, t, w, lo, i, j, a, b) AS (
        SELECT 'choose', NULL, 1, 0, 0, 1, json('[38, 27, 43, 3, 9, 82, 10]'), json('[]')
        UNION ALL
        SELECT
            CASE phase WHEN 'choose' THEN 'apply' ELSE 'choose' END,
            -- choose: из левой серии, если она не кончилась и (правая кончилась или слева не больше)
            CASE phase WHEN 'choose'
                THEN (i < min(lo + w, n) AND (j >= min(lo + 2 * w, n) OR a ->> i <= a ->> j)) END,
            -- ширина: удваиваем, когда закончилась последняя пара прохода
            CASE WHEN phase = 'apply' AND lo + 2 * w >= n
                      AND i + t >= min(lo + w, n) AND j + 1 - t >= min(lo + 2 * w, n)
                 THEN 2 * w ELSE w END,
            -- начало пары, указатели i и j
            CASE WHEN phase = 'choose' OR NOT (i + t >= min(lo + w, n) AND j + 1 - t >= min(lo + 2 * w, n)) THEN lo
                 WHEN lo + 2 * w >= n THEN 0
                 ELSE lo + 2 * w END,
            CASE WHEN phase = 'choose' THEN i
                 WHEN NOT (i + t >= min(lo + w, n) AND j + 1 - t >= min(lo + 2 * w, n)) THEN i + t
                 WHEN lo + 2 * w >= n THEN 0
                 ELSE lo + 2 * w END,
            CASE WHEN phase = 'choose' THEN j
                 WHEN NOT (i + t >= min(lo + w, n) AND j + 1 - t >= min(lo + 2 * w, n)) THEN j + 1 - t
                 WHEN lo + 2 * w >= n THEN min(2 * w, n)
                 ELSE min(lo + 3 * w, n) END,
            -- массив: после прохода его заменяет буфер с последним элементом
            CASE WHEN phase = 'apply' AND lo + 2 * w >= n
                      AND i + t >= min(lo + w, n) AND j + 1 - t >= min(lo + 2 * w, n)
                 THEN json_insert(b, '$[#]', CASE WHEN t THEN a ->> i ELSE a ->> j END)
                 ELSE a END,
            -- буфер: дописываем выбранный элемент, после прохода очищаем
            CASE WHEN phase = 'choose' THEN b
                 WHEN lo + 2 * w >= n AND i + t >= min(lo + w, n) AND j + 1 - t >= min(lo + 2 * w, n)
                 THEN json('[]')
                 ELSE json_insert(b, '$[#]', CASE WHEN t THEN a ->> i ELSE a ->> j END) END
        FROM ms, input
        WHERE w < n
    )
SELECT 'Sorted: ' || (SELECT group_concat(value, ' ') FROM json_each(a)) AS result
FROM ms, input
WHERE w >= n AND phase = 'choose';
