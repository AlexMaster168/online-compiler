-- Рюкзак 0/1: dp — JSON-массив, dp[c] — лучшая ценность при вместимости c.
-- Шаг CTE обновляет одну клетку dp[c] для предмета i; c идёт сверху вниз, чтобы брать предмет один раз.
CREATE TABLE items (idx INTEGER PRIMARY KEY, w INTEGER, v INTEGER);
INSERT INTO items VALUES (1, 1, 1), (2, 3, 4), (3, 4, 5), (4, 5, 7);

WITH RECURSIVE ks(i, c, dp) AS (
    SELECT 1, 7, json('[0, 0, 0, 0, 0, 0, 0, 0]')
    UNION ALL
    SELECT
        CASE WHEN ks.c - 1 >= items.w THEN ks.i ELSE ks.i + 1 END,
        CASE WHEN ks.c - 1 >= items.w THEN ks.c - 1 ELSE 7 END,
        json_set(ks.dp, '$[' || ks.c || ']', max(ks.dp ->> ks.c, (ks.dp ->> (ks.c - items.w)) + items.v))
    FROM ks
    JOIN items ON items.idx = ks.i
)
SELECT 'Knapsack max value: ' || (dp ->> 7) AS result
FROM ks
WHERE i = 5;
