-- Наибольшая общая подпоследовательность: таблица dp заполняется по клетке за шаг CTE.
-- prev — предыдущая строка таблицы, cur — текущая (JSON-массивы), i и j — координаты клетки.
-- Значение клетки: совпали буквы — диагональ + 1, иначе максимум из клетки сверху и слева.
WITH RECURSIVE dp(i, j, prev, cur) AS (
    SELECT 1, 1, json('[0, 0, 0, 0, 0, 0, 0]'), json('[0]')
    UNION ALL
    SELECT
        CASE WHEN j < 6 THEN i ELSE i + 1 END,
        CASE WHEN j < 6 THEN j + 1 ELSE 1 END,
        -- строка закончилась: текущая становится предыдущей
        CASE WHEN j < 6 THEN prev
             ELSE json_insert(cur, '$[#]',
                  CASE WHEN substr('ABCBDAB', i, 1) = substr('BDCABA', j, 1) THEN (prev ->> (j - 1)) + 1
                       ELSE max(prev ->> j, cur ->> (j - 1)) END) END,
        CASE WHEN j < 6
             THEN json_insert(cur, '$[#]',
                  CASE WHEN substr('ABCBDAB', i, 1) = substr('BDCABA', j, 1) THEN (prev ->> (j - 1)) + 1
                       ELSE max(prev ->> j, cur ->> (j - 1)) END)
             ELSE json('[0]') END
    FROM dp
    WHERE i <= 7
)
SELECT 'LCS(ABCBDAB, BDCABA) = ' || (prev ->> 6) AS result
FROM dp
WHERE i = 8;
