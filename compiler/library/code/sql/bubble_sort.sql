-- Сортировка пузырьком в SQL: рекурсивный CTE как машина состояний.
-- Состояние — номер прохода i, позиция сравнения j и сам массив (JSON).
-- Каждая строка CTE — одно сравнение соседей и, если нужно, обмен.
-- arr ->> j — элемент массива с индексом j (SQLite 3.38+).
WITH RECURSIVE bubble(i, j, arr) AS (
    SELECT 0, 0, json('[5, 2, 9, 1, 5, 6]')
    UNION ALL
    SELECT
        CASE WHEN j + 1 < json_array_length(arr) - 1 - i THEN i ELSE i + 1 END,
        CASE WHEN j + 1 < json_array_length(arr) - 1 - i THEN j + 1 ELSE 0 END,
        CASE
            WHEN arr ->> j > arr ->> (j + 1)
            THEN json_set(arr, '$[' || j || ']', arr ->> (j + 1), '$[' || (j + 1) || ']', arr ->> j)
            ELSE arr
        END
    FROM bubble
    WHERE i < json_array_length(arr) - 1
)
SELECT 'Sorted: ' || (SELECT group_concat(value, ' ') FROM json_each(arr)) AS result
FROM bubble
WHERE i = json_array_length(arr) - 1;
